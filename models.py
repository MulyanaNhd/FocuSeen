import sqlite3
from pathlib import Path
from datetime import date, datetime
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta

def get_db_connection():
    """Open the shared local SQLite database."""
    database_path = Path(__file__).resolve().parent / "instance" / "focuseen.db"
    database_path.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(
        database_path,
        detect_types=sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    return SQLiteConnection(connection)


class SQLiteCursor:
    def __init__(self, cursor, dictionary=False):
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, query, params=()):
        self._cursor.execute(query.replace("%s", "?"), params)
        return self

    def fetchone(self):
        row = self._cursor.fetchone()
        return self._as_dict(row) if row is not None and self._dictionary else row

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [self._as_dict(row) for row in rows] if self._dictionary else rows

    @staticmethod
    def _as_dict(row):
        result = dict(row)
        for key in ('created_at', 'last_login'):
            if isinstance(result.get(key), str):
                result[key] = datetime.fromisoformat(result[key])
        for key in ('deadline', 'date'):
            if isinstance(result.get(key), str):
                result[key] = date.fromisoformat(result[key])
        return result

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class SQLiteConnection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self, dictionary=False):
        return SQLiteCursor(self._connection.cursor(), dictionary)

    def executescript(self, script):
        return self._connection.executescript(script)

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()

# ========================================
# DATA MATA KULIAH (dari hardcoded)
# ========================================

MATA_KULIAH = [
    {"id": 1, "nama": "Numerical Method", "kode": "MSD124000", "color": "#6b302b", "icon": "🧮", "dosen": "Kiki Mustaqim, S.Si., M.Si.", "semester": 3, "link": "https://drive.google.com/drive/folders/1IotGcfDAb26D5zkXtURsAkqs0VGiI5p7?usp=sharing"},
    {"id": 2, "nama": "Programming I", "kode": "MSD124000", "color": "#7a3a36", "icon": "🖥️", "dosen": "Woro Isti Rahayu, S.T., M.T., SPFC", "semester": 3, "link": "https://drive.google.com/drive/folders/17lCvEKe5HUQmDhIwsXTB6GaMKuwXn0Ys?usp=sharing"},
    {"id": 3, "nama": "Database", "kode": "MSD124000", "color": "#8a4d47", "icon": "🗳️", "dosen": "Noviana Riza, S.Si., M.T.", "semester": 3, "link": "https://drive.google.com/drive/folders/1zq2NRGlKuUR6-eVC4Noa8TqX00X-_yoh?usp=sharing"},
    {"id": 4, "nama": "Strategy Algorithm", "kode": "MSD124000", "color": "#9c635a", "icon": "🧩", "dosen": "Fatia Amalia Maresti, S.Si., M.Si.", "semester": 3, "link": "https://drive.google.com/drive/folders/1v6DmZcAWd2cv9Bhzi0v_BVFw4kFzfkWO?usp=sharing"},
    {"id": 5, "nama": "SDGs", "kode": "MSD124000", "color": "#b07a71", "icon": "♻️", "dosen": "Rico Ricardo, S.E., M.Ec.", "semester": 3, "link": "https://drive.google.com/drive/folders/1CEhBUPoZ5Zesh9hG-KNN1v--qbNlFlSX?usp=sharing"},
    {"id": 6, "nama": "Probability Theory", "kode": "MSD124000", "color": "#c49088", "icon": "📈", "dosen": "Dr. Riharsono Prastyantoro, S.Si., M.T., CSCM", "semester": 3, "link": "https://drive.google.com/drive/folders/1PULmQYd76Abnmm3Kd6wJLl9Y-Oh0kfQv?usp=sharing"},
    {"id": 7, "nama": "Religious Education", "kode": "MSD124000", "color": "#d3a899", "icon": "🛐", "dosen": "Rizqi Akbar Maulana", "semester": 3, "link": "https://drive.google.com/drive/folders/1izDiCXLSDgkPjcilPnTKNf3YE4u_Fmvo?usp=sharing"},
    {"id": 8, "nama": "Research Methodology", "kode": "MSD124000", "color": "#e6cfc8", "icon": "🔍", "dosen": "Woro Isti Rahayu, S.T., M.T., SPFC", "semester": 3, "link": "https://drive.google.com/drive/folders/18FQ2yD17Tv4kKy1KycYFmAJpa1NDrx8M?usp=sharing"}
]

# ========================================
# DATA ANGGOTA TIM (dari hardcoded)
# ========================================

TIM_MEMBERS = [
    { 
        "id": 1,
        "nama": "Mulyana Nurhamida",
        "nim": "184240027",
        "foto": "mulya.jpg",
        "email": "184240027@std.ulbi.ac.id",
        "peran": "Frontend Developer",
        "emoji": "😍"
    },
    {
        "id": 2,
        "nama": "M Syakira Hamidan", 
        "nim": "184240025",
        "foto": "sem.jpeg",
        "email": "184240025@std.ulbi.ac.id",
        "peran": "Backend Developer",
        "emoji": "💀"
    }
]

