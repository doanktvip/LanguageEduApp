import random
from datetime import datetime, timedelta
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum, UniqueConstraint, Text
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import relationship
from eduapp import db, app


# ==========================================
# 1. CÁC ENUM (ĐỊNH NGHĨA HẰNG SỐ)
# ==========================================

class NguoiDungEnum(RoleEnum):
    HOC_VIEN = 1
    QUAN_LY = 2
    GIAO_VIEN = 3
    NHAN_VIEN = 4


class TuanEnum(RoleEnum):
    THU_HAI = 0
    THU_BA = 1
    THU_TU = 2
    THU_NAM = 3
    THU_SAU = 4
    THU_BAY = 5
    CHU_NHAT = 6


class CaHocEnum(RoleEnum):
    CA_SANG = 1
    CA_CHIEU = 2


class TinhTrangKhoaHocEnum(RoleEnum):
    DANG_TUYEN_SINH = 1
    DUNG_TUYEN_SINH = 2
    DA_KET_THUC = 3


class TrangThaiHoaDonEnum(RoleEnum):
    CHUA_THANH_TOAN = 1
    DA_THANH_TOAN = 2


class TrangThaiDiemDanhEnum(RoleEnum):
    CO_MAT = 1
    VANG_CO_PHEP = 2
    VANG_KHONG_PHEP = 3


# ==========================================
# 2. HỆ THỐNG NGƯỜI DÙNG (POLYMORPHISM)
# ==========================================

class NguoiDung(db.Model, UserMixin):
    __tablename__ = "nguoi_dung"

    ma_nguoi_dung = Column(String(20), primary_key=True)
    ten_dang_nhap = Column(String(100), nullable=False, unique=True)
    mat_khau = Column(String(100), nullable=False)
    ho_va_ten = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    so_dien_thoai = Column(String(10), nullable=False)
    tinh_trang_hoat_dong = Column(Boolean, default=True)
    ngay_tao = Column(DateTime, default=datetime.now())
    anh_chan_dung = Column(String(255),
                           default='https://res.cloudinary.com/db4bjqp4f/image/upload/v1765436438/shtnr60mecp057e2uctk.jpg')

    # Cấu hình đa hình
    vai_tro = Column(Enum(NguoiDungEnum), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': vai_tro
    }

    def __str__(self):
        return self.ho_va_ten

    def get_id(self):
        return self.ma_nguoi_dung

    @classmethod
    def tao_ma_nguoi_dung(cls, vai_tro_enum):
        prefix_map = {
            NguoiDungEnum.HOC_VIEN: "HV",
            NguoiDungEnum.GIAO_VIEN: "GV",
            NguoiDungEnum.NHAN_VIEN: "NV",
            NguoiDungEnum.QUAN_LY: "QL"
        }
        prefix = prefix_map.get(vai_tro_enum, "ND")
        current_year = datetime.now().strftime('%y')
        last_user = db.session.query(NguoiDung.ma_nguoi_dung).filter(
            NguoiDung.ma_nguoi_dung.like(f"{prefix}{current_year}%")).order_by(NguoiDung.ma_nguoi_dung.desc()).first()
        if last_user:
            try:
                last_sequence = int(last_user[0][4:])
                new_sequence = last_sequence + 1
            except ValueError:
                new_sequence = 1
        else:
            new_sequence = 1
        return f"{prefix}{current_year}{new_sequence:04d}"


class QuanLy(NguoiDung):
    __tablename__ = "quan_ly"
    ma_pin = Column(String(50), default='e10adc3949ba59abbe56e057f20f883e')
    ma_nguoi_dung = Column(String(20), ForeignKey('nguoi_dung.ma_nguoi_dung'), primary_key=True)
    __mapper_args__ = {'polymorphic_identity': NguoiDungEnum.QUAN_LY}


class NhanVien(NguoiDung):
    __tablename__ = "nhan_vien"
    ma_nguoi_dung = Column(String(20), ForeignKey('nguoi_dung.ma_nguoi_dung'), primary_key=True)
    nhung_hoa_don = relationship('HoaDon', backref='nhan_vien', lazy=True)
    __mapper_args__ = {'polymorphic_identity': NguoiDungEnum.NHAN_VIEN}


class GiaoVien(NguoiDung):
    __tablename__ = "giao_vien"
    ma_nguoi_dung = Column(String(20), ForeignKey('nguoi_dung.ma_nguoi_dung'), primary_key=True)
    nam_kinh_nghiem = Column(Integer, default=0)
    nhung_khoa_hoc = relationship('KhoaHoc', backref='giao_vien', lazy=True)
    __mapper_args__ = {'polymorphic_identity': NguoiDungEnum.GIAO_VIEN}


