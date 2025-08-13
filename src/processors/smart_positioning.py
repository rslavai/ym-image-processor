"""
Smart Positioning Module
Positions products on canvas based on category and orientation
"""

from PIL import Image, ImageDraw
import numpy as np
from typing import Tuple, Dict, Any, Optional


class SmartPositioning:
    """Intelligent product positioning on standardized canvases"""
    
    # Canvas configurations
    CANVAS_VERTICAL = (1600, 1600)  # 1:1 for vertical products
    CANVAS_STANDARD = (1200, 1600)  # 3:4 for standard products
    BACKGROUND_COLOR = "#F5F4F2"  # Light beige background
    
    # Padding configuration (10% default, can be overridden)
    DEFAULT_PADDING_PERCENT = 0.10
    
    def __init__(self):
        """Initialize positioning system"""
        self.debug_mode = False  # Set to True to show grid lines
        
    def process_image(self, 
                     image: Image.Image, 
                     analysis: Dict[str, Any],
                     padding_percent: Optional[float] = None) -> Image.Image:
        """
        Position product on appropriate canvas based on analysis
        
        Args:
            image: Product image with transparent/removed background
            analysis: GPT analysis dict with positioning data
            padding_percent: Optional custom padding (default 10%)
            
        Returns:
            Positioned image on canvas
        """
        # Extract positioning data
        orientation = analysis.get('geometry', {}).get('orientation', 'standard')
        positioning = analysis.get('canvas_settings', {}).get('positioning', 'centered')
        
        # Determine canvas size
        if orientation == 'vertical':
            canvas_size = self.CANVAS_VERTICAL
        else:
            canvas_size = self.CANVAS_STANDARD
        
        # Create canvas
        canvas = self._create_canvas(canvas_size)
        
        # Position product on canvas
        positioned = self._position_on_canvas(
            canvas, 
            image, 
            positioning,
            padding_percent or self.DEFAULT_PADDING_PERCENT
        )
        
        # Add debug grid if enabled
        if self.debug_mode:
            positioned = self._add_debug_grid(positioned)
        
        return positioned
    
    def _create_canvas(self, size: Tuple[int, int]) -> Image.Image:
        """
        Create a canvas with background color
        
        Args:
            size: Canvas dimensions (width, height)
            
        Returns:
            New canvas image
        """
        canvas = Image.new('RGBA', size, self.BACKGROUND_COLOR)
        return canvas
    
    def _position_on_canvas(self,
                           canvas: Image.Image,
                           product: Image.Image,
                           positioning: str,
                           padding_percent: float) -> Image.Image:
        """
        Position product on canvas with specified alignment
        
        Args:
            canvas: Target canvas
            product: Product image to position
            positioning: Alignment strategy (bottom_aligned|centered|fill_vertical)
            padding_percent: Padding as percentage of canvas size
            
        Returns:
            Canvas with positioned product
        """
        canvas_w, canvas_h = canvas.size
        
        # Calculate padding in pixels
        padding_x = int(canvas_w * padding_percent)
        padding_y = int(canvas_h * padding_percent)
        
        # Available space for product
        available_w = canvas_w - (2 * padding_x)
        available_h = canvas_h - (2 * padding_y)
        
        # Get product bounds including shadow
        product_bounds = self._get_image_bounds(product)
        if not product_bounds:
            # No visible content
            return canvas
        
        # Crop to actual content (including shadow)
        product_cropped = product.crop(product_bounds)
        prod_w, prod_h = product_cropped.size
        
        # Calculate scale to fit within available space
        scale_x = available_w / prod_w if prod_w > 0 else 1
        scale_y = available_h / prod_h if prod_h > 0 else 1
        
        if positioning == 'fill_vertical':
            # Maximize vertical space usage
            scale = min(scale_x, scale_y)
        else:
            # Maintain aspect ratio within bounds
            scale = min(scale_x, scale_y, 1.0)  # Don't upscale beyond original
        
        # Resize product
        new_width = int(prod_w * scale)
        new_height = int(prod_h * scale)
        product_resized = product_cropped.resize(
            (new_width, new_height),
            Image.Resampling.LANCZOS
        )
        
        # Calculate position based on alignment
        if positioning == 'bottom_aligned':
            # Align to bottom with padding
            x = (canvas_w - new_width) // 2
            y = canvas_h - padding_y - new_height
            
        elif positioning == 'fill_vertical':
            # Center horizontally, maximize vertical
            x = (canvas_w - new_width) // 2
            y = padding_y
            
        else:  # centered
            # Center both horizontally and vertically
            x = (canvas_w - new_width) // 2
            y = (canvas_h - new_height) // 2
        
        # Ensure position is within bounds
        x = max(padding_x, min(x, canvas_w - new_width - padding_x))
        y = max(padding_y, min(y, canvas_h - new_height - padding_y))
        
        # Paste product onto canvas
        canvas_copy = canvas.copy()
        
        # Use alpha channel as mask if available, otherwise no mask
        if product_resized.mode == 'RGBA':
            try:
                canvas_copy.paste(product_resized, (x, y), product_resized)
            except ValueError:
                # Fallback: paste without alpha mask
                rgb_product = product_resized.convert('RGB')
                canvas_copy.paste(rgb_product, (x, y))
        else:
            canvas_copy.paste(product_resized, (x, y))
        
        return canvas_copy
    
    def _get_image_bounds(self, image: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """
        Get bounding box of non-transparent pixels (including shadows)
        
        Args:
            image: Image to analyze
            
        Returns:
            Bounding box (left, top, right, bottom) or None if empty
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Get alpha channel
        alpha = image.split()[-1]
        
        # Find bounding box of non-transparent pixels
        # We use a low threshold to include soft shadows
        bbox = alpha.getbbox()
        
        if bbox:
            # Expand bbox slightly to ensure we don't clip shadows
            left, top, right, bottom = bbox
            width, height = image.size
            
            # Add small margin (2 pixels) to preserve shadow edges
            margin = 2
            left = max(0, left - margin)
            top = max(0, top - margin)
            right = min(width, right + margin)
            bottom = min(height, bottom + margin)
            
            return (left, top, right, bottom)
        
        return None
    
    def _add_debug_grid(self, image: Image.Image) -> Image.Image:
        """
        Add grid lines for debugging positioning
        
        Args:
            image: Image to add grid to
            
        Returns:
            Image with grid overlay
        """
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        width, height = img_copy.size
        
        # Rule of thirds lines
        for i in range(1, 3):
            # Vertical lines
            x = width * i // 3
            draw.line([(x, 0), (x, height)], fill=(200, 200, 200, 128), width=1)
            
            # Horizontal lines
            y = height * i // 3
            draw.line([(0, y), (width, y)], fill=(200, 200, 200, 128), width=1)
        
        # Center lines
        draw.line([(width//2, 0), (width//2, height)], fill=(150, 150, 150, 128), width=2)
        draw.line([(0, height//2), (width, height//2)], fill=(150, 150, 150, 128), width=2)
        
        # Padding boundaries (10%)
        padding_x = int(width * 0.1)
        padding_y = int(height * 0.1)
        
        # Draw padding rectangle
        draw.rectangle(
            [padding_x, padding_y, width - padding_x, height - padding_y],
            outline=(100, 100, 100, 128),
            width=1
        )
        
        return img_copy
    
    def set_debug_mode(self, enabled: bool):
        """
        Enable or disable debug grid overlay
        
        Args:
            enabled: True to show grid, False to hide
        """
        self.debug_mode = enabled