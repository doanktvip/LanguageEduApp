import hashlib
from eduapp import db
from eduapp.models import HocVien, GiaoVien, NhanVien, QuanLy, NguoiDungEnum, KhoaHoc, PhongHoc, LoaiKhoaHoc, NguoiDung, \
    BangDiem, CauTrucDiem


def login(username, password):
    password = str(hashlib.md5(password.encode('utf-8')).hexdigest())
    user_models = [HocVien, GiaoVien, NhanVien, QuanLy]
    for model in user_models:
        user = model.query.filter_by(ten_dang_nhap=username, mat_khau=password).first()
        if user:
            return user
    return None


def add_user(loai_nguoi_dung, **kwargs):
    map_model = {
        NguoiDungEnum.HOC_VIEN: HocVien,
        NguoiDungEnum.NHAN_VIEN: NhanVien,
        NguoiDungEnum.GIAO_VIEN: GiaoVien,
        NguoiDungEnum.QUAN_LY: QuanLy
    }
    ModelClass = map_model.get(loai_nguoi_dung)
    if not ModelClass:
        return False
    try:
        if 'ma_nguoi_dung' not in kwargs:
            try:
                kwargs['ma_nguoi_dung'] = NguoiDung.tao_ma_nguoi_dung(loai_nguoi_dung)
            except Exception as e:
                raise e
        if 'mat_khau' in kwargs:
            kwargs['mat_khau'] = str(hashlib.md5(kwargs['mat_khau'].strip().encode('utf-8')).hexdigest())
        kwargs['vai_tro'] = loai_nguoi_dung
        nguoi_dung_moi = ModelClass(**kwargs)
        db.session.add(nguoi_dung_moi)
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        return False


def get_by_id(user_id):
    model_mapping = {
        'HV': HocVien,
        'GV': GiaoVien,
        'NV': NhanVien,
        'QL': QuanLy
    }
    prefix = user_id[:2].upper()
    model = model_mapping.get(prefix)
    if model:
        return model.query.get(user_id)
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


def get_by_email(email):
    return NguoiDung.query.filter_by(email=email).first()


def get_by_course_category(course_category):
    return LoaiKhoaHoc.query.filter_by(ma_loai_khoa_hoc=course_category).first()


def get_by_course_id(course_id):
    return KhoaHoc.query.filter_by(ma_khoa_hoc=course_id).first()


def get_by_classroom_id(classroom_id):
    return PhongHoc.query.filter_by(ma_phong_hoc=classroom_id).first()


def get_by_scoreboard_id(student_id, classroom_id):
    return BangDiem.query.filter_by(ma_hoc_vien=student_id, ma_khoa_hoc=classroom_id).first()


def get_cau_truc_diem(course_id):
    return CauTrucDiem.query.filter_by(ma_khoa_hoc=course_id)
