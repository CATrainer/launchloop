from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TemplateService:
    """
    Manages landing page templates
    Currently has one template, structured for expansion
    """
    
    def __init__(self):
        # For now, one template - structure ready for more
        self.templates = {
            "problem_first": {
                "id": "problem_first",
                "name": "Problem-First",
                "description": "Leads with pain, builds urgency, reveals solution",
                "preview_image": "/templates/problem-first-preview.jpg",
                "ideal_when": [
                    "Problem is widely felt and visceral",
                    "Target audience is problem-aware",
                    "Solution is less obvious than the problem"
                ],
                "required_fields": [
                    {
                        "id": "pain_point_headline",
                        "label": "Pain Point Headline",
                        "extraction_prompt": "What's the primary frustration or pain when someone has this problem?",
                        "example": "Spending weeks building a landing page that converts nobody?",
                        "max_length": 100
                    },
                    {
                        "id": "pain_point_description",
                        "label": "Pain Point Description",
                        "extraction_prompt": "Describe the situation - what's happening when they feel this pain?",
                        "example": "You're a founder with a great idea, but you're stuck in Figma for weeks, second-guessing every pixel.",
                        "max_length": 300
                    },
                    {
                        "id": "solution_headline",
                        "label": "Solution Headline",
                        "extraction_prompt": "What's the transformation your product creates?",
                        "example": "AI-powered landing pages that convert, in minutes not weeks",
                        "max_length": 100
                    },
                    {
                        "id": "solution_description",
                        "label": "Solution Description",
                        "extraction_prompt": "How does your product solve the problem?",
                        "example": "Launch Loop uses AI to understand your product and generate professional, conversion-optimized landing pages in minutes.",
                        "max_length": 300
                    },
                    {
                        "id": "unique_value",
                        "label": "Unique Value Proposition",
                        "extraction_prompt": "What makes your solution different or better?",
                        "example": "Built specifically for founders who need to move fast, not designers who have time to spare.",
                        "max_length": 200
                    },
                    {
                        "id": "cta_text",
                        "label": "Call-to-Action",
                        "extraction_prompt": "What action do you want visitors to take?",
                        "example": "Create Your Landing Page",
                        "max_length": 50
                    }
                ]
            }
        }
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def get_all_templates(self) -> List[Dict]:
        """Get all available templates"""
        return list(self.templates.values())
    
    def calculate_template_fit(
        self,
        template_id: str,
        extracted_data: Dict
    ) -> float:
        """
        Calculate how well a template fits the user's product
        Returns score 0.0 to 1.0
        """
        template = self.get_template(template_id)
        if not template:
            return 0.0
        
        # For now, Problem-First is our default
        # In future, this will analyze extracted data to score fit
        
        problem_statement = extracted_data.get("problem_statement", {})
        target_audience = extracted_data.get("target_audience", {})
        
        score = 0.0
        
        # Has clear problem statement?
        if problem_statement.get("confidence", 0) > 0.7:
            score += 0.4
        
        # Has clear target audience?
        if target_audience.get("confidence", 0) > 0.7:
            score += 0.3
        
        # Problem-aware audience?
        audience_value = target_audience.get("value", "").lower()
        if any(word in audience_value for word in ["founders", "startups", "entrepreneurs", "developers"]):
            score += 0.3
        
        return min(score, 1.0)
    
    def generate_template_recommendation_reasoning(
        self,
        template_id: str,
        extracted_data: Dict
    ) -> str:
        """
        Generate personalized reasoning for why this template fits
        This will be enhanced with AI in full implementation
        """
        template = self.get_template(template_id)
        if not template:
            return ""
        
        problem = extracted_data.get("problem_statement", {}).get("value", "your product's problem")
        audience = extracted_data.get("target_audience", {}).get("value", "your audience")
        
        # For now, simple template - will use AI to generate personalized reasoning
        reasoning = f"The Problem-First template works great because it immediately connects with {audience} by addressing {problem}. "
        reasoning += "It builds urgency around the pain point before revealing your solution, which is proven to increase conversion rates."
        
        return reasoning
    
    def recommend_templates(self, extracted_data: Dict) -> List[Dict]:
        """
        Recommend templates based on extracted data
        Returns list of templates with scores and reasoning
        """
        recommendations = []
        
        for template_id, template in self.templates.items():
            score = self.calculate_template_fit(template_id, extracted_data)
            reasoning = self.generate_template_recommendation_reasoning(template_id, extracted_data)
            
            recommendations.append({
                "template": template,
                "score": score,
                "reasoning": reasoning
            })
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top 2 (or all if less than 2)
        return recommendations[:2]
