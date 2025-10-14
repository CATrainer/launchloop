"""
Question generation logic for problem-first template.
Extracts structured data from user input and generates follow-up questions.
"""

from typing import Dict, List, Any
from app.services.llm import llm_service


class QuestionGenerator:
    """Generates questions based on template requirements and extracted data"""
    
    def extract_product_data(self, user_input: str) -> Dict[str, Any]:
        """
        Extract structured data from user's initial product description
        
        Args:
            user_input: User's product description (2 sentences to 40 pages)
            
        Returns:
            Extracted structured data with completeness score
        """
        
        prompt = f"""Extract structured information from this product description:

"{user_input}"

Return JSON with this exact structure:
{{
  "product_type": "b2b_saas | b2c | marketplace | tool",
  "target_audience": "specific audience description",
  "problem": "problem being solved",
  "solution_approach": "how it's solved",
  "stage": "idea | building | beta | launched",
  "founder_background": "relevant experience or null",
  "product_name": "extracted name if mentioned, else null",
  "value_proposition": "core value prop if clear, else null",
  "completeness_score": 0.0-1.0
}}

Be specific and extract concrete details. Don't make assumptions."""

        try:
            response = llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are an expert at extracting structured data from product descriptions.",
                response_format="json"
            )
            
            return response
            
        except Exception as e:
            # Return minimal data if extraction fails
            return {
                "product_type": "unknown",
                "target_audience": "",
                "problem": "",
                "solution_approach": "",
                "stage": "idea",
                "founder_background": None,
                "product_name": None,
                "value_proposition": None,
                "completeness_score": 0.0
            }
    
    def generate_questions(
        self,
        extracted_data: Dict[str, Any],
        required_fields: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate follow-up questions for missing/unclear fields
        
        Args:
            extracted_data: Data extracted from user input
            required_fields: Fields required by the template
            
        Returns:
            List of questions to ask the user
        """
        
        # Build context from extracted data
        context = {
            "product_type": extracted_data.get("product_type", "unknown"),
            "target_audience": extracted_data.get("target_audience", ""),
            "problem": extracted_data.get("problem", ""),
            "solution_approach": extracted_data.get("solution_approach", ""),
            "stage": extracted_data.get("stage", "idea")
        }
        
        prompt = f"""Template "problem-first" requires these fields:
{required_fields}

We have extracted:
{context}

Generate questions to fill gaps. Rules:
- Max 5 questions total
- Specific, not generic
- Use context from extracted data
- Mark clearly if optional
- Provide helpful examples

Return JSON array: [{{"field": "field_name", "question": "question text", "example": "example answer", "required": true/false}}]
"""

        try:
            response = llm_service.call_llm(
                prompt=prompt,
                system_prompt="You are a helpful assistant generating follow-up questions for a landing page builder.",
                response_format="json"
            )
            
            # Ensure we don't ask too many questions
            questions = response if isinstance(response, list) else []
            return questions[:5]
            
        except Exception as e:
            # Return basic questions if generation fails
            return [
                {
                    "field": "value_prop_headline",
                    "question": "What's the main benefit your product provides?",
                    "example": "Save 10 hours per week on data entry",
                    "required": True
                },
                {
                    "field": "problem_headline",
                    "question": "What's the #1 problem you're solving?",
                    "example": "Manual data entry is slow and error-prone",
                    "required": True
                },
                {
                    "field": "target_audience",
                    "question": "Who specifically is this for?",
                    "example": "Operations managers at mid-size B2B companies",
                    "required": True
                }
            ]
    
    def select_best_template(self, extracted_data: Dict[str, Any]) -> str:
        """
        Select the best template based on extracted product data
        
        Currently only returns "problem-first" but can be extended
        """
        # For MVP, we only have one template
        # In future, add logic to select based on:
        # - product_type (b2b_saas -> problem-first, visual product -> product-showcase)
        # - stage (idea -> problem-first, launched -> results-first)
        # - audience (technical -> feature-first, non-technical -> benefit-first)
        
        return "problem-first"


# Singleton instance
question_generator = QuestionGenerator()
