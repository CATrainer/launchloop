"""
Webhook handlers for external services (primarily Stripe)
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
import logging

from app.config import settings
from app.database import get_db
from app.models.user import User, SubscriptionStatus, PaymentStatus, Tier
from app.models.project import Project, ProjectStatus
from datetime import datetime, timedelta

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events
    Validates signature and processes subscription events
    """
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not sig_header:
        raise HTTPException(400, "Missing stripe-signature header")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid Stripe webhook payload")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe webhook signature")
        raise HTTPException(400, "Invalid signature")
    
    # Handle different event types
    event_type = event["type"]
    event_data = event["data"]["object"]
    
    logger.info(f"Received Stripe webhook: {event_type}")
    
    try:
        if event_type == "customer.subscription.created":
            handle_subscription_created(db, event_data)
        
        elif event_type == "customer.subscription.updated":
            handle_subscription_updated(db, event_data)
        
        elif event_type == "customer.subscription.deleted":
            handle_subscription_deleted(db, event_data)
        
        elif event_type == "invoice.payment_succeeded":
            handle_payment_succeeded(db, event_data)
        
        elif event_type == "invoice.payment_failed":
            handle_payment_failed(db, event_data)
        
        else:
            logger.info(f"Unhandled event type: {event_type}")
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        # Don't raise - return 200 to prevent Stripe from retrying
        # Log error for manual review
    
    return {"received": True}


def handle_subscription_created(db: Session, subscription_data: dict):
    """Handle new subscription creation"""
    
    customer_id = subscription_data["customer"]
    subscription_id = subscription_data["id"]
    status = subscription_data["status"]
    
    # Find user by Stripe customer ID
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer: {customer_id}")
        return
    
    # Determine tier from subscription items
    tier = get_tier_from_subscription(subscription_data)
    
    # Update user
    user.stripe_subscription_id = subscription_id
    user.subscription_status = map_stripe_status(status)
    user.payment_status = PaymentStatus.ACTIVE
    user.tier = tier
    
    db.commit()
    logger.info(f"Subscription created for user {user.email}: {tier}")


def handle_subscription_updated(db: Session, subscription_data: dict):
    """Handle subscription changes (upgrades, downgrades, cancellations)"""
    
    subscription_id = subscription_data["id"]
    status = subscription_data["status"]
    
    # Find user by subscription ID
    user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if not user:
        logger.error(f"User not found for subscription: {subscription_id}")
        return
    
    old_tier = user.tier
    new_tier = get_tier_from_subscription(subscription_data)
    
    # Update user
    user.subscription_status = map_stripe_status(status)
    user.tier = new_tier
    
    # Handle downgrade - unpublish extra projects
    if is_downgrade(old_tier, new_tier):
        handle_downgrade(db, user, old_tier, new_tier)
    
    db.commit()
    logger.info(f"Subscription updated for user {user.email}: {old_tier} -> {new_tier}")


def handle_subscription_deleted(db: Session, subscription_data: dict):
    """Handle subscription cancellation"""
    
    subscription_id = subscription_data["id"]
    
    # Find user by subscription ID
    user = db.query(User).filter(User.stripe_subscription_id == subscription_id).first()
    if not user:
        logger.error(f"User not found for subscription: {subscription_id}")
        return
    
    # Downgrade to free tier
    user.tier = Tier.FREE
    user.subscription_status = SubscriptionStatus.CANCELED
    user.payment_status = PaymentStatus.ACTIVE
    
    # Unpublish all projects
    projects = db.query(Project).filter(
        Project.user_id == user.id,
        Project.status == ProjectStatus.PUBLISHED
    ).all()
    
    for project in projects:
        project.status = ProjectStatus.GENERATED
        project.subdomain_released_at = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    logger.info(f"Subscription canceled for user {user.email}, projects unpublished")


def handle_payment_succeeded(db: Session, invoice_data: dict):
    """Handle successful payment"""
    
    customer_id = invoice_data["customer"]
    
    # Find user by customer ID
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer: {customer_id}")
        return
    
    # Reset payment status if in grace period
    if user.payment_status in [PaymentStatus.FAILED, PaymentStatus.GRACE_PERIOD]:
        user.payment_status = PaymentStatus.ACTIVE
        db.commit()
        logger.info(f"Payment succeeded for user {user.email}, status reset to active")


def handle_payment_failed(db: Session, invoice_data: dict):
    """Handle failed payment - enter grace period"""
    
    customer_id = invoice_data["customer"]
    
    # Find user by customer ID
    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        logger.error(f"User not found for customer: {customer_id}")
        return
    
    # Enter grace period (7 days)
    user.payment_status = PaymentStatus.FAILED
    # Store grace period end date (you might want to add this field to User model)
    
    # Send notification email (implement via Resend)
    # send_payment_failed_email(user.email)
    
    db.commit()
    logger.info(f"Payment failed for user {user.email}, entered grace period")


# Helper functions

def get_tier_from_subscription(subscription_data: dict) -> Tier:
    """Determine tier from Stripe subscription data"""
    
    items = subscription_data.get("items", {}).get("data", [])
    if not items:
        return Tier.FREE
    
    # Get price ID from first item
    price_id = items[0]["price"]["id"]
    
    # Map price IDs to tiers
    if price_id == settings.STRIPE_PRICE_ID_PRO:
        return Tier.PRO
    elif price_id == settings.STRIPE_PRICE_ID_ULTIMATE:
        return Tier.ULTIMATE
    else:
        return Tier.FREE


def map_stripe_status(stripe_status: str) -> SubscriptionStatus:
    """Map Stripe subscription status to our status enum"""
    
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.CANCELED,
        "trialing": SubscriptionStatus.ACTIVE,
        "unpaid": SubscriptionStatus.PAST_DUE
    }
    
    return status_map.get(stripe_status, SubscriptionStatus.CANCELED)


def is_downgrade(old_tier: Tier, new_tier: Tier) -> bool:
    """Check if tier change is a downgrade"""
    
    tier_order = {
        Tier.FREE: 0,
        Tier.PRO: 1,
        Tier.ULTIMATE: 2
    }
    
    return tier_order[new_tier] < tier_order[old_tier]


def handle_downgrade(db: Session, user: User, old_tier: Tier, new_tier: Tier):
    """Handle project limits when downgrading"""
    
    # Get published project limits
    limits = {
        Tier.FREE: 0,
        Tier.PRO: 1,
        Tier.ULTIMATE: float('inf')
    }
    
    new_limit = limits[new_tier]
    
    # Get user's published projects
    published_projects = db.query(Project).filter(
        Project.user_id == user.id,
        Project.status == ProjectStatus.PUBLISHED
    ).order_by(Project.published_at).all()
    
    # If over limit, unpublish oldest projects
    if len(published_projects) > new_limit:
        projects_to_unpublish = published_projects[new_limit:]
        
        for project in projects_to_unpublish:
            project.status = ProjectStatus.GENERATED
            project.subdomain_released_at = datetime.utcnow() + timedelta(days=30)
        
        logger.info(f"Downgrade: Unpublished {len(projects_to_unpublish)} projects for user {user.email}")