class HocVien(NguoiDung):
    __tablename__ = "hoc_vien"
    ma_nguoi_dung = Column(String(20), ForeignKey('nguoi_dung.ma_nguoi_dung'), primary_key=True)
    so_dien_thoai_phu_huynh = Column(String(10))
    tinh_trang_xac_nhan_email = Column(Boolean, default=False)
    ngay_sinh = Column(DateTime)

    # Quan hệ
    ds_lop_hoc = relationship('BangDiem', backref='hoc_vien', lazy=True, cascade="all, delete-orphan")
    nhung_hoa_don = relationship('HoaDon', backref='hoc_vien', lazy=True, cascade="all, delete-orphan")
    nhung_lan_diem_danh = relationship('ChiTietDiemDanh', backref='hoc_vien', lazy=True, cascade="all, delete-orphan")

    __mapper_args__ = {'polymorphic_identity': NguoiDungEnum.HOC_VIEN}


# ==========================================
# 3. QUẢN LÝ KHÓA HỌC & LỊCH HỌC
# ==========================================

class LoaiKhoaHoc(db.Model):
    __tablename__ = "loai_khoa_hoc"
    ma_loai_khoa_hoc = Column(String(10), primary_key=True)
    ten_loai_khoa_hoc = Column(String(50), nullable=False)
    hoc_phi = Column(Float, nullable=False)
    mo_ta = Column(Text)
    nhung_khoa_hoc = relationship('KhoaHoc', backref='loai_khoa_hoc', lazy=True)

    def __str__(self):
        return self.ten_loai_khoa_hoc


class KhoaHoc(db.Model):
    __tablename__ = "khoa_hoc"
    ma_khoa_hoc = Column(String(20), primary_key=True)
    ten_khoa_hoc = Column(String(100), nullable=False)

    # Khóa ngoại
    ma_loai_khoa_hoc = Column(String(10), ForeignKey('loai_khoa_hoc.ma_loai_khoa_hoc'), nullable=False)
    ma_giao_vien = Column(String(20), ForeignKey('giao_vien.ma_nguoi_dung'), nullable=False)

    # Thông tin lớp
    si_so_hien_tai = Column(Integer, default=0)
    si_so_toi_da = Column(Integer, nullable=False)
    ngay_bat_dau = Column(DateTime, nullable=False)
    ngay_ket_thuc = Column(DateTime, nullable=False)
    tinh_trang = Column(Enum(TinhTrangKhoaHocEnum), default=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH)
    hoc_phi = Column(Float, nullable=False, default=0.0)

    # Quan hệ
    ds_dang_ky = relationship('BangDiem', backref='khoa_hoc', lazy=True, cascade="all, delete-orphan")
    lich_hoc = relationship('LichHoc', backref='khoa_hoc', lazy=True, cascade="all, delete-orphan")
    nhung_hoa_don = relationship('HoaDon', backref='khoa_hoc', lazy=True, cascade="all, delete-orphan")
    ds_diem_danh = relationship('DiemDanh', backref='khoa_hoc', lazy=True, cascade="all, delete-orphan")
    cau_truc_diem = relationship('CauTrucDiem', backref='khoa_hoc', lazy=True, cascade="all, delete-orphan")

    # Proxy: Giúp gọi khoa_hoc.ds_hoc_vien trực tiếp
    ds_hoc_vien = association_proxy('ds_dang_ky', 'hoc_vien')

    def __str__(self):
        return self.ten_khoa_hoc

    # Trong class KhoaHoc (models.py)
    @classmethod
    def tao_ma_khoa_hoc_moi(cls, ma_loai):
        prefix = ma_loai.upper()
        last_course = cls.query.filter(cls.ma_khoa_hoc.like(f"{prefix}%")).order_by(cls.ma_khoa_hoc.desc()).first()
        if last_course:
            last_number = int(last_course.ma_khoa_hoc[len(prefix):])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"{prefix}{new_number:03d}"

    def lay_danh_sach_tuan_hoc(self):
        tuan_map = {}
        days_to_subtract = self.ngay_bat_dau.weekday()
        start_date = self.ngay_bat_dau - timedelta(days=days_to_subtract)
        days_to_add = 6 - self.ngay_ket_thuc.weekday()
        end_date = self.ngay_ket_thuc + timedelta(days=days_to_add)
        current_date = start_date
        while current_date <= end_date:
            nam_iso, tuan_iso, _ = current_date.isocalendar()
            key = (nam_iso, tuan_iso)
            if key not in tuan_map:
                tuan_map[key] = {
                    "week": tuan_iso,
                    "year": nam_iso,
                    "days": [],
                    "schedule": {
                        "CA_SANG": [None] * 7,
                        "CA_CHIEU": [None] * 7,
                    }
                }
            tuan_map[key]["days"].append(current_date.strftime("%d/%m"))
            if self.ngay_bat_dau.date() <= current_date.date() <= self.ngay_ket_thuc.date():
                weekday = current_date.weekday()
                for lh in self.lich_hoc:
                    if lh.thu.value == weekday:
                        ca_key = lh.ca_hoc.name
                        if ca_key in tuan_map[key]["schedule"]:
                            tuan_map[key]["schedule"][ca_key][weekday] = lh
            current_date += timedelta(days=1)
        return list(tuan_map.values())

    def to_dict_tuyen_sinh(self):
        return {
            'Mã khóa học': self.ma_khoa_hoc,
            'Tên khóa học': self.ten_khoa_hoc,
            'Giáo viên': self.giao_vien.ho_va_ten if self.giao_vien else "Chưa phân công",
            'Sĩ số còn lại': f'{self.si_so_toi_da - self.si_so_hien_tai}',
            'Ngày bắt đầu': self.ngay_bat_dau.strftime('%d/%m/%Y'),
            'Ngày kết thúc': self.ngay_ket_thuc.strftime('%d/%m/%Y')
        }

    @staticmethod
    def chuyen_danh_sach_sang_dict(danh_sach_khoa_hoc):
        ket_qua = {}
        if danh_sach_khoa_hoc:
            for index, khoa_hoc in enumerate(danh_sach_khoa_hoc):
                ket_qua[index] = khoa_hoc.to_dict_tuyen_sinh()
        return ket_qua

    def cap_nhat_tinh_trang_tu_dong(self):
        today = datetime.now().date()
        ngay_bd = self.ngay_bat_dau.date()
        ngay_kt = self.ngay_ket_thuc.date()
        if today < ngay_bd:
            self.tinh_trang = TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
        elif ngay_bd <= today <= ngay_kt:
            self.tinh_trang = TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH
        else:
            self.tinh_trang = TinhTrangKhoaHocEnum.DA_KET_THUC
        return self.tinh_trang


