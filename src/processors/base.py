"""
Базовый класс для всех процессоров изображений.

Этот модуль определяет абстрактный базовый класс, который должны
наследовать все процессоры изображений в проекте.
"""

from abc import ABC, abstractmethod
from typing import Union, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
import os

import numpy as np
from PIL import Image


class BaseProcessor(ABC):
    """
    Абстрактный базовый класс для процессоров изображений.
    
    Определяет общий интерфейс и базовую функциональность для всех
    процессоров в системе обработки изображений Yandex Market.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация базового процессора.
        
        Args:
            config: Словарь с конфигурацией процессора
        """
        self.config = config or {}
        self.logger = self._setup_logger()
        self._debug_mode = self.config.get('debug', False)
        self._save_intermediates = self.config.get('save_intermediates', False)
        self._intermediate_dir = self.config.get('intermediate_dir', 'data/intermediates')
        
        if self._save_intermediates:
            os.makedirs(self._intermediate_dir, exist_ok=True)
    
    def _setup_logger(self) -> logging.Logger:
        """Настройка логгера для процессора."""
        logger_name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        logger = logging.getLogger(logger_name)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        
        return logger
    
    @abstractmethod
    def process(self, image: Union[str, Path, Image.Image, np.ndarray]) -> Any:
        """
        Основной метод обработки изображения.
        
        Должен быть реализован в каждом наследнике.
        
        Args:
            image: Входное изображение (путь, PIL Image или numpy array)
            
        Returns:
            Результат обработки (зависит от конкретного процессора)
        """
        pass
    
    def validate_input(self, image: Union[str, Path, Image.Image, np.ndarray]) -> Image.Image:
        """
        Валидация и нормализация входных данных.
        
        Args:
            image: Входное изображение в различных форматах
            
        Returns:
            PIL Image объект
            
        Raises:
            ValueError: Если входные данные невалидны
            FileNotFoundError: Если файл не найден
        """
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Файл не найден: {image_path}")
            
            try:
                pil_image = Image.open(image_path)
                # Конвертируем в RGB если нужно (например, из RGBA или L)
                if pil_image.mode not in ('RGB', 'RGBA'):
                    pil_image = pil_image.convert('RGB')
                return pil_image
            except Exception as e:
                raise ValueError(f"Не удалось загрузить изображение: {e}")
                
        elif isinstance(image, Image.Image):
            return image
            
        elif isinstance(image, np.ndarray):
            # Конвертируем numpy array в PIL Image
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
            
            if len(image.shape) == 2:  # Grayscale
                return Image.fromarray(image, mode='L')
            elif len(image.shape) == 3:
                if image.shape[2] == 3:  # RGB
                    return Image.fromarray(image, mode='RGB')
                elif image.shape[2] == 4:  # RGBA
                    return Image.fromarray(image, mode='RGBA')
            
            raise ValueError(f"Неподдерживаемая форма numpy array: {image.shape}")
        
        else:
            raise ValueError(
                f"Неподдерживаемый тип входных данных: {type(image)}. "
                "Ожидается: str, Path, PIL.Image или numpy.ndarray"
            )
    
    def save_intermediate_result(self, 
                               image: Union[Image.Image, np.ndarray], 
                               stage_name: str,
                               image_format: str = 'PNG') -> Optional[Path]:
        """
        Сохранение промежуточного результата обработки.
        
        Args:
            image: Изображение для сохранения
            stage_name: Название этапа обработки
            image_format: Формат сохранения (PNG, JPEG)
            
        Returns:
            Path к сохраненному файлу или None если сохранение отключено
        """
        if not self._save_intermediates:
            return None
        
        # Создаем уникальное имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.__class__.__name__}_{stage_name}_{timestamp}.{image_format.lower()}"
        filepath = Path(self._intermediate_dir) / filename
        
        # Конвертируем в PIL если нужно
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Сохраняем
        image.save(filepath, format=image_format)
        self.logger.debug(f"Сохранен промежуточный результат: {filepath}")
        
        return filepath
    
    def log_processing_info(self, 
                           input_image: Image.Image, 
                           processing_time: float,
                           additional_info: Optional[Dict[str, Any]] = None):
        """
        Логирование информации об обработке.
        
        Args:
            input_image: Входное изображение
            processing_time: Время обработки в секундах
            additional_info: Дополнительная информация для логирования
        """
        info = {
            'processor': self.__class__.__name__,
            'image_size': input_image.size,
            'image_mode': input_image.mode,
            'processing_time': f"{processing_time:.2f}s",
        }
        
        if additional_info:
            info.update(additional_info)
        
        self.logger.info(f"Обработка завершена: {info}")
    
    @property
    def name(self) -> str:
        """Возвращает имя процессора."""
        return self.__class__.__name__
    
    @property
    def description(self) -> str:
        """Возвращает описание процессора из docstring."""
        return self.__class__.__doc__ or "Описание отсутствует"