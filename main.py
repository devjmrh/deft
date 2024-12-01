import telebot
import os
from flask import Flask

# إعداد Flask لربط البوت مع الخادم
app = Flask(__name__)

# احصل على التوكن من متغيرات البيئة
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# قائمة لتخزين أسماء الملفات
uploaded_files = {}

# دالة لمعالجة بدء المحادثة
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحبًا! أرسل لي ملفات، وسأعرض لك أزرار التحكم لكل ملف.")

# دالة لاستقبال الملفات
@bot.message_handler(content_types=['document'])
def handle_file(message):
    file_info = bot.get_file(message.document.file_id)
    file_name = message.document.file_name

    # تنزيل الملف
    downloaded_file = bot.download_file(file_info.file_path)
    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)

    # إضافة الملف إلى القائمة
    uploaded_files[file_name] = False  # False يعني أن الملف غير مشغّل حاليًا

    # إرسال أزرار التحكم
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(f"تشغيل {file_name}", callback_data=f"run:{file_name}"),
        telebot.types.InlineKeyboardButton(f"إطفاء {file_name}", callback_data=f"stop:{file_name}"),
        telebot.types.InlineKeyboardButton(f"حذف {file_name}", callback_data=f"delete:{file_name}")
    )
    bot.reply_to(message, f"تم استقبال الملف: {file_name}", reply_markup=markup)

# دالة لمعالجة ضغط الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    command, file_name = call.data.split(":")
    if command == "run":
        if not uploaded_files.get(file_name):
            bot.send_message(call.message.chat.id, f"جاري تشغيل الملف: {file_name}...")
            os.system(f"python {file_name} &")  # تشغيل الملف في الخلفية
            uploaded_files[file_name] = True
        else:
            bot.send_message(call.message.chat.id, f"الملف {file_name} يعمل بالفعل.")
    elif command == "stop":
        bot.send_message(call.message.chat.id, f"لا يمكن إيقاف الملف مباشرة عبر البوت. استخدم مدير العمليات لإيقافه.")
    elif command == "delete":
        try:
            os.remove(file_name)
            uploaded_files.pop(file_name, None)
            bot.send_message(call.message.chat.id, f"تم حذف الملف: {file_name}.")
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, f"الملف {file_name} غير موجود أو تم حذفه مسبقًا.")

# إعداد تطبيق Flask
@app.route('/')
def home():
    return "البوت يعمل الآن!"

# تشغيل البوت باستخدام Flask
if __name__ == "__main__":
    # قراءة المنفذ من متغير البيئة PORT أو استخدام 5000 إذا لم يكن موجودًا
    port = int(os.environ.get("PORT", 5000))
    # تشغيل البوت مع Flask
    bot.polling(none_stop=True, interval=0)
    app.run(host="0.0.0.0", port=port)
