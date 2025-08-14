"""
Model Selection Policy for K+ Content Service V2.0
Implements intelligent model selection and fallback logic
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .model_registry import ModelRegistry, ModelInfo


class SelectionReason(Enum):
    """Reasons for model selection"""
    USER_CHOICE = "user_choice"
    AUTO_POLICY = "auto_policy"
    FALLBACK_ERROR = "fallback_error"
    FALLBACK_UNAVAILABLE = "fallback_unavailable"
    DEFAULT = "default"


@dataclass
class SelectionResult:
    """Result of model selection with explanation"""
    model: Optional[ModelInfo]
    reason: SelectionReason
    explanation: str
    fallback_chain: List[str]
    selection_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'model_id': self.model.id if self.model else None,
            'model_name': f"{self.model.name} {self.model.version}" if self.model else None,
            'reason': self.reason.value,
            'explanation': self.explanation,
            'fallback_chain': self.fallback_chain,
            'selection_metadata': self.selection_metadata
        }


class ModelSelectionPolicy:
    """Implements model selection and fallback logic"""
    
    def __init__(self):
        """Initialize selection policy"""
        self.registry = ModelRegistry()
        
        # Default fallback chain: V2 → V1 → BiRefNet
        self.default_fallback_chain = [
            'flux-kontext-lora-v2',
            'flux-kontext-lora-v1', 
            'birefnet-fallback'
        ]
    
    def select_model(
        self,
        user_model_id: Optional[str] = None,
        marketplace: Optional[str] = None,
        image_complexity: Optional[float] = None,
        require_fast: bool = False,
        require_high_quality: bool = False
    ) -> SelectionResult:
        """
        Select optimal model based on criteria
        
        Args:
            user_model_id: User-specified model ID
            marketplace: Target marketplace
            image_complexity: Image complexity score (0.0-1.0)
            require_fast: If True, prefer faster models
            require_high_quality: If True, prefer quality over speed
            
        Returns:
            SelectionResult with chosen model and explanation
        """
        
        # 1. User explicitly chose model
        if user_model_id:
            model = self.registry.get_model_by_id(user_model_id)
            if model:
                return SelectionResult(
                    model=model,
                    reason=SelectionReason.USER_CHOICE,
                    explanation=f"User explicitly selected {model.name} {model.version}",
                    fallback_chain=[user_model_id],
                    selection_metadata={
                        'user_specified': True,
                        'model_available': True
                    }
                )
            else:
                # User choice not available, fall back to auto-selection
                return self._auto_select_model(
                    marketplace=marketplace,
                    image_complexity=image_complexity,
                    require_fast=require_fast,
                    require_high_quality=require_high_quality,
                    selection_metadata={'user_specified_unavailable': user_model_id}
                )
        
        # 2. Auto-selection based on criteria
        return self._auto_select_model(
            marketplace=marketplace,
            image_complexity=image_complexity,
            require_fast=require_fast,
            require_high_quality=require_high_quality
        )
    
    def _auto_select_model(
        self,
        marketplace: Optional[str] = None,
        image_complexity: Optional[float] = None,
        require_fast: bool = False,
        require_high_quality: bool = False,
        selection_metadata: Optional[Dict[str, Any]] = None
    ) -> SelectionResult:
        """Auto-select model based on criteria"""
        
        if selection_metadata is None:
            selection_metadata = {}
        
        # Get available models
        all_models = self.registry.get_all_models(active_only=True)
        
        if not all_models:
            return SelectionResult(
                model=None,
                reason=SelectionReason.DEFAULT,
                explanation="No models available in registry",
                fallback_chain=[],
                selection_metadata=selection_metadata
            )
        
        # Filter by marketplace if specified
        candidate_models = all_models
        if marketplace:
            marketplace_models = self.registry.get_models_by_marketplace(marketplace)
            if marketplace_models:
                candidate_models = marketplace_models
                selection_metadata['marketplace_filter'] = marketplace
        
        # Apply selection logic based on requirements
        selected_model = self._apply_selection_logic(
            candidate_models,
            image_complexity=image_complexity,
            require_fast=require_fast,
            require_high_quality=require_high_quality
        )
        
        if selected_model:
            explanation = self._build_explanation(
                selected_model,
                image_complexity=image_complexity,
                require_fast=require_fast,
                require_high_quality=require_high_quality
            )
            
            return SelectionResult(
                model=selected_model,
                reason=SelectionReason.AUTO_POLICY,
                explanation=explanation,
                fallback_chain=[selected_model.id],
                selection_metadata=selection_metadata
            )
        
        # Fallback to default chain
        return self._fallback_to_default(selection_metadata)
    
    def _apply_selection_logic(
        self,
        models: List[ModelInfo],
        image_complexity: Optional[float] = None,
        require_fast: bool = False,
        require_high_quality: bool = False
    ) -> Optional[ModelInfo]:
        """Apply selection logic to choose best model"""
        
        if not models:
            return None
        
        # If specific requirements, filter accordingly
        if require_fast:
            # Prefer models with low memory usage and fewer steps
            fast_models = [
                m for m in models 
                if m.spec.memory_usage in ['low', 'medium'] and
                (m.spec.num_inference_steps or 30) <= 30
            ]
            if fast_models:
                return max(fast_models, key=lambda m: m.priority)
        
        if require_high_quality:
            # Prefer models with high quality tags and more steps
            quality_models = [
                m for m in models 
                if 'high-quality' in m.tags or 'enhanced' in m.tags or
                (m.spec.num_inference_steps or 30) >= 40
            ]
            if quality_models:
                return max(quality_models, key=lambda m: m.priority)
        
        # Image complexity based selection
        if image_complexity is not None:
            if image_complexity > 0.7:  # Complex image - use high quality
                quality_models = [
                    m for m in models 
                    if 'enhanced' in m.tags or m.version == 'v2'
                ]
                if quality_models:
                    return max(quality_models, key=lambda m: m.priority)
            
            elif image_complexity < 0.3:  # Simple image - use fast model
                simple_models = [
                    m for m in models 
                    if m.spec.memory_usage == 'low' or m.version == 'v1'
                ]
                if simple_models:
                    return max(simple_models, key=lambda m: m.priority)
        
        # Default: highest priority model
        return max(models, key=lambda m: m.priority)
    
    def _build_explanation(
        self,
        model: ModelInfo,
        image_complexity: Optional[float] = None,
        require_fast: bool = False,
        require_high_quality: bool = False
    ) -> str:
        """Build human-readable explanation for selection"""
        
        reasons = []
        
        if require_fast:
            reasons.append("optimized for speed")
        if require_high_quality:
            reasons.append("optimized for quality")
        
        if image_complexity is not None:
            if image_complexity > 0.7:
                reasons.append("selected for complex image processing")
            elif image_complexity < 0.3:
                reasons.append("selected for simple image processing")
        
        if not reasons:
            reasons.append(f"highest priority model (priority: {model.priority})")
        
        reason_text = ", ".join(reasons)
        return f"Auto-selected {model.name} {model.version} - {reason_text}"
    
    def _fallback_to_default(self, selection_metadata: Dict[str, Any]) -> SelectionResult:
        """Fallback to default chain when no model matches criteria"""
        
        for model_id in self.default_fallback_chain:
            model = self.registry.get_model_by_id(model_id)
            if model:
                return SelectionResult(
                    model=model,
                    reason=SelectionReason.DEFAULT,
                    explanation=f"Fallback to default model {model.name} {model.version}",
                    fallback_chain=self.default_fallback_chain,
                    selection_metadata=selection_metadata
                )
        
        # No models available at all
        return SelectionResult(
            model=None,
            reason=SelectionReason.DEFAULT,
            explanation="No models available in fallback chain",
            fallback_chain=self.default_fallback_chain,
            selection_metadata=selection_metadata
        )
    
    def get_fallback_model(self, failed_model_id: str, error_reason: str) -> SelectionResult:
        """
        Get fallback model when primary model fails
        
        Args:
            failed_model_id: ID of model that failed
            error_reason: Reason for failure
            
        Returns:
            SelectionResult with fallback model
        """
        
        # Find position in fallback chain
        try:
            current_index = self.default_fallback_chain.index(failed_model_id)
            fallback_chain = self.default_fallback_chain[current_index + 1:]
        except ValueError:
            # Model not in default chain, use full chain
            fallback_chain = self.default_fallback_chain
        
        # Try each fallback model
        for model_id in fallback_chain:
            model = self.registry.get_model_by_id(model_id)
            if model:
                return SelectionResult(
                    model=model,
                    reason=SelectionReason.FALLBACK_ERROR,
                    explanation=f"Fallback from {failed_model_id} ({error_reason}) to {model.name} {model.version}",
                    fallback_chain=fallback_chain,
                    selection_metadata={
                        'failed_model': failed_model_id,
                        'error_reason': error_reason,
                        'fallback_position': len(self.default_fallback_chain) - len(fallback_chain) + 1
                    }
                )
        
        # No fallback available
        return SelectionResult(
            model=None,
            reason=SelectionReason.FALLBACK_ERROR,
            explanation=f"No fallback available after {failed_model_id} failure: {error_reason}",
            fallback_chain=[],
            selection_metadata={
                'failed_model': failed_model_id,
                'error_reason': error_reason,
                'no_fallback_available': True
            }
        )
    
    def explain_selection_policy(self) -> Dict[str, Any]:
        """Get explanation of selection policy for documentation"""
        
        return {
            'policy_version': '2.0',
            'default_fallback_chain': self.default_fallback_chain,
            'selection_criteria': {
                'user_choice': 'Always preferred when specified and available',
                'auto_selection': {
                    'marketplace_filter': 'Filter models supporting target marketplace',
                    'speed_preference': 'Models with low memory usage and ≤30 steps',
                    'quality_preference': 'Models with high-quality/enhanced tags or ≥40 steps',
                    'complexity_based': {
                        'high_complexity': 'Use enhanced/v2 models for complexity >0.7',
                        'low_complexity': 'Use fast/v1 models for complexity <0.3',
                        'medium_complexity': 'Use highest priority available model'
                    }
                },
                'priority_based': 'Higher priority models preferred when criteria are equal'
            },
            'fallback_logic': {
                'on_user_choice_unavailable': 'Fall back to auto-selection',
                'on_model_failure': 'Move to next model in fallback chain',
                'on_no_models': 'Return error with explanation'
            }
        }


# Global policy instance
selection_policy = ModelSelectionPolicy()