# ========================================
# FUNGSI TUGAS (CRUD dengan MySQL)
# ========================================

def load_tugas():
    """Load semua tugas dari database"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT t.*, mk.nama as nama_matkul, mk.color as matkul_color
        FROM tugas t
        JOIN mata_kuliah mk ON t.matkul_id = mk.id
        ORDER BY t.deadline ASC, t.status ASC
    """)
    
    tugas_list = cursor.fetchall()
    conn.close()
    
    # Tambahkan days_left untuk setiap tugas
    for tugas in tugas_list:
        deadline = tugas['deadline']
        if isinstance(deadline, str):
            deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
        today = datetime.now().date()
        tugas['days_left'] = (deadline - today).days
    
    return tugas_list

def add_tugas(matkul_id, judul, deadline):
    """Tambah tugas baru"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO tugas (matkul_id, judul, deadline, status)
        VALUES (%s, %s, %s, %s)
    """, (matkul_id, judul, deadline, 0))
    
    conn.commit()
    conn.close()

def delete_tugas(tugas_id):
    """Hapus tugas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tugas WHERE id = %s", (tugas_id,))
    conn.commit()
    conn.close()

def toggle_tugas_status(tugas_id):
    """Toggle status tugas (selesai/belum)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Ambil status current
    cursor.execute("SELECT status FROM tugas WHERE id = %s", (tugas_id,))
    tugas = cursor.fetchone()
    
    # Toggle status
    new_status = not tugas['status']
    cursor.execute("UPDATE tugas SET status = %s WHERE id = %s", (new_status, tugas_id))
    
    conn.commit()
    conn.close()
    return new_status

def update_tugas(tugas_id, matkul_id, judul, deadline, status):
    """Update tugas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE tugas 
        SET matkul_id = %s, judul = %s, deadline = %s, status = %s
        WHERE id = %s
    """, (matkul_id, judul, deadline, status, tugas_id))
    
    conn.commit()
    conn.close()

# ========================================
# FUNGSI STATISTIK
# ========================================

def get_statistics():
    """Ambil statistik untuk dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    stats = {}
    
    # Total tugas
    cursor.execute("SELECT COUNT(*) as count FROM tugas")
    stats['total_tugas'] = cursor.fetchone()['count']
    
    # Tugas selesai
    cursor.execute("SELECT COUNT(*) as count FROM tugas WHERE status = 1")
    stats['tugas_selesai'] = cursor.fetchone()['count']
    
    # Tugas belum selesai
    cursor.execute("SELECT COUNT(*) as count FROM tugas WHERE status = 0")
    stats['tugas_belum'] = cursor.fetchone()['count']
    
    # Tugas mendekati deadline (3 hari ke depan)
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM tugas 
        WHERE status = 0 
        AND deadline BETWEEN date('now') AND date('now', '+3 days')
    """)
    stats['tugas_mendekati'] = cursor.fetchone()['count']
    
    conn.close()
    
    return stats

# ========================================
# FUNGSI ADMIN (CRUD Mata Kuliah & Tim)
# ========================================

def get_all_matkul():
    """Ambil semua mata kuliah"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM mata_kuliah ORDER BY semester, nama")
    matkul_list = cursor.fetchall()
    
    conn.close()
    return matkul_list

def add_matkul(nama, kode, color, icon, dosen, semester):
    """Tambah mata kuliah"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO mata_kuliah (nama, kode, color, icon, dosen, semester)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (nama, kode, color, icon, dosen, semester))
    
    conn.commit()
    conn.close()

def update_matkul(matkul_id, nama, kode, color, icon, dosen, semester):
    """Update mata kuliah"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE mata_kuliah 
        SET nama = %s, kode = %s, color = %s, icon = %s, dosen = %s, semester = %s
        WHERE id = %s
    """, (nama, kode, color, icon, dosen, semester, matkul_id))
    
    conn.commit()
    conn.close()

def delete_matkul(matkul_id):
    """Hapus mata kuliah"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cek apakah ada tugas yang menggunakan mata kuliah ini
    cursor.execute("SELECT COUNT(*) as count FROM tugas WHERE matkul_id = %s", (matkul_id,))
    result = cursor.fetchone()
    
    if result['count'] > 0:
        conn.close()
        return False  # Tidak bisa hapus karena masih ada tugas
    
    cursor.execute("DELETE FROM mata_kuliah WHERE id = %s", (matkul_id,))
    conn.commit()
    conn.close()
    return True

def get_all_anggota_tim():
    """Ambil semua anggota tim"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM anggota_tim ORDER BY nama")
    tim_list = cursor.fetchall()
    
    conn.close()
    return tim_list

