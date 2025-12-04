from datetime import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from eduapp import db, app


class NguoiDungEnum(RoleEnum):
    HOC_VIEN = 1
    QUAN_LY = 2
    GIAO_VIEN = 3
    NHAN_VIEN = 4


class TuanEnum(RoleEnum):
    THU_HAI = 2
    THU_BA = 3
    THU_TU = 4
    THU_NAM = 5
    THU_SAU = 6
    THU_BAY = 7
    CHU_NHAT = 8


class CaHocEnum(RoleEnum):
    CA_SANG = 1
    CA_CHIEU = 2


class TinhTrangKhoaHocEnum(RoleEnum):
    DANG_TUYEN_SINH = 1
    DUNG_TUYEN_SINH = 2
    DA_KET_THUC = 3


class TrangThaiHoaDonEnum(RoleEnum):  # Mới thêm cho Hóa đơn
    CHUA_THANH_TOAN = 1
    DA_THANH_TOAN = 2


class NguoiDung(db.Model, UserMixin):
    __tablename__ = "nguoi_dung"
    __abstract__ = True
    ma_nguoi_dung = Column(String(20), primary_key=True)
    ten_dang_nhap = Column(String(100), nullable=False, unique=True)
    mat_khau = Column(String(100), nullable=False)
    ho_va_ten = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    so_dien_thoai = Column(String(10), nullable=False)
    tinh_trang_hoat_dong = Column(Boolean, default=True)
    ngay_tao = Column(DateTime, default=datetime.now())
    vai_tro = Column(Enum(NguoiDungEnum), default=NguoiDungEnum.HOC_VIEN)
    anh_chan_dung = Column(String(100), default='images/avatar.png')

    def get_id(self):
        return self.ma_nguoi_dung

    @property
    def ten_vai_tro(self):
        if self.vai_tro == NguoiDungEnum.HOC_VIEN:
            return 'học viên'
        elif self.vai_tro == NguoiDungEnum.GIAO_VIEN:
            return 'giáo viên'
        elif self.vai_tro == NguoiDungEnum.NHAN_VIEN:
            return 'nhân viên'
        return 'quản lý'


class NhanVien(NguoiDung):
    __tablename__ = "nhan_vien"
    nhung_hoa_don = relationship('HoaDon', backref='nhan_vien', lazy=True)


class QuanLy(NguoiDung):
    __tablename__ = "quan_ly"


class HocVien(NguoiDung):
    __tablename__ = "hoc_vien"
    so_dien_thoai_phu_huynh = Column(String(10))
    ngay_sinh = Column(DateTime, nullable=False)
    tinh_trang_xac_nhan_email = Column(Boolean, default=False)
    nhung_bang_diem = relationship('BangDiem', backref='hoc_vien', lazy=True)
    nhung_hoa_don = relationship('HoaDon', backref='hoc_vien', lazy=True)


class GiaoVien(NguoiDung):
    __tablename__ = "giao_vien"
    nam_kinh_nghiem = Column(Integer, nullable=False)
    nhung_khoa_hoc = relationship('KhoaHoc', backref='giao_vien', lazy=True)


class LoaiKhoaHoc(db.Model):
    __tablename__ = "loai_khoa_hoc"
    ma_loai_khoa_hoc = Column(String(10), primary_key=True)
    ten_loai_khoa_hoc = Column(String(50), nullable=False)
    hoc_phi = Column(Float, nullable=False)
    nhung_khoa_hoc = relationship('KhoaHoc', backref='loai_hoc', lazy=True)


class KhoaHoc(db.Model):
    __tablename__ = "khoa_hoc"
    ma_khoa_hoc = Column(String(20), primary_key=True)
    ma_loai_khoa_hoc = Column(String(10), ForeignKey(LoaiKhoaHoc.ma_loai_khoa_hoc), nullable=False)
    si_so_hien_tai = Column(Integer, default=0)
    si_so_toi_da = Column(Integer, nullable=False)
    ngay_bat_dau = Column(DateTime, default=datetime.now())
    ngay_ket_thuc = Column(DateTime, default=datetime.now())
    tinh_trang = Column(Enum(TinhTrangKhoaHocEnum), default=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH)
    ma_giao_vien = Column(String(20), ForeignKey(GiaoVien.ma_nguoi_dung), nullable=False)
    nhung_bang_diem = relationship('BangDiem', backref='khoa_hoc', lazy=True)
    lich_hoc = relationship('LichHoc', backref='khoa_hoc', lazy=True)
    nhung_hoa_don = relationship('HoaDon', backref='khoa_hoc', lazy=True)


class LichHoc(db.Model):
    __tablename__ = "lich_hoc"
    ma_lich_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey(KhoaHoc.ma_khoa_hoc), nullable=False)
    phong_hoc = Column(String(20), nullable=False)
    thu = Column(Enum(TuanEnum), nullable=False)
    ca_hoc = Column(Enum(CaHocEnum), nullable=False)


class BangDiem(db.Model):
    __tablename__ = "bang_diem"
    ma_khoa_hoc = Column(String(20), ForeignKey(KhoaHoc.ma_khoa_hoc), primary_key=True)
    ma_hoc_vien = Column(String(20), ForeignKey(HocVien.ma_nguoi_dung), primary_key=True)
    diem_giua_ky = Column(Float)
    diem_cuoi_ky = Column(Float)
    diem_chuyen_can = Column(Float)
    diem_trung_binh = Column(Float)
    ket_qua = Column(Boolean, default=False)


