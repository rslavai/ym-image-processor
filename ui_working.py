#!/usr/bin/env python3
"""Рабочий UI для Yandex Market Image Processor."""

import gradio as gr
from PIL import Image
import numpy as np
import sys
from pathlib import Path
import traceback

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent))

# Пытаемся импортировать процессор
try:
    from src.processors.background import BackgroundRemover
    print("✓ BackgroundRemover импортирован успешно")
    remover = BackgroundRemover({
        'debug': False,
        'use_cache': True
    })
    processor_available = True
except Exception as e:
    print(f"✗ Ошибка при инициализации BackgroundRemover: {e}")
    print("Traceback:", traceback.format_exc())
    processor_available = False
    remover = None

def process_image(image, use_alpha_matting, show_mask):
    """Обработка изображения."""
    if image is None:
        return None, None, "⚠️ Загрузите изображение"
    
    if not processor_available:
        return None, None, "❌ Процессор недоступен. Проверьте консоль для деталей."
    
    try:
        # Настройки процессора
        remover.use_alpha_matting = use_alpha_matting
        
        # Обработка
        if show_mask:
            result, mask = remover.process(image, return_mask=True)
            mask_image = Image.fromarray(mask, mode='L')
        else:
            result = remover.process(image)
            mask_image = None
        
        return result, mask_image, "✅ Обработка завершена успешно!"
        
    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        print("Ошибка при обработке:", traceback.format_exc())
        return None, None, error_msg

def create_test_image(image_type):
    """Создание тестового изображения."""
    try:
        from PIL import ImageDraw
        
        if image_type == "Простой объект":
            # Белый фон с красным кругом
            img = Image.new('RGB', (400, 400), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            draw.ellipse([50, 50, 350, 350], fill=(255, 0, 0))
            
        elif image_type == "Сложный фон":
            # Градиентный фон с зеленым квадратом
            img = Image.new('RGB', (400, 400))
            pixels = img.load()
            for i in range(400):
                for j in range(400):
                    pixels[i, j] = (
                        int(i * 255 / 400),
                        int(j * 255 / 400),
                        200
                    )
            draw = ImageDraw.Draw(img)
            draw.rectangle([100, 100, 300, 300], fill=(0, 255, 0))
            
        else:  # Товар на фоне
            # Серый фон с синей "коробкой"
            img = Image.new('RGB', (400, 400), color=(200, 200, 200))
            draw = ImageDraw.Draw(img)
            # Простая коробка
            draw.rectangle([100, 150, 300, 350], fill=(50, 100, 200))
            draw.rectangle([100, 100, 300, 150], fill=(70, 120, 220))
            
        return img
    except Exception as e:
        print(f"Ошибка создания тестового изображения: {e}")
        return None

# Создаем интерфейс
with gr.Blocks(
    title="YM Image Processor",
    theme=gr.themes.Soft()
) as demo:
    
    gr.Markdown(
        """
        # 🛍️ Yandex Market Image Processor
        
        ### Модуль удаления фона
        Загрузите изображение товара для автоматического удаления фона.
        """
    )
    
    with gr.Row():
        # Левая колонка - ввод
        with gr.Column():
            input_image = gr.Image(
                label="Исходное изображение",
                type="pil",
                height=400
            )
            
            # Настройки
            with gr.Row():
                alpha_matting = gr.Checkbox(
                    label="Alpha Matting",
                    value=False,
                    info="Мягкие края (медленнее)"
                )
                show_mask = gr.Checkbox(
                    label="Показать маску",
                    value=False
                )
            
            # Кнопки
            with gr.Row():
                process_btn = gr.Button(
                    "🚀 Удалить фон",
                    variant="primary",
                    scale=2
                )
                clear_btn = gr.Button("🗑️ Очистить", scale=1)
            
            # Тестовые изображения
            gr.Markdown("### Создать тестовое изображение:")
            with gr.Row():
                test_type = gr.Radio(
                    choices=["Простой объект", "Сложный фон", "Товар на фоне"],
                    value="Простой объект",
                    label="Тип"
                )
                create_test_btn = gr.Button("Создать")
        
        # Правая колонка - результат
        with gr.Column():
            output_image = gr.Image(
                label="Результат",
                type="pil",
                height=400
            )
            mask_image = gr.Image(
                label="Маска",
                type="pil",
                height=300,
                visible=False
            )
            status = gr.Textbox(
                label="Статус",
                value="Загрузите изображение для начала",
                interactive=False
            )
    
    # Обработчики событий
    process_btn.click(
        fn=process_image,
        inputs=[input_image, alpha_matting, show_mask],
        outputs=[output_image, mask_image, status]
    )
    
    clear_btn.click(
        fn=lambda: (None, None, None, "Загрузите изображение для начала"),
        outputs=[input_image, output_image, mask_image, status]
    )
    
    create_test_btn.click(
        fn=create_test_image,
        inputs=[test_type],
        outputs=[input_image]
    )
    
    # Показ/скрытие маски
    show_mask.change(
        fn=lambda x: gr.update(visible=x),
        inputs=[show_mask],
        outputs=[mask_image]
    )

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 Запуск Yandex Market Image Processor UI")
    print("="*50)
    print(f"Версия Gradio: {gr.__version__}")
    print(f"Процессор доступен: {'✓' if processor_available else '✗'}")
    print("\nОткройте браузер по адресу: http://127.0.0.1:7864")
    print("Для остановки нажмите Ctrl+C")
    print("="*50 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7864,
        share=False,
        inbrowser=False,
        quiet=False
    )