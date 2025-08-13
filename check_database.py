#!/usr/bin/env python3
"""
Скрипт для проверки содержимого базы данных истории обработки
"""

import sqlite3
import sys

def check_database():
    """Проверить содержимое базы данных"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('/app/database/history.db')
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='batches';")
        table_structure = cursor.fetchone()
        print("Структура таблицы batches:")
        print(table_structure[0] if table_structure else "Таблица не найдена")
        print()
        
        # Получаем последние записи
        cursor.execute("""
            SELECT batch_id, zip_path, created_at, successful, failed 
            FROM batches 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        print(f"Последние {len(records)} записей:")
        print("batch_id | zip_path | created_at | successful | failed")
        print("-" * 80)
        
        for record in records:
            print(f"{record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
    except Exception as e:
        print(f"Общая ошибка: {e}")

if __name__ == "__main__":
    check_database()