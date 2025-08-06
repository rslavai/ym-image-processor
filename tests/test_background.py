"""
Тесты для модуля удаления фона.

Проверяет корректность работы BackgroundRemover на различных
типах изображений и в различных условиях.
"""

import pytest
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile
import shutil

from src.processors.background import BackgroundRemover
from src.utils.image_helpers import load_image, save_image


# Fixtures для тестов
@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def test_image():
    """Создает тестовое изображение."""
    # Создаем простое изображение с объектом на фоне
    img_array = np.zeros((200, 200, 3), dtype=np.uint8)
    # Фон - светло-серый
    img_array[:, :] = [200, 200, 200]
    # Объект - красный квадрат в центре
    img_array[50:150, 50:150] = [255, 0, 0]
    
    return Image.fromarray(img_array, mode='RGB')


@pytest.fixture
def complex_test_image():
    """Создает сложное тестовое изображение."""
    # Изображение с градиентом и несколькими объектами
    img_array = np.zeros((300, 300, 3), dtype=np.uint8)
    
    # Градиентный фон
    for i in range(300):
        img_array[i, :] = [i * 255 // 300, i * 255 // 300, 255]
    
    # Основной объект
    img_array[100:200, 100:200] = [0, 255, 0]
    # Мелкие объекты (шум)
    img_array[50:60, 50:60] = [255, 255, 0]
    img_array[240:250, 240:250] = [255, 0, 255]
    
    return Image.fromarray(img_array, mode='RGB')


@pytest.fixture
def background_remover():
    """Создает экземпляр BackgroundRemover."""
    config = {
        'debug': False,
        'post_process': True,
        'min_object_size': 500
    }
    return BackgroundRemover(config)


class TestBackgroundRemover:
    """Тесты для класса BackgroundRemover."""
    
    def test_initialization(self):
        """Тест инициализации процессора."""
        remover = BackgroundRemover()
        assert remover is not None
        assert remover.model_name == 'u2net'
        assert remover.post_process == True
    
    def test_initialization_with_config(self):
        """Тест инициализации с пользовательской конфигурацией."""
        config = {
            'model': 'u2net',
            'alpha_matting': True,
            'post_process': False,
            'min_object_size': 2000
        }
        remover = BackgroundRemover(config)
        
        assert remover.model_name == 'u2net'
        assert remover.use_alpha_matting == True
        assert remover.post_process == False
        assert remover.min_object_size == 2000
    
    def test_process_pil_image(self, background_remover, test_image):
        """Тест обработки PIL изображения."""
        result = background_remover.process(test_image)
        
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGBA'
        assert result.size == test_image.size
        
        # Проверяем, что альфа-канал присутствует
        alpha = np.array(result.split()[-1])
        assert alpha.shape == (200, 200)
        assert np.any(alpha < 255)  # Есть прозрачные области
    
    def test_process_with_mask_return(self, background_remover, test_image):
        """Тест получения маски вместе с изображением."""
        result_image, mask = background_remover.process(test_image, return_mask=True)
        
        assert isinstance(result_image, Image.Image)
        assert isinstance(mask, np.ndarray)
        assert mask.shape == (200, 200)
        assert mask.dtype == np.uint8
        
        # Проверяем, что маска содержит и объект, и фон
        unique_values = np.unique(mask)
        assert len(unique_values) >= 2
    
    def test_process_file_path(self, background_remover, test_image, temp_dir):
        """Тест обработки изображения по пути к файлу."""
        # Сохраняем тестовое изображение
        image_path = temp_dir / "test_image.jpg"
        test_image.save(image_path)
        
        # Обрабатываем
        result = background_remover.process(str(image_path))
        
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGBA'
    
    def test_process_numpy_array(self, background_remover, test_image):
        """Тест обработки numpy array."""
        img_array = np.array(test_image)
        result = background_remover.process(img_array)
        
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGBA'
    
    def test_post_processing(self, complex_test_image):
        """Тест пост-обработки маски."""
        # Создаем remover с включенной пост-обработкой
        remover = BackgroundRemover({
            'post_process': True,
            'min_object_size': 1000
        })
        
        result_image, mask = remover.process(complex_test_image, return_mask=True)
        
        # Проверяем, что мелкие объекты удалены
        # Подсчитываем количество связанных компонент
        import cv2
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            (mask > 128).astype(np.uint8)
        )
        
        # Должен остаться только фон и основной объект
        assert num_labels <= 3  # фон + основной объект + возможно еще один
    
    def test_batch_processing(self, background_remover, test_image, temp_dir):
        """Тест пакетной обработки."""
        # Создаем несколько тестовых изображений
        image_paths = []
        for i in range(3):
            path = temp_dir / f"test_{i}.jpg"
            test_image.save(path)
            image_paths.append(path)
        
        # Обрабатываем пакетом
        results = background_remover.process_batch(
            image_paths, 
            output_dir=temp_dir
        )
        
        assert len(results) == 3
        for result in results:
            assert result['success'] == True
            assert result['output'] is not None
            assert Path(result['output']).exists()
    
    def test_error_handling_invalid_input(self, background_remover):
        """Тест обработки ошибок при неверных входных данных."""
        with pytest.raises(ValueError):
            background_remover.process("invalid_input")
        
        with pytest.raises(FileNotFoundError):
            background_remover.process("/non/existent/path.jpg")
    
    def test_caching(self, test_image):
        """Тест кеширования результатов."""
        remover = BackgroundRemover({'use_cache': True})
        
        # Первая обработка
        result1 = remover.process(test_image)
        
        # Вторая обработка того же изображения
        result2 = remover.process(test_image)
        
        # Результаты должны быть идентичны
        assert np.array_equal(np.array(result1), np.array(result2))
    
    def test_alpha_matting(self, test_image):
        """Тест режима alpha matting."""
        remover = BackgroundRemover({'alpha_matting': True})
        result = remover.process(test_image)
        
        # Проверяем, что края более мягкие
        alpha = np.array(result.split()[-1])
        
        # Находим края
        edges = np.diff(alpha.astype(np.int16), axis=0)
        edge_values = np.unique(np.abs(edges))
        
        # При alpha matting должны быть промежуточные значения
        assert len(edge_values) > 2
    
    def test_intermediate_results_saving(self, background_remover, test_image, temp_dir):
        """Тест сохранения промежуточных результатов."""
        remover = BackgroundRemover({
            'debug': True,
            'save_intermediates': True,
            'intermediate_dir': str(temp_dir)
        })
        
        remover.process(test_image)
        
        # Проверяем, что промежуточные файлы созданы
        intermediate_files = list(temp_dir.glob("*"))
        assert len(intermediate_files) > 0
        
        # Должны быть файлы input, mask и output
        file_types = [f.stem.split('_')[1] for f in intermediate_files]
        assert 'input' in file_types
        assert 'mask' in file_types
        assert 'output' in file_types


