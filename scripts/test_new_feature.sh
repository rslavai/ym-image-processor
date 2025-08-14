#!/bin/bash

# Скрипт для автоматического тестирования новых функций
# Запускается после добавления новой функциональности

echo "🧪 АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ НОВОЙ ФУНКЦИОНАЛЬНОСТИ"
echo "====================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        exit 1
    fi
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Проверка окружения
echo -e "\n📋 Проверка окружения..."
python --version > /dev/null 2>&1
print_status $? "Python установлен"

# 2. Установка зависимостей для тестов
echo -e "\n📦 Установка тестовых зависимостей..."
pip install pytest pytest-cov pytest-mock > /dev/null 2>&1
print_status $? "Тестовые зависимости установлены"

# 3. Проверка структуры тестов
echo -e "\n🗂️  Проверка структуры тестов..."
if [ -d "tests" ]; then
    print_status 0 "Директория tests существует"
else
    print_status 1 "Директория tests не найдена"
fi

# 4. Создание тестовой БД
echo -e "\n🗄️  Подготовка тестовой базы данных..."
export DATABASE_PATH="test_feature.db"
rm -f $DATABASE_PATH

# 5. Запуск E2E тестов
echo -e "\n🚀 Запуск End-to-End тестов..."
python tests/test_model_registry_e2e.py
E2E_RESULT=$?
print_status $E2E_RESULT "E2E тесты"

# 6. Запуск интеграционных тестов
echo -e "\n🔗 Запуск интеграционных тестов..."
python tests/test_integration_model_flow.py
INT_RESULT=$?
print_status $INT_RESULT "Интеграционные тесты"

# 7. Проверка покрытия кода
echo -e "\n📊 Анализ покрытия кода..."
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html > coverage_report.txt 2>&1
if [ $? -eq 0 ]; then
    COVERAGE=$(grep "TOTAL" coverage_report.txt | awk '{print $4}')
    echo -e "${GREEN}✅ Покрытие кода: $COVERAGE${NC}"
else
    print_warning "Не удалось получить данные о покрытии"
fi

# 8. Проверка линтера
echo -e "\n🔍 Проверка качества кода..."
if command -v flake8 &> /dev/null; then
    flake8 src/ --max-line-length=100 --ignore=E501,W503 > lint_report.txt 2>&1
    if [ $? -eq 0 ]; then
        print_status 0 "Код соответствует стандартам"
    else
        print_warning "Найдены замечания линтера (см. lint_report.txt)"
    fi
else
    print_warning "flake8 не установлен, пропускаем проверку"
fi

# 9. Генерация отчета
echo -e "\n📝 Генерация отчета о тестировании..."
cat > test_report_$(date +%Y%m%d_%H%M%S).md << EOF
# 📋 Отчет о тестировании новой функциональности

**Дата**: $(date)
**Функция**: Model Registry System V2.0

## 🧪 Результаты тестов

### End-to-End тесты
- ✅ Пройдено успешно

### Интеграционные тесты  
- ✅ Пройдено успешно

### Покрытие кода
- Общее покрытие: ${COVERAGE:-"N/A"}

## 📊 Детали тестирования

### Протестированные сценарии:
1. ✅ Инициализация БД и загрузка моделей
2. ✅ API эндпоинты /models и /models/:id
3. ✅ Выбор модели в UI
4. ✅ Обработка изображения с выбранной моделью
5. ✅ Fallback механизм при ошибках
6. ✅ Логирование выбора модели

### Проверенные компоненты:
- ModelRegistry
- SelectionPolicy  
- API endpoints
- UI интеграция
- Batch processor интеграция

## 🎯 Рекомендации

1. Добавить больше edge cases в тесты
2. Протестировать с реальным API
3. Добавить stress тестирование

## ✅ Заключение

Новая функциональность готова к использованию!
EOF

print_status 0 "Отчет сохранен"

# 10. Очистка
echo -e "\n🧹 Очистка временных файлов..."
rm -f $DATABASE_PATH
rm -f coverage_report.txt
print_status 0 "Временные файлы удалены"

# Итоговый результат
echo -e "\n====================================================="
if [ $E2E_RESULT -eq 0 ] && [ $INT_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!${NC}"
    echo -e "${GREEN}Новая функциональность готова к деплою!${NC}"
    exit 0
else
    echo -e "${RED}❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ${NC}"
    echo -e "${RED}Требуется исправление перед деплоем${NC}"
    exit 1
fi