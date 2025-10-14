import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class TemplateRegistry:
    """Registry for all available templates"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self._templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from templates directory"""
        if not self.templates_dir.exists():
            return
        
        for template_dir in self.templates_dir.iterdir():
            if template_dir.is_dir() and (template_dir / "config.json").exists():
                config_path = template_dir / "config.json"
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self._templates[config['id']] = {
                        'config': config,
                        'path': template_dir
                    }
    
    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get template by ID"""
        return self._templates.get(template_id)
    
    def get_all_templates(self) -> List[Dict]:
        """Get all templates"""
        return [t['config'] for t in self._templates.values()]
    
    def get_template_html(self, template_id: str) -> Optional[str]:
        """Get template HTML content"""
        template = self._templates.get(template_id)
        if not template:
            return None
        
        html_path = template['path'] / "template.html"
        if not html_path.exists():
            return None
        
        with open(html_path, 'r') as f:
            return f.read()
    
    def recommend_templates(self, product_type: str, stage: str) -> List[str]:
        """Recommend templates based on product type and stage"""
        # Simple recommendation logic - can be made more sophisticated
        recommendations = []
        
        for template_id, template_data in self._templates.items():
            config = template_data['config']
            best_for = config.get('best_for', [])
            
            # Check if product type or stage matches
            if product_type in best_for or stage in best_for:
                recommendations.append(template_id)
        
        # If no matches, return all templates
        if not recommendations:
            recommendations = list(self._templates.keys())
        
        return recommendations


# Global registry instance
template_registry = TemplateRegistry()
