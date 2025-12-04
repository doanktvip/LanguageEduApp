import os
import uuid
from werkzeug.utils import secure_filename
from eduapp import app
from eduapp.models import HocVien, GiaoVien, NhanVien, QuanLy


def login(username, password):
    user_models = [HocVien, GiaoVien, NhanVien, QuanLy]
    for model in user_models:
        user = model.query.filter_by(ten_dang_nhap=username, mat_khau=password).first()
        if user:
            return user
    return None


def get_by_id(user_id):
    user_models = [HocVien, GiaoVien, NhanVien, QuanLy]
    for model in user_models:
        user = model.query.get(user_id)
        if user:
            return user
    return None


def get_by_username(username):
    user_models = [HocVien, GiaoVien, NhanVien, QuanLy]
    for model in user_models:
        user = model.query.filter_by(ten_dang_nhap=username).first()
        if user:
            return user
    return None


def get_by_username_email(username, email):
    user_models = [HocVien, GiaoVien, NhanVien, QuanLy]
    for model in user_models:
        user = model.query.filter_by(ten_dang_nhap=username, email=email).first()
        if user:
            return user
    return None


def add_image(image_file):
    avatar_path = None
    if image_file:
        filename = secure_filename(image_file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        upload_path = os.path.join(app.root_path, 'static/images', unique_filename)
        image_file.save(upload_path)
        avatar_path = 'images/' + unique_filename
    return avatar_path
