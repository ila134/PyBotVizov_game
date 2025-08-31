import logging
import random
import requests
import json
import time
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8180790759:AAG9G76WQASopp_861C1vpVf5NNxD_9yAec"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

(START, STAGE1, STAGE2_DICE, STAGE2, STAGE2_REFORMULATE,
 STAGE3_FIRST_CHOICE, STAGE3_SECOND_CHOICE, STAGE4_CARDS, COMPLETED) = range(9)

USER_REQUEST, STAGE2_ANSWER, STAGE3_SHAPES, CARD_DRAWN = "user_request", "stage2_answer", "stage3_shapes", "card_drawn"
user_states, user_data = {}, {}

SHAPE_IMAGES = {
    'square': 'AgACAgIAAxkBAAMKZmXwCq1s6v1i9hVlQq3hJp5Wv1AAAp3LMRtPb9BJQhVU8hLf0CkBAAMCAAN5AAMvBA',
    'triangle': 'AgACAgIAAxkBAAMMZmXwDgABk3h9b8fN3QABH1MAAbKQ3AACncsxG09v0EmQx5wv3qk0JwEAAwIAA3kAAy8E',
    'circle': 'AgACAgIAAxkBAAMOZmXwEf8YQrXv9Wt3v1hQY3sAAUcXAAKeyzEbT2_QSQAB8hUAAXzQTwEAAwIAA3kAAy8E',
    'zigzag': 'AgACAgIAAxkBAAMQZmXwFp3gAAHwGvXQAAHp5zY3n2UAAQACn8sxG09v0En3w8t3tUfVJwEAAwIAA3kAAy8E',
    'rectangle': 'AgACAgIAAxkBAAMKZmXwCq1s6v1i9hVlQq3hJp5Wv1AAAp3LMRtPb9BJQhVU8hLf0CkBAAMCAAN5AAMvBA'
}

SHAPE_DESCRIPTION_FILES = {
    'square': 'психогеометрия-изображения-1.jpg',
    'triangle': 'психогеометрия-изображения-2.jpg',
    'circle': 'психогеометрия-изображения-3.jpg',
    'zigzag': 'психогеометрия-изображения-4.jpg',
    'rectangle': 'психогеометрия-изображения-5.jpg'
}

METAPHORICAL_CARDS = [{"id": i, "image": f"метафорические карты вызов-изображения-{i}.jpg"} for i in range(1, 53)]

def send_photo(chat_id, photo_path, caption=None, reply_markup=None):
    url = f"{BASE_URL}/sendPhoto"
    if photo_path.startswith('AgAC'):
        payload = {'chat_id': chat_id, 'photo': photo_path}
        if caption: payload['caption'] = caption
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        try: return requests.post(url, json=payload).json()
        except Exception as e: logger.error(f"Error sending photo by file_id: {e}"); return None
    else:
        try:
            with open(photo_path, 'rb') as photo_file:
                files, payload = {'photo': photo_file}, {'chat_id': chat_id}
                if caption: payload['caption'] = caption
                if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
                return requests.post(url, data=payload, files=files).json()
        except FileNotFoundError:
            logger.error(f"File not found: {photo_path}")
            send_message(chat_id, f"⚠️ Файл с описанием не найден: {photo_path}")
            return None
        except Exception as e: logger.error(f"Error sending photo file: {e}"); return None

def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    url, payload = f"{BASE_URL}/sendMessage", {'chat_id': chat_id, 'text': text}
    if parse_mode: payload['parse_mode'] = parse_mode
    if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
    try: return requests.post(url, json=payload).json()
    except Exception as e: logger.error(f"Error sending message: {e}"); return None

def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode=None):
    url, payload = f"{BASE_URL}/editMessageText", {'chat_id': chat_id, 'message_id': message_id, 'text': text}
    if parse_mode: payload['parse_mode'] = parse_mode
    if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
    try: return requests.post(url, json=payload).json()
    except Exception as e: logger.error(f"Error editing message: {e}"); return None