class PhongHoc(db.Model):
    __tablename__ = "phong_hoc"
    ma_phong_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ten_phong_hoc = Column(String(20), nullable=False)
    nhung_lich_hoc = relationship('LichHoc', backref='phong_hoc', lazy=True)

    def __str__(self):
        return self.ten_phong_hoc


class LichHoc(db.Model):
    __tablename__ = "lich_hoc"
    ma_lich_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ma_phong_hoc = Column(Integer, ForeignKey('phong_hoc.ma_phong_hoc'), nullable=False)
    thu = Column(Enum(TuanEnum), nullable=False)
    ca_hoc = Column(Enum(CaHocEnum), nullable=False)

    def thoi_gian_theo_ca(self):
        if self.ca_hoc == CaHocEnum.CA_SANG:
            return 7, 11
        return 13, 17


# ==========================================
# 4. HỆ THỐNG ĐIỂM DANH (ATTENDANCE)
# ==========================================

class DiemDanh(db.Model):
    """Đại diện cho 1 buổi học cụ thể"""
    __tablename__ = "diem_danh"
    id = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ngay_diem_danh = Column(DateTime, default=datetime.now())
    ca_diem_danh = Column(Enum(CaHocEnum), nullable=False)

    # Chi tiết: Buổi này ai đi, ai vắng
    chi_tiet = relationship('ChiTietDiemDanh', backref='buoi_diem_danh', lazy=True, cascade="all, delete-orphan")


class ChiTietDiemDanh(db.Model):
    """Trạng thái của 1 học viên trong 1 buổi học"""
    __tablename__ = "chi_tiet_diem_danh"
    ma_diem_danh = Column(Integer, ForeignKey('diem_danh.id'), primary_key=True)
    ma_hoc_vien = Column(String(20), ForeignKey('hoc_vien.ma_nguoi_dung'), primary_key=True)
    trang_thai = Column(Enum(TrangThaiDiemDanhEnum), default=TrangThaiDiemDanhEnum.CO_MAT)


# ==========================================
# 5. HỆ THỐNG ĐIỂM ĐỘNG (DYNAMIC GRADING)
# ==========================================

class CauTrucDiem(db.Model):
    """Định nghĩa cột điểm cho khóa học (VD: Giữa kỳ 30%)"""
    __tablename__ = "cau_truc_diem"
    id = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ten_loai_diem = Column(String(100), nullable=False)
    trong_so = Column(Float, nullable=False)  # VD: 0.3

    ds_diem_chi_tiet = relationship('ChiTietDiem', backref='cau_truc_diem', lazy=True, cascade="all, delete-orphan")


