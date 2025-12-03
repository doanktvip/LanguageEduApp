import os
import uuid
from werkzeug.utils import secure_filename
from eduapp import app
from eduapp.models import HocVien


def login(username, password):
    return HocVien.query.filter(HocVien.ten_dang_nhap == username or HocVien.mat_khau == password).first()


def get_by_id(id):
    return HocVien.query.get(id)


def get_by_username(username):
    return HocVien.query.filter_by(ten_dang_nhap=username).first()


def get_by_username_email(username, email):
    return HocVien.query.filter_by(ten_dang_nhap=username, email=email).first()


def add_image(image_file):
    avatar_path = None
    if image_file:
        filename = secure_filename(image_file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        upload_path = os.path.join(app.root_path, 'static/images', unique_filename)
        image_file.save(upload_path)
        avatar_path = 'images/' + unique_filename
    return avatar_path