def answer_callback_query(callback_query_id, text=None):
    url, payload = f"{BASE_URL}/answerCallbackQuery", {'callback_query_id': callback_query_id}
    if text: payload['text'] = text
    try: return requests.post(url, json=payload).json()
    except Exception as e: logger.error(f"Error answering callback: {e}"); return None

def create_reply_keyboard(buttons, resize_keyboard=True):
    return {'keyboard': buttons, 'resize_keyboard': resize_keyboard, 'one_time_keyboard': True}

def create_inline_keyboard(buttons): return {'inline_keyboard': buttons}

def create_inline_button(text, callback_data): return {'text': text, 'callback_data': callback_data}

def send_welcome_message(chat_id, first_name):
    welcome_text = f"""👋 Привет, {first_name}! Ты оказался(лась) в обучающей психологической игре «Вызов!» — это трансформационное путешествие к себе, своему делу и авторской позиции в жизни.

🌟 Здесь не будет правильных или неправильных ответов. Только ты, твой путь, подсказки и прозрения.

🌀 Погрузись в интерактивную историю, где каждый ход — это шаг к себе. Тебя ждут психологические тесты, кейсы, вопросы для размышления, которые многое о тебе расскажут, и мягкие подсказки, ведущие к осознанию.

🎯 Играй, исследуй, открывай — в твоём ритме."""
    keyboard = create_reply_keyboard([['🎯 НАЧАТЬ ИГРУ']])
    send_message(chat_id, welcome_text, reply_markup=keyboard)

def start(chat_id, user_id, first_name):
    user_states[user_id], user_data[user_id] = START, {}
    send_welcome_message(chat_id, first_name)

def stage_intro(chat_id, user_id):
    user_states[user_id] = STAGE1
    stage1_text = """🧩 <b>Этап 1. Формулируем запрос</b>

💬 С каким вопросом, тревогой, проблемой, цели ты пришёл в игру?

Это может быть:
• Желание выйти из найма и начать своё дело
• Стремление повысить доход и финансовую устойчивость
• Поиск своей уникальности и предназначения
• Направление дела души, которое будет вдохновлять
• Преодоление сомнений и неопределённости
• Выбор между несколькими путями развития

📌 <b>Напиши коротко свой запрос:</b>
Можно начать с фраз:
«Я хочу понять, как…»
«Меня беспокоит…» 
«Я стою перед выбором…»
«Мне важно разобраться с…»
«Хочу найти способ…»

✨ Не переживай о формулировках — это только начала твоего пути. Главное, чтобы это было искренне."""
    send_message(chat_id, stage1_text, parse_mode='HTML')

def stage1_get_request(chat_id, user_id, text):
    user_data[user_id][USER_REQUEST], user_states[user_id] = text, STAGE2_DICE
    keyboard = create_inline_keyboard([[create_inline_button("🎲 Бросить кубик", "throw_dice")]])
    confirmation_text = f"""✅ <b>Запрос сохранен:</b> 
«{text}»

🎲 <b>Этап 2. Калибровка запроса (интерактив)</b>

Теперь бросим воображаемый кубик интуиции.
Задай себе вопрос:
«Мой запрос истинный?»
Если выпадет чётное число — это ДА, нечётное — НЕТ.
Нажми на кнопку 🎲 — и узнаем!"""
    send_message(chat_id, confirmation_text, parse_mode='HTML', reply_markup=keyboard)

def stage2_throw_dice(chat_id, message_id, user_id, callback_query_id):
    answer_callback_query(callback_query_id)
    dice_roll = random.randint(1, 6)
    is_even = dice_roll % 2 == 0
    result_text = "ДА" if is_even else "НЕТ"  # Исправлено: правильное присвоение значения

    user_data[user_id][STAGE2_ANSWER] = result_text
    user_states[user_id] = STAGE2

    message = f"🎲 Выпало: {dice_roll} ({result_text})\n\n"

    if is_even:
        message += "✅ Отлично! Твой запрос истинный и резонирует с твоим внутренним состоянием.\n\nПродолжаем исследование!"
        keyboard = create_inline_keyboard([[create_inline_button("➡️ Далее", "next_stage")]])
    else:
        message += "🤔 Значит, ты ещё можешь переформулировать запрос. Попробуй заглянуть глубже."
        keyboard = create_inline_keyboard([
            [create_inline_button("🔄 Переформулировать", "reformulate")],
            [create_inline_button("➡️ Продолжить как есть", "next_stage")]
        ])
    edit_message_text(chat_id, message_id, message, reply_markup=keyboard)

