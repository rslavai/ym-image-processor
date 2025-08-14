-- Seed data: Initial LoRA models for registry
-- Version: V2.0
-- Date: 2025-01-14

INSERT OR REPLACE INTO models (
    id, name, version, provider, endpoint, dataset_notes, pros, cons, spec, tags, supports_marketplaces, priority
) VALUES 

-- FLUX Kontext LoRA V1 (Original)
(
    'flux-kontext-lora-v1',
    'FLUX Kontext LoRA',
    'v1',
    'fal-ai',
    'fal-ai/flux-kontext-lora',
    'Обучена на товарах Яндекс.Маркета. Базовая модель для удаления фона с хорошим балансом скорости и качества.',
    '["Быстрая обработка (30 сек)", "Стабильные результаты", "Хорошо работает с простыми фонами", "Низкое потребление ресурсов"]',
    '["Ограниченная точность на сложных изображениях", "Может оставлять артефакты на краях", "Требует четкого промпта"]',
    '{
        "guidance_scale": 2.5,
        "num_inference_steps": 30,
        "supports_alpha": true,
        "max_resolution": "1024x1024",
        "default_output_format": "png",
        "supports_batch": false,
        "memory_usage": "low"
    }',
    '["ecommerce", "background-removal", "product-photography", "marketplace", "baseline"]',
    '["yandex-market", "ozon", "wildberries"]',
    10
),

-- FLUX Kontext LoRA V2 (Enhanced)
(
    'flux-kontext-lora-v2',
    'FLUX Kontext LoRA',
    'v2',
    'fal-ai', 
    'fal-ai/flux-kontext-lora',
    'Улучшенная модель, обученная на расширенном датасете с более точным удалением фона и лучшим качеством краев.',
    '["Высокое качество обработки", "Точное выделение краев", "Работает с прозрачными объектами", "Улучшенная обработка теней"]',
    '["Медленнее V1 (50 сек)", "Выше требования к ресурсам", "Более чувствительна к промптам", "Может быть избыточной для простых изображений"]',
    '{
        "guidance_scale": 3.5,
        "num_inference_steps": 50,
        "supports_alpha": true,
        "max_resolution": "1024x1024",
        "default_output_format": "png",
        "supports_batch": false,
        "memory_usage": "medium",
        "enhanced_edges": true
    }',
    '["ecommerce", "background-removal", "product-photography", "marketplace", "enhanced", "high-quality"]',
    '["yandex-market", "ozon", "wildberries", "amazon"]',
    20
),

-- BiRefNet Fallback
(
    'birefnet-fallback',
    'BiRefNet',
    'v1',
    'fal-ai',
    'fal-ai/birefnet',
    'Универсальная модель удаления фона. Используется как fallback когда LoRA модели недоступны или дают ошибки.',
    '["Высокая надежность", "Универсальность", "Быстрая обработка", "Не требует промптов", "Стабильная работа"]',
    '["Менее точная для товаров", "Общего назначения", "Может терять детали", "Ограниченная настройка"]',
    '{
        "guidance_scale": null,
        "num_inference_steps": null,
        "supports_alpha": true,
        "max_resolution": "1024x1024", 
        "default_output_format": "png",
        "supports_batch": true,
        "memory_usage": "low",
        "requires_prompt": false
    }',
    '["background-removal", "universal", "fallback", "reliable"]',
    '["yandex-market", "ozon", "wildberries", "amazon", "general"]',
    5
);

-- Verify seed data
SELECT 
    id,
    name || ' ' || version as model_name,
    provider,
    priority,
    json_extract(spec, '$.guidance_scale') as guidance_scale,
    json_extract(spec, '$.num_inference_steps') as steps
FROM models 
ORDER BY priority DESC;