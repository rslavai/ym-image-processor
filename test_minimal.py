#!/usr/bin/env python3
"""Минимальный тест для диагностики проблем."""

import gradio as gr
import sys
from pathlib import Path

print("Python версия:", sys.version)
print("Gradio версия:", gr.__version__)

# Простейшая функция
def greet(name):
    return f"Привет, {name}!"

# Минимальный интерфейс
demo = gr.Interface(
    fn=greet,
    inputs="text",
    outputs="text",
    title="Тест Gradio"
)

if __name__ == "__main__":
    print("\n🚀 Запуск минимального теста...")
    print("Попробуйте открыть: http://localhost:7863")
    print("Или: http://127.0.0.1:7863")
    print("Или: http://0.0.0.0:7863")
    
    # Запускаем с разными настройками
    demo.launch(
        server_name="0.0.0.0",  # Слушаем все интерфейсы
        server_port=7863,
        share=False,
        inbrowser=False,
        quiet=False,
        show_api=False,
        prevent_thread_lock=False
    )