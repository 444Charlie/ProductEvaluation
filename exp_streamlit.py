import streamlit as st
import pandas as pd
import random
import json
from datetime import datetime
import os

# Настройка страницы
st.set_page_config(page_title="Оценка потребительских предпочтений", layout="centered")

# Константы
GROUPS = {
    "premium": "Премиум",
    "base": "Базовая",
    "control": "Контрольная"
}
MAX_PARTICIPANTS_PER_GROUP = 15

# Инициализация session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'start'  # start, instruction, survey, finish
    st.session_state.participant_number = None
    st.session_state.group_key = None
    st.session_state.group_name = None
    st.session_state.current_product = 0
    st.session_state.responses = []
    st.session_state.product_start_time = None

# Функции для работы с группами (используем session_state вместо файлов)
def load_group_distribution():
    """Загрузить распределение групп"""
    if 'group_distribution' not in st.session_state:
        st.session_state.group_distribution = {key: 0 for key in GROUPS.keys()}
    return st.session_state.group_distribution

def save_group_distribution(distribution):
    """Сохранить распределение групп"""
    st.session_state.group_distribution = distribution

def assign_group():
    """Назначить группу участнику"""
    distribution = load_group_distribution()
    
    # Доступные группы
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

# Список товаров для демонстрации (замените на реальные пути к изображениям)
PRODUCTS = {
    "premium": ["product1.png", "product2.png", "product3.png"],
    "base": ["product1.png", "product2.png", "product3.png"],
    "control": ["product1.png", "product2.png", "product3.png"]
}

# ==================== ЭКРАНЫ ====================

if st.session_state.stage == 'start':
    st.title("🛍️ Оценка потребительских предпочтений")
    st.write("")
    
    participant_number = st.text_input("Введите ваш номер респондента:", key="participant_input")
    
    if st.button("Начать", type="primary"):
        if participant_number:
            # Назначаем группу
            group_key, group_name = assign_group()
            
            if group_key is None:
                st.error("❌ Все группы заполнены! Максимум 15 участников в каждой группе.")
            else:
                st.session_state.participant_number = participant_number
                st.session_state.group_key = group_key
                st.session_state.group_name = group_name
                st.session_state.stage = 'instruction'
                st.rerun()
        else:
            st.warning("⚠️ Пожалуйста, введите номер респондента")

elif st.session_state.stage == 'instruction':
    st.title("Инструкция")
    
    st.markdown("""
    ### Уважаемый участник!
    
    Благодарим вас за согласие принять участие в нашем исследовании. 
    Ваша задача - оценить ряд товаров, как если бы вы рассматривали 
    их в интернет-магазине.
    
    **Процедура:**
    
    1. Вы увидите изображение товара и его цену
    2. Нажмите кнопку "Перейти к оценке"
    3. Ответьте на 3 вопроса о товаре
    
    **Важно:**
    - Постарайтесь отвечать быстро и интуитивно, как при реальной покупке в интернете
    - Не задумывайтесь слишком долго над ответами
    """)
    
    if st.button("Начать опрос", type="primary"):
        st.session_state.stage = 'survey'
        st.session_state.current_product = 0
        st.session_state.product_start_time = datetime.now()
        st.rerun()

elif st.session_state.stage == 'survey':
    products = PRODUCTS[st.session_state.group_key]
    current_idx = st.session_state.current_product
    
    if current_idx < len(products):
        st.title(f"Товар {current_idx + 1} из {len(products)}")
        st.write(f"**Группа:** {st.session_state.group_name}")
        
        # Показываем изображение товара
        st.image(f"https://via.placeholder.com/400x400.png?text=Товар+{current_idx+1}", 
                 caption=f"Товар {current_idx + 1}", 
                 use_container_width=True)
        
        st.write("---")
        
        # Форма с вопросами
        with st.form(key=f"product_form_{current_idx}"):
            st.subheader("Оцените товар:")
            
            # Вопрос 1
            q1 = st.radio(
                "1. Насколько справедливой вам кажется указанная цена товара?",
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
                key=f"q1_{current_idx}"
            )
            
            # Вопрос 2
            q2 = st.number_input(
                "2. Какова максимальная сумма, которую вы были бы готовы заплатить за этот товар? (в рублях)",
                min_value=0,
                step=100,
                key=f"q2_{current_idx}"
            )
            
            # Вопрос 3
            q3 = st.radio(
                "3. Насколько вероятно, что вы купили бы этот товар по указанной цене?",
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
                key=f"q3_{current_idx}"
            )
            
            submitted = st.form_submit_button("Следующий товар" if current_idx < len(products) - 1 else "Завершить опрос")
            
            if submitted:
                # Вычисляем время реакции
                reaction_time = (datetime.now() - st.session_state.product_start_time).total_seconds()
                
                # Сохраняем ответы
                response = {
                    'participant_number': st.session_state.participant_number,
                    'group': st.session_state.group_name,
                    'group_key': st.session_state.group_key,
                    'product_number': current_idx + 1,
                    'total_products': len(products),
                    'image_file': products[current_idx],
                    'reaction_time': round(reaction_time, 3),
                    'price_fairness': q1,
                    'max_price': q2,
                    'purchase_probability': q3,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                st.session_state.responses.append(response)
                
                # Переходим к следующему товару или завершаем
                if current_idx < len(products) - 1:
                    st.session_state.current_product += 1
                    st.session_state.product_start_time = datetime.now()
                    st.rerun()
                else:
                    # Сохраняем результаты
                    df = pd.DataFrame(st.session_state.responses)
                    # Здесь можно добавить сохранение в файл или базу данных
                    
                    st.session_state.stage = 'finish'
                    st.rerun()

elif st.session_state.stage == 'finish':
    st.title("✅ Опрос завершен!")
    st.success("Благодарим вас за участие!")
    st.balloons()
    
    st.write("**Thank you, goodbye!**")
    
    # Показываем результаты (для отладки)
    if st.checkbox("Показать мои ответы"):
        st.dataframe(pd.DataFrame(st.session_state.responses))
    
    if st.button("Начать новый опрос"):
        # Сброс состояния
        st.session_state.stage = 'start'
        st.session_state.participant_number = None
        st.session_state.group_key = None
        st.session_state.group_name = None
        st.session_state.current_product = 0
        st.session_state.responses = []
        st.session_state.product_start_time = None
        st.rerun()
