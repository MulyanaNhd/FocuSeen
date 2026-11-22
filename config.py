# config.py

# Email Configuration (untuk reminder)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'syakirahamidan69@gmail.com',  # Ganti dengan email kamu
    'sender_password': '123456789',   # Gunakan App Password Gmail
    'enabled': False  # Set True jika mau aktifkan reminder email
}

# Flask Configuration
SECRET_KEY = 'lya_sam_admin_secret_2026'
DEBUG = True