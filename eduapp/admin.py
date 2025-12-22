import hashlib
from flask import redirect, url_for, session, request, jsonify
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func
from eduapp import app, db
from eduapp.models import (NguoiDungEnum, HocVien, GiaoVien, NhanVien, LoaiKhoaHoc, KhoaHoc, PhongHoc, HoaDon,
                           TrangThaiHoaDonEnum, TinhTrangKhoaHocEnum, LichHoc)


# ==============================================================================
# 0. LOGIC BẢO MẬT CHUNG (MIXIN) - QUAN TRỌNG
# ==============================================================================
class AdminSecurityMixin:
    def is_accessible(self):
        return (current_user.is_authenticated and current_user.vai_tro == NguoiDungEnum.QUAN_LY and session.get(
            'admin_unlocked') is True)

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return redirect('/')


# ==============================================================================
# 1. CÁC HÀM FORMATTER (ĐỊNH DẠNG HIỂN THỊ)
# ==============================================================================
def format_du_lieu_trong(view, context, model, name):
    val = getattr(model, name)
    return val if val is not None and val != "" else "--"


def format_tien_te(view, context, model, name):
    value = getattr(model, name)
    return "{:,.0f} VNĐ".format(value).replace(",", ".") if value is not None else ""


def format_anh_dai_dien(view, context, model, name):
    if not model.anh_chan_dung: return ""
    return Markup(
        f'<img src="{model.anh_chan_dung}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #ddd;">')


def format_trang_thai_hd(view, context, model, name):
    if getattr(model, name) == TrangThaiHoaDonEnum.DA_THANH_TOAN:
        return Markup('<span class="badge bg-success text-white">Đã thanh toán</span>')
    return Markup('<span class="badge bg-danger text-white">Chưa thanh toán</span>')


def format_trang_thai_hoat_dong(view, context, model, name):
    if getattr(model, name):
        return Markup('<span class="badge bg-success text-white" style="padding: 5px 10px;">Đang hoạt động</span>')
    return Markup('<span class="badge bg-danger text-white" style="padding: 5px 10px;">Ngưng hoạt động</span>')


def format_tinh_trang_khoa(view, context, model, name):
    tt = getattr(model, name)
    colors = {TinhTrangKhoaHocEnum.DANG_TUYEN_SINH: 'success', TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH: 'warning',
              TinhTrangKhoaHocEnum.DA_KET_THUC: 'secondary'}
    labels = {TinhTrangKhoaHocEnum.DANG_TUYEN_SINH: 'Đang Tuyển', TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH: 'Đang Học',
              TinhTrangKhoaHocEnum.DA_KET_THUC: 'Kết Thúc'}
    return Markup(f'<span class="badge bg-{colors.get(tt, "secondary")} text-white">{labels.get(tt, tt.name)}</span>')


def format_xac_nhan_email(view, context, model, name):
    if getattr(model, name):
        return Markup('<span class="badge bg-success text-white"><i class="bi bi-check me-1"></i>Đã xác nhận</span>')
    return Markup('<span class="badge bg-danger text-white"><i class="bi bi-x me-1"></i>Chưa xác nhận</span>')


# ==============================================================================
# 2. CÁC CLASS VIEW CƠ BẢN
# ==============================================================================

# Kế thừa AdminSecurityMixin để áp dụng bảo mật
class AuthenticatedView(AdminSecurityMixin, ModelView):
    can_export = True
    page_size = app.config.get("PAGE_SIZE")
    can_view_details = True


class UserBaseView(AuthenticatedView):
    column_exclude_list = ['mat_khau', 'vai_tro']
    common_columns = ['anh_chan_dung', 'ma_nguoi_dung', 'ho_va_ten', 'ten_dang_nhap', 'email', 'so_dien_thoai',
                      'ngay_tao', 'tinh_trang_hoat_dong']
    column_formatters = {
        'anh_chan_dung': format_anh_dai_dien,
        'tinh_trang_hoat_dong': format_trang_thai_hoat_dong,
        'so_dien_thoai': format_du_lieu_trong,
        'email': format_du_lieu_trong,
        'ten_dang_nhap': format_du_lieu_trong
    }
    column_labels = dict(ma_nguoi_dung='Mã người dùng', ho_va_ten='Họ và tên', ten_dang_nhap='Tên đăng nhập',
                         email='Email', so_dien_thoai='SĐT', tinh_trang_hoat_dong='Trạng thái', ngay_tao='Ngày tạo',
                         anh_chan_dung='Ảnh')
    form_excluded_columns = ['ngay_tao', 'vai_tro']


