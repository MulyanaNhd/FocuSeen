import os
import certifi
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from models import * # Mengambil model lama (User, Tugas Dashboard Utama, dll)
from config import SECRET_KEY, DEBUG
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ========================================
# KONFIGURASI DATABASE FOCUSEEN
# ========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///focuseen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#init_db()

# --- MODEL UNTUK FITUR FOCUSEEN ---
class FocusTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    deadline_days = db.Column(db.Integer, nullable=False)
    progress = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class FocusSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duration_minutes = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now().date())
    created_at = db.Column(db.DateTime, default=datetime.now)

class FocusSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    date = db.Column(db.Date, default=lambda: datetime.now().date())

# ========================================
# LOGIKA FITUR FOCUSEEN (REVISI FINAL)
# ========================================

def get_focus_stats():
    """Menghitung statistik harian secara real-time"""
    today = datetime.now().date()
    
    # 1. Hitung Durasi & Sesi Fokus (HANYA HARI INI)
    sessions_today = FocusSession.query.filter_by(date=today).all()
    total_minutes = sum(s.duration_minutes for s in sessions_today)
    
    # Logika Sesi: 25 menit = 1 sesi
    session_count = 0
    for s in sessions_today:
        if s.duration_minutes >= 25:
            session_count += (s.duration_minutes // 25)
            
    hours = total_minutes // 60
    minutes = total_minutes % 60
    
    # 2. Hitung Tugas (SEMUA TASK AKTIF)
    # Hitung semua task (tidak dibedakan berdasarkan tanggal dibuat, karena bisa memiliki deadline di masa depan)
    all_tasks = FocusTask.query.all()
    
    total_tasks = len(all_tasks)
    completed_tasks = sum(1 for t in all_tasks if t.is_completed)
    
    # 3. Hitung Streak
    streak = 0
    check_date = today
    while True:
        sessions = FocusSession.query.filter(
            FocusSession.date == check_date, 
            FocusSession.duration_minutes >= 25
        ).count()
        
        if sessions > 0:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            if check_date == today and sessions == 0:
                check_date -= timedelta(days=1)
                continue
            break
            
    return {
        'focus_time': f"{hours}h {minutes}m",
        'session_count': session_count,
        'tasks_completed': f"{completed_tasks}/{total_tasks}", # Format: Selesai/Total Task
        'streak': streak,
        'efficiency': '100%' 
    }

# ========================================
# ROUTES KHUSUS FOCUSEEN
# ========================================

@app.route('/focuseen-app')
def buka_focuseen():
    """Halaman Utama Fitur FocuSeen"""
    db.create_all() # Buat tabel jika belum ada
    
    stats = get_focus_stats()
    
    # Tampilkan task urut berdasarkan: Belum selesai duluan, lalu yang terbaru
    tasks = FocusTask.query.order_by(FocusTask.is_completed.asc(), FocusTask.created_at.desc()).all()
    
    today = datetime.now().date()
    # ambil seluruh jadwal, urut menurut tanggal dan jam mulai
    schedules = FocusSchedule.query.order_by(FocusSchedule.date, FocusSchedule.start_time).all()
    
    return render_template('fitur_focuseen.html', 
                           stats=stats, 
                           tasks=tasks,
                           schedules=schedules,
                           today=today)

# --- API SAVE TIMER ---
@app.route('/api/focus/save', methods=['POST'])
def save_focus_session():
    """API untuk menyimpan sesi fokus dari Timer JavaScript"""
    data = request.json
    minutes = data.get('minutes')
    
    if minutes and int(minutes) > 0:
        today = datetime.now().date()
        new_session = FocusSession(
            duration_minutes=int(minutes),
            date=today
        )
        db.session.add(new_session)
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

# --- ACTION ROUTES (Task & Schedule) ---

@app.route('/add_task', methods=['POST'])
def add_task_focuseen():
    """Menambah Task Baru"""
    title = request.form.get('title')
    deadline_days = request.form.get('deadline_days')
    
    # Default 1 hari jika user tidak mengisi
    if not deadline_days:
        deadline_days = 1
        
    if title:
        task = FocusTask(title=title, deadline_days=int(deadline_days))
        db.session.add(task)
        db.session.commit()
        
    return redirect(url_for('buka_focuseen'))

@app.route('/toggle_task/<int:task_id>', methods=['GET'])
def toggle_task_focuseen(task_id):
    """Mengubah status task (Selesai/Belum)"""
    task = FocusTask.query.get_or_404(task_id)
    
    # Toggle status
    task.is_completed = not task.is_completed
    
    # Update progress bar otomatis
    if task.is_completed:
        task.progress = 100
    else:
        task.progress = 0
        
    db.session.commit()
    return redirect(url_for('buka_focuseen'))

@app.route('/update_progress/<int:task_id>', methods=['POST'])
def update_progress_focuseen(task_id):
    """Update manual progress bar"""
    task = FocusTask.query.get_or_404(task_id)
    progress_change = request.form.get('progress')
    
    if progress_change:
        new_progress = int(progress_change)
        task.progress = max(0, min(100, new_progress))
        task.is_completed = (task.progress >= 100)
            
    db.session.commit()
    return redirect(url_for('buka_focuseen'))

@app.route('/delete_task/<int:task_id>', methods=['GET'])
def delete_task_focuseen(task_id):
    """Hapus Task"""
    task = FocusTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('buka_focuseen'))

