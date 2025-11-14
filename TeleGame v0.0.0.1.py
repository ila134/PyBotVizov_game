from telegram import ReplyKeyboardMarkup, Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8180790759:AAG9G76WQASopp_861C1vpVf5NNxD_9yAec"
VIDEO_PATH = "path/to/your/video.mp4"  # Update this to your actual video path

# All available shapes
ALL_SHAPES = {
    "🔺 Треугольник": "треугольник",
    "🟥 Квадрат": "квадрат",
    "🟡 Круг": "круг",
    "🟦 Прямоугольник": "прямоугольник",
    "〰️ Зигзаг": "зигзаг"
}

# Texts for each shape
FIGURE_TEXTS = {
    "треугольник": [
        "1. Треугольник - лидер. "
        "Треугольник честолюбив, решителен, уверен в себе, независим. Они обладают способностью "
        "концентрироваться на главной цели и с успехом её добиваться. Треугольники боятся оказываться неправыми "
        "и с большим трудом признают свои ошибки. Острые углы этой фигуры тоже оставляют отпечаток на "
        "характере: треугольники часто бывают резкими, способны плести интриги. Для Треугольника власть "
        "и достижения - мотив сами по себе. Если надо, он ради этого и грязной работой может заняться. "
        "Треугольник, будучи хорошим политиком, скорее заставит другие фигуры работать на себя. "
        "В отличие от Квадратов, Треугольников не останавливает новая ситуация, они не ждут, пока родится или спустится "
        '"сверху" правильное решение. Они – авантюристы и ориентируются на себя и собственные представления, '
        "скорее создавая собственные правила игры, чем подчиняясь чужим! Рано или поздно он построит свою систему.",
    ],
    "квадрат": [
        "Квадрат – исполнитель.\n"
        "Внимательный, выносливый и организованный.\n"
        "На него можно положиться: он либо выполняет обещания, либо не дает обещаний вовсе.\n"
        "Достоинство и одновременно слабость Квадрата – он слишком правильный, поэтому в бизнесе редко "
        'выбивается на самый верх! Квадраты – прекрасные исполнители в условиях, когда им "сверху" спускают '
        "инструкции или чёткие регламенты поведения. Наткнувшись на неопределённость, Квадрат тормозит, "
        "пока не найдёт правильного, с его точки зрения, решения, и поэтому часто опаздывает - а это недопустимо "
        "в быстро меняющихся обстоятельствах. Зато Квадраты прекрасно делают карьеру чиновников, из них выходят "
        "добротные бюрократы, полковники и генералы. Подчинённые Квадрата слушаются, могут ценить и уважать, "
        "но очень редко любят. Он для этого суховат и отстранён. Поэтому Квадраты – менеджеры, но никак не лидеры",
    ],
    "круг": [
        "Круг – коммуникатор.\n"
        "Обратите внимание: это первая фигура без углов. Круг не жёсток, но и неустойчивым его назвать нельзя: "
        "он может катиться, но не может упасть. Для Круга главное - гармония отношений, бесконфликтность, "
        "демократичность. Они – отличные коммуникаторы, отличаются эмпатией, доброжелательны, щедры, уступчивы. "
        "В отношениях с окружающими гибки, могут одинаково хорошо общаться с самыми разными психологическими типами. "
        "Легко попадают под чужое влияние и попадают в созависимые отношения с партнерами, начальниками и клиентами. "
        "Им трудно назвать свою цену и очерчивать свои личностные границы! Они часто выбирают «мягкую» нишу на "
        "рынке - социальное предпринимательство. Кругам очень важно постоянно отслеживать свои личные цели "
        "и потребности и разделять их от чужих. Круг — это нелинейная форма правополушарных мыслителей, "
        "у которых преобладает образное, интуитивное, эмоционально окрашенное мышление",
    ],
    "прямоугольник": [
        "Прямоугольник – переходная фигура.\n"
        "Из пяти предложенных фигур — прямоугольник — самая неустойчивая. Люди, выбравшие для себя "
        "эту фигуру, на самом деле испытывают переломный момент. Прямоугольник — это временная форма личности, "
        "которую могут «носить» остальные четыре фигуры в определённые периоды жизни. Это люди, "
        "не удовлетворённые тем образом жизни, который они ведут сейчас, и поэтому занятые поисками "
        "лучшего положения. Поступки прямоугольников часто непоследовательны и непредсказуемы. "
        "Самооценка у этого типа чрезвычайно низка, поэтому они часто становятся жертвами манипуляций и интриг. "
        "Тем не менее, как и у всех людей, у прямоугольников есть позитивные качества, привлекающие к ним "
        "окружающих, — любознательность, пытливость, смелость.",
    ],
    "зигзаг": [
        "Зигзаг – творец.\n"
        "Главный вектор Зигзага - креативность, бунтарство, энтузиазм, жажда изменений. Для Зигзага нет авторитетов. "
        "Он творчески настроен, не заинтересован в консенсусе, стремится к независимости, к разнообразию и новизне. "
        "Несдержан и возбудим, эксцентричен в действиях и словах. В деловой среде Зигзаги встречаются гораздо реже "
        "других фигур. Он может работать до изнеможения над реализацией своих идей, но ему редко что удаётся довести "
        "до конца: бросает, потому что ему становится скучно. В жизни он разбросан, непостоянен, недисциплинирован. "
        "Мораль, законы, общественное мнение ему безразличны. Хорошо проявляет себя в творческой и проектной сфере "
        "бизнеса, где отсутствует жесткая дисциплина и монотонность. Представители этой фигуры — неутомимые проповедники "
        "своих идей и умеют завлекать, мотивировать всех вокруг себя.",
    ]
}

