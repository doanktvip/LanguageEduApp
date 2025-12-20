import cloudinary
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_babel import Babel

app = Flask(__name__)
app.secret_key = "123dasdadasdasdasd"

# --- CẤU HÌNH DATABASE ---
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost/eduappdb?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 5

# --- CẤU HÌNH NGÔN NGỮ (BABEL) ---
app.config['BABEL_DEFAULT_LOCALE'] = 'vi'

# --- CẤU HÌNH OTP ---
app.config["OTP_LIFETIME"] = 60
app.config["MAX_RESEND_LIMIT"] = 3
app.config["RESEND_BLOCK_TIME"] = 600

# --- CẤU HÌNH FLASK-MAIL ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'edu.simple.talk@gmail.com'
app.config['MAIL_PASSWORD'] = 'iqmf vlko yvbo bsdm'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = 'edu.simple.talk@gmail.com'

# --- CẤU HÌNH CLOUDINARY ---
cloudinary.config(cloud_name='db4bjqp4f',
                  api_key='588892363794189',
                  api_secret='eT9TiV07X91x0SFmKN6yjZyF2zk')

# --- KHỞI TẠO CÁC EXTENSION ---
mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)


# --- KHỞI TẠO BABEL ---
def get_locale():
    return 'vi'


babel = Babel(app, locale_selector=get_locale)