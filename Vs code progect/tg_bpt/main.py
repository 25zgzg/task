from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI
import base64

TG_TOKEN = "8618116997:AAErOggEykQxDX8-ThTHJPh6LuUMm-oLKOA"
lm = OpenAI(base_url="http://localhost:1234/v1", api_key="sk-lm-cSJpWV7U:aB21v7kfsKkqRbU76RhM")

# Обробник тексту (той самий що був)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    sent = await update.message.reply_text("⏳")

    stream = lm.chat.completions.create(
        model="local-model",
        messages=[{"role": "user", "content": user_text}],
        stream=True
    )

    full_text = ""
    chunk_count = 0
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_text += delta
            chunk_count += 1
            if chunk_count % 10 == 0:
                await sent.edit_text(full_text)
    await sent.edit_text(full_text)


# Новий обробник фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent = await update.message.reply_text("⏳ Дивлюсь на фото...")

    # Беремо фото найкращої якості (останнє в списку = найбільше)
    photo = update.message.photo[-1]

    # Завантажуємо фото як байти
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()

    # Конвертуємо в base64 — це формат який розуміє API
    photo_b64 = base64.b64encode(photo_bytes).decode("utf-8")

    # Текст від юзера якщо є (підпис до фото)
    caption = update.message.caption or "Що на цьому фото?"

    stream = lm.chat.completions.create(
        model="local-model",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{photo_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": caption
                    }
                ]
            }
        ],
        stream=True
    )

    full_text = ""
    chunk_count = 0
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            full_text += delta
            chunk_count += 1
            if chunk_count % 10 == 0:
                await sent.edit_text(full_text)
    await sent.edit_text(full_text)


app = ApplicationBuilder().token(TG_TOKEN).build()

# Реєструємо обидва обробники
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()