from functools import wraps
from flask_login import current_user
from flask import redirect

from eduapp.models import NguoiDungEnum


def login_user_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def anonymous_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def giao_vien_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.vai_tro != NguoiDungEnum.GIAO_VIEN:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def hoc_vien_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.vai_tro != NguoiDungEnum.HOC_VIEN:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def nhan_vien_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.vai_tro != NguoiDungEnum.NHAN_VIEN:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def quan_ly_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.vai_tro != NguoiDungEnum.QUAN_LY:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def giao_vien_hoac_hoc_vien_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.vai_tro not in [NguoiDungEnum.GIAO_VIEN, NguoiDungEnum.HOC_VIEN]:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func


def tinh_trang_xac_nhan_email_required(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.tinh_trang_xac_nhan_email:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_func
