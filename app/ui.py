"""
Минимальный UI для тестирования Yandex Market Image Processor.

Использует Gradio для создания веб-интерфейса.
"""

import gradio as gr
from PIL import Image
import numpy as np
from pathlib import Path
import sys
import time
from typing import Optional, Tuple
import io
import zipfile

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from src.processors.background import BackgroundRemover
from src.utils.image_helpers import calculate_image_complexity


class ImageProcessorUI:
    """Класс для управления интерфейсом обработки изображений."""
    
    def __init__(self):
        """Инициализация UI и процессоров."""
        self.remover = None
        self._init_processor()
        
    def _init_processor(self):
        """Инициализация процессора удаления фона."""
        try:
            self.remover = BackgroundRemover({
                'debug': False,
                'use_cache': True
            })
            return "✅ Процессор инициализирован"
        except Exception as e:
            return f"❌ Ошибка инициализации: {str(e)}"
    
    def process_single_image(
        self, 
        image: Optional[Image.Image],
        use_alpha_matting: bool,
        post_process: bool,
        min_object_size: int,
        show_mask: bool
    ) -> Tuple[Optional[Image.Image], Optional[Image.Image], str]:
        """
        Обработка одного изображения.
        
        Returns:
            Кортеж (результат, маска, информация)
        """
        if image is None:
            return None, None, "⚠️ Загрузите изображение"
        
        try:
            start_time = time.time()
            
            # Обновляем настройки процессора
            self.remover.use_alpha_matting = use_alpha_matting
            self.remover.post_process = post_process
            self.remover.min_object_size = min_object_size
            
            # Анализ сложности
            complexity = calculate_image_complexity(image)
            
            # Обработка
            if show_mask:
                result, mask = self.remover.process(image, return_mask=True)
                # Конвертируем маску в PIL Image
                mask_image = Image.fromarray(mask, mode='L')
            else:
                result = self.remover.process(image)
                mask_image = None
            
            # Время обработки
            processing_time = time.time() - start_time
            
            # Информация об обработке
            info = f"""
### ✅ Обработка завершена

**Время обработки:** {processing_time:.2f} сек  
**Размер изображения:** {image.size[0]}x{image.size[1]}  
**Сложность изображения:** {complexity['overall_complexity']:.2f}  
**Режим:** {'Alpha Matting' if use_alpha_matting else 'Обычный'}  
**Пост-обработка:** {'Включена' if post_process else 'Выключена'}
            """
            
            return result, mask_image, info
            
        except Exception as e:
            error_info = f"### ❌ Ошибка обработки\n\n{str(e)}"
            return None, None, error_info
    
    def process_batch(
        self,
        files,
        use_alpha_matting: bool,
        post_process: bool,
        min_object_size: int
    ) -> Tuple[Optional[str], str]:
        """
        Пакетная обработка изображений.
        
        Returns:
            Кортеж (путь к zip архиву, информация)
        """
        if not files:
            return None, "⚠️ Загрузите изображения"
        
        try:
            # Обновляем настройки
            self.remover.use_alpha_matting = use_alpha_matting
            self.remover.post_process = post_process
            self.remover.min_object_size = min_object_size
            
            # Создаем временный zip архив
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                processed = 0
                errors = 0
                
                for file in files:
                    try:
                        # Загружаем изображение
                        image = Image.open(file.name)
                        
                        # Обрабатываем
                        result = self.remover.process(image)
                        
                        # Сохраняем в архив
                        img_buffer = io.BytesIO()
                        result.save(img_buffer, format='PNG')
                        
                        filename = Path(file.name).stem + '_no_bg.png'
                        zip_file.writestr(filename, img_buffer.getvalue())
                        
                        processed += 1
                        
                    except Exception as e:
                        errors += 1
                        print(f"Ошибка при обработке {file.name}: {e}")
            
            # Сохраняем архив
            output_path = "processed_images.zip"
            with open(output_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            
            info = f"""
### ✅ Пакетная обработка завершена

**Обработано успешно:** {processed}  
**Ошибок:** {errors}  
**Всего файлов:** {len(files)}
            """
            
            return output_path, info
            
        except Exception as e:
            return None, f"### ❌ Ошибка пакетной обработки\n\n{str(e)}"
    
    def create_demo_image(self, demo_type: str) -> Optional[Image.Image]:
        """Создание демонстрационного изображения."""
        try:
            from PIL import ImageDraw
            
            if demo_type == "Простой объект":
                img = Image.new('RGB', (400, 400), color=(220, 220, 220))
                draw = ImageDraw.Draw(img)
                draw.ellipse([100, 100, 300, 300], fill=(255, 100, 100))
                
            elif demo_type == "Сложный фон":
                img = Image.new('RGB', (400, 400))
                pixels = img.load()
                # Градиентный фон
                for i in range(400):
                    for j in range(400):
                        pixels[i, j] = (
                            int(i * 255 / 400),
                            int(j * 255 / 400),
                            200
                        )
                draw = ImageDraw.Draw(img)
                # Объект
                draw.rectangle([150, 150, 250, 250], fill=(0, 200, 0))
                
            elif demo_type == "Реалистичный товар":
                img = Image.new('RGB', (400, 400), color=(240, 240, 240))
                draw = ImageDraw.Draw(img)
                # Коробка в 3D
                # Передняя грань
                draw.polygon([(100, 200), (200, 150), (200, 350), (100, 300)], 
                           fill=(100, 150, 200), outline=(50, 75, 100), width=2)
                # Верхняя грань
                draw.polygon([(100, 200), (200, 150), (300, 200), (200, 250)], 
                           fill=(120, 170, 220), outline=(50, 75, 100), width=2)
                # Боковая грань
                draw.polygon([(200, 150), (300, 200), (300, 300), (200, 350)], 
                           fill=(80, 130, 180), outline=(50, 75, 100), width=2)
            else:
                return None
                
            return img
            
        except Exception as e:
            print(f"Ошибка создания демо: {e}")
            return None
    
    def create_interface(self) -> gr.Blocks:
        """Создание интерфейса Gradio."""
        
        with gr.Blocks(
            title="YM Image Processor",
            theme=gr.themes.Soft()
        ) as interface:
            
            # Заголовок
            gr.Markdown(
                """
                # 🛍️ Yandex Market Image Processor
                
                Тестовый интерфейс для обработки изображений товаров.
                Текущий модуль: **Удаление фона**
                """
            )
            
            with gr.Tabs():
                # Вкладка одиночной обработки
                with gr.TabItem("🖼️ Обработка изображения"):
                    with gr.Row():
                        # Левая колонка - ввод
                        with gr.Column(scale=1):
                            input_image = gr.Image(
                                label="Исходное изображение",
                                type="pil",
                                height=400
                            )
                            
                            # Настройки в аккордеоне
                            with gr.Accordion("⚙️ Настройки обработки", open=False):
                                alpha_matting = gr.Checkbox(
                                    label="Alpha Matting (мягкие края)",
                                    value=False,
                                    info="Более качественная обработка краев, но медленнее"
                                )
                                post_process = gr.Checkbox(
                                    label="Пост-обработка маски",
                                    value=True,
                                    info="Удаление артефактов и улучшение маски"
                                )
                                min_size = gr.Slider(
                                    minimum=100,
                                    maximum=5000,
                                    value=1000,
                                    step=100,
                                    label="Минимальный размер объекта (пикс.)",
                                    info="Объекты меньше этого размера будут удалены"
                                )
                                show_mask = gr.Checkbox(
                                    label="Показать маску",
                                    value=False,
                                    info="Отобразить маску сегментации"
                                )
                            
                            # Кнопки
                            with gr.Row():
                                process_btn = gr.Button(
                                    "🚀 Обработать",
                                    variant="primary",
                                    scale=2
                                )
                                clear_btn = gr.Button("🗑️ Очистить", scale=1)
                            
                            # Демо изображения
                            with gr.Accordion("🎨 Создать тестовое изображение", open=False):
                                demo_type = gr.Radio(
                                    choices=["Простой объект", "Сложный фон", "Реалистичный товар"],
                                    label="Тип изображения",
                                    value="Простой объект"
                                )
                                create_demo_btn = gr.Button("Создать демо")
                        
                        # Правая колонка - результат
                        with gr.Column(scale=1):
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
                            info_text = gr.Markdown("Загрузите изображение для начала")
                    
                    # Обработчики событий
                    process_btn.click(
                        fn=self.process_single_image,
                        inputs=[input_image, alpha_matting, post_process, min_size, show_mask],
                        outputs=[output_image, mask_image, info_text]
                    )
                    
                    clear_btn.click(
                        fn=lambda: (None, None, None, "Загрузите изображение для начала"),
                        inputs=[],
                        outputs=[input_image, output_image, mask_image, info_text]
                    )
                    
                    create_demo_btn.click(
                        fn=self.create_demo_image,
                        inputs=[demo_type],
                        outputs=[input_image]
                    )
                    
                    # Показ/скрытие маски
                    show_mask.change(
                        fn=lambda x: gr.update(visible=x),
                        inputs=[show_mask],
                        outputs=[mask_image]
                    )
                
                # Вкладка пакетной обработки
                with gr.TabItem("📦 Пакетная обработка"):
                    gr.Markdown(
                        """
                        ### Загрузите несколько изображений для пакетной обработки
                        
                        Результаты будут сохранены в ZIP архив.
                        """
                    )
                    
                    with gr.Row():
                        with gr.Column():
                            batch_files = gr.File(
                                label="Загрузите изображения",
                                file_count="multiple",
                                file_types=["image"]
                            )
                            
                            # Настройки
                            with gr.Accordion("⚙️ Настройки", open=True):
                                batch_alpha = gr.Checkbox(label="Alpha Matting", value=False)
                                batch_post = gr.Checkbox(label="Пост-обработка", value=True)
                                batch_min_size = gr.Slider(
                                    minimum=100,
                                    maximum=5000,
                                    value=1000,
                                    label="Мин. размер объекта"
                                )
                            
                            batch_process_btn = gr.Button(
                                "🚀 Обработать все",
                                variant="primary"
                            )
                        
                        with gr.Column():
                            batch_output = gr.File(
                                label="Скачать результаты",
                                visible=False
                            )
                            batch_info = gr.Markdown("")
                    
                    batch_process_btn.click(
                        fn=self.process_batch,
                        inputs=[batch_files, batch_alpha, batch_post, batch_min_size],
                        outputs=[batch_output, batch_info]
                    ).then(
                        fn=lambda x: gr.update(visible=x is not None),
                        inputs=[batch_output],
                        outputs=[batch_output]
                    )
                
                # Вкладка информации
                with gr.TabItem("ℹ️ О программе"):
                    gr.Markdown(
                        """
                        ## Yandex Market Image Processor
                        
                        ### 📌 Версия: 0.1.0
                        
                        ### 🔧 Текущие возможности:
                        - **Удаление фона** - автоматическое удаление фона с использованием нейросети U²-Net
                        - **Пост-обработка** - улучшение качества масок
                        - **Alpha Matting** - продвинутая обработка полупрозрачных краев
                        - **Пакетная обработка** - обработка нескольких изображений одновременно
                        
                        ### 🚀 В разработке:
                        - Генерация теней
                        - Цветокоррекция
                        - Увеличение разрешения
                        - Полный pipeline обработки
                        
                        ### 📊 Рекомендации:
                        - Для лучших результатов используйте изображения с четким контрастом между объектом и фоном
                        - Alpha Matting рекомендуется для изображений с мягкими краями (ткань, волосы)
                        - Пост-обработка помогает убрать мелкие артефакты
                        
                        ### 🛠️ Технологии:
                        - Python 3.8+
                        - rembg (U²-Net)
                        - OpenCV
                        - Pillow
                        - Gradio
                        """
                    )
            
            # Футер
            gr.Markdown(
                """
                ---
                <center>
                    Made with ❤️ for Yandex Market | 
                    <a href="https://github.com/anthropics/claude-code" target="_blank">🤖 Generated with Claude Code</a>
                </center>
                """,
                elem_id="footer"
            )
        
        return interface


def main():
    """Запуск приложения."""
    print("🚀 Запуск Yandex Market Image Processor UI...")
    
    # Создаем интерфейс
    ui = ImageProcessorUI()
    interface = ui.create_interface()
    
    # Запускаем
    interface.launch(
        server_name="127.0.0.1",
        server_port=7861,
        share=False,
        inbrowser=True
    )


if __name__ == "__main__":
    main()