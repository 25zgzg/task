import sqlite3
import base64
import requests
import time
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

# --- НАЛАШТУВАННЯ ---
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")
LM_STUDIO_BASE = "http://localhost:1234"
LM_API_BASE = f"{LM_STUDIO_BASE}/v1"

client = OpenAI(base_url=LM_API_BASE, api_key="lm-studio")

MANUAL_SMALL  = "qwen2.5-0.5b-instruct"
MANUAL_BIG    = "qwen/qwen3.5-9b"
MANUAL_VISION = "google/gemma-4-e4b"

# Track which model is currently loaded on the LM server (best-effort)
CURRENT_MODEL_ID = None

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect("bot_history.db")
    cur = conn.cursor()
    # Create table if missing (full schema). If a previous version of the DB
    # exists with fewer columns, we will add missing columns below.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id          INTEGER,
            input_type       TEXT,      -- 'text' | 'photo' | 'document' | 'voice' | 'unknown'
            input_text       TEXT,      -- текст або підпис
            ocr_result       TEXT,      -- текст витягнутий з фото (якщо є)
            step1_prompt     TEXT,      -- що подали в малу модель
            step1_result     TEXT,      -- що мала модель відповіла
            step2_prompt     TEXT,      -- що подали у велику модель
            final_response   TEXT,      -- фінальна відповідь
            model_used       TEXT       -- яка модель відповіла фінально
        )
    """)
    conn.commit()

    # Migration: ensure all expected columns exist (safe for older DBs)
    cur.execute("PRAGMA table_info(tasks)")
    existing_cols = {row[1] for row in cur.fetchall()}  # row[1] is column name

    expected = [
        ("user_id", "INTEGER"),
        ("input_type", "TEXT"),
        ("input_text", "TEXT"),
        ("ocr_result", "TEXT"),
        ("step1_prompt", "TEXT"),
        ("step1_result", "TEXT"),
        ("step2_prompt", "TEXT"),
        ("final_response", "TEXT"),
        ("model_used", "TEXT"),
    ]

    for col_name, col_type in expected:
        if col_name not in existing_cols:
            try:
                cur.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"ℹ️ Додано колонку до tasks: {col_name} {col_type}")
            except Exception as e:
                print(f"⚠️ Не вдалося додати колонку {col_name}: {e}")

    conn.close()

def db_save(user_id, input_type, input_text, ocr_result,
            step1_prompt, step1_result, step2_prompt, final_response, model_used):
    conn = sqlite3.connect("bot_history.db")
    conn.execute("""
        INSERT INTO tasks 
        (user_id, input_type, input_text, ocr_result, step1_prompt, step1_result, step2_prompt, final_response, model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, input_type, input_text, ocr_result,
          step1_prompt, step1_result, step2_prompt, final_response, model_used))
    conn.commit()
    conn.close()

# --- МОДЕЛІ ---
def force_unload():
    try:
        resp = requests.get(f"{LM_API_BASE}/models")
        if resp.status_code == 200:
            for m in resp.json().get('data', []):
                requests.post(f"{LM_API_BASE}/models/unload", json={"model": m.get('id')})
        # small pause to allow server to process unloads (reduced)
        time.sleep(0.8)
    except Exception as e:
        print(f"⚠️ Помилка очищення: {e}")

def unload_model(model_id):
    """Вивантажує тільки конкретну модель"""
    try:
        requests.post(f"{LM_API_BASE}/models/unload", json={"model": model_id})
        # brief wait after unload (reduced)
        time.sleep(0.6)
        print(f"ℹ️ Unloaded model: {model_id}")
    except Exception as e:
        print(f"⚠️ Помилка вивантаження {model_id}: {e}")


def force_unload_heavy():
    """Вивантажує тільки важкі моделі, малу не чіпає"""
    unload_model(MANUAL_BIG)
    unload_model(MANUAL_VISION)
    # short pause before loading a big model (reduced)
    time.sleep(0.6)

def safe_load(model_id, heavy_only=False):
    """Load a model safely. If heavy_only=True, only unload heavy models first.

    This helps keep the small/model used for light tasks loaded while freeing
    memory used by big/vision models.
    """
    if heavy_only:
        force_unload_heavy()
    else:
        force_unload()
    try:
        print(f"ℹ️ Loading model: {model_id}")
        resp = requests.post(f"{LM_API_BASE}/models/load", json={"model": model_id}, timeout=120)
        if resp.status_code == 200:
            # brief stabilization pause (reduced)
            time.sleep(0.8)
            # update tracker
            global CURRENT_MODEL_ID
            CURRENT_MODEL_ID = model_id
            return True
        print(f"❌ Не вдалося завантажити {model_id}: {resp.text}")
        return False
    except Exception as e:
        print(f"⚠️ Помилка: {e}")
        return False


def ensure_model_loaded(model_id, heavy_only=False):
    """Ensure a given model is loaded. If it's already the current model, do nothing."""
    global CURRENT_MODEL_ID
    if CURRENT_MODEL_ID == model_id:
        return True
    return safe_load(model_id, heavy_only=heavy_only)

# --- ВИЗНАЧЕННЯ ТИПУ ---
def detect_input_type(message):
    if message.photo:
        return "photo"
    if message.document:
        # Treat image documents (sent as file to preserve quality) as photos
        mime = getattr(message.document, 'mime_type', '') or ''
        fname = getattr(message.document, 'file_name', '') or ''
        if mime.startswith("image/") or fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            return "photo"
        return "document"
    if message.voice or message.audio:
        return "voice"
    if message.text:
        return "text"
    return "unknown"


