"""
GPT-4 Vision Analyzer for product image analysis
Analyzes products to generate optimal prompts and positioning data
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from PIL import Image
import io
import requests


class GPTProductAnalyzer:
    """Analyzes product images using GPT-4 Vision API"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY', '')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.api_url = "https://api.openai.com/v1/responses"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Detailed system prompt for comprehensive analysis
        self.system_prompt = """
Analyze product for marketplace photography processing.

Return JSON with detailed analysis:
{
  "category": "electronics|home|diy|fashion|appliances|fmcg",
  "product_identification": {
    "type": "product name",
    "brand": "if visible",
    "model": "if applicable"
  },
  "visual_properties": {
    "primary_color": "main color",
    "secondary_colors": ["color1", "color2"],
    "material": "plastic|metal|fabric|leather|wood|glass|mixed",
    "texture": "smooth|rough|glossy|matte",
    "transparency": "opaque|translucent|transparent"
  },
  "geometry": {
    "orientation": "vertical|standard",
    "aspect_ratio": 0.00,
    "has_shadow": true/false,
    "physical_property": "stands|hangs|floats|lies_flat"
  },
  "lora_optimization": {
    "main_object_description": "detailed description for prompt",
    "special_instructions": "handle reflections|preserve logo|keep texture details|none",
    "shadow_handling": "preserve|enhance|minimize"
  },
  "canvas_settings": {
    "size": "1600x1600|1200x1600",
    "positioning": "bottom_aligned|centered|fill_vertical"
  }
}

Rules:
- orientation: "vertical" if height/width ratio > 1.3, else "standard"
- physical_property: "stands" for items with base (shoes, bottles), "hangs" for clothing, "floats" for accessories, "lies_flat" for books/tablets
- canvas_settings.size: "1600x1600" for vertical, "1200x1600" for standard
- positioning: "bottom_aligned" for stands items, "centered" for floats/hangs/lies_flat, "fill_vertical" for tall stands items
- Focus on creating highly specific main_object_description that will help AI understand exact product details
- Include color, material, and distinguishing features in main_object_description
"""

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze product image using GPT-4 Vision
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict with analysis results
        """
        try:
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Prepare the request using new OpenAI Responses API format
            # Note: System prompt is combined with user request in single input
            combined_prompt = f"{self.system_prompt}\n\nAnalyze this product image and return the structured JSON response."
            
            payload = {
                "model": "gpt-4.1",
                "input": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": combined_prompt
                            },
                            {
                                "type": "input_image",
                                "image_url": f"data:image/png;base64,{img_base64}"
                            }
                        ]
                    }
                ]
            }
            
            # Make the API call
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # New Responses API returns output_text instead of choices
                content = result.get('output_text', '')
                
                # Extract JSON from response
                # GPT might wrap it in ```json ... ``` markers
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                # Parse JSON
                analysis = json.loads(content.strip())
                
                # Add computed aspect ratio if image provided
                if image:
                    width, height = image.size
                    analysis['geometry']['aspect_ratio'] = round(width / height, 2)
                    
                    # Verify orientation calculation
                    if height / width > 1.3:
                        analysis['geometry']['orientation'] = 'vertical'
                        analysis['canvas_settings']['size'] = '1600x1600'
                    else:
                        analysis['geometry']['orientation'] = 'standard'
                        analysis['canvas_settings']['size'] = '1200x1600'
                
                return {
                    'success': True,
                    'analysis': analysis
                }
                
            else:
                # Detailed error handling for debugging
                try:
                    error_response = response.json()
                except:
                    error_response = {"message": response.text}
                
                error_detail = ""
                if response.status_code == 400:
                    error_detail = f" (Bad Request - possibly invalid model or format): {error_response}"
                elif response.status_code == 429:
                    error_detail = f" (Rate limit exceeded): {error_response}"
                elif response.status_code == 401:
                    error_detail = f" (Invalid API key): {error_response}"
                elif response.status_code == 404:
                    error_detail = f" (Model/endpoint not found): {error_response}"
                else:
                    error_detail = f" (Unknown error): {error_response}"
                    
                print(f"OpenAI Responses API error: {response.status_code}{error_detail}")
                print(f"Payload sent: {payload}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}{error_detail}",
                    'fallback': self._get_fallback_analysis(image)
                }
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse GPT response as JSON: {e}")
            return {
                'success': False,
                'error': f"JSON parsing error: {str(e)}",
                'fallback': self._get_fallback_analysis(image)
            }
            
        except Exception as e:
            print(f"Error in GPT analysis: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': self._get_fallback_analysis(image)
            }
    
    def _get_fallback_analysis(self, image: Image.Image) -> Dict[str, Any]:
        """
        Provide fallback analysis when GPT-4 Vision fails
        
        Args:
            image: PIL Image object
            
        Returns:
            Basic analysis dict
        """
        width, height = image.size
        aspect_ratio = round(width / height, 2)
        is_vertical = height / width > 1.3
        
        return {
            'category': 'unknown',
            'product_identification': {
                'type': 'product',
                'brand': 'unknown',
                'model': 'unknown'
            },
            'visual_properties': {
                'primary_color': 'unknown',
                'secondary_colors': [],
                'material': 'unknown',
                'texture': 'unknown',
                'transparency': 'opaque'
            },
            'geometry': {
                'orientation': 'vertical' if is_vertical else 'standard',
                'aspect_ratio': aspect_ratio,
                'has_shadow': True,
                'physical_property': 'floats'
            },
            'lora_optimization': {
                'main_object_description': 'product item',
                'special_instructions': 'none',
                'shadow_handling': 'preserve'
            },
            'canvas_settings': {
                'size': '1600x1600' if is_vertical else '1200x1600',
                'positioning': 'centered'
            }
        }
    
    def create_lora_prompt(self, analysis: Dict[str, Any]) -> str:
        """
        Create optimized prompt for LoRA model based on GPT analysis
        
        Args:
            analysis: Analysis dict from GPT-4 Vision
            
        Returns:
            Formatted prompt string for LoRA
        """
        # Extract main object description
        main_object = analysis.get('lora_optimization', {}).get('main_object_description', 'product')
        item_type = analysis.get('product_identification', {}).get('type', 'item')
        
        # Build the prompt
        prompt = f"""Clean product photo of {main_object}:
- Keep only the main {item_type} and its natural shadow
- Pure #F5F4F2 background (light beige)
- Remove ALL extra elements (text, watermarks, frames, logos, graphics, price tags)
- Consistent soft lighting from top-back at 45°, diffused shadow underneath
- Keep original resolution, no upscaling
- Professional e-commerce style"""
        
        # Add special instructions if any
        special = analysis.get('lora_optimization', {}).get('special_instructions', '')
        if special and special != 'none':
            prompt += f"\n- Special: {special}"
        
        return prompt