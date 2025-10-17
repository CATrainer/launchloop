from typing import Dict, List, Optional
from app.models.conversation import Conversation, ConversationPhase, EngagementLevel
from app.services.conversation import ConversationService
from app.services.template_service import TemplateService
from app.services.llm import LLMService
import json
import logging

logger = logging.getLogger(__name__)

class ConversationAI:
    """
    The SECRET SAUCE - generates intelligent, contextual AI responses
    Makes the conversation feel natural, not like a form
    """
    
    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()
        self.conversation_service = ConversationService(None)  # Will set db per request
        self.template_service = TemplateService()
    
    def build_ai_prompt(self, conversation: Conversation) -> str:
        """
        Constructs the system prompt for Claude based on current state
        This is where the MAGIC happens - context-aware, intelligent prompts
        """
        
        # Phase-specific instructions (detailed, strategic)
        phase_instructions = self._get_phase_instructions(conversation)
        
        # Format what we know with confidence scores
        knowledge_state = self.conversation_service.format_knowledge_state(conversation)
        
        # Format recent conversation
        recent_conversation = self.conversation_service.format_conversation_history(conversation, last_n=5)
        
        # Get missing fields
        missing_fields = self.conversation_service.get_missing_fields(conversation)
        missing_str = ", ".join(missing_fields) if missing_fields else "None - we have enough to proceed"
        
        # Build full prompt
        prompt = f"""You are an expert strategist and copywriter helping founders create landing pages.

**CRITICAL RULES:**
1. Never announce phase transitions ("Now let's talk about X")
2. Never ask generic form-like questions ("What is your target audience?")
3. Always reference and build on what they've said
4. Match their communication style (if brief, be concise; if detailed, be expansive)
5. Ask maximum 2 questions per response
6. Reflect back their words before asking next question
7. When you have enough info, move forward naturally
8. Be conversational, not robotic
9. Show understanding and intelligence

**CURRENT STATE:**
Phase: {conversation.phase.value} (NEVER mention this to user)
Messages exchanged: {conversation.message_count}
User engagement: {conversation.user_engagement_level.value}

**WHAT WE KNOW (with confidence scores):**
{knowledge_state}

**WHAT WE STILL NEED:**
{missing_str}

**RECENT CONVERSATION:**
{recent_conversation}

**YOUR TASK:**
{phase_instructions}

**RESPONSE FORMAT:**
Return ONLY valid JSON with this structure:
{{
  "message": "Your conversational response (markdown supported)",
  "message_type": "text" | "quick_replies" | "template_selection" | "thinking",
  "quick_replies": ["Option 1", "Option 2"],  // if message_type = quick_replies
  "templates": [...],  // if message_type = template_selection
  "thinking_status": "...",  // if message_type = thinking
  "extracted_data": {{
    "field_name": {{"value": "...", "confidence": 0.8, "reasoning": "..."}}
  }},
  "should_transition": false,
  "next_phase": null  // or "TEMPLATE_SELECTION" etc if should_transition=true
}}

**REMEMBER:** The conversation should feel like talking to a smart friend who's helping 
you think through your landing page, NOT like filling out a form.

Be intelligent. Be contextual. Be natural.
"""
        
        return prompt
    
    def _get_phase_instructions(self, conversation: Conversation) -> str:
        """Get phase-specific instructions for the AI"""
        
        phase = conversation.phase
        engagement = conversation.user_engagement_level
        
        # Adjust verbosity based on user engagement
        verbosity_note = {
            EngagementLevel.LOW: "User gives brief responses - be concise and punchy.",
            EngagementLevel.MEDIUM: "User is conversational - match their energy.",
            EngagementLevel.HIGH: "User gives detailed responses - you can be expansive and go deeper."
        }[engagement]
        
        instructions = {
            ConversationPhase.IDEA_SATURATION: f"""
**Your goal:** Understand the product deeply enough to recommend templates.

**Extract and build confidence in:**
- What problem does it solve? (Be specific - not vague)
- Who is it for? (Narrow audience, not "businesses")
- What makes it different/valuable?
- What stage is the product at? (idea, MVP, launched)

**How to ask questions:**
- Open-ended and contextual
- Reference what they've said
- Bundle related questions (max 2 at once)
- Offer frameworks or examples if they're stuck
- {verbosity_note}

**Examples of GOOD questions:**
- "When you say solo founders - are we talking technical folks who can code but hate design? Or non-technical founders who need everything done for them?"
- "What's the moment when someone feels this problem most acutely? Like, what triggers the frustration?"

**Examples of BAD questions (NEVER DO THIS):**
- "What is your target audience?"
- "Describe your value proposition"
- "What features does your product have?"

**When to move forward:**
You have high confidence (>0.7) on problem and audience. Then naturally transition to discussing naming.
Don't announce the transition - make it feel organic. Example:
"Okay, I'm getting a really clear picture of this. Before I show you some directions, 
do you have a name yet, or is that still TBD?"
""",
            
            ConversationPhase.NAME_DISCUSSION: f"""
**Your goal:** Find out if they have a product name.

**If they have a name:**
- Affirm it positively
- Maybe make a brief comment on why it works
- Transition to showing templates

**If they don't have a name:**
- You can suggest 2-3 options based on what you know
- Make them feel like brainstorm ideas, not final decisions
- Don't spend too much time here
- Transition to showing templates

**Then naturally flow into template recommendations.**

{verbosity_note}

Example transition:
"Love it. So with [Name], and knowing your audience is [audience], let me show you 
a direction for the landing page that I think will really work..."
""",
            
            ConversationPhase.TEMPLATE_SELECTION: f"""
**Your goal:** Recommend the Problem-First template with good reasoning.

**Present the template as a strategic choice:**
- Explain WHY it works for THEIR specific product
- Reference their problem, audience, stage
- Make it feel personalized, not generic
- Show the preview
- Include reasoning that shows you understand their product

**Template to recommend:**
{json.dumps(self.template_service.get_template("problem_first"), indent=2)}

**Example reasoning:**
"The Problem-First template works great for you because [specific reference to their product]. 
It leads with the pain point that [their audience] feels, builds urgency, then reveals 
your solution. This structure is proven to convert better when your audience is problem-aware."

Once they select, naturally transition to gathering template data.

{verbosity_note}
""",
            
            ConversationPhase.DATA_GATHERING: f"""
**Your goal:** Extract specific data to populate the selected template.

**Template fields needed:**
{json.dumps(self.template_service.get_template("problem_first")["required_fields"], indent=2)}

**How to ask for data:**
- Questions should feel like creative brainstorming, NOT form-filling
- Reference the template context: "Since we're leading with the problem..."
- Be specific and actionable
- Offer examples if they're stuck
- Maximum 2 questions at a time

**Examples of GOOD questions:**
- "For the hero section, what's the internal dialogue when someone has this problem? 
   Like, what are they thinking or feeling?"
- "If you had to explain this in an elevator, what's the first thing you'd say?"

**Examples of BAD questions:**
- "What is your value proposition?"
- "Describe your solution"

**Track confidence:**
- High confidence (0.8+): They gave explicit, clear information
- Medium confidence (0.5-0.7): Somewhat clear but could be better
- Low confidence (<0.5): Vague or missing

{verbosity_note}

When all required fields have high confidence (>0.7), naturally offer to generate the page.
""",
            
            ConversationPhase.GENERATION: """
**Your goal:** Confirm we have everything and trigger generation.

Show them what you've captured, confirm it looks good, then start generation.

Example:
"Perfect! I have everything I need:
- Pain point: [what they said]
- Solution: [what they said]
- Unique angle: [what they said]

Ready to generate your landing page? It'll take about 30 seconds."

Then set message_type to "thinking" with status "Generating your landing page..."
"""
        }
        
        return instructions.get(phase, "Continue the conversation naturally.")
    
    async def generate_response(
        self,
        conversation: Conversation,
        user_message: str
    ) -> Dict:
        """
        Generate AI response based on conversation state
        Returns structured response with message, type, extracted data, etc.
        """
        
        # Build prompt
        prompt = self.build_ai_prompt(conversation)
        
        # Add user's new message to context
        full_prompt = f"""{prompt}

**USER'S NEW MESSAGE:**
"{user_message}"

**YOUR RESPONSE (JSON only):**"""
        
        # Call Claude
        try:
            response = await self.llm.messages.create(
                model=self.llm.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            response_data = self._extract_json_from_response(response_text)
            
            if not response_data:
                # Fallback if JSON parsing fails
                return {
                    "message": response_text,
                    "message_type": "text",
                    "extracted_data": {},
                    "should_transition": False
                }
            
            return response_data
            
        except Exception as e:
            logger.error(f"AI response generation failed: {str(e)}", exc_info=True)
            
            # Fallback response
            return {
                "message": "I'm having trouble processing that. Could you rephrase?",
                "message_type": "text",
                "extracted_data": {},
                "should_transition": False
            }
    
    async def extract_data_from_message(
        self,
        user_message: str,
        conversation: Conversation
    ) -> Dict[str, Dict]:
        """
        Extract structured data from user's message with confidence scores
        This runs in parallel with response generation for efficiency
        """
        
        current_data = conversation.extracted_data or {}
        
        prompt = f"""Extract structured data from this user message with confidence scores.

**USER MESSAGE:**
"{user_message}"

**CONTEXT (what we already know):**
{json.dumps(current_data, indent=2)}

**TASK:**
Identify information about:
- problem_statement: What problem does the product solve?
- target_audience: Who is the product for?
- unique_value: What makes it special/different?
- product_stage: Is it an idea, MVP, launched, etc?
- product_name: Name of the product

**For each field found:**
- Extract the value
- Assign confidence 0.0-1.0:
  * 1.0 = Directly stated, unambiguous
  * 0.8 = Strongly implied
  * 0.6 = Somewhat implied
  * 0.4 = Weak inference
  * Only include if confidence > 0.4
- Provide reasoning for the confidence score

**Return ONLY valid JSON:**
{{
  "problem_statement": {{"value": "...", "confidence": 0.8, "reasoning": "User said X"}},
  "target_audience": {{"value": "...", "confidence": 0.7, "reasoning": "..."}}
}}

Only include fields mentioned in the message. Skip fields not found.
"""
        
        try:
            response = await self.llm.messages.create(
                model=self.llm.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            extracted = self._extract_json_from_response(response_text)
            
            return extracted or {}
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return {}
    
    def _extract_json_from_response(self, text: str) -> Optional[Dict]:
        """Extract JSON from AI response (may have markdown formatting)"""
        import re
        
        # Try direct JSON parse
        try:
            return json.loads(text)
        except:
            pass
        
        # Try extracting from code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.+?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Try finding first JSON object
        json_match = re.search(r'\{.+\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        return None