@app.route('/delete_schedule/<int:schedule_id>', methods=['GET'])
def delete_schedule_focuseen(schedule_id):
    """Hapus jadwal fokus"""
    sched = FocusSchedule.query.get_or_404(schedule_id)
    db.session.delete(sched)
    db.session.commit()
    return redirect(url_for('buka_focuseen'))

@app.route('/add_schedule', methods=['POST'])
def add_schedule_focuseen():
    """Tambah Jadwal"""
    title = request.form.get('title')
    location = request.form.get('location')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    date_str = request.form.get('date')

    # konversi tanggal jika disediakan, gunakan tanggal sekarang sebagai default
    if date_str:
        try:
            schedule_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            schedule_date = datetime.now().date()
    else:
        schedule_date = datetime.now().date()
    
    if all([title, location, start_time, end_time]):
        schedule = FocusSchedule(
            title=title, location=location, 
            start_time=start_time, end_time=end_time,
            date=schedule_date
        )
        db.session.add(schedule)
        db.session.commit()
    return redirect(url_for('buka_focuseen'))

# ========================================
# DECORATOR (HELPER LAMA)
# ========================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Silakan login terlebih dahulu!', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ========================================
# ROUTES USER UTAMA (DARI KODE ASLI)
# ========================================

@app.route('/')
def index():
    tugas_list = load_tugas()
    stats = get_statistics()
    is_logged_in = 'user_id' in session
    user_data = None
    if is_logged_in:
        user_tugas = get_user_tugas(session['user_id'])
        unread_count = get_unread_count(session['user_id'])
        user_data = {
            'username': session['username'],
            'unread_notifications': unread_count,
            'user_tugas': user_tugas
        }
    return render_template('index.html', mata_kuliah=MATA_KULIAH, tugas_list=tugas_list, 
                           total_tugas=stats['total_tugas'], tugas_selesai=stats['tugas_selesai'], 
                           is_logged_in=is_logged_in, user_data=user_data)

@app.route('/biodata/<nama>')
def biodata(nama):
    member_data = None
    for m in TIM_MEMBERS:
        if m['nama'].lower().replace(' ', '-') == nama.lower():
            member_data = m
            break
    if member_data:
        return render_template('biodata.html', member=member_data)
    return "Member tidak ditemukan", 404

# ========================================
# AUTHENTICATION ROUTES
# ========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash('Username, email, dan password wajib diisi!', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Password tidak sama!', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'danger')
            return redirect(url_for('register'))
        
        if register_user(username, email, password):
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username atau email sudah terdaftar!', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = authenticate_user(username, password)
        
        if user:
            session['user_logged_in'] = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_email'] = user['email']
            flash('Login berhasil!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username/email atau password salah!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout berhasil!', 'info')
    return redirect(url_for('index'))

