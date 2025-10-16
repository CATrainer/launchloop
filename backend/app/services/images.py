import openai
import requests
from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ImageService:
    """Service for AI image generation"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "dall-e-3"
        self.size = "1024x1024"
        self.quality = "standard"
    
    def build_image_prompt(
        self,
        spec: Dict[str, Any],
        input_data: Dict[str, Any],
        generated_copy: Dict[str, Any]
    ) -> str:
        """Build image generation prompt from template spec"""
        
        prompt = spec.get("prompt_template", "")
        
        # Replace variables with actual data
        replacements = {
            "{product_concept}": input_data.get("productDescription", "product"),
            "{current_pain}": input_data.get("currentPain", "problem"),
            "{solution_approach}": generated_copy.get("solution_description", "solution"),
            "{target_audience}": generated_copy.get("target_audience", "users"),
            "{color_palette}": "soft blue and white tones",
        }
        
        for placeholder, value in replacements.items():
            prompt = prompt.replace(placeholder, value)
        
        return prompt
    
    def generate_single_image(
        self,
        prompt: str,
        image_id: str,
        retry: bool = False
    ) -> Dict[str, Any]:
        """Generate a single image"""
        
        try:
            response = openai.images.generate(
                model=self.model,
                prompt=prompt,
                size=self.size,
                quality=self.quality,
                n=1
            )
            
            image_url = response.data[0].url
            
            logger.debug("Image generated successfully", extra={"image_id": image_id})
            
            return {
                "id": image_id,
                "url": image_url,
                "prompt": prompt,
                "status": "success"
            }
        
        except Exception as e:
            # Retry once if first attempt fails
            if not retry:
                logger.warning("Image generation failed, retrying", extra={
                    "image_id": image_id,
                    "error": str(e)
                })
                return self.generate_single_image(prompt, image_id, retry=True)
            
            logger.error("Image generation failed after retry", extra={
                "image_id": image_id,
                "error": str(e)
            })
            
            return {
                "id": image_id,
                "url": None,
                "prompt": prompt,
                "status": "failed",
                "error": str(e)
            }
    
    def generate_images(
        self,
        image_specs: List[Dict[str, Any]],
        input_data: Dict[str, Any],
        generated_copy: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Generate multiple images in parallel"""
        
        results = []
        
        # Use ThreadPoolExecutor for parallel generation
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            for spec in image_specs:
                prompt = self.build_image_prompt(spec, input_data, generated_copy)
                image_id = spec.get("id")
                
                future = executor.submit(
                    self.generate_single_image,
                    prompt,
                    image_id
                )
                futures[future] = image_id
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Sort by original order
        spec_ids = [spec.get("id") for spec in image_specs]
        results.sort(key=lambda x: spec_ids.index(x["id"]))
        
        # Calculate cost
        # DALL-E 3: $0.04 per 1024x1024 standard quality image
        cost_per_image = 0.04
        successful_images = sum(1 for r in results if r["status"] == "success")
        total_cost = successful_images * cost_per_image
        
        logger.info("Image generation batch complete", extra={
            "total_images": len(results),
            "successful": successful_images,
            "failed": len(results) - successful_images,
            "total_cost": round(total_cost, 4)
        })
        
        return results, total_cost
    
    def download_image(self, url: str) -> bytes:
        """Download image from URL"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content


# Global service instance
image_service = ImageService()