async def progressive_edit(chat_status_message, full_text: str, chunk_size: int = 120, delay: float = 0.12):
    """Gradually edit a Telegram message to reveal `full_text` in chunks.

    This is a client-side simulation of streaming: the model result is
    displayed progressively to the user. It is safe against Telegram rate
    limits when using moderate `chunk_size` and `delay`.
    """
    if not full_text:
        try:
            await chat_status_message.edit_text("")
        except Exception:
            pass
        return

    pos = 0
    length = len(full_text)
    try:
        while pos < length:
            pos = min(length, pos + chunk_size)
            snippet = full_text[:pos]
            try:
                await chat_status_message.edit_text(snippet)
            except Exception:
                # If editing fails for some reason, stop trying to reduce spam
                break
            await __import__('asyncio').sleep(delay)

        # Ensure final full text is present
        try:
            await chat_status_message.edit_text(full_text)
        except Exception:
            pass
    except Exception:
        # Never raise from UI helper
        return

# --- ОБРОБНИК ---
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    msg = update.message
    user_id = msg.from_user.id
    input_type = detect_input_type(msg)
    input_text = msg.text or msg.caption or "Запит без тексту"

    # Змінні для БД
    ocr_result    = None
    step1_prompt  = None
    step1_result  = None
    step2_prompt  = None
    final_response = None
    model_used    = None

    status = await msg.reply_text(f"📨 Отримано: {input_type}. Обробляю...")

    try:
        # ── ФОТО: OCR → велика модель ──────────────────────────────
        if input_type == "photo":
            # Support both regular photos and images sent as documents (to preserve quality)
            if msg.photo:
                file_obj = msg.photo[-1]
            else:
                file_obj = msg.document

            # Check file size (avoid extremely large files)
            file_size = getattr(file_obj, 'file_size', None) or (getattr(msg.document, 'file_size', None) if msg.document else None)
            MAX_BYTES = 50 * 1024 * 1024  # 50 MB
            if file_size and file_size > MAX_BYTES:
                await status.edit_text("⚠️ Файл занадто великий для обробки (підтримується до 50 MB).")
                final_response = "⚠️ Файл занадто великий."
                model_used = "none"
                await msg.reply_text("Файл занадто великий. Надішли, будь ласка, зменшену версію або як фото (не документ).")
            else:
                try:
                    f = await context.bot.get_file(file_obj.file_id)
                    b = await f.download_as_bytearray()
                except Exception as e:
                    await status.edit_text(f"⚠️ Помилка завантаження файлу: {e}")
                    final_response = f"⚠️ Помилка завантаження: {e}"
                    model_used = "none"
                    b = None

                if b:
                    b64 = base64.b64encode(b).decode("utf-8")

                    await status.edit_text("👁 Читаю текст з фото (MANUAL_VISION)...")
                    safe_load(MANUAL_VISION, heavy_only=True)

                    ocr_prompt = "Витягни весь текст з зображення. Виводь тільки текст, нічого більше."
                    ocr_response = client.chat.completions.create(
                        model=MANUAL_VISION,
                        messages=[{"role": "user", "content": [
                            {"type": "text", "text": ocr_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        ]}]
                    )
                    ocr_result = ocr_response.choices[0].message.content
                    print(f"📄 OCR: {ocr_result}")

                    await status.edit_text("🧠 Текст зчитано. Вирішую задачу (MANUAL_BIG)...")
                    safe_load(MANUAL_BIG, heavy_only=True)

                    user_instruction = input_text if input_text != "Запит без тексту" else "Якщо є задача — вирішуй. Якщо просто текст — поясни."
                    step2_prompt = f"{user_instruction}\n\nТекст з фото:\n{ocr_result}"

                    resp = client.chat.completions.create(
                        model=MANUAL_BIG,
                        messages=[{"role": "user", "content": step2_prompt}]
                    )
                    final_response = resp.choices[0].message.content
                    model_used = MANUAL_BIG

        # ── ТЕКСТ: надсилати одразу в велику модель ───────────────────────
        elif input_type == "text":
            await status.edit_text("🚀 Обробляю запит (MANUAL_BIG)...")
            ensure_model_loaded(MANUAL_BIG, heavy_only=True)

            step2_prompt = input_text
            resp = client.chat.completions.create(
                model=MANUAL_BIG,
                messages=[{"role": "user", "content": step2_prompt}]
            )
            final_response = resp.choices[0].message.content
            model_used = MANUAL_BIG

        # ── ІНШІ ТИПИ ──────────────────────────────────────────────
        else:
            final_response = f"⚠️ Тип '{input_type}' поки не підтримується."
            model_used = "none"

        # If the final response came from the big model, reveal it progressively
        status_shown = False
        if model_used == MANUAL_BIG and final_response:
            try:
                await progressive_edit(status, final_response)
                status_shown = True
            except Exception:
                status_shown = False

        if not status_shown:
            await status.edit_text(final_response)

    except Exception as e:
        final_response = f"⚠️ Помилка: {e}"
        await msg.reply_text(final_response)

    finally:
        # Зберігаємо ВСЕ в БД незалежно від результату
        db_save(user_id, input_type, input_text, ocr_result,
                step1_prompt, step1_result, step2_prompt, final_response, model_used)
        force_unload_heavy()

# --- ЗАПУСК ---
if __name__ == "__main__":
    init_db()
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_input))
    print("🤖 Бот запущений...")
    app.run_polling()