class HoaDon(db.Model):
    __tablename__ = "hoa_don"
    ma_hoa_don = Column(Integer, autoincrement=True, primary_key=True)
    ngay_nop = Column(DateTime, default=datetime.now())
    so_tien = Column(Float, nullable=False)
    trang_thai = Column(Enum(TrangThaiHoaDonEnum), default=TrangThaiHoaDonEnum.CHUA_THANH_TOAN)
    ma_hoc_vien = Column(String(20), ForeignKey(HocVien.ma_nguoi_dung), nullable=False)
    ma_khoa_hoc = Column(String(20), ForeignKey(KhoaHoc.ma_khoa_hoc), nullable=False)
    ma_nhan_vien = Column(String(20), ForeignKey(NhanVien.ma_nguoi_dung), nullable=False)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        quan_ly = QuanLy(
            ma_nguoi_dung="QL001",
            ten_dang_nhap="admin",
            mat_khau="123456",  # Lưu ý: Trong thực tế nên mã hóa mật khẩu (hash)
            ho_va_ten="Nguyễn Văn Quản Lý",
            email="admin@edu.com",
            so_dien_thoai="0909123456",
            vai_tro=NguoiDungEnum.QUAN_LY
        )

        # Nhân viên (Người thu tiền/tạo hóa đơn)
        nhan_vien = NhanVien(
            ma_nguoi_dung="NV001",
            ten_dang_nhap="nhanvien1",
            mat_khau="123456",
            ho_va_ten="Trần Thị Nhân Viên",
            email="nhanvien@edu.com",
            so_dien_thoai="0909111222",
            vai_tro=NguoiDungEnum.NHAN_VIEN
        )

        # Giáo viên
        giao_vien_1 = GiaoVien(
            ma_nguoi_dung="GV001",
            ten_dang_nhap="giaovien1",
            mat_khau="123456",
            ho_va_ten="Lê Thầy Giáo",
            email="gv1@edu.com",
            so_dien_thoai="0912333444",
            vai_tro=NguoiDungEnum.GIAO_VIEN,
            nam_kinh_nghiem=5
        )

        # Học viên
        hoc_vien_1 = HocVien(
            ma_nguoi_dung="HV001",
            ten_dang_nhap="hocvien1",
            mat_khau="123456",
            ho_va_ten="Phạm Em Học",
            email="hv1@edu.com",
            so_dien_thoai="0987654321",
            vai_tro=NguoiDungEnum.HOC_VIEN,
            so_dien_thoai_phu_huynh="0911222333",
            ngay_sinh=datetime(2005, 5, 20),
            tinh_trang_xac_nhan_email=True
        )

        db.session.add_all([quan_ly, nhan_vien, giao_vien_1, hoc_vien_1])
        db.session.commit()  # Commit để lấy ID cho các bước sau

        # --- 2. Tạo Loại Khóa Học ---
        loai_toeic = LoaiKhoaHoc(
            ma_loai_khoa_hoc="LKH01",
            ten_loai_khoa_hoc="Luyện thi TOEIC",
            hoc_phi=5000000.0
        )

        loai_ielts = LoaiKhoaHoc(
            ma_loai_khoa_hoc="LKH02",
            ten_loai_khoa_hoc="Luyện thi IELTS",
            hoc_phi=8000000.0
        )

        db.session.add_all([loai_toeic, loai_ielts])
        db.session.commit()

        # --- 3. Tạo Khóa Học ---
        khoa_hoc_1 = KhoaHoc(
            ma_khoa_hoc="TOEIC500",
            ma_loai_khoa_hoc="LKH01",
            si_so_hien_tai=1,
            si_so_toi_da=30,
            ngay_bat_dau=datetime(2023, 10, 1),
            ngay_ket_thuc=datetime(2024, 1, 1),
            tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH,
            ma_giao_vien="GV001"  # Foreign Key trỏ tới Giáo viên 1
        )

        db.session.add(khoa_hoc_1)
        db.session.commit()

        # --- 4. Tạo Lịch Học ---
        # Lớp học này học Thứ 2 và Thứ 4
        lich_hoc_1 = LichHoc(
            ma_khoa_hoc="TOEIC500",
            phong_hoc="P101",
            thu=TuanEnum.THU_HAI,
            ca_hoc=CaHocEnum.CA_SANG
        )

        lich_hoc_2 = LichHoc(
            ma_khoa_hoc="TOEIC500",
            phong_hoc="P101",
            thu=TuanEnum.THU_TU,
            ca_hoc=CaHocEnum.CA_SANG
        )

        db.session.add_all([lich_hoc_1, lich_hoc_2])

        # --- 5. Tạo Bảng Điểm (Đăng ký học viên vào lớp) ---
        bang_diem = BangDiem(
            ma_khoa_hoc="TOEIC500",
            ma_hoc_vien="HV001",
            diem_giua_ky=7.5,
            diem_cuoi_ky=8.0,
            diem_chuyen_can=10.0,
            diem_trung_binh=8.2,
            ket_qua=True
        )

        db.session.add(bang_diem)

        # --- 6. Tạo Hóa Đơn ---
        hoa_don = HoaDon(
            so_tien=5000000.0,
            trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN,
            ma_hoc_vien="HV001",
            ma_khoa_hoc="TOEIC500",
            ma_nhan_vien="NV001",  # Nhân viên NV001 lập hóa đơn này
            ngay_nop=datetime.now()
        )

        db.session.add(hoa_don)

        # Lưu tất cả vào database
        db.session.commit()
        print("Đã tạo dữ liệu mẫu thành công!")
