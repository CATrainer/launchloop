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
        
        prompt = f"""You are an expert at understanding product ideas. Extract structured information from this product description:

"{user_input}"

CRITICAL RULES:
1. If the user mentions ANY problem or pain point, extract it
2. If the user mentions ANY solution or approach, extract it
3. Be generous with interpretation - infer from context
4. NEVER return "Unknown" - always extract SOMETHING from the text
5. If truly unclear, ask for clarification by lowering completeness_score

Examples of good extraction:
Input: "helps developers deploy faster"
→ problem: "developers spend too long deploying apps"
→ solution: "streamlined deployment process"

Input: "app for founders to focus on important tasks"
→ problem: "founders waste time on low-value tasks"
→ solution: "task prioritization system that highlights most important work"

Return ONLY valid JSON with this exact structure:
{{
  "product_type": "b2b_saas" | "b2c" | "marketplace" | "tool",
  "target_audience": "specific audience (be specific, e.g. 'early-stage SaaS founders')",
  "problem": "clear problem statement (NEVER 'Unknown problem')",
  "solution_approach": "how it's solved (NEVER 'Unknown solution')",
  "stage": "idea" | "building" | "beta" | "launched",
  "founder_background": "relevant experience or null",
  "completeness_score": 0.0-1.0,
  "value_prop_headline": "if clear from description, extract it",
  "missing_info": ["list", "of", "missing", "details"] or []
}}

Score guidance:
- 0.8-1.0: Problem, solution, audience all clear
- 0.5-0.7: Most info present, some details missing
- 0.3-0.4: Basic idea clear but needs lots of details
- <0.3: Very unclear, need much more info"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Log what we got back
            print(f"📊 Extraction response: {response_text}")
            
            extracted = json.loads(response_text)
            
            # Validate we didn't get "Unknown" values
            if "Unknown" in extracted.get("problem", "") or "Unknown" in extracted.get("solution_approach", ""):
                print(f"⚠️ Got 'Unknown' in extraction, this should not happen!")
                print(f"   User input was: {user_input}")
            
            return extracted
        
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            # Return default extraction on error - but with user input as context
            return {
                "product_type": "b2b_saas",
                "target_audience": "users",
                "problem": f"Needs more detail about the problem being solved",
                "solution_approach": f"Needs more detail about the solution",
                "stage": "idea",
                "founder_background": None,
                "completeness_score": 0.2,
                "missing_info": ["problem description", "solution details", "target audience"]
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