class BangDiem(db.Model):
    """
    Bảng Enrollment (Đăng ký học) & Tổng kết điểm.
    Kết nối N-N giữa HocVien và KhoaHoc.
    """
    __tablename__ = "bang_diem"
    id = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ma_hoc_vien = Column(String(20), ForeignKey('hoc_vien.ma_nguoi_dung'), nullable=False)

    # Kết quả tổng kết (Được tính toán từ bảng ChiTietDiem)
    diem_trung_binh = Column(Float, nullable=True)
    xep_loai = Column(String(20))
    ket_qua = Column(Boolean, default=False)

    ds_diem_thanh_phan = relationship('ChiTietDiem', backref='bang_diem', lazy=True, cascade="all, delete-orphan")

    # Ràng buộc: 1 Học viên chỉ có 1 Bảng điểm trong 1 Khóa học
    __table_args__ = (UniqueConstraint('ma_khoa_hoc', 'ma_hoc_vien', name='_enrollment_uc'),)

    def lay_chi_tiet_diem(self, list_cau_truc_diem):
        bang_diem = {}
        for ct in list_cau_truc_diem:
            bang_diem[ct.ten_loai_diem] = [None, ct.trong_so, False]
        for chi_tiet in self.ds_diem_thanh_phan:
            ten_loai = chi_tiet.cau_truc_diem.ten_loai_diem
            if ten_loai in bang_diem:
                bang_diem[ten_loai][0] = chi_tiet.gia_tri_diem
                bang_diem[ten_loai][2] = chi_tiet.ban_nhap
        bang_diem['Tổng kết'] = [self.diem_trung_binh, None, False]
        bang_diem['Kết quả'] = [self.ket_qua, None, False]

        return bang_diem

    def cap_nhat_tong_ket(self):
        tong_diem = 0
        for chi_tiet in self.ds_diem_thanh_phan:
            trong_so = chi_tiet.cau_truc_diem.trong_so
            tong_diem += chi_tiet.gia_tri_diem * trong_so
        tong_trong_so_chuan = 1.0
        self.diem_trung_binh = round(tong_diem / tong_trong_so_chuan, 2)
        self.ket_qua = self.diem_trung_binh >= 5.0


class ChiTietDiem(db.Model):
    """Lưu giá trị điểm thực tế (VD: 8.5)"""
    __tablename__ = "chi_tiet_diem"
    id = Column(Integer, autoincrement=True, primary_key=True)
    ma_bang_diem = Column(Integer, ForeignKey('bang_diem.id'), nullable=False)
    ma_cau_truc_diem = Column(Integer, ForeignKey('cau_truc_diem.id'), nullable=False)

    gia_tri_diem = Column(Float, nullable=False)
    ngay_nhap = Column(DateTime, default=datetime.now())
    ban_nhap = Column(Boolean, default=False)


# ==========================================
# 6. TÀI CHÍNH
# ==========================================

class HoaDon(db.Model):
    __tablename__ = "hoa_don"
    ma_hoa_don = Column(Integer, autoincrement=True, primary_key=True)
    ngay_tao = Column(DateTime, default=datetime.now())
    ngay_han = Column(DateTime, nullable=True)
    ngay_nop = Column(DateTime, nullable=True)
    so_tien = Column(Float, nullable=False)
    trang_thai = Column(Enum(TrangThaiHoaDonEnum), default=TrangThaiHoaDonEnum.CHUA_THANH_TOAN)

    ma_hoc_vien = Column(String(20), ForeignKey('hoc_vien.ma_nguoi_dung'), nullable=False)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ma_nhan_vien = Column(String(20), ForeignKey('nhan_vien.ma_nguoi_dung'), nullable=True)

    def __init__(self, **kwargs):
        super(HoaDon, self).__init__(**kwargs)
        if self.ngay_han is None:
            self.tu_dong_tinh_ngay_han()

    def tu_dong_tinh_ngay_han(self):
        if self.ma_khoa_hoc:
            kh = db.session.get(KhoaHoc, self.ma_khoa_hoc)

            if kh:
                self.ngay_han = kh.ngay_bat_dau + timedelta(days=10)
            else:
                self.ngay_han = datetime.now() + timedelta(days=30)

    def to_dict(self):
        return {
            'Mã khóa học': self.ma_khoa_hoc,
            'Số tiền': self.so_tien,
            'Trạng thái': self.trang_thai.value
        }

    @staticmethod
    def chuyen_danh_sach_sang_dict(danh_sach_hoa_don):
        ket_qua = {}
        if danh_sach_hoa_don:
            for index, hoa_don in enumerate(danh_sach_hoa_don):
                ket_qua[index] = hoa_don.to_dict()
        return ket_qua


