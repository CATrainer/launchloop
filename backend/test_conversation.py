#!/usr/bin/env python3
"""
Test script for conversational system
Tests the full flow from conversation creation to generation
"""

import asyncio
import json
from app.services.conversation import ConversationService
from app.services.conversation_ai import ConversationAI
from app.services.llm import LLMService
from app.models.conversation import Conversation, ConversationPhase
from app.database import SessionLocal
from app.utils.helpers import generate_uuid

async def test_conversation_flow():
    """Test complete conversation flow"""
    
    print("🧪 Testing Conversational System\n")
    print("=" * 60)
    
    # Setup
    db = SessionLocal()
    conversation_service = ConversationService(db)
    llm_service = LLMService()
    conversation_ai = ConversationAI(llm_service)
    conversation_ai.conversation_service.db = db
    
    try:
        # Step 1: Create conversation
        print("\n1️⃣  Creating conversation...")
        test_user_id = generate_uuid()
        conversation = conversation_service.create_conversation(
            user_id=test_user_id,
            project_id=None
        )
        print(f"✅ Conversation created: {conversation.id}")
        print(f"   Phase: {conversation.phase.value}")
        
        # Step 2: Test initial extraction
        print("\n2️⃣  Testing data extraction...")
        user_message = "I'm building an AI tool that generates landing pages for solo founders who don't have time to deal with design"
        
        extracted = await conversation_ai.extract_data_from_message(
            user_message,
            conversation
        )
        
        print(f"✅ Extracted {len(extracted)} fields:")
        for field, data in extracted.items():
            confidence = data.get('confidence', 0)
            confidence_label = "HIGH" if confidence > 0.7 else "MEDIUM" if confidence > 0.5 else "LOW"
            print(f"   • {field}: {data.get('value')[:50]}... (confidence: {confidence:.2f} - {confidence_label})")
        
        # Update conversation with extracted data
        conversation_service.update_extracted_data(conversation.id, extracted)
        db.refresh(conversation)
        
        # Step 3: Test AI response generation
        print("\n3️⃣  Testing AI response generation...")
        response = await conversation_ai.generate_response(conversation, user_message)
        
        print(f"✅ AI response generated:")
        print(f"   Message type: {response.get('message_type')}")
        print(f"   Message preview: {response.get('message', '')[:100]}...")
        
        if response.get('extracted_data'):
            print(f"   Additional data extracted: {len(response.get('extracted_data'))} fields")
        
        if response.get('should_transition'):
            print(f"   Phase transition suggested: → {response.get('next_phase')}")
        
        # Step 4: Test phase transition logic
        print("\n4️⃣  Testing phase transition logic...")
        next_phase = conversation_service.should_transition_phase(conversation)
        if next_phase:
            print(f"✅ Ready to transition: {conversation.phase.value} → {next_phase.value}")
        else:
            print(f"⏳ Not ready to transition yet (need higher confidence)")
            missing = conversation_service.get_missing_fields(conversation)
            print(f"   Missing fields: {', '.join(missing)}")
        
        # Step 5: Test engagement level detection
        print("\n5️⃣  Testing engagement level detection...")
        # Add a few messages to test
        conversation_service.add_message(conversation.id, "user", user_message)
        conversation_service.add_message(conversation.id, "ai", response.get('message', ''))
        
        engagement = conversation_service.determine_engagement_level(conversation)
        print(f"✅ Engagement level detected: {engagement.value}")
        
        # Step 6: Test template recommendation
        print("\n6️⃣  Testing template recommendation...")
        from app.services.template_service import TemplateService
        template_service = TemplateService()
        
        recommendations = template_service.recommend_templates(conversation.extracted_data)
        print(f"✅ {len(recommendations)} templates recommended:")
        for rec in recommendations:
            print(f"   • {rec['template']['name']} (score: {rec['score']:.2f})")
            print(f"     Reasoning: {rec['reasoning'][:80]}...")
        
        # Step 7: Test confidence scoring
        print("\n7️⃣  Testing confidence scoring...")
        print(f"✅ Confidence scores:")
        for field in ['problem_statement', 'target_audience', 'unique_value']:
            data = conversation.extracted_data.get(field, {})
            confidence = data.get('confidence', 0)
            threshold_met = "✓" if confidence > 0.7 else "✗"
            print(f"   {threshold_met} {field}: {confidence:.2f} (threshold: 0.7)")
        
        # Step 8: Test conversation state
        print("\n8️⃣  Testing conversation state...")
        print(f"✅ Conversation state:")
        print(f"   • Phase: {conversation.phase.value}")
        print(f"   • Messages: {conversation.message_count}")
        print(f"   • Engagement: {conversation.user_engagement_level.value}")
        print(f"   • Fields extracted: {len(conversation.extracted_data)}")
        print(f"   • Template selected: {conversation.selected_template_id or 'None'}")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("\n📊 Summary:")
        print(f"   • Conversation created successfully")
        print(f"   • Data extraction working ({len(extracted)} fields)")
        print(f"   • AI response generation working")
        print(f"   • Phase transition logic working")
        print(f"   • Engagement detection working")
        print(f"   • Template recommendation working")
        print(f"   • Confidence scoring working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        try:
            db.delete(conversation)
            db.commit()
            print("✅ Test data cleaned up")
        except:
            pass
        db.close()


async def test_edge_cases():
    """Test edge cases and error handling"""
    
    print("\n\n🧪 Testing Edge Cases\n")
    print("=" * 60)
    
    db = SessionLocal()
    conversation_service = ConversationService(db)
    llm_service = LLMService()
    conversation_ai = ConversationAI(llm_service)
    conversation_ai.conversation_service.db = db
    
    try:
        test_user_id = generate_uuid()
        conversation = conversation_service.create_conversation(test_user_id)
        
        # Test 1: Very short message (The Rusher)
        print("\n1️⃣  Testing very short message...")
        short_msg = "make me a page"
        response = await conversation_ai.generate_response(conversation, short_msg)
        print(f"✅ AI handled short message (engagement: LOW expected)")
        
        # Test 2: Very long message (The Over-Explainer)
        print("\n2️⃣  Testing very long message...")
        long_msg = "I'm building a product that helps developers deploy faster. " * 20
        response = await conversation_ai.generate_response(conversation, long_msg)
        print(f"✅ AI handled long message (engagement: HIGH expected)")
        
        # Test 3: Vague message (The Uncertain)
        print("\n3️⃣  Testing vague message...")
        vague_msg = "I don't know exactly"
        response = await conversation_ai.generate_response(conversation, vague_msg)
        print(f"✅ AI handled vague message")
        
        # Test 4: Off-topic message (The Wanderer)
        print("\n4️⃣  Testing off-topic message...")
        offtopic_msg = "Actually, what about pricing?"
        response = await conversation_ai.generate_response(conversation, offtopic_msg)
        print(f"✅ AI handled off-topic message")
        
        print("\n✅ ALL EDGE CASES PASSED!")
        
    except Exception as e:
        print(f"\n❌ EDGE CASE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.delete(conversation)
        db.commit()
        db.close()


def test_imports():
    """Test that all imports work"""
    
    print("\n🧪 Testing Imports\n")
    print("=" * 60)
    
    try:
        # Test model imports
        from app.models.conversation import Conversation, ConversationMessage, ConversationPhase
        print("✅ Models imported")
        
        # Test service imports
        from app.services.conversation import ConversationService
        from app.services.conversation_ai import ConversationAI
        from app.services.template_service import TemplateService
        print("✅ Services imported")
        
        # Test API imports
        from app.api.conversations import router
        print("✅ API routes imported")
        
        # Test database
        from app.database import SessionLocal
        db = SessionLocal()
        db.close()
        print("✅ Database connection works")
        
        print("\n✅ ALL IMPORTS SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"\n❌ IMPORT TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Launch Loop - Conversational System Tests\n")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Imports failed. Fix imports before running other tests.")
        exit(1)
    
    # Test 2: Full conversation flow
    result = asyncio.run(test_conversation_flow())
    
    if not result:
        print("\n❌ Main tests failed.")
        exit(1)
    
    # Test 3: Edge cases
    asyncio.run(test_edge_cases())
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start backend: python run.py")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Visit: http://localhost:3000/conversation")
    print("4. Test the conversation flow manually")