def add_anggota_tim(nama, nim, email, peran, foto='photo.jpg'):
    """Tambah anggota tim"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO anggota_tim (nama, nim, foto, email, peran)
            VALUES (%s, %s, %s, %s, %s)
        """, (nama, nim, foto, email, peran))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # NIM sudah ada
    finally:
        conn.close()

def update_anggota_tim(anggota_id, nama, nim, email, peran, foto='photo.jpg'):
    """Update anggota tim"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE anggota_tim 
        SET nama = %s, nim = %s, foto = %s, email = %s, peran = %s
        WHERE id = %s
    """, (nama, nim, foto, email, peran, anggota_id))
    
    conn.commit()
    conn.close()

def delete_anggota_tim(anggota_id):
    """Hapus anggota tim"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM anggota_tim WHERE id = %s", (anggota_id,))
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password menggunakan SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password):
    """Register user baru"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        hashed_pw = hash_password(password)
        cursor.execute("""
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username/email sudah ada
    finally:
        conn.close()

def authenticate_user(username, password):
    """Login user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    hashed_pw = hash_password(password)
    cursor.execute("""
        SELECT id, username, email 
        FROM users 
        WHERE (username = %s OR email = %s) AND password = %s
    """, (username, username, hashed_pw))
    
    user = cursor.fetchone()
    
    if user:
        # Update last_login
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s", (user['id'],))
        conn.commit()
    
    conn.close()
    return user

# ========================================
# FUNGSI USER TASK TRACKING
# ========================================

def get_user_tugas(user_id):
    """Ambil semua tugas user dengan progress"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ut.*, t.judul, t.deadline, mk.nama as matkul_nama, mk.color as matkul_color
        FROM user_tugas ut
        JOIN tugas t ON ut.tugas_id = t.id
        JOIN mata_kuliah mk ON t.matkul_id = mk.id
        WHERE ut.user_id = %s
        ORDER BY t.deadline ASC
    """, (user_id,))
    
    user_tugas = cursor.fetchall()
    conn.close()
    return user_tugas

def update_user_tugas(user_id, tugas_id, status=None, bookmarked=None, notes=None, progress=None):
    """Update progress tugas user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cek apakah sudah ada
    cursor.execute("SELECT id FROM user_tugas WHERE user_id = %s AND tugas_id = %s", (user_id, tugas_id))
    existing = cursor.fetchone()
    
    if existing:
        # Update
        updates = []
        params = []
        
        if status:
            updates.append("status = %s")
            params.append(status)
        if bookmarked is not None:
            updates.append("bookmarked = %s")
            params.append(bookmarked)
        if notes is not None:
            updates.append("notes = %s")
            params.append(notes)
        if progress is not None:
            updates.append("progress_percentage = %s")
            params.append(progress)
        
        params.extend([user_id, tugas_id])
        
        query = f"UPDATE user_tugas SET {', '.join(updates)} WHERE user_id = %s AND tugas_id = %s"
        cursor.execute(query, params)
    else:
        # Insert baru
        cursor.execute("""
            INSERT INTO user_tugas (user_id, tugas_id, status, bookmarked, notes, progress_percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, tugas_id, status or 'pending', bookmarked or False, notes or None, progress or 0))
    
    conn.commit()
    conn.close()

def toggle_bookmark(user_id, tugas_id):
    """Toggle bookmark tugas"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cek status bookmark saat ini
    cursor.execute("SELECT bookmarked FROM user_tugas WHERE user_id = %s AND tugas_id = %s", (user_id, tugas_id))
    result = cursor.fetchone()
    
    if result:
        new_bookmark = not result['bookmarked']
        cursor.execute("UPDATE user_tugas SET bookmarked = %s WHERE user_id = %s AND tugas_id = %s", 
                      (new_bookmark, user_id, tugas_id))
    else:
        cursor.execute("INSERT INTO user_tugas (user_id, tugas_id, bookmarked) VALUES (%s, %s, %s)",
                      (user_id, tugas_id, True))
    
    conn.commit()
    conn.close()
    return new_bookmark if result else True

# ========================================
# FUNGSI NOTIFIKASI
# ========================================

def add_notification(user_id, message, notif_type='system'):
    """Tambah notifikasi untuk user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO notifications (user_id, message, type, is_read)
        VALUES (%s, %s, %s, %s)
    """, (user_id, message, notif_type, False))
    
    conn.commit()
    conn.close()

def get_notifications(user_id, limit=10):
    """Ambil notifikasi user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (user_id, limit))
    
    notifications = cursor.fetchall()
    conn.close()
    return notifications