# ========================================
# USER TASK ROUTES
# ========================================

@app.route('/my-tasks')
@login_required
def my_tasks():
    user_tugas = get_user_tugas(session['user_id'])
    user_data = {
        'username': session['username'],
        'unread_notifications': get_unread_count(session['user_id']),
    }
    return render_template(
        'my_tasks.html',
        user_tugas=user_tugas,
        is_logged_in=True,
        user_data=user_data,
    )

@app.route('/api/user-tugas/<int:tugas_id>', methods=['POST'])
@login_required
def api_update_user_tugas(tugas_id):
    data = request.json
    update_user_tugas(
        session['user_id'],
        tugas_id,
        status=data.get('status'),
        bookmarked=data.get('bookmarked'),
        notes=data.get('notes'),
        progress=data.get('progress')
    )
    return jsonify({'success': True})

@app.route('/api/bookmark/<int:tugas_id>', methods=['POST'])
@login_required
def api_toggle_bookmark(tugas_id):
    new_status = toggle_bookmark(session['user_id'], tugas_id)
    return jsonify({'success': True, 'bookmarked': new_status})

# ========================================
# NOTIFICATION & API ROUTES
# ========================================

@app.route('/api/notifications')
@login_required
def api_notifications():
    notifications = get_notifications(session['user_id'], limit=20)
    unread_count = get_unread_count(session['user_id'])
    return jsonify({
        'notifications': notifications,
        'unread_count': unread_count
    })

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def api_mark_notification_read(notification_id):
    mark_notification_read(notification_id)
    return jsonify({'success': True})

@app.route('/api/tugas', methods=['POST'])
def api_add_tugas():
    data = request.json
    add_tugas(data['matkul_id'], data['judul'], data['deadline'])
    return jsonify({'success': True})

@app.route('/api/tugas/<int:tugas_id>', methods=['DELETE'])
def api_delete_tugas(tugas_id):
    delete_tugas(tugas_id)
    return jsonify({'success': True})

@app.route('/api/tugas/<int:tugas_id>/toggle', methods=['POST'])
def api_toggle_tugas(tugas_id):
    new_status = toggle_tugas_status(tugas_id)
    return jsonify({'success': True, 'status': new_status})

