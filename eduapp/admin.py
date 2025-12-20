from flask import redirect, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from markupsafe import Markup
from sqlalchemy import func
from eduapp import app, db
from eduapp.models import (NguoiDungEnum, HocVien, GiaoVien, NhanVien, QuanLy, LoaiKhoaHoc, KhoaHoc, PhongHoc, HoaDon,
                           TrangThaiHoaDonEnum, TinhTrangKhoaHocEnum, LichHoc)


# ==============================================================================
# 1. CÁC HÀM FORMATTER (ĐỊNH DẠNG HIỂN THỊ DỮ LIỆU)
# ==============================================================================

def format_tien_te(view, context, model, name):
    value = getattr(model, name)
    if value is None:
        return ""
    return "{:,.0f} VNĐ".format(value).replace(",", ".")


def format_anh_dai_dien(view, context, model, name):
    if not model.anh_chan_dung:
        return ""
    return Markup(
        f'<img src="{model.anh_chan_dung}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 1px solid #ddd;">'
    )


def format_trang_thai_hd(view, context, model, name):
    trang_thai = getattr(model, name)
    if trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN:
        return Markup(f'<span class="badge bg-success text-white">Đã thanh toán</span>')
    return Markup(f'<span class="badge bg-danger text-white">Chưa thanh toán</span>')


def format_tinh_trang_khoa(view, context, model, name):
    tt = getattr(model, name)
    colors = {
        TinhTrangKhoaHocEnum.DANG_TUYEN_SINH: 'success',
        TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH: 'warning',
        TinhTrangKhoaHocEnum.DA_KET_THUC: 'secondary'
    }
    color = colors.get(tt, 'secondary')
    ten_hien_thi = {
        TinhTrangKhoaHocEnum.DANG_TUYEN_SINH: 'Đang Tuyển',
        TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH: 'Đang Học',
        TinhTrangKhoaHocEnum.DA_KET_THUC: 'Kết Thúc'
    }
    return Markup(f'<span class="badge bg-{color} text-white">{ten_hien_thi.get(tt, tt.name)}</span>')


# ==============================================================================
# 2. CÁC CLASS VIEW CƠ BẢN (BASE VIEW)
# ==============================================================================

class AuthenticatedView(ModelView):
    can_export = True
    page_size = app.config["PAGE_SIZE"]
    can_view_details = True

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.vai_tro == NguoiDungEnum.QUAN_LY

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))


class UserBaseView(AuthenticatedView):
    column_exclude_list = ['mat_khau', 'vai_tro']
    column_formatters = {
        'anh_chan_dung': format_anh_dai_dien
    }


# ==============================================================================
# 3. CHI TIẾT CÁC VIEW (CẤU HÌNH TỪNG BẢNG)
# ==============================================================================

class HocVienView(UserBaseView):
    column_list = ['anh_chan_dung', 'ma_nguoi_dung', 'ho_va_ten', 'email', 'so_dien_thoai', 'so_dien_thoai_phu_huynh']
    column_searchable_list = ['ho_va_ten', 'ma_nguoi_dung', 'so_dien_thoai', 'email']

    column_labels = dict(
        ma_nguoi_dung='Mã Học Viên',
        ho_va_ten='Họ và Tên',
        anh_chan_dung='Ảnh',
        so_dien_thoai='SĐT Cá Nhân',
        so_dien_thoai_phu_huynh='SĐT Phụ Huynh',
        email='Email',
        ngay_sinh='Ngày Sinh',
        ngay_tao='Ngày Tạo'
    )
    form_columns = ['ho_va_ten', 'email', 'mat_khau', 'so_dien_thoai', 'so_dien_thoai_phu_huynh', 'ngay_sinh',
                    'anh_chan_dung', 'tinh_trang_hoat_dong']


