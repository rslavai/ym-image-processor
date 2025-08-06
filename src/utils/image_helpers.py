"""
Вспомогательные функции для работы с изображениями.

Этот модуль содержит утилиты для загрузки, сохранения и базовой
обработки изображений в проекте Yandex Market Image Processor.
"""

from typing import Union, Tuple, Optional, List, Dict, Any
from pathlib import Path
import hashlib
from io import BytesIO
import logging

import numpy as np
from PIL import Image, ImageOps, ExifTags
import cv2


logger = logging.getLogger(__name__)


# Поддерживаемые форматы изображений
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}

# Максимальный размер для обработки (для защиты от слишком больших изображений)
MAX_IMAGE_SIZE = 10000  # пикселей по любой стороне


def load_image(image_path: Union[str, Path], 
               fix_orientation: bool = True) -> Image.Image:
    """
    Загрузка изображения с обработкой ориентации EXIF.
    
    Args:
        image_path: Путь к изображению
        fix_orientation: Исправлять ли ориентацию согласно EXIF
        
    Returns:
        PIL Image объект
        
    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если формат не поддерживается
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    
    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Неподдерживаемый формат: {path.suffix}. "
            f"Поддерживаются: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    try:
        image = Image.open(path)
        
        # Исправляем ориентацию если нужно
        if fix_orientation:
            image = fix_image_orientation(image)
        
        # Проверяем размер
        if max(image.size) > MAX_IMAGE_SIZE:
            logger.warning(
                f"Изображение слишком большое: {image.size}. "
                f"Максимальный размер: {MAX_IMAGE_SIZE}"
            )
            # Можно добавить автоматическое уменьшение
        
        return image
        
    except Exception as e:
        raise ValueError(f"Ошибка при загрузке изображения: {e}")


def save_image(image: Image.Image, 
               output_path: Union[str, Path],
               format: Optional[str] = None,
               quality: int = 95,
               optimize: bool = True) -> Path:
    """
    Сохранение изображения с оптимизацией.
    
    Args:
        image: PIL Image для сохранения
        output_path: Путь для сохранения
        format: Формат файла (если None, определяется по расширению)
        quality: Качество для JPEG (1-100)
        optimize: Оптимизировать ли размер файла
        
    Returns:
        Path к сохраненному файлу
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Определяем формат
    if format is None:
        format = output_path.suffix.upper().lstrip('.')
        if format == 'JPG':
            format = 'JPEG'
    
    # Параметры сохранения
    save_kwargs = {
        'format': format,
        'optimize': optimize
    }
    
    # Специфичные параметры для разных форматов
    if format == 'JPEG':
        save_kwargs['quality'] = quality
        save_kwargs['progressive'] = True
        # Конвертируем RGBA в RGB для JPEG
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
    
    elif format == 'PNG':
        save_kwargs['compress_level'] = 9 if optimize else 6
    
    # Сохраняем
    image.save(output_path, **save_kwargs)
    logger.info(f"Изображение сохранено: {output_path} ({format})")
    
    return output_path


def fix_image_orientation(image: Image.Image) -> Image.Image:
    """
    Исправление ориентации изображения согласно EXIF данным.
    
    Args:
        image: PIL Image
        
    Returns:
        Исправленное изображение
    """
    try:
        # Получаем EXIF данные
        exif = image._getexif()
        if exif is None:
            return image
        
        # Находим тег ориентации
        orientation_key = None
        for key, value in ExifTags.TAGS.items():
            if value == 'Orientation':
                orientation_key = key
                break
        
        if orientation_key is None:
            return image
        
        orientation = exif.get(orientation_key)
        
        # Применяем соответствующую трансформацию
        if orientation == 2:
            return ImageOps.mirror(image)
        elif orientation == 3:
            return image.rotate(180, expand=True)
        elif orientation == 4:
            return ImageOps.flip(image)
        elif orientation == 5:
            return ImageOps.mirror(image.rotate(270, expand=True))
        elif orientation == 6:
            return image.rotate(270, expand=True)
        elif orientation == 7:
            return ImageOps.mirror(image.rotate(90, expand=True))
        elif orientation == 8:
            return image.rotate(90, expand=True)
        
    except Exception as e:
        logger.warning(f"Не удалось обработать EXIF ориентацию: {e}")
    
    return image


def resize_image(image: Image.Image, 
                 max_size: Optional[int] = None,
                 target_size: Optional[Tuple[int, int]] = None,
                 maintain_aspect: bool = True,
                 resample: int = Image.Resampling.LANCZOS) -> Image.Image:
    """
    Изменение размера изображения.
    
    Args:
        image: Исходное изображение
        max_size: Максимальный размер по большей стороне
        target_size: Целевой размер (width, height)
        maintain_aspect: Сохранять ли соотношение сторон
        resample: Метод интерполяции
        
    Returns:
        Измененное изображение
    """
    if max_size is not None:
        # Уменьшаем по максимальной стороне
        ratio = max_size / max(image.size)
        if ratio < 1:
            new_size = tuple(int(dim * ratio) for dim in image.size)
            return image.resize(new_size, resample=resample)
    
    elif target_size is not None:
        if maintain_aspect:
            # Вписываем в целевой размер с сохранением пропорций
            image.thumbnail(target_size, resample=resample)
            return image
        else:
            # Точное изменение размера
            return image.resize(target_size, resample=resample)
    
    return image