# ========================================
# ADMIN ROUTES
# ========================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah!', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout', methods=['GET', 'POST'])
def admin_logout():
    session.clear()
    flash('Logout berhasil!', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = get_statistics()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT t.*, mk.nama as nama_matkul, mk.color as matkul_color
        FROM tugas t
        JOIN mata_kuliah mk ON t.matkul_id = mk.id
        ORDER BY t.created_at DESC LIMIT 5
    """)
    tugas_terbaru = cursor.fetchall()
    cursor.execute("SELECT * FROM mata_kuliah ORDER BY created_at DESC LIMIT 5")
    matkul_terbaru = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) as count FROM mata_kuliah")
    total_matkul = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM anggota_tim")
    total_anggota = cursor.fetchone()['count']
    conn.close()
    return render_template('admin/dashboard.html', stats=stats, tugas_terbaru=tugas_terbaru, 
                           matkul_terbaru=matkul_terbaru, total_matkul=total_matkul, total_anggota=total_anggota)

# --- ADMIN KELOLA TUGAS ---
@app.route('/admin/tugas')
@admin_required
def admin_tugas():
    tugas_list = load_tugas()
    mata_kuliah = get_all_matkul()
    return render_template('admin/tugas.html', tugas_list=tugas_list, mata_kuliah=mata_kuliah)

@app.route('/admin/tugas/add', methods=['POST'])
@admin_required
def admin_add_tugas():
    add_tugas(request.form.get('matkul_id'), request.form.get('judul'), request.form.get('deadline'))
    flash('Tugas berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_tugas'))

@app.route('/admin/tugas/edit/<int:tugas_id>', methods=['POST'])
@admin_required
def admin_edit_tugas(tugas_id):
    update_tugas(tugas_id, request.form.get('matkul_id'), request.form.get('judul'), 
                 request.form.get('deadline'), request.form.get('status') == 'on')
    flash('Tugas berhasil diupdate!', 'success')
    return redirect(url_for('admin_tugas'))

@app.route('/admin/tugas/delete/<int:tugas_id>', methods=['POST'])
@admin_required
def admin_delete_tugas(tugas_id):
    delete_tugas(tugas_id)
    flash('Tugas berhasil dihapus!', 'success')
    return redirect(url_for('admin_tugas'))

@app.route('/admin/tugas/toggle/<int:tugas_id>', methods=['POST'])
@admin_required
def admin_toggle_tugas(tugas_id):
    new_status = toggle_tugas_status(tugas_id)
    return jsonify({'success': True, 'status': new_status})

# --- ADMIN KELOLA MATKUL ---
@app.route('/admin/matkul')
@admin_required
def admin_matkul():
    return render_template('admin/matkul.html', mata_kuliah=get_all_matkul())

@app.route('/admin/matkul/add', methods=['POST'])
@admin_required
def admin_add_matkul():
    add_matkul(request.form.get('nama'), request.form.get('kode'), request.form.get('color'), 
               request.form.get('icon'), request.form.get('dosen'), request.form.get('semester'))
    flash('Mata kuliah berhasil ditambahkan!', 'success')
    return redirect(url_for('admin_matkul'))

@app.route('/admin/matkul/edit/<int:matkul_id>', methods=['POST'])
@admin_required
def admin_edit_matkul(matkul_id):
    update_matkul(matkul_id, request.form.get('nama'), request.form.get('kode'), request.form.get('color'), 
                  request.form.get('icon'), request.form.get('dosen'), request.form.get('semester'))
    flash('Mata kuliah berhasil diupdate!', 'success')
    return redirect(url_for('admin_matkul'))

@app.route('/admin/matkul/delete/<int:matkul_id>', methods=['POST'])
@admin_required
def admin_delete_matkul(matkul_id):
    if delete_matkul(matkul_id):
        flash('Mata kuliah berhasil dihapus!', 'success')
    else:
        flash('Gagal! Matkul masih memiliki tugas.', 'danger')
    return redirect(url_for('admin_matkul'))

# --- ADMIN KELOLA TIM ---
@app.route('/admin/tim')
@admin_required
def admin_tim():
    return render_template('admin/tim.html', anggota_tim=get_all_anggota_tim())

@app.route('/admin/tim/add', methods=['POST'])
@admin_required
def admin_add_tim():
    if add_anggota_tim(request.form.get('nama'), request.form.get('nim'), request.form.get('email'), 
                       request.form.get('peran'), request.form.get('foto') or 'photo.jpg'):
        flash('Anggota tim berhasil ditambahkan!', 'success')
    else:
        flash('NIM sudah terdaftar!', 'danger')
    return redirect(url_for('admin_tim'))

@app.route('/admin/tim/edit/<int:anggota_id>', methods=['POST'])
@admin_required
def admin_edit_tim(anggota_id):
    update_anggota_tim(anggota_id, request.form.get('nama'), request.form.get('nim'), request.form.get('email'), 
                       request.form.get('peran'), request.form.get('foto') or 'photo.jpg')
    flash('Anggota tim berhasil diupdate!', 'success')
    return redirect(url_for('admin_tim'))

@app.route('/admin/tim/delete/<int:anggota_id>', methods=['POST'])
@admin_required
def admin_delete_tim(anggota_id):
    delete_anggota_tim(anggota_id)
    flash('Anggota tim berhasil dihapus!', 'success')
    return redirect(url_for('admin_tim'))

if __name__ == '__main__':
    host = '127.0.0.1'
    port = 5000
    base = f"http://{host}:{port}"
    print("=" * 60)
    print(f"FocuSeen + LYA & SAM Running on: {base}")
    print(f"Register (user): {base}/register")
    print(f"Admin login:     {base}/admin/login")
    print("=" * 60)
    app.run(host=host, port=port, debug=DEBUG)