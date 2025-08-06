#!/usr/bin/env python3
"""
Простой CLI интерфейс для тестирования обработки изображений.
Работает напрямую без веб-сервера.
"""

import sys
import os
from pathlib import Path
from PIL import Image
import argparse

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from src.processors.background import BackgroundRemover


def process_image(input_path, output_path=None):
    """
    Обработка одного изображения.
    
    Args:
        input_path: Путь к входному изображению
        output_path: Путь для сохранения результата
    """
    print(f"\n📸 Обработка изображения: {input_path}")
    print("-" * 50)
    
    # Проверяем существование файла
    if not os.path.exists(input_path):
        print(f"❌ Файл не найден: {input_path}")
        return False
    
    try:
        # Инициализируем процессор с улучшенными настройками
        print("🔧 Инициализация процессора...")
        processor = BackgroundRemover({
            'model': 'u2net',
            'alpha_matting': True,
            'post_process': True,
            'min_object_size': 500
        })
        
        # Обрабатываем изображение
        print("🎨 Удаление фона...")
        result = processor.process(input_path)
        
        # Определяем путь для сохранения
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.parent / f"{input_file.stem}_no_bg.png"
        
        # Сохраняем результат
        print(f"💾 Сохранение результата: {output_path}")
        result.save(str(output_path), 'PNG')
        
        print(f"✅ Успешно обработано!")
        print(f"📁 Результат сохранен: {output_path}")
        
        # Показываем размеры
        original = Image.open(input_path)
        print(f"\n📊 Информация:")
        print(f"   Исходный размер: {original.size}")
        print(f"   Формат результата: RGBA (с прозрачностью)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")
        return False


def batch_process(folder_path, output_folder=None):
    """
    Пакетная обработка всех изображений в папке.
    
    Args:
        folder_path: Путь к папке с изображениями
        output_folder: Папка для сохранения результатов
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Папка не найдена: {folder_path}")
        return
    
    # Создаем папку для результатов
    if output_folder:
        output_dir = Path(output_folder)
    else:
        output_dir = folder / "processed"
    
    output_dir.mkdir(exist_ok=True)
    
    # Находим все изображения
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    images = []
    for ext in image_extensions:
        images.extend(folder.glob(f"*{ext}"))
        images.extend(folder.glob(f"*{ext.upper()}"))
    
    if not images:
        print(f"⚠️  Изображения не найдены в папке: {folder_path}")
        return
    
    print(f"\n📂 Найдено изображений: {len(images)}")
    print(f"📁 Результаты будут сохранены в: {output_dir}")
    print("-" * 50)
    
    # Обрабатываем каждое изображение
    successful = 0
    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Обработка: {img_path.name}")
        output_path = output_dir / f"{img_path.stem}_no_bg.png"
        
        if process_image(str(img_path), str(output_path)):
            successful += 1
    
    print("\n" + "=" * 50)
    print(f"✨ Обработка завершена!")
    print(f"✅ Успешно обработано: {successful}/{len(images)}")
    print(f"📁 Результаты в папке: {output_dir}")


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description='🛍️ Yandex Market Image Processor - удаление фона с изображений товаров',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Обработать одно изображение
  python test_processor.py image.jpg
  
  # Сохранить с конкретным именем
  python test_processor.py image.jpg -o result.png
  
  # Обработать все изображения в папке
  python test_processor.py --batch ./images
  
  # Сохранить результаты в конкретную папку
  python test_processor.py --batch ./images -o ./output
        """
    )
    
    parser.add_argument('input', nargs='?', help='Путь к изображению для обработки')
    parser.add_argument('-o', '--output', help='Путь для сохранения результата')
    parser.add_argument('--batch', metavar='FOLDER', help='Пакетная обработка всех изображений в папке')
    
    args = parser.parse_args()
    
    # Проверяем аргументы
    if not args.input and not args.batch:
        print("\n🎯 Интерактивный режим")
        print("-" * 50)
        
        choice = input("\nВыберите режим:\n1. Обработать одно изображение\n2. Обработать папку с изображениями\n\nВаш выбор (1 или 2): ")
        
        if choice == '1':
            input_path = input("\nВведите путь к изображению: ").strip()
            if input_path:
                output_path = input("Путь для сохранения (Enter для автоматического): ").strip()
                process_image(input_path, output_path if output_path else None)
        
        elif choice == '2':
            folder_path = input("\nВведите путь к папке с изображениями: ").strip()
            if folder_path:
                output_folder = input("Папка для результатов (Enter для автоматической): ").strip()
                batch_process(folder_path, output_folder if output_folder else None)
        else:
            print("❌ Неверный выбор")
    
    elif args.batch:
        # Пакетная обработка
        batch_process(args.batch, args.output)
    
    elif args.input:
        # Обработка одного файла
        process_image(args.input, args.output)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🛍️ YANDEX MARKET IMAGE PROCESSOR")
    print("Удаление фона с изображений товаров")
    print("=" * 50)
    
    main()