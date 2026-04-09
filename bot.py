import os
from gtts import gTTS
from deep_translator import GoogleTranslator
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

BOT_TOKEN = "YOUR_BOT_TOKEN"

os.makedirs("downloads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Video Bot Ready!\n\n"
        "Send a video 🎥\n\n"
        "Commands:\n"
        "/480p /720p /1080p /2160p\n"
        "/translate"
    )

# SAVE VIDEO
async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.video.get_file()
    file_path = f"downloads/{update.message.video.file_id}.mp4"
    await file.download_to_drive(file_path)

    context.user_data["video"] = file_path
    await update.message.reply_text("✅ Video saved! Now choose option.")

# RESOLUTION CHANGE
def change_resolution(input_file, output_file, resolution):
    os.system(f"ffmpeg -i {input_file} -vf scale=-2:{resolution} {output_file}")

async def process_resolution(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "video" not in context.user_data:
        await update.message.reply_text("❌ Send video first")
        return

    res = update.message.text.replace("/", "")
    input_file = context.user_data["video"]
    output_file = f"outputs/output_{res}.mp4"

    await update.message.reply_text("⏳ Processing...")

    change_resolution(input_file, output_file, res)

    await update.message.reply_video(video=open(output_file, "rb"))

# TRANSLATION FUNCTION
def translate_video(input_video):
    audio_file = "outputs/audio.wav"

    # extract audio
    os.system(f"ffmpeg -i {input_video} {audio_file}")

    # translate
    tamil_text = GoogleTranslator(source='auto', target='ta').translate("This is a test video")

    # text to speech
    tts = gTTS(tamil_text, lang='ta')
    tamil_audio = "outputs/tamil.mp3"
    tts.save(tamil_audio)

    # merge audio
    output_video = "outputs/translated.mp4"
    os.system(f"ffmpeg -i {input_video} -i {tamil_audio} -map 0:v -map 1:a -c:v copy {output_video}")

    return output_video

# TRANSLATE COMMAND
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "video" not in context.user_data:
        await update.message.reply_text("❌ Send video first")
        return

    await update.message.reply_text("⏳ Translating... (may take time)")

    output = translate_video(context.user_data["video"])

    try:
    await update.message.reply_video(video=open(output, "rb"))
except Exception as e:
    await update.message.reply_text(f"Error: {e}")

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/(480p|720p|1080p|2160p)$"), process_resolution))
app.add_handler(CommandHandler("translate", translate))
app.add_handler(MessageHandler(filters.VIDEO, save_video))

app.run_polling()