user_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user_id = update.message.from_user.id
    user_data[user_id] = {
        'selected_shapes': [],
        'available_shapes': list(ALL_SHAPES.keys())
    }

    await show_shapes_menu(update, user_id)


async def show_shapes_menu(update: Update, user_id: int):
    """Show the shapes selection menu."""
    # Create keyboard from available shapes
    shapes_keyboard = []
    row = []

    for shape in user_data[user_id]['available_shapes']:
        row.append(shape)
        if len(row) == 2:  # 2 buttons per row
            shapes_keyboard.append(row)
            row = []

    if row:  # Add remaining buttons
        shapes_keyboard.append(row)

    # Add control buttons
    if user_data[user_id]['selected_shapes']:
        shapes_keyboard.append(["✅ Завершить выбор", "🔄 Сбросить"])
    else:
        shapes_keyboard.append(["❌ Отмена"])

    message = "Выберите фигуры:" if not user_data[user_id]['selected_shapes'] else \
        f"Выбрано: {len(user_data[user_id]['selected_shapes'])}. Выберите ещё или завершите:"

    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(
            shapes_keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages."""
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data:
        await start(update, context)
        return

    # Handle shape selection
    if text in ALL_SHAPES:
        shape_key = text
        shape_name = ALL_SHAPES[shape_key]

        # Add selected shape
        user_data[user_id]['selected_shapes'].append(shape_name)
        # Remove from available
        user_data[user_id]['available_shapes'].remove(shape_key)

        await show_shapes_menu(update, user_id)

    # Complete selection
    elif text == "✅ Завершить выбор":
        if len(user_data[user_id]['selected_shapes']) > 0:
            await show_results(update, user_id)
        else:
            await update.message.reply_text("Вы не выбрали ни одной фигуры!")
            await show_shapes_menu(update, user_id)

    # Reset selection
    elif text == "🔄 Сбросить":
        user_data[user_id] = {
            'selected_shapes': [],
            'available_shapes': list(ALL_SHAPES.keys())
        }
        await show_shapes_menu(update, user_id)

    # Cancel
    elif text == "❌ Отмена":
        await update.message.reply_text(
            "Выбор отменён",
            reply_markup=ReplyKeyboardMarkup([["🔷 Начать заново"]], resize_keyboard=True)
        )
        user_data.pop(user_id, None)

    # Start over
    elif text == "🔷 Начать заново":
        await start(update, context)

    else:
        await update.message.reply_text("Пожалуйста, используйте кнопки меню")


async def show_results(update: Update, user_id: int):
    """Show results for selected shapes."""
    # Send texts for all selected shapes
    for shape in user_data[user_id]['selected_shapes']:
        await update.message.reply_text(f"🔷 {shape.capitalize()}:")
        for text in FIGURE_TEXTS[shape]:
            await update.message.reply_text(text)
        await update.message.reply_text("━━━━━━━━━━")

    # Send video
    try:
        if os.path.exists(VIDEO_PATH):
            with open(VIDEO_PATH, 'rb') as video_file:
                await update.message.reply_video(
                    video=InputFile(video_file),
                    caption="Видео-пояснение по выбранным фигурам"
                )
        else:
            await update.message.reply_text("Видео-пояснение недоступно")
            logger.warning(f"Video file not found at {VIDEO_PATH}")
    except Exception as e:
        await update.message.reply_text("Произошла ошибка при отправке видео")
        logger.error(f"Error sending video: {e}")

    # Offer new actions
    await update.message.reply_text(
        "Выбор завершён!",
        reply_markup=ReplyKeyboardMarkup(
            [["🔷 Начать заново", "❌ Выход"]],
            resize_keyboard=True
        )
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    if update and update.message:
        await update.message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте снова или начните заново с /start."
        )


def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()