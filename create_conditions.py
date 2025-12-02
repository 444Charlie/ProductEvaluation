#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для создания файлов условий для PsychoPy Builder
Создает CSV файлы для каждой группы, используя реальные имена файлов
"""

import pandas as pd
import os
import glob

# Путь к папке с фотографиями
PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'photos')

# Создаем условия для каждой группы
groups = {
    'premium': 'premium',
    'base': 'base',
    'control': 'control'
}

for group_key, group_name in groups.items():
    # Получаем список всех изображений в папке группы
    group_path = os.path.join(PHOTOS_DIR, group_name)
    
    # Ищем все изображения (png, jpg, jpeg)
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
        image_files.extend(glob.glob(os.path.join(group_path, ext)))
    
    # Сортируем файлы по имени
    image_files = sorted(image_files)
    
    if not image_files:
        print(f"⚠️  Внимание: Не найдены изображения в папке {group_path}")
        continue
    
    # Создаем список условий
    conditions = []
    for i, image_path in enumerate(image_files, 1):
        # Получаем только имя файла
        filename = os.path.basename(image_path)
        # Путь относительно папки photos (для использования в Pavlovia)
        relative_path = f'{group_name}/{filename}'
        
        conditions.append({
            'product_number': i,
            'image_path': relative_path,
            'total_products': len(image_files)
        })
    
    # Создаем DataFrame
    df = pd.DataFrame(conditions)
    
    # Сохраняем в CSV (совместимо с PsychoPy Builder)
    filename = f'conditions_{group_key}.csv'
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"✅ Создан файл: {filename} ({len(conditions)} товаров)")
    
    # Также создаем Excel версию, если openpyxl доступен
    try:
        excel_filename = f'conditions_{group_key}.xlsx'
        df.to_excel(excel_filename, index=False, engine='openpyxl')
        print(f"✅ Создан файл: {excel_filename}")
    except:
        pass  # Excel не обязателен

print("\n✅ Все файлы условий созданы!")
print("📝 Используйте эти файлы в PsychoPy Builder для настройки Loop.")
print("\n💡 Совет: Убедитесь, что пути к изображениям в условиях совпадают")
print("   с путями файлов, загруженных на Pavlovia.")