def stage2_reformulate(chat_id, message_id, user_id, callback_query_id):
    answer_callback_query(callback_query_id); user_states[user_id] = STAGE2_REFORMULATE
    reformulate_text = """🔄 <b>Переформулируем запрос</b>

Попробуй посмотреть на свою ситуацию с другой стороны:
• Может быть, изменить угол зрения?
• Или сформулировать более конкретно?
• Или наоборот — более широко и открыто?

Напиши новый вариант своего запроса:"""
    edit_message_text(chat_id, message_id, reformulate_text, parse_mode='HTML')

def stage2_get_reformulation(chat_id, user_id, text):
    user_data[user_id][USER_REQUEST], user_states[user_id] = text, STAGE2_DICE
    keyboard = create_inline_keyboard([[create_inline_button("🎲 Бросить снова", "throw_dice")]])
    retry_text = f"""✅ <b>Новый запрос:</b> 
«{text}»

Проверим его снова с помощью кубика интуиции!"""
    send_message(chat_id, retry_text, parse_mode='HTML', reply_markup=keyboard)

def stage2_next(chat_id, message_id, user_id, callback_query_id):
    answer_callback_query(callback_query_id); user_states[user_id] = STAGE3_FIRST_CHOICE
    intro_text = """🔺 <b>Этап 3. Психогеометрия — кто ты в этой игре?</b>

Представь пять геометрических фигур:
🔷 Квадрат, 🔺 Треугольник, ⚪ Круг, 🌀 Зигзаг, 🔶 Прямоугольник

Сейчас ты выберешь две фигуры, которые откликаются тебе сильнее других.

📌 <b>Инструкция:</b>
Закрой глаза на пару секунд и спроси себя:
«Какая из этих фигур мне ближе всего? Что я часто рисую на полях? Какая вызывает доверие или внутренний отклик?»

Расставь 5 фигур по степени отклика — от 1 до 5.
Самая первая — это твой текущий психотип.
Вторая — дополнительный ресурс."""
    keyboard = create_inline_keyboard([[create_inline_button("🔘 Готов(а) выбрать", "ready_for_shapes")]])
    send_message(chat_id, intro_text, parse_mode='HTML', reply_markup=keyboard)

def stage3_show_shapes(chat_id, message_id, user_id, callback_query_id):
    answer_callback_query(callback_query_id)
    try: delete_message(chat_id, message_id)
    except: pass
    for shape_key, file_id in SHAPE_IMAGES.items():
        send_photo(chat_id, file_id); time.sleep(0.5)
    keyboard = create_inline_keyboard([
        [create_inline_button("🔷 Квадрат", "shape_square")],
        [create_inline_button("🔺 Треугольник", "shape_triangle")],
        [create_inline_button("⚪ Круг", "shape_circle")],
        [create_inline_button("🌀 Зигзаг", "shape_zigzag")],
        [create_inline_button("🔶 Прямоугольник", "shape_rectangle")]
    ])
    send_message(chat_id, "Выбери первую фигуру, которая тебе ближе всего:", reply_markup=keyboard)

def stage3_first_choice(chat_id, message_id, user_id, shape_key, callback_query_id):
    answer_callback_query(callback_query_id)
    try: delete_message(chat_id, message_id)
    except: pass
    user_data[user_id][STAGE3_SHAPES], user_states[user_id] = [shape_key], STAGE3_SECOND_CHOICE
    all_shapes, remaining_shapes = ['square', 'triangle', 'circle', 'zigzag', 'rectangle'], [s for s in ['square', 'triangle', 'circle', 'zigzag', 'rectangle'] if s != shape_key]
    keyboard_buttons = []
    for shape in remaining_shapes:
        shape_name = {"square": "🔷 Квадрат", "triangle": "🔺 Треугольник", "circle": "⚪ Круг", "zigzag": "🌀 Зигзаг", "rectangle": "🔶 Прямоугольник"}[shape]
        keyboard_buttons.append([create_inline_button(shape_name, f"shape_{shape}")])
    keyboard = create_inline_keyboard(keyboard_buttons)
    send_message(chat_id, "Отлично! Теперь выбери вторую фигуру из оставшихся:", reply_markup=keyboard)

