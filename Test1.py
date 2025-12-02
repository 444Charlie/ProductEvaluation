#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Эксперимент: Оценка потребительских предпочтений
PsychoPy experiment for consumer preference evaluation
"""

from psychopy import visual, core, event, gui
import random
import os
import pandas as pd
from datetime import datetime
import glob
import json

# ==================== НАСТРОЙКИ ====================
FULLSCREEN = True  # Полноэкранный режим
PHOTOS_DIR = os.path.expanduser("~/Desktop/exp/photos")
GROUPS = {
    "premium": "Премиум",
    "base": "Базовая",
    "control": "Контрольная"
}
RESULTS_DIR = os.path.expanduser("~/Desktop/exp/results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "results_all.xlsx")  # Единый файл для всех результатов
MAX_PARTICIPANTS_PER_GROUP = 15  # Максимальное количество участников в каждой группе
GROUP_DISTRIBUTION_FILE = os.path.expanduser("~/Desktop/exp/group_distribution.json")

# Создаем папку для результатов, если её нет
os.makedirs(RESULTS_DIR, exist_ok=True)

# Переменная для окна (будет создана после ввода номера)
win = None

def create_window():
    """Создать окно PsychoPy"""
    global win
    if win is None:
        # В полноэкранном режиме размер определяется автоматически
        win = visual.Window(
            fullscr=FULLSCREEN,
            monitor="testMonitor",
            units="pix",
            color='white',
            allowGUI=True,
            screen=0  # Использовать основной экран
        )
    return win

# ==================== ФУНКЦИИ ====================

def get_participant_number():
    """Получить номер респондента"""
    info = {'Номер респондента': ''}
    dlg = gui.DlgFromDict(dictionary=info, title='Оценка потребительских предпочтений')
    if dlg.OK:
        return info['Номер респондента']
    else:
        core.quit()
        return None

def load_group_distribution():
    """Загрузить текущее распределение участников по группам"""
    if os.path.exists(GROUP_DISTRIBUTION_FILE):
        try:
            with open(GROUP_DISTRIBUTION_FILE, 'r', encoding='utf-8') as f:
                distribution = json.load(f)
            # Убедимся, что все группы присутствуют
            for key in GROUPS.keys():
                if key not in distribution:
                    distribution[key] = 0
            return distribution
        except:
            pass
    # Если файла нет или ошибка чтения, создаем новое распределение
    return {key: 0 for key in GROUPS.keys()}

def save_group_distribution(distribution):
    """Сохранить распределение участников по группам"""
    try:
        with open(GROUP_DISTRIBUTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(distribution, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка при сохранении распределения: {e}")

def assign_group():
    """Определение группы с балансировкой (максимум 15 участников в каждой)"""
    distribution = load_group_distribution()
    
    # Получаем список доступных групп (где еще не набрано 15 участников)
    available_groups = [
        key for key, count in distribution.items() 
        if count < MAX_PARTICIPANTS_PER_GROUP
    ]
    
    # Если все группы заполнены
    if not available_groups:
        # Создаем окно, если еще не создано
        win = create_window()
        # Показываем сообщение об ошибке
        error_text = visual.TextStim(
            win,
            text="Все группы заполнены!\nМаксимум 15 участников в каждой группе.\n\nНажмите ESC для выхода",
            height=40,
            color='red',
            wrapWidth=800,
            pos=(0, 0)
        )
        error_text.draw()
        win.flip()
        event.waitKeys(keyList=['escape'])
        win.close()
        core.quit()
        return None, None
    
    # Выбираем группу из доступных с наименьшим количеством участников для лучшей балансировки
    # Если несколько групп с одинаковым минимумом, выбираем случайно
    min_count = min(distribution[key] for key in available_groups)
    groups_with_min = [key for key in available_groups if distribution[key] == min_count]
    group_key = random.choice(groups_with_min)
    
    # Обновляем распределение
    distribution[group_key] += 1
    save_group_distribution(distribution)
    
    return group_key, GROUPS[group_key]

def show_instruction(win):
    """Показать инструкцию"""
    instruction_text = """
Уважаемый участник!

Благодарим вас за согласие принять участие в нашем исследовании. 
Ваша задача - оценить ряд товаров, как если бы вы рассматривали 
их в интернет-магазине.

Пожалуйста, внимательно ознакомьтесь с правилами:

Вам будет последовательно представлен ряд товаров. 
Ваша задача — оценить каждый из них по нескольким параметрам.

ПРОЦЕДУРА:

1. Вы увидите изображение товара и его цену

2. Нажмите на изображение товара, чтобы перейти к оценке

3. Ответьте на 3 вопроса о товаре

Важно: 

- Постарайтесь отвечать быстро и интуитивно, как при реальной покупке в интернете

- Не задумывайтесь слишком долго над ответами


Нажмите ПРОБЕЛ, чтобы начать
"""
    
    instruction = visual.TextStim(
        win,
        text=instruction_text,
        height=30,
        color='black',
        wrapWidth=1200,
        pos=(0, 0)
    )
    
    instruction.draw()
    win.flip()
    
    # Ждем нажатия пробела
    keys = event.waitKeys(keyList=['space', 'escape'])
    if 'escape' in keys:
        core.quit()

def show_product(win, image_path, product_number, total_products):
    """Показать товар и вернуть время начала показа"""
    # Получаем размер окна для адаптивного размера изображения
    win_size = win.size
    # Используем большую часть экрана для изображения (примерно 70% от высоты или ширины, что меньше)
    max_size = min(win_size[0] * 0.7, win_size[1] * 0.7)
    
    # Загружаем изображение
    try:
        product_image = visual.ImageStim(
            win,
            image=image_path,
            pos=(0, 0),
            size=(max_size, max_size),  # Увеличенный размер изображения
            units='pix'
        )
    except:
        # Если не удалось загрузить изображение, показываем текст
        product_image = visual.TextStim(
            win,
            text=f"Изображение не найдено: {os.path.basename(image_path)}",
            height=30,
            color='red'
        )
    
    # Текст с номером товара
    product_text = visual.TextStim(
        win,
        text=f"Товар {product_number} из {total_products}",
        height=40,
        color='black',
        pos=(0, -400),
        bold=True
    )
    
    # Инструкция
    instruction_text = visual.TextStim(
        win,
        text="Нажмите на изображение товара, чтобы перейти к оценке",
        height=30,
        color='black',
        pos=(0, 450)
    )
    
    # Показываем экран
    start_time = core.getTime()
    mouse = event.Mouse(win=win)
    mouse.clickReset()
    
    clicked = False
    while not clicked:
        product_image.draw()
        product_text.draw()
        instruction_text.draw()
        win.flip()
        
        # Проверяем клик на изображении
        if mouse.isPressedIn(product_image, buttons=[0]):
            # Ждем, пока кнопка будет отпущена
            while mouse.getPressed()[0]:
                core.wait(0.01)
            clicked = True
            click_time = core.getTime()
            reaction_time = click_time - start_time
        
        # Проверяем нажатие Escape или пробела (альтернативный способ)
        keys = event.getKeys(keyList=['escape', 'space'])
        if 'escape' in keys:
            core.quit()
        elif 'space' in keys:
            clicked = True
            click_time = core.getTime()
            reaction_time = click_time - start_time
    
    return reaction_time

def show_scale_question(win, question_text, labels, selected_value=None):
    """Показать вопрос со шкалой 1-7 с визуально выделенными вариантами ответов"""
    # Основной текст вопроса
    q_text = visual.TextStim(
        win,
        text=question_text,
        height=40,
        color='black',
        pos=(0, 350),
        wrapWidth=1200,
        bold=True
    )
    
    # Инструкция
    instruction = visual.TextStim(
        win,
        text="Нажмите цифру от 1 до 7 на клавиатуре",
        height=30,
        color='blue',
        pos=(0, -350),
        bold=True
    )
    
    # Создаем визуальные кнопки для каждого варианта ответа
    option_boxes = []
    option_numbers = []
    option_labels = []
    
    # Цвета для разных уровней (от красного к зеленому)
    colors = [
        (0.9, 0.2, 0.2),  # 1 - красный
        (0.9, 0.4, 0.2),  # 2 - оранжево-красный
        (0.9, 0.6, 0.2),  # 3 - оранжевый
        (0.9, 0.9, 0.9),  # 4 - серый (нейтральный)
        (0.2, 0.6, 0.9),  # 5 - светло-синий
        (0.2, 0.8, 0.9),  # 6 - бирюзовый
        (0.2, 0.9, 0.5),  # 7 - зеленый
    ]
    
    start_x = -480
    spacing = 160
    
    for i in range(7):
        x_pos = start_x + i * spacing
        
        # Рамка для варианта
        box = visual.Rect(
            win,
            width=150,
            height=140,
            pos=(x_pos, 50),
            fillColor=colors[i],
            lineColor='black',
            lineWidth=4
        )
        
        # Цифра
        number = visual.TextStim(
            win,
            text=str(i + 1),
            height=70,
            color='white',
            pos=(x_pos, 80),
            bold=True
        )
        
        # Текст подписи (сокращенный)
        label_parts = labels[i].split(' — ')
        label_text = label_parts[1] if len(label_parts) > 1 else label_parts[0]
        # Разбиваем длинный текст на несколько строк
        words = label_text.split()
        if len(words) > 2:
            mid = len(words) // 2
            label_text = ' '.join(words[:mid]) + '\n' + ' '.join(words[mid:])
        
        label = visual.TextStim(
            win,
            text=label_text,
            height=18,
            color='black',
            pos=(x_pos, -25),
            wrapWidth=135
        )
        
        option_boxes.append(box)
        option_numbers.append(number)
        option_labels.append(label)
    
    # Отображаем все элементы
    q_text.draw()
    instruction.draw()
    
    for box, num, label in zip(option_boxes, option_numbers, option_labels):
        box.draw()
        num.draw()
        label.draw()
    
    win.flip()
    
    # Ждем выбора
    keys = event.waitKeys(keyList=['1', '2', '3', '4', '5', '6', '7', 'escape'])
    if 'escape' in keys:
        core.quit()
    
    selected = int(keys[0])
    
    # Показываем выбранный вариант подсветкой
    q_text.draw()
    instruction.draw()
    
    for i, (box, num, label) in enumerate(zip(option_boxes, option_numbers, option_labels)):
        if i + 1 == selected:
            # Подсвечиваем выбранный вариант
            highlight_box = visual.Rect(
                win,
                width=170,
                height=150,
                pos=(box.pos[0], box.pos[1]),
                fillColor=None,
                lineColor='yellow',
                lineWidth=6
            )
            highlight_box.draw()
        box.draw()
        num.draw()
        label.draw()
    
    win.flip()
    core.wait(0.3)  # Небольшая пауза для визуальной обратной связи
    
    return selected

def show_survey(win):
    """Показать опрос и получить ответы"""
    responses = {}
    
    # Вопрос 1: Справедливость цены
    q1_labels = [
        "1 — Совершенно несправедливо",
        "2 — Очень несправедливо",
        "3 — Скорее несправедливо",
        "4 — Ни да, ни нет (Нейтрально)",
        "5 — Скорее справедливо",
        "6 — Очень справедливо",
        "7 — Абсолютно справедливо"
    ]
    
    responses['price_fairness'] = show_scale_question(
        win,
        "1. Насколько справедливой вам кажется указанная цена товара?",
        q1_labels
    )
    
    # Вопрос 2: Максимальная сумма
    q2_text = visual.TextStim(
        win,
        text="2. Какова максимальная сумма, которую вы были бы готовы заплатить за этот товар? (Укажите в рублях)",
        height=40,
        color='black',
        pos=(0, 300),
        wrapWidth=1200,
        bold=True
    )
    
    q2_instruction = visual.TextStim(
        win,
        text="Введите число и нажмите ENTER",
        height=35,
        color='blue',
        pos=(0, 0),
        bold=True
    )
    
    # Простой ввод через клавиатуру
    user_input = ''
    input_display = visual.TextStim(
        win,
        text=f"{user_input} руб.",
        height=50,
        color='black',
        pos=(0, -150),
        bold=True
    )
    
    # Рамка для поля ввода
    input_box = visual.Rect(
        win,
        width=400,
        height=80,
        pos=(0, -150),
        fillColor='lightgray',
        lineColor='blue',
        lineWidth=3
    )
    
    while True:
        q2_text.draw()
        q2_instruction.draw()
        input_box.draw()
        input_display.setText(f"{user_input} руб." if user_input else "0 руб.")
        input_display.draw()
        win.flip()
        
        keys = event.waitKeys(keyList=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'return', 'escape', 'backspace'])
        
        if 'escape' in keys:
            core.quit()
        elif 'return' in keys:
            if user_input:
                try:
                    responses['max_price'] = float(user_input)
                    break
                except:
                    pass
        elif 'backspace' in keys:
            user_input = user_input[:-1] if user_input else ''
        elif keys[0] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            user_input += keys[0]
    
    # Вопрос 3: Вероятность покупки
    q3_labels = [
        "1 — Точно нет",
        "2 — Крайне маловероятно",
        "3 — Маловероятно",
        "4 — Затрудняюсь ответить",
        "5 — Вероятно",
        "6 — Очень вероятно",
        "7 — Определенно да"
    ]
    
    responses['purchase_probability'] = show_scale_question(
        win,
        "3. Насколько вероятно, что вы купили бы этот товар по указанной цене?",
        q3_labels
    )
    
    return responses

def show_finish_screen(win):
    """Показать финальный экран с кнопкой 'Завершить опрос'"""
    finish_text = visual.TextStim(
        win,
        text="Завершить опрос",
        height=50,
        color='white',
        pos=(0, 0),
        bold=True
    )
    
    finish_bg = visual.Rect(
        win,
        width=400,
        height=100,
        pos=(0, 0),
        fillColor='green',
        lineColor='darkgreen',
        lineWidth=4
    )
    
    instruction = visual.TextStim(
        win,
        text="Нажмите ПРОБЕЛ для завершения",
        height=30,
        color='black',
        pos=(0, -150)
    )
    
    finish_bg.draw()
    finish_text.draw()
    instruction.draw()
    win.flip()
    
    event.waitKeys(keyList=['space', 'escape'])

# ==================== ОСНОВНОЙ ЭКСПЕРИМЕНТ ====================

# Получаем номер респондента (окно показывается ДО создания окна PsychoPy)
participant_number = get_participant_number()

if participant_number:
    # Создаем окно PsychoPy после получения номера участника
    win = create_window()
    # Определяем группу
    group_key, group_name = assign_group()
    
    # Проверяем, что группа была назначена
    if group_key is None or group_name is None:
        win.close()
        core.quit()
    
    # Загружаем изображения из нужной папки
    photos_path = os.path.join(PHOTOS_DIR, group_key)
    image_files = sorted(glob.glob(os.path.join(photos_path, "*.png")))
    
    if not image_files:
        # Если PNG не найдены, пробуем другие форматы
        image_files = sorted(glob.glob(os.path.join(photos_path, "*.*")))
    
    if not image_files:
        error_text = visual.TextStim(
            win,
            text=f"Ошибка: Изображения не найдены в папке {photos_path}\nНажмите ESC для выхода",
            height=30,
            color='red',
            wrapWidth=1000
        )
        error_text.draw()
        win.flip()
        event.waitKeys(keyList=['escape'])
        core.quit()
    
    total_products = len(image_files)
    
    # Показываем инструкцию
    show_instruction(win)
    
    # Список для хранения данных
    all_data = []
    
    # Основной цикл эксперимента
    for idx, image_path in enumerate(image_files, 1):
        # Показываем товар и получаем время реакции
        reaction_time = show_product(win, image_path, idx, total_products)
        
        # Показываем опрос
        responses = show_survey(win)
        
        # Сохраняем данные
        data_row = {
            'participant_number': participant_number,
            'group': group_name,
            'group_key': group_key,
            'product_number': idx,
            'total_products': total_products,
            'image_file': os.path.basename(image_path),
            'reaction_time': round(reaction_time, 3),
            'price_fairness': responses['price_fairness'],
            'max_price': responses['max_price'],
            'purchase_probability': responses['purchase_probability'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        all_data.append(data_row)
    
    # Показываем финальный экран с кнопкой "Завершить опрос"
    show_finish_screen(win)
    
    # Сохраняем данные в единый файл Excel
    # Загружаем существующие данные, если файл есть
    if os.path.exists(RESULTS_FILE):
        try:
            existing_df = pd.read_excel(RESULTS_FILE, engine='openpyxl')
            # Объединяем с новыми данными
            new_df = pd.DataFrame(all_data)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception as e:
            # Если файл поврежден или пуст, создаем новый
            print(f"Ошибка при чтении файла результатов: {e}")
            combined_df = pd.DataFrame(all_data)
    else:
        # Файл не существует, создаем новый
        combined_df = pd.DataFrame(all_data)
    
    # Сохраняем все данные в единый файл
    combined_df.to_excel(RESULTS_FILE, index=False, engine='openpyxl')
    
    # Финальное сообщение
    final_text = visual.TextStim(
        win,
        text="Thank you, goodbye!",
        height=50,
        color='black',
        wrapWidth=800,
        pos=(0, 0),
        bold=True
    )
    
    final_text.draw()
    win.flip()
    event.waitKeys(keyList=['escape'])
    
    # Закрываем окно
    win.close()
else:
    # Если пользователь отменил ввод номера
    print("Эксперимент отменен пользователем")

# Закрываем окно, если оно было создано
if win is not None:
    win.close()
core.quit()