class GiaoVienView(UserBaseView):
    column_list = ['anh_chan_dung', 'ma_nguoi_dung', 'ho_va_ten', 'email', 'nam_kinh_nghiem']
    column_searchable_list = ['ho_va_ten', 'email']

    column_labels = dict(
        ma_nguoi_dung='Mã Giáo Viên',
        ho_va_ten='Họ và Tên',
        anh_chan_dung='Ảnh',
        email='Email',
        nam_kinh_nghiem='Kinh Nghiệm (Năm)',
        nhung_khoa_hoc='Các Khóa Dạy'
    )
    form_columns = ['ho_va_ten', 'email', 'mat_khau', 'so_dien_thoai', 'nam_kinh_nghiem', 'anh_chan_dung',
                    'tinh_trang_hoat_dong']


class NhanVienView(UserBaseView):
    column_list = ['ma_nguoi_dung', 'ho_va_ten', 'email', 'tinh_trang_hoat_dong']

    column_labels = dict(
        ma_nguoi_dung='Mã Nhân Viên',
        ho_va_ten='Họ và Tên',
        email='Email',
        tinh_trang_hoat_dong='Trạng Thái'
    )


class QuanLyView(UserBaseView):
    column_list = ['ma_nguoi_dung', 'ho_va_ten', 'email']
    column_labels = dict(
        ma_nguoi_dung='Mã Quản Lý',
        ho_va_ten='Họ Tên',
        email='Email'
    )


class KhoaHocView(AuthenticatedView):
    can_create = False
    can_edit = True
    can_delete = True
    column_list = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'hoc_phi', 'si_so_hien_tai',
                   'tinh_trang']
    column_searchable_list = ['ten_khoa_hoc', 'ma_khoa_hoc']
    column_filters = ['tinh_trang', 'hoc_phi', 'giao_vien.ho_va_ten']

    form_columns = ['ma_khoa_hoc', 'ten_khoa_hoc', 'loai_khoa_hoc', 'giao_vien', 'ngay_bat_dau', 'ngay_ket_thuc',
                    'si_so_toi_da', 'hoc_phi', 'tinh_trang']

    column_formatters = {
        'hoc_phi': format_tien_te,
        'tinh_trang': format_tinh_trang_khoa
    }

    column_labels = dict(
        ma_khoa_hoc='Mã Khóa',
        ten_khoa_hoc='Tên Khóa Học',
        loai_khoa_hoc='Loại Khóa',
        giao_vien='Giáo Viên',
        hoc_phi='Học Phí',
        si_so_hien_tai='Sĩ Số',
        tinh_trang='Trạng Thái',
        ngay_bat_dau='Ngày Bắt Đầu',
        ngay_ket_thuc='Ngày Kết Thúc',
        si_so_toi_da='Sĩ Số Tối Đa'
    )
    inline_models = [
        (LichHoc, dict(
            form_label='Chi Tiết Lịch Học',
            form_columns=['ma_lich_hoc', 'thu', 'ca_hoc', 'phong_hoc'],
            column_labels={
                'ma_lich_hoc': 'ID',
                'thu': 'Thứ Trong Tuần',
                'ca_hoc': 'Ca Học',
                'phong_hoc': 'Phòng Học'
            }
        ))
    ]


class LoaiKhoaHocView(AuthenticatedView):
    column_list = ['ma_loai_khoa_hoc', 'ten_loai_khoa_hoc', 'hoc_phi']
    column_labels = dict(
        ma_loai_khoa_hoc='Mã Loại',
        ten_loai_khoa_hoc='Tên Loại Khóa',
        hoc_phi='Học Phí Tham Khảo'
    )
    column_formatters = {'hoc_phi': format_tien_te}


class PhongHocView(AuthenticatedView):
    column_list = ['ma_phong_hoc', 'ten_phong_hoc']
    column_labels = dict(
        ma_phong_hoc='Mã Phòng',
        ten_phong_hoc='Tên Phòng'
    )