def stage3_second_choice(chat_id, message_id, user_id, shape_key, callback_query_id):
    answer_callback_query(callback_query_id)
    try: delete_message(chat_id, message_id)
    except: pass
    if user_id not in user_data: user_data[user_id] = {}
    if STAGE3_SHAPES not in user_data[user_id]: user_data[user_id][STAGE3_SHAPES] = []
    user_shapes = user_data[user_id][STAGE3_SHAPES]; user_shapes.append(shape_key)
    if len(user_shapes) < 2: send_message(chat_id, "Ошибка: не выбраны фигуры. Начните заново с /start"); user_states[user_id] = START; return
    final_text = """✨ <b>Отлично! Ты завершил(а) этап психогеометрии.</b>

Вот расшифровка выбранных тобой фигур:

Каждая фигура отражает определённые качества личности, стиль мышления и поведения. Сочетание двух фигур показывает твой уникальный профиль."""
    send_message(chat_id, final_text, parse_mode='HTML'); time.sleep(1)
    for shape in user_shapes:
        if shape in SHAPE_DESCRIPTION_FILES:
            photo_path = SHAPE_DESCRIPTION_FILES[shape]
            print(f"Пытаемся отправить фото: {photo_path}")
            if os.path.exists(photo_path):
                print(f"Файл существует: {photo_path}"); send_photo(chat_id, photo_path); time.sleep(1)
            else:
                print(f"Файл не найден: {photo_path}")
                shape_descriptions = {
                    'square': "🔷 Квадрат: Организованный, практичный, надежный",
                    'triangle': "🔺 Треугольник: Лидер, целеустремленный, амбициозный",
                    'circle': "⚪ Круг: Дружелюбный, заботливый, коммуникабельный",
                    'zigzag': "🌀 Зигзаг: Креативный, инновационный, непредсказуемый",
                    'rectangle': "🔶 Прямоугольник: Переходное состояние, поиск, изменение"
                }
                send_message(chat_id, f"📝 {shape_descriptions.get(shape, 'Описание фигуры')}")
    time.sleep(2); stage4_intro(chat_id, user_id)

def stage4_intro(chat_id, user_id):
    user_states[user_id] = STAGE4_CARDS
    intro_text = """🃏 <b>Этап 4. Метафорические карты в игре</b>

В течение игры ты можешь (и даже нужно) вытягивать метафорическую карту — визуальный образ, который работает как зеркало твоего бессознательного.

🪞 Карта может показать:
– твоё внутреннее состояние (о чём ты не говорил, но чувствуешь);
– скрытые мотивы и желания, которые управляют твоими решениями;
– то, что мешает двигаться вперёд — страх, образ врага, тень, старая роль;
– ресурс, о котором ты забыл, или новый угол зрения на ситуацию.

📌 Ты можешь просить карту:
– на каждом поле,
– перед важным выбором,
– когда «застрял» или не чувствуешь энергии.

Просто скажи: «Хочу карту», и она придёт."""
    keyboard = create_reply_keyboard([['🎴 Вытянуть карту'], ['➡️ Завершить игру']])
    send_message(chat_id, intro_text, parse_mode='HTML', reply_markup=keyboard)

