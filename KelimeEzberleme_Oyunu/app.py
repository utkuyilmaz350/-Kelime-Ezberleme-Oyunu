import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import random
import requests
import base64

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Veritabanı bağlantısı
DATABASE = 'kelime.db'

# 6 sefer ve zaman aralıklı quiz algoritması
REVIEW_INTERVALS = [1, 7, 30, 90, 180, 365]  # gün cinsinden: 1g, 1h, 1a, 3a, 6a, 1y

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserName TEXT NOT NULL,
            Password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Words (
            WordID INTEGER PRIMARY KEY AUTOINCREMENT,
            EngWordName TEXT,
            TurWordName TEXT,
            Picture TEXT,
            Pronunciation TEXT
        );
        CREATE TABLE IF NOT EXISTS WordSamples (
            WordSamplesID INTEGER PRIMARY KEY AUTOINCREMENT,
            WordID INTEGER,
            Samples TEXT
        );
        CREATE TABLE IF NOT EXISTS UserWordProgress (
            UserID INTEGER,
            WordID INTEGER,
            CorrectCount INTEGER DEFAULT 0,
            LastTested DATE
        );
        CREATE TABLE IF NOT EXISTS UserSettings (
            UserID INTEGER PRIMARY KEY,
            QuizCount INTEGER DEFAULT 10
        );
        ''')
        # Eski Words tablosunda Pronunciation yoksa ekle
        try:
            db.execute('ALTER TABLE Words ADD COLUMN Pronunciation TEXT')
        except Exception:
            pass
        db.commit()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM Users WHERE UserName=?', (username,)).fetchone()
        if user:
            flash('Bu kullanıcı adı zaten alınmış.')
            return redirect(url_for('register'))
        db.execute('INSERT INTO Users (UserName, Password) VALUES (?, ?)', (username, password))
        db.commit()
        user_id = db.execute('SELECT UserID FROM Users WHERE UserName=?', (username,)).fetchone()['UserID']
        db.execute('INSERT OR IGNORE INTO UserSettings (UserID, QuizCount) VALUES (?, ?)', (user_id, 10))
        db.commit()
        flash('Kayıt başarılı, giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM Users WHERE UserName=? AND Password=?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['UserID']
            session['username'] = user['UserName']
            return redirect(url_for('dashboard'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/add_word', methods=['GET', 'POST'])
def add_word():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        eng = request.form['eng']
        tur = request.form['tur']
        samples = request.form.getlist('samples')
        picture = request.files['picture']
        pronunciation = request.form.get('pronunciation', '')
        pronunciation_file = request.files.get('pronunciation_file')
        picture_path = ''
        pronunciation_file_path = ''
        if picture and picture.filename:
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)
        if pronunciation_file and pronunciation_file.filename:
            filename = secure_filename(pronunciation_file.filename)
            pronunciation_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pronunciation_file.save(pronunciation_file_path)
        db.execute('INSERT INTO Words (EngWordName, TurWordName, Picture, Pronunciation) VALUES (?, ?, ?, ?)', (eng, tur, picture_path, pronunciation))
        db.commit()
        word_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        for sample in samples:
            if sample.strip():
                db.execute('INSERT INTO WordSamples (WordID, Samples) VALUES (?, ?)', (word_id, sample.strip()))
        db.commit()
        flash('Kelime başarıyla eklendi.')
        return redirect(url_for('add_word'))
    words = db.execute('SELECT * FROM Words ORDER BY WordID DESC LIMIT 10').fetchall()
    word_list = []
    for w in words:
        samples = db.execute('SELECT Samples FROM WordSamples WHERE WordID=?', (w['WordID'],)).fetchall()
        pronunciation_file = ''
        for ext in ['mp3', 'wav', 'ogg']:
            possible = os.path.join(app.config['UPLOAD_FOLDER'], f"{w['WordID']}.{ext}")
            if os.path.exists(possible):
                pronunciation_file = possible.replace('\\', '/')
        word_list.append({
            'EngWordName': w['EngWordName'],
            'TurWordName': w['TurWordName'],
            'Picture': w['Picture'],
            'Pronunciation': w['Pronunciation'],
            'PronunciationFile': pronunciation_file,
            'samples': [s['Samples'] for s in samples]
        })
    return render_template('add_word.html', words=word_list)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    quiz_count = session.get('quiz_count', 10)
    today = datetime.now().date()

    if 'quiz_progress' not in session or session.get('quiz_progress_date') != str(today):
        session['quiz_progress'] = []
        session['quiz_progress_date'] = str(today)
    quiz_progress = session['quiz_progress']

    # Kullanıcının kelime ilerlemelerini çek
    progresses = db.execute('SELECT * FROM UserWordProgress WHERE UserID=?', (user_id,)).fetchall()
    progresses_dict = {p['WordID']: p for p in progresses}

    # Tüm kelimeleri çek
    words = db.execute('SELECT * FROM Words').fetchall()
    available_words = []
    today = datetime.now().date()
    for w in words:
        wid = w['WordID']
        if wid in quiz_progress:
            continue
        p = progresses_dict.get(wid)
        if not p:
            # Hiç sorulmamış kelimeler öncelikli
            available_words.append((0, w))
        elif p['CorrectCount'] < 6:
            interval = REVIEW_INTERVALS[p['CorrectCount']]
            last = p['LastTested']
            if last:
                last_date = datetime.strptime(last, '%Y-%m-%d').date()
                if (today - last_date).days >= interval:
                    available_words.append((1, w))
    # Öncelik: önce aralığı gelenler, sonra yeni kelimeler
    available_words.sort(key=lambda x: x[0])
    available_words = [w for _, w in available_words]
    # Eğer yeterli kelime yoksa, kalanları hiç sorulmamışlardan tamamla
    if len(available_words) < quiz_count - len(quiz_progress):
        used_ids = set([w['WordID'] for w in available_words] + quiz_progress)
        for w in words:
            if w['WordID'] not in used_ids:
                available_words.append(w)
            if len(available_words) >= quiz_count - len(quiz_progress):
                break
    if len(quiz_progress) >= quiz_count or not available_words:
        session.pop('quiz_progress', None)
        session.pop('quiz_progress_date', None)
        return render_template('quiz.html', word=None, options=None, question_no=quiz_count, total=quiz_count)

    word = available_words[0]
    correct = word['TurWordName']
    wrongs = db.execute('SELECT TurWordName FROM Words WHERE WordID != ? ORDER BY RANDOM() LIMIT 3', (word['WordID'],)).fetchall()
    options = [correct] + [w['TurWordName'] for w in wrongs]
    random.shuffle(options)

    if request.method == 'POST':
        answer = request.form['answer']
        quiz_progress.append(word['WordID'])
        session['quiz_progress'] = quiz_progress
        p = db.execute('SELECT * FROM UserWordProgress WHERE UserID=? AND WordID=?', (user_id, word['WordID'])).fetchone()
        if answer == correct:
            if p:
                new_count = min(p['CorrectCount'] + 1, 6)
                db.execute('UPDATE UserWordProgress SET CorrectCount=?, LastTested=? WHERE UserID=? AND WordID=?', (new_count, today, user_id, word['WordID']))
            else:
                db.execute('INSERT INTO UserWordProgress (UserID, WordID, CorrectCount, LastTested) VALUES (?, ?, 1, ?)', (user_id, word['WordID'], today))
            db.commit()
            flash('Doğru cevap!')
        else:
            if p:
                db.execute('UPDATE UserWordProgress SET CorrectCount=0, LastTested=? WHERE UserID=? AND WordID=?', (today, user_id, word['WordID']))
            else:
                db.execute('INSERT INTO UserWordProgress (UserID, WordID, CorrectCount, LastTested) VALUES (?, ?, 0, ?)', (user_id, word['WordID'], today))
            db.commit()
            flash('Yanlış cevap!')
        return redirect(url_for('quiz'))

    question_no = len(quiz_progress) + 1
    return render_template('quiz.html', word=word, options=options, question_no=question_no, total=quiz_count)

@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM Words').fetchone()[0] or 0
    known = db.execute('SELECT COUNT(*) FROM UserWordProgress WHERE UserID=? AND CorrectCount>=6', (user_id,)).fetchone()[0] or 0
    percent = round((known / total) * 100, 2) if total > 0 else 0
    known_words = db.execute('''
        SELECT DISTINCT w.EngWordName, w.TurWordName FROM Words w
        JOIN UserWordProgress uwp ON w.WordID = uwp.WordID
        WHERE uwp.UserID=? AND uwp.CorrectCount>=6
    ''', (user_id,)).fetchall()
    return render_template('report.html', total=total, known=known, percent=percent, known_words=known_words)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    db = get_db()
    row = db.execute('SELECT QuizCount FROM UserSettings WHERE UserID=?', (user_id,)).fetchone()
    if row:
        quiz_count = row['QuizCount']
    else:
        quiz_count = 10
        db.execute('INSERT OR IGNORE INTO UserSettings (UserID, QuizCount) VALUES (?, ?)', (user_id, quiz_count))
        db.commit()
    if request.method == 'POST':
        quiz_count = int(request.form['quiz_count'])
        db.execute('UPDATE UserSettings SET QuizCount=? WHERE UserID=?', (quiz_count, user_id))
        db.commit()
        session['quiz_count'] = quiz_count
        flash('Ayarlar kaydedildi.')
        return redirect(url_for('settings'))
    return render_template('settings.html', quiz_count=quiz_count)

@app.route('/wordle', methods=['GET', 'POST'])
def wordle():
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()
        words = db.execute('SELECT EngWordName FROM Words').fetchall()
        if not words:
            # Wordle için hiç kelime yoksa, wordle.html'de uyarı göster
            return render_template('wordle.html', word=None, word_length=0, guesses=[], feedback=[], result=None)
        if 'wordle_word' not in session:
            session['wordle_word'] = random.choice(words)['EngWordName'].lower()
            session['wordle_guesses'] = []
            session['wordle_feedback'] = []
        word = session['wordle_word']
        guesses = session.get('wordle_guesses', [])
        feedback = session.get('wordle_feedback', [])
        result = None
        word_length = len(word)
        if request.method == 'POST':
            guess = request.form['guess'].lower()
            if len(guess) != word_length:
                flash(f'Lütfen {word_length} harfli bir kelime girin.')
            else:
                guesses.append(guess)
                session['wordle_guesses'] = guesses
                current_feedback = []
                for i in range(word_length):
                    if guess[i] == word[i]:
                        current_feedback.append('correct')
                    elif guess[i] in word:
                        current_feedback.append('present')
                    else:
                        current_feedback.append('absent')
                feedback.append({
                    'guess': guess,
                    'colors': current_feedback
                })
                session['wordle_feedback'] = feedback
                if guess == word:
                    result = 'Tebrikler! Kelimeyi buldunuz!'
                    session.pop('wordle_word', None)
                    session.pop('wordle_guesses', None)
                    session.pop('wordle_feedback', None)
                elif len(guesses) >= 6:
                    result = f'Kaybettiniz! Doğru kelime: {word.upper()}'
                    session.pop('wordle_word', None)
                    session.pop('wordle_guesses', None)
                    session.pop('wordle_feedback', None)
        return render_template('wordle.html', word=word, word_length=word_length, guesses=guesses, feedback=feedback, result=result)
    except Exception as e:
        app.logger.error(f"Wordle hatası: {str(e)}")
        flash('Bir hata oluştu. Lütfen tekrar deneyin.')
        return redirect(url_for('dashboard'))

with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True) 