import anthropic
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings
from app.utils.validators import validate_copy_content
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=60.0  # 60 second timeout
        )
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
            logger.info("Product info extraction complete", extra={"response_length": len(response_text)})
            
            # Strip markdown code fences if present
            response_text = response_text.strip()
            if response_text.startswith("```"):
                # Remove opening fence
                lines = response_text.split("\n")
                lines = lines[1:] if len(lines) > 1 else lines
                # Remove closing fence
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
            
            if not response_text:
                raise ValueError("Empty response after stripping markdown")
            
            extracted = json.loads(response_text)
            
            # Validate we didn't get "Unknown" values
            if "Unknown" in extracted.get("problem", "") or "Unknown" in extracted.get("solution_approach", ""):
                logger.warning("Extraction returned 'Unknown' values", extra={
                    "problem": extracted.get("problem"),
                    "solution": extracted.get("solution_approach"),
                    "input_length": len(user_input)
                })
            
            return extracted
        
        except Exception as e:
            logger.error("Product info extraction failed", extra={"error": str(e)}, exc_info=True)
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
    ) -> Tuple[Dict[str, Any], float]:
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

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- NO markdown formatting (no ```json blocks)
- NO explanatory text before or after the JSON
- Just the raw JSON object with these exact fields:
{{
  {", ".join([f'"{field}": "..."' for field in required_fields])}
}}

EXAMPLES:
BAD: "Revolutionize your workflow with cutting-edge AI"
GOOD: "Stop wasting hours on work that doesn't matter"

Now generate the copy (JSON only, no markdown):"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Calculate API cost
            # Claude Sonnet: $3/1M input tokens, $15/1M output tokens
            input_cost = (message.usage.input_tokens / 1_000_000) * 3
            output_cost = (message.usage.output_tokens / 1_000_000) * 15
            total_cost = input_cost + output_cost
            
            logger.info("Claude copy generation complete", extra={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "cost_usd": round(total_cost, 4),
                "response_length": len(response_text)
            })
            
            # Try to extract JSON from response (handle markdown wrapping)
            generated_copy = self._extract_json_from_text(response_text)
            
            if not generated_copy:
                logger.error("Failed to extract JSON from Claude response", extra={
                    "response_preview": response_text[:500]
                })
                raise Exception("Could not extract valid JSON from Claude response")
            
            logger.debug("JSON extraction successful", extra={"field_count": len(generated_copy)})
            
            # Validate all fields
            all_valid = True
            violations_found = []
            for field, value in generated_copy.items():
                is_valid, violations = validate_copy_content(str(value))
                if not is_valid:
                    all_valid = False
                    violations_found.extend(violations)
                    logger.warning("Copy validation failed", extra={
                        "field": field,
                        "violations": violations
                    })
            
            # If validation fails and this isn't a retry, try once more
            if not all_valid and not retry:
                logger.info("Retrying generation due to validation failures", extra={
                    "violations": violations_found
                })
                return self.generate_copy(template_config, input_data, retry=True)
            
            return generated_copy, total_cost
        
        except Exception as e:
            logger.error("Copy generation failed", extra={"error": str(e)}, exc_info=True)
            raise Exception(f"Failed to generate copy: {str(e)}")
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text that may contain markdown or other formatting"""
        
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except:
            pass
        
        # Try to find JSON in markdown code blocks
        
        # Pattern 1: ```json {...} ```
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass
        
        # Pattern 2: Find any {...} block
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except:
                continue
        
        # Pattern 3: Try to extract everything between first { and last }
        try:
            start = text.index('{')
            end = text.rindex('}') + 1
            json_str = text[start:end]
            return json.loads(json_str)
        except:
            pass
        
        return None


# Global service instance
llm_service = LLMService()