def calculate_image_complexity(image: Union[Image.Image, np.ndarray]) -> Dict[str, float]:
    """
    Расчет метрик сложности изображения.
    
    Используется для определения сложности удаления фона.
    
    Args:
        image: Изображение для анализа
        
    Returns:
        Словарь с метриками сложности
    """
    # Конвертируем в numpy если нужно
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image
    
    # Конвертируем в grayscale для анализа
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Вычисляем метрики
    metrics = {}
    
    # 1. Количество краев (сложность контуров)
    edges = cv2.Canny(gray, 50, 150)
    metrics['edge_density'] = np.sum(edges > 0) / edges.size
    
    # 2. Стандартное отклонение (контрастность)
    metrics['std_dev'] = np.std(gray)
    
    # 3. Энтропия (информационная сложность)
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    hist_norm = hist / hist.sum()
    hist_norm = hist_norm[hist_norm > 0]  # Убираем нули для log
    metrics['entropy'] = -np.sum(hist_norm * np.log2(hist_norm))
    
    # 4. Количество уникальных цветов (для цветных изображений)
    if len(img_array.shape) == 3:
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[2]), axis=0))
        metrics['color_complexity'] = unique_colors / img_array.size * 1000
    
    # 5. Общая оценка сложности (0-1)
    complexity_score = (
        metrics['edge_density'] * 0.3 +
        min(metrics['std_dev'] / 100, 1) * 0.3 +
        metrics['entropy'] / 8 * 0.4
    )
    metrics['overall_complexity'] = min(complexity_score, 1.0)
    
    return metrics


def create_image_mask(image: Union[Image.Image, np.ndarray],
                      lower_bound: Tuple[int, int, int] = (0, 0, 0),
                      upper_bound: Tuple[int, int, int] = (255, 255, 255)) -> np.ndarray:
    """
    Создание маски на основе цветового диапазона.
    
    Args:
        image: Исходное изображение
        lower_bound: Нижняя граница цвета (R, G, B)
        upper_bound: Верхняя граница цвета (R, G, B)
        
    Returns:
        Бинарная маска (numpy array)
    """
    if isinstance(image, Image.Image):
        img_array = np.array(image)
    else:
        img_array = image
    
    # Создаем маску
    mask = cv2.inRange(img_array, lower_bound, upper_bound)
    
    return mask


def combine_masks(masks: List[np.ndarray], mode: str = 'union') -> np.ndarray:
    """
    Объединение нескольких масок.
    
    Args:
        masks: Список масок для объединения
        mode: Режим объединения ('union', 'intersection', 'difference')
        
    Returns:
        Объединенная маска
    """
    if not masks:
        raise ValueError("Список масок пуст")
    
    result = masks[0].copy()
    
    for mask in masks[1:]:
        if mode == 'union':
            result = cv2.bitwise_or(result, mask)
        elif mode == 'intersection':
            result = cv2.bitwise_and(result, mask)
        elif mode == 'difference':
            result = cv2.bitwise_xor(result, mask)
        else:
            raise ValueError(f"Неизвестный режим: {mode}")
    
    return result


def apply_morphology(mask: np.ndarray, 
                     operation: str = 'close',
                     kernel_size: int = 5,
                     iterations: int = 1) -> np.ndarray:
    """
    Применение морфологических операций к маске.
    
    Args:
        mask: Бинарная маска
        operation: Тип операции ('close', 'open', 'dilate', 'erode')
        kernel_size: Размер ядра
        iterations: Количество итераций
        
    Returns:
        Обработанная маска
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    if operation == 'close':
        return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=iterations)
    elif operation == 'open':
        return cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=iterations)
    elif operation == 'dilate':
        return cv2.dilate(mask, kernel, iterations=iterations)
    elif operation == 'erode':
        return cv2.erode(mask, kernel, iterations=iterations)
    else:
        raise ValueError(f"Неизвестная операция: {operation}")


def get_image_hash(image: Union[Image.Image, str, Path]) -> str:
    """
    Вычисление хеша изображения для кеширования.
    
    Args:
        image: Изображение или путь к нему
        
    Returns:
        MD5 хеш изображения
    """
    if isinstance(image, (str, Path)):
        with open(image, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    else:
        # Для PIL Image
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return hashlib.md5(buffer.getvalue()).hexdigest()