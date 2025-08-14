#!/bin/bash

# Быстрый тест для проверки новой функциональности
# Запускается после каждого commit'а с новыми функциями

echo "⚡ БЫСТРЫЙ ТЕСТ НОВОЙ ФУНКЦИОНАЛЬНОСТИ"
echo "======================================"

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Устанавливаем заглушки для тестов
export OPENAI_API_KEY="test-key"

echo -e "${BLUE}📋 Запуск упрощенного E2E теста...${NC}"
python3 tests/test_simple_e2e.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ ТЕСТ ПРОЙДЕН УСПЕШНО!${NC}"
    echo -e "${GREEN}Model Registry System работает корректно${NC}"
    exit 0
else
    echo -e "\n${RED}❌ ТЕСТ ПРОВАЛЕН${NC}"
    echo -e "${RED}Требуется исправление перед коммитом${NC}"
    exit 1
fi