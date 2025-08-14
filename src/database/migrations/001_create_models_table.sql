-- Migration: Create models table for LoRA model registry
-- Version: V2.0
-- Date: 2025-01-14

CREATE TABLE IF NOT EXISTS models (
    -- Primary identification
    id TEXT PRIMARY KEY,              -- flux-kontext-lora-v1, flux-kontext-lora-v2
    name TEXT NOT NULL,               -- FLUX Kontext LoRA
    version TEXT NOT NULL,            -- v1, v2, v3
    provider TEXT NOT NULL,           -- fal-ai, replicate, huggingface
    endpoint TEXT NOT NULL,           -- fal-ai/flux-kontext-lora
    
    -- Model description and training info
    dataset_notes TEXT,               -- Training dataset description
    
    -- Model characteristics (JSON arrays for flexibility)
    pros JSON NOT NULL DEFAULT '[]', -- ["Fast processing", "High quality", "Stable results"]
    cons JSON NOT NULL DEFAULT '[]', -- ["Limited accuracy on complex images", "Requires specific prompts"]
    
    -- Technical specifications
    spec JSON NOT NULL DEFAULT '{}', -- {
                                     --   "guidance_scale": 2.5,
                                     --   "num_inference_steps": 30,
                                     --   "supports_alpha": true,
                                     --   "max_resolution": "1024x1024",
                                     --   "default_output_format": "png"
                                     -- }
    
    -- Categorization and search
    tags JSON NOT NULL DEFAULT '[]', -- ["ecommerce", "background-removal", "product-photography"]
    
    -- Marketplace compatibility
    supports_marketplaces JSON NOT NULL DEFAULT '[]', -- ["yandex-market", "ozon", "wildberries", "amazon"]
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,   -- For soft-delete and model lifecycle
    priority INTEGER DEFAULT 0       -- For auto-selection ordering (higher = preferred)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_version ON models(version);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_models_priority ON models(priority DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_models_timestamp 
    AFTER UPDATE ON models
    FOR EACH ROW
    BEGIN
        UPDATE models SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;