class TestBackgroundRemoverIntegration:
    """Интеграционные тесты для BackgroundRemover."""
    
    def test_process_different_image_modes(self, background_remover):
        """Тест обработки изображений в разных цветовых режимах."""
        # RGB
        rgb_image = Image.new('RGB', (100, 100), color='red')
        result_rgb = background_remover.process(rgb_image)
        assert result_rgb.mode == 'RGBA'
        
        # RGBA
        rgba_image = Image.new('RGBA', (100, 100), color=(255, 0, 0, 255))
        result_rgba = background_remover.process(rgba_image)
        assert result_rgba.mode == 'RGBA'
        
        # Grayscale
        gray_image = Image.new('L', (100, 100), color=128)
        result_gray = background_remover.process(gray_image)
        assert result_gray.mode == 'RGBA'
    
    def test_large_image_processing(self, background_remover):
        """Тест обработки больших изображений."""
        # Создаем большое изображение
        large_image = Image.new('RGB', (2000, 2000), color='blue')
        # Добавляем объект
        from PIL import ImageDraw
        draw = ImageDraw.Draw(large_image)
        draw.ellipse([500, 500, 1500, 1500], fill='yellow')
        
        result = background_remover.process(large_image)
        assert result.size == (2000, 2000)
        assert result.mode == 'RGBA'


# Вспомогательные функции для тестов
def create_test_image_with_transparency():
    """Создает тестовое изображение с прозрачностью."""
    img = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    # Полупрозрачный круг
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for i in range(50, 150):
        for j in range(50, 150):
            if (i - 100) ** 2 + (j - 100) ** 2 < 50 ** 2:
                img.putpixel((i, j), (255, 0, 0, 128))
    return img


def compare_images(img1: Image.Image, img2: Image.Image, threshold: float = 0.95) -> bool:
    """Сравнивает два изображения на схожесть."""
    arr1 = np.array(img1)
    arr2 = np.array(img2)
    
    if arr1.shape != arr2.shape:
        return False
    
    # Вычисляем процент совпадающих пикселей
    matches = np.sum(arr1 == arr2)
    total = arr1.size
    
    return matches / total >= threshold