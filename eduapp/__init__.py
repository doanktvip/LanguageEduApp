import cloudinary
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.secret_key = "123dasdadasdasdasd"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/eduappdb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 5

app.config["OTP_LIFETIME"] = 60
app.config["MAX_RESEND_LIMIT"] = 3
app.config["RESEND_BLOCK_TIME"] = 600

# --- CẤU HÌNH FLASK-MAIL (Ví dụ dùng Gmail) ---
# Tên máy chủ email (SMTP server)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# Cổng kết nối (Port) - 465 cho SSL hoặc 587 cho TLS
app.config['MAIL_PORT'] = 465
# Email của bạn (người gửi)
app.config['MAIL_USERNAME'] = 'nd21032005@gmail.com'
# Mật khẩu ứng dụng (App Password) - KHÔNG phải mật khẩu đăng nhập Gmail
app.config['MAIL_PASSWORD'] = 'uvoc ehnq pxsk kbmq'
# Sử dụng mã hóa SSL để bảo mật
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
# Email mặc định gửi mail
app.config['MAIL_DEFAULT_SENDER'] = 'nd21032005@gmail.com'

cloudinary.config(cloud_name='db4bjqp4f',
                  api_key='588892363794189',
                  api_secret='eT9TiV07X91x0SFmKN6yjZyF2zk')

mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
