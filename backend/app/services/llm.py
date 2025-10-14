import anthropic
import json
from typing import Dict, Any, List, Optional
from app.config import settings
from app.utils.validators import validate_copy_content


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"
    
    def extract_product_info(self, user_input: str) -> Dict[str, Any]:
        """Extract structured information from user's product description"""
        
        prompt = f"""Extract structured information from this product description:

"{user_input}"

Return ONLY valid JSON with this exact structure:
{{
  "product_type": "b2b_saas or b2c or marketplace or tool",
  "target_audience": "specific audience",
  "problem": "problem being solved",
  "solution_approach": "how it's solved",
  "stage": "idea or building or beta or launched",
  "founder_background": "relevant experience or null",
  "completeness_score": 0.0-1.0
}}"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            return json.loads(response_text)
        
        except Exception as e:
            # Return default extraction on error
            return {
                "product_type": "b2b_saas",
                "target_audience": "founders",
                "problem": "Unknown problem",
                "solution_approach": "Unknown solution",
                "stage": "idea",
                "founder_background": None,
                "completeness_score": 0.3
            }
    
    def generate_questions(
        self,
        template_config: Dict,
        extracted_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate questions to fill gaps in data"""
        
        required_fields = template_config.get('required_fields', [])
        
        prompt = f"""Template "{template_config['name']}" requires these fields:
{json.dumps(required_fields, indent=2)}

We have extracted:
{json.dumps(extracted_data, indent=2)}

Generate questions to fill gaps. Rules:
- Max 5 questions
- Specific, not generic
- Use context from extracted data in question
- Mark clearly if optional

Return ONLY valid JSON array: [{{"field": "...", "question": "...", "example": "...", "required": true}}]"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            return json.loads(response_text)
        
        except Exception as e:
            # Return basic questions on error
            return [
                {
                    "field": "value_prop_headline",
                    "question": "What's the main benefit your product provides?",
                    "example": "Ship landing pages in 5 minutes",
                    "required": True
                }
            ]
    
    def generate_copy(
        self,
        template_config: Dict,
        input_data: Dict[str, Any],
        retry: bool = False
    ) -> Dict[str, Any]:
        """Generate landing page copy"""
        
        required_fields = template_config.get('required_fields', [])
        
        strict_warning = "\n\nIMPORTANT: Your previous attempt included banned content. Be extremely careful to avoid emojis and generic marketing speak." if retry else ""
        
        prompt = f"""You are a world-class copywriter specializing in landing pages for early-stage products.

CONTEXT:
{json.dumps(input_data, indent=2)}

TASK:
Generate landing page copy following these strict rules:

MANDATORY RULES:
- NO emojis (🚫)
- NO generic marketing speak: "revolutionary", "game-changing", "cutting-edge", "transform", "unlock"
- NO superlatives without proof: "best", "leading", "top", "#1"
- NO fake social proof: testimonials, user counts, "trusted by thousands"
- Be specific and concrete, not vague
- Use active voice and short sentences
- Honest about being pre-launch
- Benefit-driven (what user gets), not feature-driven
- Conversational but professional tone

STYLE:
- Write like talking to a technical founder
- Clear, confident, human
- No fluff or filler
- Each word must earn its place{strict_warning}

OUTPUT (strict JSON with these exact fields):
{{
  {", ".join([f'"{field}": "..."' for field in required_fields])}
}}

EXAMPLES:
BAD: "Revolutionize your workflow with cutting-edge AI"
GOOD: "Stop wasting hours on work that doesn't matter"

Now generate the copy:"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            generated_copy = json.loads(response_text)
            
            # Validate all fields
            all_valid = True
            for field, value in generated_copy.items():
                is_valid, violations = validate_copy_content(str(value))
                if not is_valid:
                    all_valid = False
                    break
            
            # If validation fails and this isn't a retry, try once more
            if not all_valid and not retry:
                return self.generate_copy(template_config, input_data, retry=True)
            
            return generated_copy
        
        except Exception as e:
            raise Exception(f"Failed to generate copy: {str(e)}")


# Global service instance
llm_service = LLMService()
