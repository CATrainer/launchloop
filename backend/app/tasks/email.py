from app.tasks import celery_app
import resend
from app.config import settings


resend.api_key = settings.RESEND_API_KEY


@celery_app.task
def send_welcome_email(email: str, name: str = None):
    """Send welcome email to new user"""
    try:
        params = {
            "from": "Launch Loop <onboarding@thelaunchloop.com>",
            "to": [email],
            "subject": "Welcome to Launch Loop",
            "html": f"""
                <h1>Welcome to Launch Loop!</h1>
                <p>Thanks for signing up. You're ready to create your first landing page.</p>
                <p><a href="{settings.FRONTEND_URL}/dashboard">Get Started</a></p>
            """
        }
        
        resend.Emails.send(params)
    except Exception as e:
        # Log error but don't fail the task
        print(f"Failed to send welcome email: {str(e)}")


@celery_app.task
def send_signup_notification(email: str, project_name: str, project_subdomain: str):
    """Send notification when someone signs up on a landing page"""
    try:
        params = {
            "from": "Launch Loop <notifications@thelaunchloop.com>",
            "to": [email],
            "subject": f"New signup on {project_name}",
            "html": f"""
                <h2>New Signup!</h2>
                <p>Someone just signed up on your landing page: <strong>{project_name}</strong></p>
                <p>View all signups: <a href="{settings.FRONTEND_URL}/projects/{project_subdomain}/dashboard">Dashboard</a></p>
            """
        }
        
        resend.Emails.send(params)
    except Exception as e:
        print(f"Failed to send signup notification: {str(e)}")