# ==============================================================================
# 3. CHI TIẾT CÁC VIEW
# ==============================================================================

class HocVienView(UserBaseView):
    column_list = UserBaseView.common_columns + ['ngay_sinh', 'so_dien_thoai_phu_huynh', 'tinh_trang_xac_nhan_email']
    column_searchable_list = ['ho_va_ten', 'ma_nguoi_dung', 'so_dien_thoai', 'email', 'so_dien_thoai_phu_huynh']
    column_labels = dict(UserBaseView.column_labels, ngay_sinh='Ngày sinh', so_dien_thoai_phu_huynh='SĐT phụ huynh',
                         tinh_trang_xac_nhan_email='Xác thực Email')
    column_formatters = dict(UserBaseView.column_formatters, so_dien_thoai_phu_huynh=format_du_lieu_trong,
                             tinh_trang_xac_nhan_email=format_xac_nhan_email)
    form_columns = ['ho_va_ten', 'email', 'ten_dang_nhap', 'mat_khau', 'so_dien_thoai', 'so_dien_thoai_phu_huynh',
                    'ngay_sinh', 'anh_chan_dung', 'tinh_trang_hoat_dong']


class GiaoVienView(UserBaseView):
    column_list = UserBaseView.common_columns + ['nam_kinh_nghiem']
    column_searchable_list = ['ho_va_ten', 'email', 'ma_nguoi_dung']
    column_labels = dict(UserBaseView.column_labels, nam_kinh_nghiem='Kinh nghiệm (Năm)')
    column_formatters = dict(UserBaseView.column_formatters, nam_kinh_nghiem=format_du_lieu_trong)
    form_columns = ['ho_va_ten', 'email', 'ten_dang_nhap', 'mat_khau', 'so_dien_thoai', 'nam_kinh_nghiem',
                    'anh_chan_dung', 'tinh_trang_hoat_dong']


class NhanVienView(UserBaseView):
    column_list = UserBaseView.common_columns
    column_searchable_list = ['ho_va_ten', 'email', 'ma_nguoi_dung']
    form_columns = ['ho_va_ten', 'email', 'ten_dang_nhap', 'mat_khau', 'so_dien_thoai', 'anh_chan_dung',
                    'tinh_trang_hoat_dong']


class KhoaHocView(AuthenticatedView):
    can_create = False;
    can_edit = True;
    can_delete = True
    column_list = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'hoc_phi', 'si_so_hien_tai',
                   'tinh_trang']
    column_searchable_list = ['ten_khoa_hoc', 'ma_khoa_hoc']
    column_filters = ['tinh_trang', 'hoc_phi', 'giao_vien.ho_va_ten']
    form_columns = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'ngay_bat_dau', 'ngay_ket_thuc',
                    'si_so_toi_da', 'hoc_phi', 'tinh_trang']
    column_formatters = {'hoc_phi': format_tien_te, 'tinh_trang': format_tinh_trang_khoa}
    column_labels = dict(ma_khoa_hoc='Mã Khóa', ten_khoa_hoc='Tên Khóa Học', loai_khoa_hoc='Loại Khóa',
                         giao_vien='Giáo Viên', hoc_phi='Học Phí', si_so_hien_tai='Sĩ Số', tinh_trang='Trạng Thái',
                         ngay_bat_dau='Ngày Bắt Đầu', ngay_ket_thuc='Ngày Kết Thúc', si_so_toi_da='Sĩ Số Tối Đa')
    inline_models = [(LichHoc,
                      dict(form_label='Chi Tiết Lịch Học', form_columns=['ma_lich_hoc', 'thu', 'ca_hoc', 'phong_hoc'],
                           column_labels={'ma_lich_hoc': 'ID', 'thu': 'Thứ Trong Tuần', 'ca_hoc': 'Ca Học',
                                          'phong_hoc': 'Phòng Học'}))]


