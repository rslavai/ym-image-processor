"""
Модуль для удаления фона с изображений.

Использует библиотеку rembg с моделью U²-Net для автоматического
удаления фона с товарных изображений.
"""

import time
from typing import Union, Tuple, Optional, Dict, Any, List
from pathlib import Path
import warnings

import numpy as np
from PIL import Image
import cv2
import rembg

from .base import BaseProcessor
from ..utils.image_helpers import (
    load_image, save_image, calculate_image_complexity,
    apply_morphology, get_image_hash
)


class BackgroundRemover(BaseProcessor):
    """
    Процессор для удаления фона с изображений товаров.
    
    Использует нейросетевую модель для автоматической сегментации
    и удаления фона, оставляя только объект товара.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация процессора удаления фона.
        
        Args:
            config: Конфигурация процессора, может содержать:
                - model: Имя модели rembg (по умолчанию 'u2net')
                - alpha_matting: Использовать ли alpha matting
                - post_process: Применять ли пост-обработку маски
                - min_object_size: Минимальный размер объекта в пикселях
        """
        super().__init__(config)
        
        # Параметры обработки - УЛУЧШЕННЫЕ настройки для качества
        self.model_name = self.config.get('model', 'u2net')  # u2net лучше для товаров
        self.use_alpha_matting = self.config.get('alpha_matting', True)  # Включаем для лучших краев
        self.post_process = self.config.get('post_process', True)
        self.min_object_size = self.config.get('min_object_size', 500)  # Уменьшаем для сохранения деталей
        
        # Инициализация сессии rembg
        self._init_session()
        
        # Кеш для оптимизации
        self._cache = {} if self.config.get('use_cache', True) else None
        
        self.logger.info(f"BackgroundRemover инициализирован с моделью: {self.model_name}")
    
    def _init_session(self):
        """Инициализация сессии rembg."""
        try:
            self.session = rembg.new_session(self.model_name)
            self.logger.info(f"Сессия rembg создана с моделью {self.model_name}")
        except Exception as e:
            self.logger.error(f"Ошибка при создании сессии rembg: {e}")
            raise
    
    def process(self, 
                image: Union[str, Path, Image.Image, np.ndarray],
                return_mask: bool = False) -> Union[Image.Image, Tuple[Image.Image, np.ndarray]]:
        """
        Удаление фона с изображения.
        
        Args:
            image: Входное изображение
            return_mask: Возвращать ли маску вместе с изображением
            
        Returns:
            Изображение с прозрачным фоном (RGBA) или кортеж (изображение, маска)
        """
        start_time = time.time()
        
        # Валидация и загрузка изображения
        pil_image = self.validate_input(image)
        
        # Проверяем кеш
        if self._cache is not None:
            image_hash = get_image_hash(pil_image)
            if image_hash in self._cache:
                self.logger.info("Результат найден в кеше")
                cached_result = self._cache[image_hash]
                return (cached_result['image'], cached_result['mask']) if return_mask else cached_result['image']
        
        # Анализ сложности изображения
        complexity = calculate_image_complexity(pil_image)
        self.logger.info(f"Сложность изображения: {complexity['overall_complexity']:.2f}")
        
        # Сохраняем промежуточный результат если включен debug режим
        if self._debug_mode:
            self.save_intermediate_result(pil_image, "input")
        
        # Удаление фона
        try:
            # Основная обработка через rembg
            output_image = self._remove_background(pil_image)
            
            # Извлекаем маску из альфа-канала
            mask = np.array(output_image.split()[-1])
            
            # Пост-обработка маски если включена
            if self.post_process:
                mask = self._post_process_mask(mask, complexity)
                # Применяем обновленную маску
                output_image = self._apply_mask_to_image(pil_image, mask)
            
            # Сохраняем промежуточные результаты
            if self._debug_mode:
                self.save_intermediate_result(mask, "mask")
                self.save_intermediate_result(output_image, "output")
            
            # Кешируем результат
            if self._cache is not None:
                self._cache[image_hash] = {
                    'image': output_image,
                    'mask': mask
                }
            
            # Логируем информацию
            processing_time = time.time() - start_time
            self.log_processing_info(
                pil_image, 
                processing_time,
                {
                    'complexity': complexity['overall_complexity'],
                    'mask_coverage': np.sum(mask > 128) / mask.size
                }
            )
            
            if return_mask:
                return output_image, mask
            return output_image
            
        except Exception as e:
            self.logger.error(f"Ошибка при удалении фона: {e}")
            raise
    
    def _remove_background(self, image: Image.Image) -> Image.Image:
        """
        Основная функция удаления фона через rembg.
        
        Args:
            image: Входное изображение
            
        Returns:
            Изображение с прозрачным фоном
        """
        # Применяем alpha matting если включено - с улучшенными параметрами
        if self.use_alpha_matting:
            output = rembg.remove(
                image, 
                session=self.session,
                alpha_matting=True,
                alpha_matting_foreground_threshold=270,  # Увеличиваем для четких краев
                alpha_matting_background_threshold=10,   # Уменьшаем для удаления артефактов
                alpha_matting_erode_size=2  # Уменьшаем для сохранения деталей
            )
        else:
            output = rembg.remove(image, session=self.session)
        
        return output
    
    def _post_process_mask(self, mask: np.ndarray, complexity: Dict[str, float]) -> np.ndarray:
        """
        Пост-обработка маски для улучшения качества.
        
        Args:
            mask: Исходная маска
            complexity: Метрики сложности изображения
            
        Returns:
            Улучшенная маска
        """
        # Копируем маску для обработки
        processed_mask = mask.copy()
        
        # 1. Удаление мелких артефактов
        if complexity['overall_complexity'] > 0.5:
            # Для сложных изображений используем более агрессивную очистку
            processed_mask = self._remove_small_objects(processed_mask, self.min_object_size)
        
        # 2. Заполнение дыр в маске
        processed_mask = self._fill_holes(processed_mask)
        
        # 3. Сглаживание краев с адаптивными параметрами
        if complexity['edge_density'] > 0.3:
            # Для изображений с большим количеством деталей
            kernel_size = 3
            iterations = 1
        else:
            kernel_size = 5
            iterations = 2
        
        # Применяем морфологическое закрытие для заполнения пробелов
        processed_mask = apply_morphology(
            processed_mask, 
            operation='close', 
            kernel_size=kernel_size,
            iterations=iterations
        )
        
        # Дополнительное открытие для удаления мелких артефактов
        processed_mask = apply_morphology(
            processed_mask,
            operation='open',
            kernel_size=3,
            iterations=1
        )
        
        # 4. Улучшение краев для прозрачных объектов
        if self.use_alpha_matting:
            processed_mask = self._refine_edges(processed_mask)
        
        return processed_mask
    
    def _remove_small_objects(self, mask: np.ndarray, min_size: int) -> np.ndarray:
        """
        Удаление мелких объектов из маски.
        
        Args:
            mask: Бинарная маска
            min_size: Минимальный размер объекта в пикселях
            
        Returns:
            Очищенная маска
        """
        # Находим все связанные компоненты
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            mask.astype(np.uint8), 
            connectivity=8
        )
        
        # Создаем новую маску только с крупными объектами
        cleaned_mask = np.zeros_like(mask)
        
        for i in range(1, num_labels):  # Пропускаем фон (label 0)
            if stats[i, cv2.CC_STAT_AREA] >= min_size:
                cleaned_mask[labels == i] = 255
        
        return cleaned_mask.astype(np.uint8)
    
    def _fill_holes(self, mask: np.ndarray) -> np.ndarray:
        """
        Заполнение дыр в маске.
        
        Args:
            mask: Бинарная маска
            
        Returns:
            Маска с заполненными дырами
        """
        # Находим контуры
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), 
            cv2.RETR_EXTERNAL, 
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Заполняем контуры
        filled_mask = np.zeros_like(mask)
        cv2.drawContours(filled_mask, contours, -1, 255, -1)
        
        return filled_mask.astype(np.uint8)
    
    def _refine_edges(self, mask: np.ndarray, feather_amount: int = 2) -> np.ndarray:
        """
        Улучшение краев маски для более естественного вида.
        
        Args:
            mask: Бинарная маска
            feather_amount: Количество пикселей для размытия краев
            
        Returns:
            Маска с улучшенными краями
        """
        # Применяем guided filter для сохранения краев
        # Сначала применяем bilateral filter для сглаживания с сохранением краев
        refined_mask = cv2.bilateralFilter(
            mask.astype(np.uint8),
            d=5,  # Диаметр фильтра
            sigmaColor=75,  # Фильтр сигма в цветовом пространстве
            sigmaSpace=75   # Фильтр сигма в координатном пространстве
        )
        
        # Затем применяем небольшое размытие только к краям
        # Находим края
        edges = cv2.Canny(refined_mask, 50, 150)
        edges_dilated = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=1)
        
        # Применяем размытие только к областям краев
        blurred_edges = cv2.GaussianBlur(refined_mask.astype(np.float32), (5, 5), 1.0)
        
        # Комбинируем: размытые края + четкая внутренняя часть
        result = refined_mask.astype(np.float32)
        result[edges_dilated > 0] = blurred_edges[edges_dilated > 0]
        
        # Нормализуем обратно к uint8
        refined_mask = np.clip(result, 0, 255).astype(np.uint8)
        
        return refined_mask
    
    def _apply_mask_to_image(self, image: Image.Image, mask: np.ndarray) -> Image.Image:
        """
        Применение маски к изображению с антиалиасингом.
        
        Args:
            image: Исходное изображение
            mask: Маска для применения
            
        Returns:
            Изображение с примененной маской (RGBA)
        """
        # Конвертируем изображение в RGBA если нужно
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Применяем маску как альфа-канал с антиалиасингом
        image_array = np.array(image)
        
        # Применяем сглаживание к альфа-каналу для мягких краев
        # Это поможет избежать резких пикселей на границах
        smoothed_mask = cv2.GaussianBlur(mask.astype(np.float32), (3, 3), 0.5)
        smoothed_mask = np.clip(smoothed_mask, 0, 255).astype(np.uint8)
        
        image_array[:, :, 3] = smoothed_mask
        
        # Создаем изображение с примененным антиалиасингом
        result = Image.fromarray(image_array, mode='RGBA')
        
        return result
    
    def process_batch(self, 
                      image_paths: List[Union[str, Path]], 
                      output_dir: Optional[Union[str, Path]] = None,
                      progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Пакетная обработка изображений.
        
        Args:
            image_paths: Список путей к изображениям
            output_dir: Директория для сохранения результатов
            progress_callback: Функция для отслеживания прогресса
            
        Returns:
            Список результатов обработки
        """
        results = []
        total = len(image_paths)
        
        for idx, image_path in enumerate(image_paths):
            try:
                # Обрабатываем изображение
                result_image = self.process(image_path)
                
                # Сохраняем если указана директория
                if output_dir:
                    output_path = Path(output_dir) / f"{Path(image_path).stem}_no_bg.png"
                    save_image(result_image, output_path, format='PNG')
                    result_path = output_path
                else:
                    result_path = None
                
                results.append({
                    'input': image_path,
                    'output': result_path,
                    'success': True,
                    'image': result_image
                })
                
            except Exception as e:
                self.logger.error(f"Ошибка при обработке {image_path}: {e}")
                results.append({
                    'input': image_path,
                    'output': None,
                    'success': False,
                    'error': str(e)
                })
            
            # Вызываем callback если предоставлен
            if progress_callback:
                progress_callback(idx + 1, total)
        
        return results