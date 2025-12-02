import streamlit as st
import pandas as pd
import random
from datetime import datetime
import os
import glob
import gspread
from google.oauth2.service_account import Credentials

# Настройка страницы
st.set_page_config(page_title="Оценка потребительских предпочтений", layout="centered")

# Константы
GROUPS = {
    "premium": "Премиум",
    "base": "Базовая",
    "control": "Контрольная"
}
MAX_PARTICIPANTS_PER_GROUP = 15
PHOTOS_DIR = "photos"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1V7noJAH2l1ZPqhZw7LSntPz4K7d3i79O70TLufSZdbo/edit?pli=1&gid=0#gid=0"

# Инициализация Google Sheets
@st.cache_resource
def init_gspread():
    """Инициализация подключения к Google Sheets"""
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Ошибка подключения к Google Sheets: {e}")
        return None

def save_to_sheets(data):
    """Сохранить данные в Google Sheets"""
    try:
        client = init_gspread()
        if client is None:
            return False
        
        # Открываем таблицу
        sheet = client.open_by_url(SHEET_URL).sheet1
        
        # Получаем существующие данные
        existing_data = sheet.get_all_values()
        
        # Если таблица пустая, добавляем заголовки
        if len(existing_data) == 0:
            headers = [
                'participant_number', 'group', 'group_key', 'product_number',
                'total_products', 'image_file', 'reaction_time', 'price_fairness',
                'max_price', 'purchase_probability', 'timestamp'
            ]
            sheet.append_row(headers)
        
        # Добавляем новую строку с данными
        row = [
            data['participant_number'],
            data['group'],
            data['group_key'],
            data['product_number'],
            data['total_products'],
            data['image_file'],
            data['reaction_time'],
            data['price_fairness'],
            data['max_price'],
            data['purchase_probability'],
            data['timestamp']
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения в Google Sheets: {e}")
        return False

# Инициализация session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'start'
    st.session_state.participant_number = None
    st.session_state.group_key = None
    st.session_state.group_name = None
    st.session_state.current_product = 0
    st.session_state.responses = []
    st.session_state.product_start_time = None
    st.session_state.products = []

# Функции для работы с группами
def load_group_distribution():
    """Загрузить распределение групп из session state"""
    if 'group_distribution' not in st.session_state:
        st.session_state.group_distribution = {key: 0 for key in GROUPS.keys()}
    return st.session_state.group_distribution

def save_group_distribution(distribution):
    """Сохранить распределение групп в session state"""
    st.session_state.group_distribution = distribution

def assign_group():
    """Назначить группу участнику с балансировкой"""
    distribution = load_group_distribution()
    
    # Доступные группы (где еще не 15 участников)
    available_groups = [
        key for key, count in distribution.items() 
        if count < MAX_PARTICIPANTS_PER_GROUP
    ]
    
    if not available_groups:
        return None, None
    
    # Выбираем группу с минимальным количеством участников
    min_count = min(distribution[key] for key in available_groups)
    groups_with_min = [key for key in available_groups if distribution[key] == min_count]
    group_key = random.choice(groups_with_min)
    
    # Обновляем распределение
    distribution[group_key] += 1
    save_group_distribution(distribution)
    
    return group_key, GROUPS[group_key]

def load_products(group_key):
    """Загрузить список изображений товаров для группы"""
    photos_path = os.path.join(PHOTOS_DIR, group_key)
    
    # Ищем изображения
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']:
        image_files.extend(glob.glob(os.path.join(photos_path, ext)))
    
    return sorted(image_files)

# ==================== ЭКРАНЫ ====================

if st.session_state.stage == 'start':
    st.title("🛍️ Оценка потребительских предпочтений")
    st.write("")
    
    st.markdown("""
    ### Добро пожаловать в исследование!
    
    Это экспериментальное исследование оценки потребительских предпочтений.
    """)
    
    participant_number = st.text_input("📝 Введите ваш номер респондента:", key="participant_input")
    
    if st.button("▶️ Начать", type="primary", use_container_width=True):
        if participant_number:
            # Назначаем группу
            group_key, group_name = assign_group()
            
            if group_key is None:
                st.error("❌ Все группы заполнены! Максимум 15 участников в каждой группе.")
            else:
                # Загружаем продукты для этой группы
                products = load_products(group_key)
                
                if not products:
                    st.error(f"❌ Ошибка: изображения не найдены в папке {PHOTOS_DIR}/{group_key}/")
                else:
                    st.session_state.participant_number = participant_number
                    st.session_state.group_key = group_key
                    st.session_state.group_name = group_name
                    st.session_state.products = products
                    st.session_state.stage = 'instruction'
                    st.rerun()
        else:
            st.warning("⚠️ Пожалуйста, введите номер респондента")

elif st.session_state.stage == 'instruction':
    st.title("📋 Инструкция")
    
    st.markdown("""
    ### Уважаемый участник!
    
    Благодарим вас за согласие принять участие в нашем исследовании. 
    Ваша задача - оценить ряд товаров, как если бы вы рассматривали 
    их в интернет-магазине.
    
    #### Процедура:
    
    1. 🖼️ Вы увидите изображение товара и его цену
    2. ✅ Нажмите кнопку "Перейти к оценке"
    3. 📝 Ответьте на 3 вопроса о товаре
    
    #### Важно:
    - ⚡ Постарайтесь отвечать быстро и интуитивно, как при реальной покупке в интернете
    - 💭 Не задумывайтесь слишком долго над ответами
    
    ---
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("▶️ Начать опрос", type="primary", use_container_width=True):
            st.session_state.stage = 'survey'
            st.session_state.current_product = 0
            st.session_state.product_start_time = datetime.now()
            st.rerun()

elif st.session_state.stage == 'survey':
    products = st.session_state.products
    current_idx = st.session_state.current_product
    
    if current_idx < len(products):
        # Прогресс-бар
        progress = (current_idx + 1) / len(products)
        st.progress(progress, text=f"Товар {current_idx + 1} из {len(products)}")
        
        st.markdown("---")
        
        # Показываем изображение товара
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            try:
                st.image(products[current_idx], use_container_width=True)
            except Exception as e:
                st.error(f"Ошибка загрузки изображения: {e}")
                st.write(f"Путь: {products[current_idx]}")
        
        st.markdown("---")
        
        # Форма с вопросами
        with st.form(key=f"product_form_{current_idx}"):
            st.subheader("📊 Оцените товар:")
            
            # Вопрос 1
            st.markdown("##### 1. Насколько справедливой вам кажется указанная цена товара?")
            q1 = st.radio(
                "Выберите вариант:",
                options=[1, 2, 3, 4, 5, 6, 7],
                format_func=lambda x: {
                    1: "1 — Совершенно несправедливо",
                    2: "2 — Очень несправедливо",
                    3: "3 — Скорее несправедливо",
                    4: "4 — Ни да, ни нет (Нейтрально)",
                    5: "5 — Скорее справедливо",
                    6: "6 — Очень справедливо",
                    7: "7 — Абсолютно справедливо"
                }[x],
                key=f"q1_{current_idx}",
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Вопрос 2
            st.markdown("##### 2. Какова максимальная сумма, которую вы были бы готовы заплатить за этот товар?")
            q2 = st.number_input(
                "Введите сумму в рублях:",
                min_value=0,
                step=100,
                key=f"q2_{current_idx}",
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Вопрос 3
            st.markdown("##### 3. Насколько вероятно, что вы купили бы этот товар по указанной цене?")
            q3 = st.radio(
                "Выберите вариант:",
                options=[1, 2, 3, 4, 5, 6, 7],
                format_func=lambda x: {
                    1: "1 — Точно нет",
                    2: "2 — Крайне маловероятно",
                    3: "3 — Маловероятно",
                    4: "4 — Затрудняюсь ответить",
                    5: "5 — Вероятно",
                    6: "6 — Очень вероятно",
                    7: "7 — Определенно да"
                }[x],
                key=f"q3_{current_idx}",
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            
            # Кнопка отправки
            button_text = "➡️ Следующий товар" if current_idx < len(products) - 1 else "✅ Завершить опрос"
            submitted = st.form_submit_button(button_text, type="primary", use_container_width=True)
            
            if submitted:
                # Вычисляем время реакции
                reaction_time = (datetime.now() - st.session_state.product_start_time).total_seconds()
                
                # Создаем объект с данными
                response = {
                    'participant_number': st.session_state.participant_number,
                    'group': st.session_state.group_name,
                    'group_key': st.session_state.group_key,
                    'product_number': current_idx + 1,
                    'total_products': len(products),
                    'image_file': os.path.basename(products[current_idx]),
                    'reaction_time': round(reaction_time, 3),
                    'price_fairness': q1,
                    'max_price': q2,
                    'purchase_probability': q3,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Сохраняем в Google Sheets
                with st.spinner('Сохранение данных...'):
                    success = save_to_sheets(response)
                
                if success:
                    st.session_state.responses.append(response)
                    
                    # Переходим к следующему товару или завершаем
                    if current_idx < len(products) - 1:
                        st.session_state.current_product += 1
                        st.session_state.product_start_time = datetime.now()
                        st.rerun()
                    else:
                        st.session_state.stage = 'finish'
                        st.rerun()
                else:
                    st.error("❌ Ошибка сохранения данных. Попробуйте еще раз.")

elif st.session_state.stage == 'finish':
    st.title("✅ Опрос завершен!")
    st.success("Благодарим вас за участие в исследовании!")
    st.balloons()
    
    st.markdown("---")
    st.markdown("### Thank you, goodbye!")
    
    st.markdown("---")
    
    if st.button("🔄 Начать новый опрос", use_container_width=True):
        # Сброс состояния
        st.session_state.stage = 'start'
        st.session_state.participant_number = None
        st.session_state.group_key = None
        st.session_state.group_name = None
        st.session_state.current_product = 0
        st.session_state.responses = []
        st.session_state.product_start_time = None
        st.session_state.products = []
        st.rerun()