class LoaiKhoaHocView(AuthenticatedView):
    column_list = ['ma_loai_khoa_hoc', 'ten_loai_khoa_hoc', 'hoc_phi']
    column_labels = dict(ma_loai_khoa_hoc='Mã Loại', ten_loai_khoa_hoc='Tên Loại Khóa', hoc_phi='Học Phí Tham Khảo')
    column_formatters = {'hoc_phi': format_tien_te}


class PhongHocView(AuthenticatedView):
    column_list = ['ma_phong_hoc', 'ten_phong_hoc']
    column_labels = dict(ma_phong_hoc='Mã Phòng', ten_phong_hoc='Tên Phòng')


class HoaDonView(AuthenticatedView):
    can_create = False;
    can_edit = False;
    can_delete = True
    column_list = ['ma_hoa_don', 'hoc_vien', 'khoa_hoc', 'so_tien', 'trang_thai', 'ngay_tao', 'ngay_nop']
    column_filters = ['trang_thai', 'ngay_tao', 'hoc_vien.ho_va_ten']
    column_sortable_list = ['ngay_tao', 'so_tien', 'trang_thai']
    column_formatters = {'so_tien': format_tien_te, 'trang_thai': format_trang_thai_hd}
    column_labels = dict(ma_hoa_don='Mã HĐ', hoc_vien='Học Viên', khoa_hoc='Khóa Học', so_tien='Số Tiền',
                         trang_thai='Trạng Thái', ngay_tao='Ngày Tạo', ngay_nop='Ngày Thanh Toán',
                         nhan_vien='Nhân Viên Thu')


# ==============================================================================
# 4. DASHBOARD INDEX (TRANG CHỦ ADMIN)
# ==============================================================================

class MyAdminIndexView(AdminSecurityMixin, AdminIndexView):
    @expose('/')
    def index(self):
        tong_doanh_thu = db.session.query(func.sum(HoaDon.so_tien)).filter(
            HoaDon.trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN).scalar() or 0
        so_hoa_don_no = HoaDon.query.filter_by(trang_thai=TrangThaiHoaDonEnum.CHUA_THANH_TOAN).count()
        so_hoc_vien = HocVien.query.count()
        so_giao_vien = GiaoVien.query.count()
        so_nhan_vien = NhanVien.query.count()
        khoa_dang_tuyen = KhoaHoc.query.filter_by(tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH).count()
        lop_dang_hoc = KhoaHoc.query.filter_by(tinh_trang=TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH).count()
        so_phong_hoc = PhongHoc.query.count()

        return self.render('admin/index.html', tong_doanh_thu="{:,.0f}".format(tong_doanh_thu).replace(",", "."),
                           so_hoa_don_no=so_hoa_don_no, so_hoc_vien=so_hoc_vien, so_giao_vien=so_giao_vien,
                           so_nhan_vien=so_nhan_vien, khoa_dang_tuyen=khoa_dang_tuyen, lop_dang_hoc=lop_dang_hoc,
                           so_phong_hoc=so_phong_hoc)


# ==============================================================================
# 5. KHỞI TẠO ADMIN & ADD VIEWS
# ==============================================================================

admin = Admin(app=app, name="Hệ Thống Quản Lý", index_view=MyAdminIndexView())

admin.add_view(HocVienView(HocVien, db.session, name='Học Viên', category='Người Dùng'))
admin.add_view(GiaoVienView(GiaoVien, db.session, name='Giáo Viên', category='Người Dùng'))
admin.add_view(NhanVienView(NhanVien, db.session, name='Nhân Viên', category='Người Dùng'))

admin.add_view(KhoaHocView(KhoaHoc, db.session, name='Danh Sách Khóa', category='Đào Tạo'))
admin.add_view(LoaiKhoaHocView(LoaiKhoaHoc, db.session, name='Loại Khóa', category='Đào Tạo'))
admin.add_view(PhongHocView(PhongHoc, db.session, name='Phòng Học', category='Đào Tạo'))

admin.add_view(HoaDonView(HoaDon, db.session, name='Hóa Đơn', category='Tài Chính'))
