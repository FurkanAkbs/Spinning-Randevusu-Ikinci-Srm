from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import os
import re

app = Flask(__name__)

# Admin doğrulaması (basit kullanıcı adı ve şifre)
admin_username = 'admin'
admin_password = 'admin123'

# Veritabanını başlatma (UNIQUE kısıtlaması eklemek için)
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # reservations tablosunda user_contact sütununu UNIQUE yap
    c.execute('''
    CREATE TABLE IF NOT EXISTS bicycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bicycle_id INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        user_contact TEXT NOT NULL UNIQUE,
        FOREIGN KEY (bicycle_id) REFERENCES bicycles (id)
    )
    ''')
    conn.commit()
    conn.close()

# Uygulama başlarken veritabanını başlat
init_db()

# Ana sayfa
@app.route('/')
def home():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM bicycles')
    bicycles = c.fetchall()  # Veritabanından tüm bisikletleri al
    conn.close()
    # Her bisikleti bir sözlük haline dönüştürelim
    bicycles_list = [{"id": row[0], "name": row[1], "status": row[2]} for row in bicycles]
    return render_template('index.html', bicycles=bicycles_list)

# Rezervasyon işlemi
@app.route("/reserve", methods=["POST"])
def reserve():
    bicycle_id = request.form.get("bicycle_id")
    user_name = request.form.get("user_name")
    user_contact = request.form.get("user_contact")

    # E-posta formatını kontrol et
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    if not re.match(email_regex, user_contact):
        return "Geçersiz e-posta adresi. Lütfen doğru bir formatta e-posta girin.", 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # E-posta adresinin daha önce rezervasyon yapıp yapmadığını kontrol et
    c.execute('SELECT * FROM reservations WHERE user_contact = ?', (user_contact,))
    existing_reservation = c.fetchone()
    if existing_reservation:
        conn.close()
        return "Bu e-posta adresiyle daha önce bir rezervasyon yapılmış. Lütfen başka bir e-posta adresi kullanın.", 400

    # Bisikletin müsait olup olmadığını kontrol et
    c.execute('SELECT status FROM bicycles WHERE id = ?', (bicycle_id,))
    status = c.fetchone()[0]
    if status == 'available':
        # Rezervasyon yap
        c.execute('INSERT INTO reservations (bicycle_id, user_name, user_contact) VALUES (?, ?, ?)',
                  (bicycle_id, user_name, user_contact))
        c.execute('UPDATE bicycles SET status = "reserved" WHERE id = ?', (bicycle_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('success'))
    else:
        conn.close()
        return "Bu bisiklet zaten rezerve edilmiş.", 400

# Admin paneli
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        # Admin giriş bilgileri kontrol edilecek
        username = request.form['username']
        password = request.form['password']
        if username == admin_username and password == admin_password:
            # Giriş başarılı, rezervasyonları göster
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('SELECT r.id, r.bicycle_id, r.user_name, r.user_contact, b.name FROM reservations r JOIN bicycles b ON r.bicycle_id = b.id')
            reservations = c.fetchall()
            conn.close()
            return render_template('admin.html', reservations=reservations)
        else:
            return "Giriş bilgileri yanlış!", 403
    return render_template('admin_login.html')

# Rezervasyon iptali
@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Rezervasyonu bul ve bisikleti tekrar müsait yap
    c.execute('SELECT bicycle_id FROM reservations WHERE id = ?', (reservation_id,))
    bicycle = c.fetchone()
    if bicycle:
        bicycle_id = bicycle[0]
        c.execute('DELETE FROM reservations WHERE id = ?', (reservation_id,))
        c.execute('UPDATE bicycles SET status = "available" WHERE id = ?', (bicycle_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# Rezervasyonları Excel'e aktarma
@app.route('/export_reservations')
def export_reservations():
    # Excel dosyasının kaydedileceği dizin
    save_directory = os.path.join(os.getcwd(), 'uploads')
    
    # Eğer 'uploads' dizini yoksa oluştur
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Veritabanına bağlan
    conn = sqlite3.connect('database.db')
    query = 'SELECT * FROM reservations'
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Dosya yolu
    file_path = os.path.join(save_directory, 'reservations.xlsx')

    # Excel dosyasını kaydet
    df.to_excel(file_path, index=False)

    # Dosyayı kullanıcıya gönder
    return send_file(file_path, as_attachment=True)

# Başarılı rezervasyon
@app.route("/success")
def success():
    return render_template('success.html')

if __name__ == "__main__":
    app.run(debug=True)