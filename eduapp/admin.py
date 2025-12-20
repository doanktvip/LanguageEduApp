from flask import Flask, redirect
from flask_admin import Admin, AdminIndexView, expose
# from flask_admin.theme import Bootstrap4Theme
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from eduapp import app, db
from eduapp import app, db
from eduapp.models import (
    NguoiDungEnum,
    HocVien, GiaoVien, NhanVien, QuanLy,
    LoaiKhoaHoc, KhoaHoc, PhongHoc,
    HoaDon, TrangThaiHoaDonEnum
)

class AuthenticatedView(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.vai_tro == NguoiDungEnum.QUAN_LY
    def is_not_accessible(self) -> bool:
        if not current_user.is_authenticated:
            return redirect('/login')


class UserBaseView(AuthenticatedView):
    column_exclude_list = ['mat_khau']

class HocVienView(UserBaseView):
    column_list = ['ma_nguoi_dung', 'ho_va_ten', 'email', 'so_dien_thoai', 'so_dien_thoai_phu_huynh']
    column_searchable_list = ['ho_va_ten', 'ma_nguoi_dung', 'so_dien_thoai']
    column_labels = dict(ho_va_ten='Họ tên', so_dien_thoai='SĐT', so_dien_thoai_phu_huynh='SĐT Phụ huynh')

class GiaoVienView(UserBaseView):
    column_list = ['ma_nguoi_dung', 'ho_va_ten', 'email', 'nam_kinh_nghiem', 'nhung_khoa_hoc']
    column_labels = dict(ho_va_ten='Họ tên', nam_kinh_nghiem='Kinh nghiệm (năm)')

class NhanVienView(UserBaseView):
    column_list = ['ma_nguoi_dung', 'ho_va_ten', 'email', 'tinh_trang_hoat_dong']


class KhoaHocView(AuthenticatedView):
    column_list = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'hoc_phi', 'si_so_hien_tai',
                   'tinh_trang']
    column_searchable_list = ['ten_khoa_hoc', 'ma_khoa_hoc']
    column_filters = ['tinh_trang', 'hoc_phi']
    form_columns = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'ngay_bat_dau', 'ngay_ket_thuc',
                    'si_so_toi_da', 'hoc_phi', 'tinh_trang']

    column_labels = dict(loai_khoa_hoc='Loại khóa', giao_vien='Giáo viên CN', si_so_hien_tai='Sĩ số')


class PhongHocView(AuthenticatedView):
    column_list = ['ma_phong_hoc', 'ten_phong_hoc']
    form_columns = ['ten_phong_hoc']


class HoaDonView(AuthenticatedView):
    can_create = False
    column_list = ['ma_hoa_don', 'hoc_vien', 'khoa_hoc', 'so_tien', 'trang_thai', 'ngay_tao']
    column_filters = ['trang_thai', 'ngay_tao']

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self) -> str:
        return self.render('admin/index.html')


admin = Admin(app=app, name="Language Center", index_view=MyAdminIndexView())

admin.add_view(HocVienView(HocVien, db.session, name='Học Viên', category='Người Dùng'))
admin.add_view(GiaoVienView(GiaoVien, db.session, name='Giáo Viên', category='Người Dùng'))
admin.add_view(NhanVienView(NhanVien, db.session, name='Nhân Viên', category='Người Dùng'))
admin.add_view(UserBaseView(QuanLy, db.session, name='Quản Trị Viên', category='Người Dùng'))

admin.add_view(KhoaHocView(KhoaHoc, db.session, name='Khóa Học', category='Đào Tạo'))
admin.add_view(AuthenticatedView(LoaiKhoaHoc, db.session, name='Loại Khóa', category='Đào Tạo'))
admin.add_view(PhongHocView(PhongHoc, db.session, name='Phòng Học', category='Đào Tạo'))

admin.add_view(HoaDonView(HoaDon, db.session, name='Hóa Đơn', category='Tài Chính'))
