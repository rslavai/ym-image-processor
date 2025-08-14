#!/usr/bin/env python3
"""Простой тест Gradio UI."""

import gradio as gr
from PIL import Image
import numpy as np
import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent))

try:
    from src.processors.background import BackgroundRemover
    print("✓ BackgroundRemover импортирован успешно")
    processor_available = True
    remover = BackgroundRemover()
except Exception as e:
    print(f"✗ Ошибка импорта BackgroundRemover: {e}")
    processor_available = False
    remover = None

def process_image(image):
    if image is None:
        return None, "Загрузите изображение"
    
    if not processor_available:
        return image, "Процессор недоступен - проверьте консоль для ошибок"
    
    try:
        result = remover.process(image)
        return result, "✅ Обработка завершена!"
    except Exception as e:
        return image, f"❌ Ошибка: {str(e)}"

# Создаем простой интерфейс
with gr.Blocks(title="YM Image Processor - Тест") as demo:
    gr.Markdown("# 🛍️ Yandex Market Image Processor - Простой тест")
    
    with gr.Row():
        with gr.Column():
            input_image = gr.Image(
                label="Исходное изображение",
                type="pil"
            )
            process_btn = gr.Button("🚀 Удалить фон", variant="primary")
        
        with gr.Column():
            output_image = gr.Image(
                label="Результат",
                type="pil"
            )
            status = gr.Textbox(label="Статус", interactive=False)
    
    process_btn.click(
        fn=process_image,
        inputs=[input_image],
        outputs=[output_image, status]
    )

if __name__ == "__main__":
    print("🚀 Запуск простого тестового UI...")
    print("Откройте браузер по адресу: http://127.0.0.1:7862")
    demo.launch(
        server_name="127.0.0.1",
        server_port=7862,
        share=False,
        inbrowser=False,  # Не открывать автоматически
        quiet=False  # Показывать все логи
    )