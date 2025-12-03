from datetime import datetime
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from eduapp import db, app


class NguoiDungEnum(RoleEnum):
    HOC_VIEN = 1
    QUAN_TRI = 2
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
    tinh_trang_xac_nhan_email = Column(Boolean, default=False)
    ngay_tao = Column(DateTime, default=datetime.now())
    vai_tro = Column(Enum(NguoiDungEnum), default=NguoiDungEnum.HOC_VIEN)
    anh_chan_dung = Column(String(100), default='images/avatar.png')

    def get_id(self):
        return self.ma_nguoi_dung


class NhanVien(NguoiDung):
    __tablename__ = "nhan_vien"
    nhung_hoa_don = relationship('HoaDon', backref='nhan_vien', lazy=True)


class QuanLy(NguoiDung):
    __tablename__ = "quan_ly"


class HocVien(NguoiDung):
    __tablename__ = "hoc_vien"
    so_dien_thoai_phu_huynh = Column(String(10))
    ngay_sinh = Column(DateTime, nullable=False)
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
        loai_kh_1 = LoaiKhoaHoc(
            ma_loai_khoa_hoc="LKH001",
            ten_loai_khoa_hoc="Tiếng Anh Giao Tiếp",
            hoc_phi=1500000.0
        )
        db.session.add(loai_kh_1)

        # 2. Tạo Người Dùng (Quản lý, Nhân viên, Giáo viên, Học viên)
        # Lưu ý: Mật khẩu ở đây đang để plain text để test, thực tế nên mã hóa (hash)

        # Quản trị viên
        admin = QuanLy(
            ma_nguoi_dung="ADMIN01",
            ten_dang_nhap="admin",
            mat_khau="123456",
            ho_va_ten="Nguyễn Quản Trị",
            email="admin@edu.com",
            so_dien_thoai="0901234567",
            vai_tro=NguoiDungEnum.QUAN_TRI
        )

        # Nhân viên
        nhan_vien = NhanVien(
            ma_nguoi_dung="NV001",
            ten_dang_nhap="nhanvien1",
            mat_khau="123456",
            ho_va_ten="Lê Nhân Viên",
            email="nv1@edu.com",
            so_dien_thoai="0901112223",
            vai_tro=NguoiDungEnum.NHAN_VIEN
        )

        # Giáo viên (cần năm kinh nghiệm)
        giao_vien = GiaoVien(
            ma_nguoi_dung="GV001",
            ten_dang_nhap="giaovien1",
            mat_khau="123456",
            ho_va_ten="Trần Thầy Giáo",
            email="gv1@edu.com",
            so_dien_thoai="0909888777",
            vai_tro=NguoiDungEnum.GIAO_VIEN,
            nam_kinh_nghiem=5
        )

        # Học viên (cần ngày sinh, sđt phụ huynh)
        hoc_vien = HocVien(
            ma_nguoi_dung="HV001",
            ten_dang_nhap="hocvien1",
            mat_khau="123456",
            ho_va_ten="Phạm Học Trò",
            email="hv1@edu.com",
            so_dien_thoai="0905555666",
            vai_tro=NguoiDungEnum.HOC_VIEN,
            ngay_sinh=datetime(2005, 5, 20),
            so_dien_thoai_phu_huynh="0905555888"
        )

        db.session.add_all([admin, nhan_vien, giao_vien, hoc_vien])
        db.session.commit()  # Commit user trước để lấy ID cho khóa học

        # 3. Tạo Khóa Học (Liên kết với Loại KH và Giáo viên)
        khoa_hoc = KhoaHoc(
            ma_khoa_hoc="KH001",
            ma_loai_khoa_hoc="LKH001",
            ma_giao_vien="GV001",
            si_so_hien_tai=1,
            si_so_toi_da=30,
            ngay_bat_dau=datetime(2023, 9, 1),
            ngay_ket_thuc=datetime(2023, 12, 1),
            tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
        )
        db.session.add(khoa_hoc)
        db.session.commit()  # Commit khóa học trước

        # 4. Tạo Lịch Học
        lich_hoc = LichHoc(
            ma_khoa_hoc="KH001",
            phong_hoc="P101",
            thu=TuanEnum.THU_HAI,
            ca_hoc=CaHocEnum.CA_SANG
        )
        db.session.add(lich_hoc)

        # 5. Tạo Bảng Điểm (Liên kết Khóa học và Học viên)
        bang_diem = BangDiem(
            ma_khoa_hoc="KH001",
            ma_hoc_vien="HV001",
            diem_giua_ky=8.5,
            diem_cuoi_ky=9.0,
            diem_chuyen_can=10.0,
            diem_trung_binh=9.0,
            ket_qua=True
        )
        db.session.add(bang_diem)

        # 6. Tạo Hóa Đơn (Liên kết Học viên, Khóa học, Nhân viên)
        hoa_don = HoaDon(
            so_tien=1500000.0,
            trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN,
            ma_hoc_vien="HV001",
            ma_khoa_hoc="KH001",
            ma_nhan_vien="NV001"
        )
        db.session.add(hoa_don)

        # Lưu tất cả vào DB
        db.session.commit()
        print("Đã thêm dữ liệu mẫu thành công!")