def tao_du_lieu_mau():
    print("--- BẮT ĐẦU TẠO DỮ LIỆU MẪU (NÂNG CAO) ---")

    # 0. RESET DATABASE
    db.drop_all()
    db.create_all()

    mat_khau_chung = "202cb962ac59075b964b07152d234b70"  # password: 123
    today = datetime.now()

    # ==========================================
    # 1. DỮ LIỆU CỐ ĐỊNH (THEO YÊU CẦU)
    # ==========================================
    loai_khoa_hocs = [
        LoaiKhoaHoc(
            ma_loai_khoa_hoc="ENG-BEG",
            ten_loai_khoa_hoc="Tiếng Anh Beginner",
            hoc_phi=3000000,
            mo_ta="""
            <p><strong>Khóa học dành cho người mất gốc:</strong></p>
            <ul>
                <li>Hệ thống lại toàn bộ ngữ pháp nền tảng.</li>
                <li>Luyện chuẩn phát âm theo bảng IPA.</li>
                <li>Xây dựng vốn từ vựng cơ bản thông dụng.</li>
            </ul>
            """
        ),
        LoaiKhoaHoc(
            ma_loai_khoa_hoc="ENG-INT",
            ten_loai_khoa_hoc="Tiếng Anh Intermediate",
            hoc_phi=4500000,
            mo_ta="""
            <p><strong>Tập trung vào Giao tiếp phản xạ:</strong></p>
            <ul>
                <li>Thực hành hội thoại theo chủ đề công sở và đời sống.</li>
                <li>Cải thiện kỹ năng Nghe - Nói tự nhiên.</li>
                <li>Tăng cường sự tự tin khi giao tiếp với người nước ngoài.</li>
            </ul>
            """
        ),
        LoaiKhoaHoc(
            ma_loai_khoa_hoc="ENG-ADV",
            ten_loai_khoa_hoc="Tiếng Anh Advanced",
            hoc_phi=6000000,
            mo_ta="""
            <p><strong>Luyện thi chứng chỉ quốc tế (IELTS/TOEIC):</strong></p>
            <ul>
                <li>Trang bị chiến thuật làm bài thi hiệu quả.</li>
                <li>Nâng cao toàn diện 4 kỹ năng: Nghe, Nói, Đọc, Viết.</li>
                <li>Luyện đề chuyên sâu và giải đáp thắc mắc chi tiết.</li>
            </ul>
            """
        )
    ]
    phong_hoc1 = PhongHoc(ten_phong_hoc="P101")
    phong_hoc2 = PhongHoc(ten_phong_hoc="P102")
    phong_hoc3 = PhongHoc(ten_phong_hoc="P103")

    # Lưu vào DB để lấy ID dùng cho các bước sau
    db.session.add_all(loai_khoa_hocs + [phong_hoc1, phong_hoc2, phong_hoc3])
    db.session.commit()

    # ==========================================
    # 2. TẠO NHÂN SỰ VÀ HỌC VIÊN
    # ==========================================
    # --- Quản trị & Nhân viên ---
    admin = QuanLy(
        ma_nguoi_dung=NguoiDung.tao_ma_nguoi_dung(NguoiDungEnum.QUAN_LY),
        ten_dang_nhap="admin", mat_khau=mat_khau_chung, ho_va_ten="Super Admin",
        email="admin@edu.vn", so_dien_thoai="0909000000", vai_tro=NguoiDungEnum.QUAN_LY
    )
    nv1 = NhanVien(
        ma_nguoi_dung=NguoiDung.tao_ma_nguoi_dung(NguoiDungEnum.NHAN_VIEN),
        ten_dang_nhap="staff", mat_khau=mat_khau_chung, ho_va_ten="Nguyễn Thu Ngân",
        email="staff@edu.vn", so_dien_thoai="0909000001", vai_tro=NguoiDungEnum.NHAN_VIEN
    )

    # --- Giáo viên (2 người) ---
    gv1 = GiaoVien(
        ma_nguoi_dung=NguoiDung.tao_ma_nguoi_dung(NguoiDungEnum.GIAO_VIEN),
        ten_dang_nhap="teacher1", mat_khau=mat_khau_chung, ho_va_ten="Thầy John Smith",
        email="john@edu.vn", so_dien_thoai="0909000002", vai_tro=NguoiDungEnum.GIAO_VIEN, nam_kinh_nghiem=10
    )
    db.session.add(gv1);
    db.session.commit()  # Commit để lấy mã cho GV tiếp theo

    gv2 = GiaoVien(
        ma_nguoi_dung=NguoiDung.tao_ma_nguoi_dung(NguoiDungEnum.GIAO_VIEN),
        ten_dang_nhap="teacher2", mat_khau=mat_khau_chung, ho_va_ten="Cô Mary Jane",
        email="mary@edu.vn", so_dien_thoai="0909000003", vai_tro=NguoiDungEnum.GIAO_VIEN, nam_kinh_nghiem=5
    )

    # --- Học viên (6 người với các profile khác nhau) ---
    ds_hv_info = [
        ("hv_gioi", "Lê Văn Giỏi", "gioi@edu.vn"),  # Luôn đi học, điểm cao
        ("hv_kha", "Nguyễn Thị Khá", "kha@edu.vn"),  # Học đều
        ("hv_tb", "Trần Trung Bình", "tb@edu.vn"),  # Sức học bình thường
        ("hv_yeu", "Phạm Văn Yếu", "yeu@edu.vn"),  # Hay rớt môn
        ("hv_cup", "Lê Hay Cúp", "cup@edu.vn"),  # Vắng không phép nhiều
        ("hv_moi", "Vũ Văn Mới", "moi@edu.vn")  # Mới đăng ký
    ]

    ds_hoc_vien = []
    for user, ten, mail in ds_hv_info:
        hv = HocVien(
            ma_nguoi_dung=NguoiDung.tao_ma_nguoi_dung(NguoiDungEnum.HOC_VIEN),
            ten_dang_nhap=user, mat_khau=mat_khau_chung, ho_va_ten=ten, email=mail,
            so_dien_thoai="0900000000", vai_tro=NguoiDungEnum.HOC_VIEN, ngay_sinh=datetime(2003, 1, 1)
        )
        db.session.add(hv)
        db.session.commit()  # Commit từng người để mã tăng dần
        ds_hoc_vien.append(hv)

    db.session.add_all([admin, nv1, gv2])
    db.session.commit()

    # Helper function: Tự động tạo điểm danh cho khóa học
    def tao_du_lieu_diem_danh_tu_dong(khoa_hoc, danh_sach_hoc_vien_lop):
        """
        Duyệt từ ngày bắt đầu đến ngày kết thúc (hoặc hôm nay).
        Nếu ngày đó trúng lịch học -> Tạo Điểm danh -> Tạo Chi tiết điểm danh cho từng HV.
        """
        ngay_chay = khoa_hoc.ngay_bat_dau
        # Nếu khóa học chưa kết thúc, chỉ điểm danh tới hôm nay
        ngay_ket_thuc_thuc_te = min(khoa_hoc.ngay_ket_thuc, datetime.now())

        lich_hoc_map = {}  # Key: weekday (0-6), Value: LichHoc obj
        for lh in khoa_hoc.lich_hoc:
            lich_hoc_map[lh.thu.value] = lh

        while ngay_chay <= ngay_ket_thuc_thuc_te:
            weekday = ngay_chay.weekday()
            if weekday in lich_hoc_map:
                lich = lich_hoc_map[weekday]

                # Tạo buổi điểm danh
                dd = DiemDanh(
                    ma_khoa_hoc=khoa_hoc.ma_khoa_hoc,
                    ngay_diem_danh=ngay_chay,  # Giờ cụ thể có thể random trong ca
                    ca_diem_danh=lich.ca_hoc
                )
                db.session.add(dd)
                db.session.commit()  # Để lấy dd.id

                # Tạo chi tiết cho từng học viên
                for hv in danh_sach_hoc_vien_lop:
                    # Random trạng thái: 80% Có mặt, 10% Có phép, 10% Không phép
                    rand = random.random()
                    trang_thai = TrangThaiDiemDanhEnum.CO_MAT

                    # Logic riêng cho học viên "Lê Hay Cúp" (index 4)
                    if hv.email == "cup@edu.vn":
                        trang_thai = TrangThaiDiemDanhEnum.VANG_KHONG_PHEP if rand > 0.3 else TrangThaiDiemDanhEnum.CO_MAT
                    else:
                        if rand > 0.95:
                            trang_thai = TrangThaiDiemDanhEnum.VANG_KHONG_PHEP
                        elif rand > 0.90:
                            trang_thai = TrangThaiDiemDanhEnum.VANG_CO_PHEP

                    ct = ChiTietDiemDanh(
                        ma_diem_danh=dd.id,
                        ma_hoc_vien=hv.ma_nguoi_dung,
                        trang_thai=trang_thai
                    )
                    db.session.add(ct)

            ngay_chay += timedelta(days=1)
        db.session.commit()

    # ==========================================
    # 3. KỊCH BẢN KHÓA HỌC
    # ==========================================

    # --- KỊCH BẢN 1: KHÓA ĐÃ KẾT THÚC (Hoàn tất điểm, đóng tiền xong) ---
    # ENG-BEG, GV1, 2-4-6 Sáng
    kh1 = KhoaHoc(
        ma_khoa_hoc=KhoaHoc.tao_ma_khoa_hoc_moi("ENG-BEG"),
        ten_khoa_hoc="Tiếng Anh Sơ Cấp K1 (Đã Xong)",
        ma_loai_khoa_hoc="ENG-BEG", ma_giao_vien=gv1.ma_nguoi_dung,
        si_so_toi_da=10, hoc_phi=3000000,
        ngay_bat_dau=today - timedelta(days=100),
        ngay_ket_thuc=today - timedelta(days=10),
        tinh_trang=TinhTrangKhoaHocEnum.DA_KET_THUC
    )
    db.session.add(kh1);
    db.session.commit()

    # Lịch học K1
    for thu in [TuanEnum.THU_HAI, TuanEnum.THU_TU, TuanEnum.THU_SAU]:
        db.session.add(LichHoc(ma_khoa_hoc=kh1.ma_khoa_hoc, ma_phong_hoc=phong_hoc1.ma_phong_hoc, thu=thu,
                               ca_hoc=CaHocEnum.CA_SANG))

    # Cấu trúc điểm K1
    ct1_gk = CauTrucDiem(ma_khoa_hoc=kh1.ma_khoa_hoc, ten_loai_diem="Giữa kỳ", trong_so=0.4)
    ct1_ck = CauTrucDiem(ma_khoa_hoc=kh1.ma_khoa_hoc, ten_loai_diem="Cuối kỳ", trong_so=0.6)
    db.session.add_all([ct1_gk, ct1_ck]);
    db.session.commit()

    # Đăng ký K1: Học viên Giỏi, Khá, Yếu
    lop_k1 = [ds_hoc_vien[0], ds_hoc_vien[1], ds_hoc_vien[3]]
    diem_k1 = [(9.0, 9.5), (7.5, 8.0), (4.0, 4.5)]  # (Giữa kỳ, Cuối kỳ)

    for i, hv in enumerate(lop_k1):
        # BangDiem
        bd = BangDiem(ma_khoa_hoc=kh1.ma_khoa_hoc, ma_hoc_vien=hv.ma_nguoi_dung)
        db.session.add(bd)
        db.session.commit()
        kh1.si_so_hien_tai += 1

        # Hóa đơn (Đã thanh toán)
        hd = HoaDon(ma_khoa_hoc=kh1.ma_khoa_hoc, ma_hoc_vien=hv.ma_nguoi_dung, so_tien=3000000,
                    trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN, ma_nhan_vien=nv1.ma_nguoi_dung,
                    ngay_nop=kh1.ngay_bat_dau)
        db.session.add(hd)

        # Nhập điểm (ĐÃ CHỐT -> ban_nhap = False (0))
        d_gk, d_ck = diem_k1[i]
        db.session.add(ChiTietDiem(ma_bang_diem=bd.id, ma_cau_truc_diem=ct1_gk.id, gia_tri_diem=d_gk, ban_nhap=False))
        db.session.add(ChiTietDiem(ma_bang_diem=bd.id, ma_cau_truc_diem=ct1_ck.id, gia_tri_diem=d_ck, ban_nhap=False))

        # Tính toán tổng kết
        bd.cap_nhat_tong_ket()

    # Tự động sinh điểm danh K1
    tao_du_lieu_diem_danh_tu_dong(kh1, lop_k1)

    # --- KỊCH BẢN 2: KHÓA ĐANG HỌC (Điểm danh dở dang, Điểm chưa chốt hết) ---
    # ENG-INT, GV2, 3-5-7 Chiều
    kh2 = KhoaHoc(
        ma_khoa_hoc=KhoaHoc.tao_ma_khoa_hoc_moi("ENG-INT"),
        ten_khoa_hoc="Tiếng Anh Trung Cấp K2 (Đang Học)",
        ma_loai_khoa_hoc="ENG-INT", ma_giao_vien=gv2.ma_nguoi_dung,
        si_so_toi_da=15, hoc_phi=4500000,
        ngay_bat_dau=today - timedelta(days=30),
        ngay_ket_thuc=today + timedelta(days=30),
        tinh_trang=TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH
    )
    db.session.add(kh2);
    db.session.commit()

    # Lịch học K2
    for thu in [TuanEnum.THU_BA, TuanEnum.THU_NAM, TuanEnum.THU_BAY]:
        db.session.add(LichHoc(ma_khoa_hoc=kh2.ma_khoa_hoc, ma_phong_hoc=phong_hoc2.ma_phong_hoc, thu=thu,
                               ca_hoc=CaHocEnum.CA_CHIEU))

    # Cấu trúc điểm K2
    ct2_gk = CauTrucDiem(ma_khoa_hoc=kh2.ma_khoa_hoc, ten_loai_diem="Mid-term Speaking", trong_so=0.3)
    ct2_ck = CauTrucDiem(ma_khoa_hoc=kh2.ma_khoa_hoc, ten_loai_diem="Final Test", trong_so=0.7)
    db.session.add_all([ct2_gk, ct2_ck]);
    db.session.commit()

    # Đăng ký K2: TB, Hay Cúp, và Giỏi (học tiếp lên)
    lop_k2 = [ds_hoc_vien[2], ds_hoc_vien[4], ds_hoc_vien[0]]

    for i, hv in enumerate(lop_k2):
        bd = BangDiem(ma_khoa_hoc=kh2.ma_khoa_hoc, ma_hoc_vien=hv.ma_nguoi_dung)
        db.session.add(bd);
        db.session.commit()
        kh2.si_so_hien_tai += 1

        # Hóa đơn: Giỏi đóng rồi, Hay Cúp nợ tiền
        status_hd = TrangThaiHoaDonEnum.DA_THANH_TOAN if i != 1 else TrangThaiHoaDonEnum.CHUA_THANH_TOAN
        hd = HoaDon(ma_khoa_hoc=kh2.ma_khoa_hoc, ma_hoc_vien=hv.ma_nguoi_dung, so_tien=4500000, trang_thai=status_hd)
        if status_hd == TrangThaiHoaDonEnum.CHUA_THANH_TOAN:
            hd.ngay_han = today - timedelta(days=5)  # Nợ quá hạn
        else:
            hd.ma_nhan_vien = nv1.ma_nguoi_dung
            hd.ngay_nop = today - timedelta(days=15)
        db.session.add(hd)

        # Nhập điểm: Giữa kỳ ĐÃ CHỐT (0), Cuối kỳ CHƯA CHỐT (1) - BẢN NHÁP
        db.session.add(ChiTietDiem(ma_bang_diem=bd.id, ma_cau_truc_diem=ct2_gk.id, gia_tri_diem=random.randint(5, 9),
                                   ban_nhap=False))
        # Chỉ nhập nháp điểm cuối kỳ cho học viên Giỏi để test
        if i == 2:
            db.session.add(ChiTietDiem(ma_bang_diem=bd.id, ma_cau_truc_diem=ct2_ck.id, gia_tri_diem=9.5, ban_nhap=True))

    # Tự động sinh điểm danh K2 (Chỉ sinh đến hôm nay)
    tao_du_lieu_diem_danh_tu_dong(kh2, lop_k2)

    # --- KỊCH BẢN 3: KHÓA SẮP MỞ (Chưa học, chưa điểm danh) ---
    kh3 = KhoaHoc(
        ma_khoa_hoc=KhoaHoc.tao_ma_khoa_hoc_moi("ENG-ADV"),
        ten_khoa_hoc="Tiếng Anh Cao Cấp K3 (Sắp mở)",
        ma_loai_khoa_hoc="ENG-ADV", ma_giao_vien=gv1.ma_nguoi_dung,
        si_so_toi_da=8, hoc_phi=6000000,
        ngay_bat_dau=today + timedelta(days=7),
        ngay_ket_thuc=today + timedelta(days=90),
        tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
    )
    db.session.add(kh3);
    db.session.commit()

    # Lịch K3
    for thu in [TuanEnum.THU_HAI, TuanEnum.THU_TU, TuanEnum.THU_SAU]:
        db.session.add(LichHoc(ma_khoa_hoc=kh3.ma_khoa_hoc, ma_phong_hoc=phong_hoc3.ma_phong_hoc, thu=thu,
                               ca_hoc=CaHocEnum.CA_CHIEU))

    # Cấu trúc điểm
    db.session.add(CauTrucDiem(ma_khoa_hoc=kh3.ma_khoa_hoc, ten_loai_diem="Final Project", trong_so=1.0))

    # Học viên Mới đăng ký
    hv_moi = ds_hoc_vien[5]
    bd_moi = BangDiem(ma_khoa_hoc=kh3.ma_khoa_hoc, ma_hoc_vien=hv_moi.ma_nguoi_dung)
    db.session.add(bd_moi)
    kh3.si_so_hien_tai += 1

    hd_moi = HoaDon(ma_khoa_hoc=kh3.ma_khoa_hoc, ma_hoc_vien=hv_moi.ma_nguoi_dung, so_tien=6000000,
                    trang_thai=TrangThaiHoaDonEnum.CHUA_THANH_TOAN)
    db.session.add(hd_moi)

    db.session.commit()
    print(f"-> Đã tạo dữ liệu mẫu thành công!")
    print(f"   + 3 Khóa học: Đã xong (K1), Đang học (K2), Sắp mở (K3).")
    print(f"   + 6 Học viên: Giỏi, Khá, Yếu, Hay Cúp, Trung Bình, Mới.")
    print(f"   + Điểm danh: Đầy đủ theo lịch.")
    print(f"   + Điểm số: Có điểm chốt (ban_nhap=0) và điểm nháp (ban_nhap=1).")


if __name__ == "__main__":
    with app.app_context():
        tao_du_lieu_mau()