class HoaDonView(AuthenticatedView):
    can_create = False
    can_edit = False
    can_delete = True
    column_list = ['ma_hoa_don', 'hoc_vien', 'khoa_hoc', 'so_tien', 'trang_thai', 'ngay_tao', 'ngay_nop']
    column_filters = ['trang_thai', 'ngay_tao', 'hoc_vien.ho_va_ten']
    column_sortable_list = ['ngay_tao', 'so_tien', 'trang_thai']

    column_formatters = {
        'so_tien': format_tien_te,
        'trang_thai': format_trang_thai_hd
    }

    column_labels = dict(
        ma_hoa_don='Mã HĐ',
        hoc_vien='Học Viên',
        khoa_hoc='Khóa Học',
        so_tien='Số Tiền',
        trang_thai='Trạng Thái',
        ngay_tao='Ngày Tạo',
        ngay_nop='Ngày Thanh Toán',
        nhan_vien='Nhân Viên Thu'
    )


# ==============================================================================
# 4. DASHBOARD INDEX (TRANG CHỦ ADMIN)
# ==============================================================================


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or current_user.vai_tro != NguoiDungEnum.QUAN_LY:
            return redirect(url_for('login'))

        # --- NHÓM 1: TÀI CHÍNH ---
        # 1. Tổng doanh thu (Đã thu)
        tong_doanh_thu = db.session.query(func.sum(HoaDon.so_tien)).filter(
            HoaDon.trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN
        ).scalar() or 0

        # 2. Công nợ (Chưa thu) - Số lượng hóa đơn chưa thanh toán
        so_hoa_don_no = HoaDon.query.filter_by(trang_thai=TrangThaiHoaDonEnum.CHUA_THANH_TOAN).count()

        # --- NHÓM 2: CON NGƯỜI ---
        # 3. Số học viên
        so_hoc_vien = HocVien.query.count()
        # 4. Số giáo viên
        so_giao_vien = GiaoVien.query.count()
        # 5. Số nhân viên
        so_nhan_vien = NhanVien.query.count()

        # --- NHÓM 3: ĐÀO TẠO & CƠ SỞ VẬT CHẤT ---
        # 6. Khóa đang tuyển sinh
        khoa_dang_tuyen = KhoaHoc.query.filter_by(tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH).count()
        # 7. Lớp đang học (Đã chốt lớp, đang giảng dạy)
        lop_dang_hoc = KhoaHoc.query.filter_by(tinh_trang=TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH).count()
        # 8. Phòng học
        so_phong_hoc = PhongHoc.query.count()

        return self.render('admin/index.html', tong_doanh_thu="{:,.0f}".format(tong_doanh_thu).replace(",", "."),
                           so_hoa_don_no=so_hoa_don_no, so_hoc_vien=so_hoc_vien, so_giao_vien=so_giao_vien,
                           so_nhan_vien=so_nhan_vien, khoa_dang_tuyen=khoa_dang_tuyen, lop_dang_hoc=lop_dang_hoc,
                           so_phong_hoc=so_phong_hoc)


# ==============================================================================
# 5. KHỞI TẠO ADMIN & ADD VIEWS
# ==============================================================================

admin = Admin(app=app, name="Hệ Thống Quản Lý", index_view=MyAdminIndexView())

# Nhóm Người Dùng
admin.add_view(HocVienView(HocVien, db.session, name='Học Viên', category='Người Dùng'))
admin.add_view(GiaoVienView(GiaoVien, db.session, name='Giáo Viên', category='Người Dùng'))
admin.add_view(NhanVienView(NhanVien, db.session, name='Nhân Viên', category='Người Dùng'))
admin.add_view(QuanLyView(QuanLy, db.session, name='Quản Trị Viên', category='Người Dùng'))

# Nhóm Đào Tạo
admin.add_view(KhoaHocView(KhoaHoc, db.session, name='Danh Sách Khóa', category='Đào Tạo'))
admin.add_view(LoaiKhoaHocView(LoaiKhoaHoc, db.session, name='Loại Khóa', category='Đào Tạo'))
admin.add_view(PhongHocView(PhongHoc, db.session, name='Phòng Học', category='Đào Tạo'))

# Nhóm Tài Chính
admin.add_view(HoaDonView(HoaDon, db.session, name='Hóa Đơn', category='Tài Chính'))
