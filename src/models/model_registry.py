"""
Model Registry for K+ Content Service V2.0
Manages LoRA model information and selection logic
"""

import json
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from ..database.db_manager import db_manager


@dataclass
class ModelSpec:
    """Model specification data class"""
    guidance_scale: Optional[float]
    num_inference_steps: Optional[int]
    supports_alpha: bool
    max_resolution: str
    default_output_format: str
    supports_batch: bool
    memory_usage: str
    requires_prompt: bool = True
    
    @classmethod
    def from_json(cls, spec_json: str) -> 'ModelSpec':
        """Create ModelSpec from JSON string"""
        spec_dict = json.loads(spec_json) if isinstance(spec_json, str) else spec_json
        return cls(
            guidance_scale=spec_dict.get('guidance_scale'),
            num_inference_steps=spec_dict.get('num_inference_steps'),
            supports_alpha=spec_dict.get('supports_alpha', True),
            max_resolution=spec_dict.get('max_resolution', '1024x1024'),
            default_output_format=spec_dict.get('default_output_format', 'png'),
            supports_batch=spec_dict.get('supports_batch', False),
            memory_usage=spec_dict.get('memory_usage', 'medium'),
            requires_prompt=spec_dict.get('requires_prompt', True)
        )


@dataclass 
class ModelInfo:
    """Complete model information"""
    id: str
    name: str
    version: str
    provider: str
    endpoint: str
    dataset_notes: Optional[str]
    pros: List[str]
    cons: List[str]
    spec: ModelSpec
    tags: List[str]
    supports_marketplaces: List[str]
    created_at: str
    updated_at: str
    is_active: bool
    priority: int
    
    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> 'ModelInfo':
        """Create ModelInfo from database row"""
        return cls(
            id=row['id'],
            name=row['name'],
            version=row['version'],
            provider=row['provider'],
            endpoint=row['endpoint'],
            dataset_notes=row['dataset_notes'],
            pros=json.loads(row['pros']) if row['pros'] else [],
            cons=json.loads(row['cons']) if row['cons'] else [],
            spec=ModelSpec.from_json(row['spec']),
            tags=json.loads(row['tags']) if row['tags'] else [],
            supports_marketplaces=json.loads(row['supports_marketplaces']) if row['supports_marketplaces'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_active=bool(row['is_active']),
            priority=row['priority']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'provider': self.provider,
            'endpoint': self.endpoint,
            'dataset_notes': self.dataset_notes,
            'pros': self.pros,
            'cons': self.cons,
            'spec': {
                'guidance_scale': self.spec.guidance_scale,
                'num_inference_steps': self.spec.num_inference_steps,
                'supports_alpha': self.spec.supports_alpha,
                'max_resolution': self.spec.max_resolution,
                'default_output_format': self.spec.default_output_format,
                'supports_batch': self.spec.supports_batch,
                'memory_usage': self.spec.memory_usage,
                'requires_prompt': self.spec.requires_prompt
            },
            'tags': self.tags,
            'supports_marketplaces': self.supports_marketplaces,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_active': self.is_active,
            'priority': self.priority
        }


class ModelRegistry:
    """Registry for managing LoRA models"""
    
    def __init__(self):
        """Initialize model registry"""
        self.db_manager = db_manager
    
    def get_all_models(self, active_only: bool = True) -> List[ModelInfo]:
        """
        Get all models from registry
        
        Args:
            active_only: If True, return only active models
            
        Returns:
            List of ModelInfo objects
        """
        try:
            conn = self.db_manager.get_connection()
            
            query = """
                SELECT * FROM models 
                WHERE (? = 0 OR is_active = 1)
                ORDER BY priority DESC, name ASC, version ASC
            """
            
            rows = conn.execute(query, (1 if active_only else 0,)).fetchall()
            conn.close()
            
            return [ModelInfo.from_db_row(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Failed to get models: {e}")
            return []
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get specific model by ID
        
        Args:
            model_id: Model identifier
            
        Returns:
            ModelInfo object or None if not found
        """
        try:
            conn = self.db_manager.get_connection()
            
            row = conn.execute(
                "SELECT * FROM models WHERE id = ? AND is_active = 1",
                (model_id,)
            ).fetchone()
            
            conn.close()
            
            return ModelInfo.from_db_row(row) if row else None
            
        except Exception as e:
            print(f"❌ Failed to get model {model_id}: {e}")
            return None
    
    def get_models_by_tag(self, tag: str) -> List[ModelInfo]:
        """
        Get models by tag
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of matching ModelInfo objects
        """
        try:
            conn = self.db_manager.get_connection()
            
            # Use JSON_EXTRACT for SQLite JSON search
            rows = conn.execute("""
                SELECT * FROM models 
                WHERE is_active = 1 
                AND EXISTS (
                    SELECT 1 FROM json_each(tags) 
                    WHERE json_each.value = ?
                )
                ORDER BY priority DESC
            """, (tag,)).fetchall()
            
            conn.close()
            
            return [ModelInfo.from_db_row(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Failed to get models by tag {tag}: {e}")
            return []
    
    def get_models_by_marketplace(self, marketplace: str) -> List[ModelInfo]:
        """
        Get models supporting specific marketplace
        
        Args:
            marketplace: Marketplace name (e.g., 'yandex-market')
            
        Returns:
            List of compatible ModelInfo objects
        """
        try:
            conn = self.db_manager.get_connection()
            
            rows = conn.execute("""
                SELECT * FROM models 
                WHERE is_active = 1 
                AND EXISTS (
                    SELECT 1 FROM json_each(supports_marketplaces) 
                    WHERE json_each.value = ?
                )
                ORDER BY priority DESC
            """, (marketplace,)).fetchall()
            
            conn.close()
            
            return [ModelInfo.from_db_row(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Failed to get models for marketplace {marketplace}: {e}")
            return []
    
    def get_model_summary(self) -> Dict[str, Any]:
        """
        Get registry summary statistics
        
        Returns:
            Dictionary with registry statistics
        """
        try:
            conn = self.db_manager.get_connection()
            
            # Get counts
            total_models = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
            active_models = conn.execute("SELECT COUNT(*) FROM models WHERE is_active = 1").fetchone()[0]
            
            # Get providers
            providers = [row[0] for row in conn.execute(
                "SELECT DISTINCT provider FROM models WHERE is_active = 1 ORDER BY provider"
            ).fetchall()]
            
            # Get unique tags
            all_tags = []
            for row in conn.execute("SELECT tags FROM models WHERE is_active = 1").fetchall():
                if row[0]:
                    all_tags.extend(json.loads(row[0]))
            unique_tags = sorted(list(set(all_tags)))
            
            conn.close()
            
            return {
                'total_models': total_models,
                'active_models': active_models,
                'providers': providers,
                'available_tags': unique_tags,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Failed to get model summary: {e}")
            return {}


# Global registry instance
model_registry = ModelRegistry()