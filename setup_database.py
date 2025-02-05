import sqlite3

# Veritabanı oluştur
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Bisikletler tablosu
c.execute('''
    CREATE TABLE IF NOT EXISTS bicycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT DEFAULT 'available'
    )
''')

# Rezervasyonlar tablosu
c.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bicycle_id INTEGER,
        user_name TEXT,
        user_contact TEXT,
        FOREIGN KEY (bicycle_id) REFERENCES bicycles(id)
    )
''')

# Örnek bisikletler ekle (Eğer bisikletler zaten eklenmişse tekrar ekleme)
c.execute('SELECT COUNT(*) FROM bicycles')
bicycle_count = c.fetchone()[0]

if bicycle_count == 0:
    for i in range(1, 21):
        c.execute('INSERT INTO bicycles (name) VALUES (?)', (f'Bisiklet {i}',))

conn.commit()
conn.close()

print("Veritabani hazir!")