def mark_notification_read(notification_id):
    """Tandai notifikasi sudah dibaca"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
    conn.commit()
    conn.close()

def get_unread_count(user_id):
    """Hitung notifikasi belum dibaca"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = FALSE", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ========================================
# FUNGSI REMINDER EMAIL
# ========================================

def send_email_reminder(user_email, tugas_list):
    """Kirim email reminder deadline"""
    from config import EMAIL_CONFIG
    
    if not EMAIL_CONFIG['enabled']:
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = user_email
        msg['Subject'] = '🔔 Reminder: Tugas Mendekati Deadline'
        
        # Buat isi email
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #5C4033;">Reminder Tugas</h2>
            <p>Hi!</p>
            <p>Berikut tugas-tugas yang akan mendekati deadline:</p>
            <ul>
        """
        
        for tugas in tugas_list:
            body += f"""
                <li>
                    <strong>{tugas['judul']}</strong><br>
                    Mata Kuliah: {tugas['matkul_nama']}<br>
                    Deadline: {tugas['deadline'].strftime('%d %B %Y')}<br>
                    Status: {tugas['status']}
                </li>
            """
        
        body += """
            </ul>
            <p>Segera selesaikan tugas-tugas tersebut ya!</p>
            <p style="color: #8B7355; font-size: 12px;">Email otomatis dari LYA & SAM Dashboard</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Kirim email
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error kirim email: {e}")
        return False

def check_deadline_reminders():
    """Cek tugas yang deadline 3 hari lagi dan kirim reminder"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Cari tugas yang deadline 3 hari lagi
    cursor.execute("""
        SELECT t.*, mk.nama as matkul_nama, u.email, u.id as user_id
        FROM tugas t
        JOIN mata_kuliah mk ON t.matkul_id = mk.id
        JOIN user_tugas ut ON t.id = ut.tugas_id
        JOIN users u ON ut.user_id = u.id
        WHERE t.deadline = date('now', '+3 days')
        AND ut.status != 'completed'
    """)
    
    reminders = cursor.fetchall()
    conn.close()
    
    # Kelompokkan per user
    user_reminders = {}
    for reminder in reminders:
        user_id = reminder['user_id']
        if user_id not in user_reminders:
            user_reminders[user_id] = {
                'email': reminder['email'],
                'tugas': []
            }
        user_reminders[user_id]['tugas'].append(reminder)
    
    # Kirim email ke setiap user
    for user_id, data in user_reminders.items():
        if send_email_reminder(data['email'], data['tugas']):
            # Tambah notifikasi juga
            for tugas in data['tugas']:
                add_notification(
                    user_id, 
                    f"Reminder: Tugas '{tugas['judul']}' deadline dalam 3 hari!",
                    'reminder'
                )
    
    return len(user_reminders)


def init_db():
    """Create the app tables and seed the static dashboard data once."""
    conn = get_db_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mata_kuliah (
            id INTEGER PRIMARY KEY,
            nama TEXT NOT NULL,
            kode TEXT NOT NULL,
            color TEXT NOT NULL,
            icon TEXT NOT NULL,
            dosen TEXT NOT NULL,
            semester INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS anggota_tim (
            id INTEGER PRIMARY KEY,
            nama TEXT NOT NULL,
            nim TEXT NOT NULL UNIQUE,
            foto TEXT NOT NULL,
            email TEXT NOT NULL,
            peran TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matkul_id INTEGER NOT NULL REFERENCES mata_kuliah(id),
            judul TEXT NOT NULL,
            deadline DATE NOT NULL,
            status INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            last_login DATETIME
        );
        CREATE TABLE IF NOT EXISTS user_tugas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            tugas_id INTEGER NOT NULL REFERENCES tugas(id),
            status TEXT NOT NULL DEFAULT 'pending',
            bookmarked INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            progress_percentage INTEGER NOT NULL DEFAULT 0,
            UNIQUE(user_id, tugas_id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'system',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM mata_kuliah")
    if cursor.fetchone()[0] == 0:
        for matkul in MATA_KULIAH:
            cursor.execute("""
                INSERT INTO mata_kuliah (id, nama, kode, color, icon, dosen, semester)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                matkul['id'], matkul['nama'], matkul['kode'], matkul['color'],
                matkul['icon'], matkul['dosen'], matkul['semester'],
            ))

    cursor.execute("SELECT COUNT(*) FROM anggota_tim")
    if cursor.fetchone()[0] == 0:
        for member in TIM_MEMBERS:
            cursor.execute("""
                INSERT INTO anggota_tim (id, nama, nim, foto, email, peran)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                member['id'], member['nama'], member['nim'], member['foto'],
                member['email'], member['peran'],
            ))

    conn.commit()
    conn.close()