def draw_metaphorical_card(chat_id, user_id):
    card = random.choice(METAPHORICAL_CARDS); user_data[user_id][CARD_DRAWN] = card
    if os.path.exists(card['image']): send_photo(chat_id, card['image'], caption="🎴 Выпала карта!"); time.sleep(1)
    card_text = """🎴 <b>Выпала карта!</b>

💭 Поразмышляй над этими вопросами:
• Как этот образ откликается в тебе?
• Что он говорит о твоём текущем состоянии?
• Какое послание он несёт для твоего запроса?
• Как этот образ может помочь тебе в твоём пути?

🔄 Если хочешь вытянуть ещё одну карту или получить помощь в интерпретации, используй кнопки ниже."""
    keyboard = create_reply_keyboard([['🎴 Вытянуть другую карту'], ['🤔 Помощь в интерпретации'], ['➡️ Завершить игру']])
    send_message(chat_id, card_text, parse_mode='HTML', reply_markup=keyboard)

def interpret_card(chat_id, user_id):
    if user_id in user_data and CARD_DRAWN in user_data[user_id]:
        card = user_data[user_id][CARD_DRAWN]
        interpretation_text = f"""🤔 <b>Интерпретация выпавшей карты (ID: {card['id']})</b>

📝 <b>Вопросы для самоанализа:</b>
1. Как этот образ связан с твоим запросом "{user_data[user_id].get(USER_REQUEST, '')}"?
2. Что в этом образе кажется тебе знакомым, а что новым?
3. Если бы этот образ был советником, что бы он посоветовал тебе?
4. Какие чувства вызывает у тебя этот образ?

✨ Не ищи "правильного" толкования — доверься своей интуиции. 
То, что первым пришло в голову — часто и есть самое верное для тебя."""
        send_message(chat_id, interpretation_text, parse_mode='HTML')
    else: send_message(chat_id, "Сначала вытяни карту, чтобы я мог помочь с интерпретацией.")

def complete_game(chat_id, user_id):
    completion_text = """🎉 <b>Поздравляю! Ты завершил(а) игру «Вызов!»</b>

💡 Используй эти insights о себе в жизни:
• Для понимания своих сильных сторон
• Для осознания зон развития  
• Для лучшего понимания своих мотиваций
• Для выбора направлений, которые будут тебе resonate

🔄 Если хочешь пройти игру снова с другим запросом или просто для закрепления — напиши /start

🌟 Помни: самопознание — это continuous journey, а не destination!"""
    send_message(chat_id, completion_text, parse_mode='HTML'); user_states[user_id] = COMPLETED

def delete_message(chat_id, message_id):
    url, payload = f"{BASE_URL}/deleteMessage", {'chat_id': chat_id, 'message_id': message_id}
    try: return requests.post(url, json=payload).json()
    except Exception as e: logger.error(f"Error deleting message: {e}"); return None

def cancel(chat_id, user_id):
    send_message(chat_id, 'До свидания! Напиши /start чтобы начать заново.'); user_states[user_id] = START

