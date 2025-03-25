from flask import Flask, request, jsonify
import os
from io import BytesIO
from flask import send_file
from googletrans import Translator
import sqlite3
import requests

app = Flask(__name__)

# تهيئة المترجم
translator = Translator()

# --- تهيئة قاعدة البيانات ---
DATABASE = 'responses.db'

def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            reply TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# دالة لحفظ السؤال والجواب في قاعدة البيانات
def save_response(question, reply):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO responses (question, reply) VALUES (?, ?)', (question, reply))
    conn.commit()
    conn.close()

# --- وظائف Gemini API ---
GEMINI_API_KEY = "AIzaSyBv9u4u5bdDfTVxFDbTZbstw7G0cl9YSsU"  # استبدل هذا بالمفتاح الخاص بك إذا كان لديك مفتاح آخر

def ask_gemini(question):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GEMINI_API_KEY}'
    }
    data = {
        "contents": [{
            "parts": [{"text": question}]
        }]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"خطأ في الاتصال بـ Gemini: {response.text}"

# --- نقاط نهاية API ---
@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    user_question = data['question']
    user_language = data.get('language', 'ar')

    try:
        # ترجمة السؤال إلى الإنجليزية إذا لزم الأمر
        if user_language != 'en':
            translated_question = translator.translate(user_question, dest='en').text
        else:
            translated_question = user_question

        # الحصول على الرد من Gemini
        bot_reply_en = ask_gemini(translated_question)

        # ترجمة الرد إلى اللغة المطلوبة
        if user_language != 'en':
            translated_reply = translator.translate(bot_reply_en, dest=user_language).text
        else:
            translated_reply = bot_reply_en

        # حفظ السؤال والجواب
        save_response(user_question, translated_reply)

    except Exception as e:
        translated_reply = f"حدث خطأ: {str(e)}"

    return jsonify({'reply': translated_reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)