def process_update(update):
    try:
        print(f"Получено обновление: {update}")
        if 'message' in update:
            message = update['message']; chat_id = message['chat']['id']; user_id = message['from']['id']; first_name = message['from'].get('first_name', 'Пользователь')
            print(f"Сообщение от {first_name} (ID: {user_id}): {message.get('text', 'Нет текста')}")
            if user_id not in user_states: user_states[user_id] = START
            if user_id not in user_data: user_data[user_id] = {}
            if 'text' in message:
                text = message['text']
                if text == '/start': print("Обработка команды /start"); start(chat_id, user_id, first_name)
                elif text == '/cancel': print("Обработка команды /cancel"); cancel(chat_id, user_id)
                else:
                    current_state = user_states.get(user_id, START); print(f"Текущее состояние пользователя: {current_state}")
                    if current_state == START and text == '🎯 НАЧАТЬ ИГРУ': print("Начало игры"); stage_intro(chat_id, user_id)
                    elif current_state == STAGE1: print("Получен запрос пользователя"); stage1_get_request(chat_id, user_id, text)
                    elif current_state == STAGE2_REFORMULATE: print("Получена переформулировка запроса"); stage2_get_reformulation(chat_id, user_id, text)
                    elif current_state == STAGE4_CARDS:
                        if text == '🎴 Вытянуть карту' or text.lower() == 'хочу карту' or text == '🎴 Вытянуть другую карту': print("Вытягивание метафорической карты"); draw_metaphorical_card(chat_id, user_id)
                        elif text == '🤔 Помощь в интерпретации': print("Запрос интерпретации карты"); interpret_card(chat_id, user_id)
                        elif text == '➡️ Завершить игру': print("Завершение игры"); complete_game(chat_id, user_id)
                        else: print("Неизвестная команда на этапе карт"); send_message(chat_id, "Используй кнопки для взаимодействия с картами или напиши 'Хочу карту'")
                    else: print("Неизвестная команда"); send_message(chat_id, "Напишите /start чтобы начать игру")
        elif 'callback_query' in update:
            callback_query = update['callback_query']; message = callback_query['message']; chat_id = message['chat']['id']; message_id = message['message_id']; user_id = callback_query['from']['id']; callback_query_id = callback_query['id']; data = callback_query['data']
            print(f"Callback от пользователя {user_id}: {data}")
            if user_id not in user_states: user_states[user_id] = START
            if user_id not in user_data: user_data[user_id] = {}
            current_state = user_states.get(user_id, START); print(f"Текущее состояние пользователя: {current_state}")
            if data == 'throw_dice' and current_state == STAGE2_DICE: print("Бросок кубика"); stage2_throw_dice(chat_id, message_id, user_id, callback_query_id)
            elif data == 'reformulate' and current_state == STAGE2: print("Переформулировка запроса"); stage2_reformulate(chat_id, message_id, user_id, callback_query_id)
            elif data == 'next_stage' and current_state == STAGE2: print("Переход к следующему этапу"); stage2_next(chat_id, message_id, user_id, callback_query_id)
            elif data == 'ready_for_shapes' and current_state == STAGE3_FIRST_CHOICE: print("Пользователь готов выбрать фигуры"); stage3_show_shapes(chat_id, message_id, user_id, callback_query_id)
            elif data.startswith('shape_'):
                shape_key = data.replace('shape_', ''); print(f"Выбрана фигура: {shape_key}")
                if current_state == STAGE3_FIRST_CHOICE: stage3_first_choice(chat_id, message_id, user_id, shape_key, callback_query_id)
                elif current_state == STAGE3_SECOND_CHOICE: stage3_second_choice(chat_id, message_id, user_id, shape_key, callback_query_id)
            else: print(f"Необработанный callback в состоянии {current_state}: {data}"); answer_callback_query(callback_query_id, "Действие недоступно. Начните заново с /start")
    except Exception as e: logger.error(f"Error processing update: {e}"); logger.error(f"Update content: {update}")

def test_bot_connection():
    print("Тестирование подключения к боту..."); url = f"{BASE_URL}/getMe"
    try:
        response = requests.get(url, timeout=10); result = response.json(); print(f"Результат теста: {result}")
        if result.get('ok'): print("✅ Бот подключен успешно!"); print(f"Имя бота: {result['result']['first_name']}"); print(f"Username бота: @{result['result']['username']}"); return True
        else: print("❌ Ошибка подключения к боту"); print(f"Описание ошибки: {result.get('description')}"); return False
    except Exception as e: print(f"❌ Ошибка при тестировании подключения: {e}"); return False

def main():
    print("=" * 50); print("Запуск бота..."); print(f"Токен бота: {TOKEN[:10]}...{TOKEN[-5:]}"); print("=" * 50)
    if not test_bot_connection(): print("Не удалось подключиться к боту. Проверьте токен и интернет-соединение."); return
    offset = 0; print("Бот готов к работе. Ожидание сообщений...")
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=30"; print(f"Запрос обновлений: offset={offset}")
            response = requests.get(url, timeout=35); updates = response.json()
            if updates.get('ok'):
                if updates['result']:
                    print(f"Получено {len(updates['result'])} обновлений")
                    for update in updates['result']: offset = update['update_id'] + 1; process_update(update)
                else: print("Нет новых обновлений"); time.sleep(1)
            else: print(f"Ошибка API: {updates}"); time.sleep(5)
        except requests.exceptions.Timeout: print("Таймаут запроса, продолжаем..."); continue
        except Exception as e: print(f"Ошибка в основном цикле: {e}"); time.sleep(5)

if __name__ == '__main__': main()