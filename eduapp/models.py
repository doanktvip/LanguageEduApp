from datetime import datetime, timedelta
from enum import Enum as RoleEnum
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum, UniqueConstraint
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
    """Bảng cha chứa thông tin chung"""
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
                           default='https://res.cloudinary.com/db4bjqp4f/image/upload/v1765002051/hew7wdmqad2sqw3kpixe.png')

    # Cấu hình đa hình
    vai_tro = Column(Enum(NguoiDungEnum), nullable=False)
    __mapper_args__ = {
        'polymorphic_on': vai_tro
    }

    def get_id(self):
        return self.ma_nguoi_dung

    @classmethod
    def tao_ma_nguoi_dung(cls, vai_tro_enum):
        """Hàm tự động sinh mã theo vai trò (VD: HV240001, GV240001)"""
        prefix_map = {
            NguoiDungEnum.HOC_VIEN: "HV",
            NguoiDungEnum.GIAO_VIEN: "GV",
            NguoiDungEnum.NHAN_VIEN: "NV",
            NguoiDungEnum.QUAN_LY: "QL"
        }
        prefix = prefix_map.get(vai_tro_enum, "ND")
        current_year = datetime.now().strftime('%y')

        # Tìm user cuối cùng có prefix này
        last_user = db.session.query(NguoiDung.ma_nguoi_dung) \
            .filter(NguoiDung.ma_nguoi_dung.like(f"{prefix}{current_year}%")) \
            .order_by(NguoiDung.ma_nguoi_dung.desc()).first()

        if last_user:
            try:
                last_sequence = int(last_user[0][4:])  # Lấy phần số đuôi
                new_sequence = last_sequence + 1
            except ValueError:
                new_sequence = 1
        else:
            new_sequence = 1

        return f"{prefix}{current_year}{new_sequence:04d}"


class QuanLy(NguoiDung):
    __tablename__ = "quan_ly"
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
    ds_lop_hoc = relationship('BangDiem', backref='hoc_vien', lazy=True)
    nhung_hoa_don = relationship('HoaDon', backref='hoc_vien', lazy=True)
    nhung_lan_diem_danh = relationship('ChiTietDiemDanh', backref='hoc_vien', lazy=True)

    __mapper_args__ = {'polymorphic_identity': NguoiDungEnum.HOC_VIEN}


# ==========================================
# 3. QUẢN LÝ KHÓA HỌC & LỊCH HỌC
# ==========================================

class LoaiKhoaHoc(db.Model):
    __tablename__ = "loai_khoa_hoc"
    ma_loai_khoa_hoc = Column(String(10), primary_key=True)
    ten_loai_khoa_hoc = Column(String(50), nullable=False)
    hoc_phi = Column(Float, nullable=False)
    nhung_khoa_hoc = relationship('KhoaHoc', backref='loai_khoa_hoc', lazy=True)


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

    # Quan hệ
    ds_dang_ky = relationship('BangDiem', backref='khoa_hoc', lazy=True)  # Liên kết tới bảng Enrollment
    lich_hoc = relationship('LichHoc', backref='khoa_hoc', lazy=True)
    nhung_hoa_don = relationship('HoaDon', backref='khoa_hoc', lazy=True)
    ds_diem_danh = relationship('DiemDanh', backref='khoa_hoc', lazy=True)
    cau_truc_diem = relationship('CauTrucDiem', backref='khoa_hoc', lazy=True)

    # Proxy: Giúp gọi khoa_hoc.ds_hoc_vien trực tiếp
    ds_hoc_vien = association_proxy('ds_dang_ky', 'hoc_vien')

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


class PhongHoc(db.Model):
    __tablename__ = "phong_hoc"
    ma_phong_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ten_phong_hoc = Column(String(20), nullable=False)
    nhung_lich_hoc = relationship('LichHoc', backref='phong_hoc', lazy=True)


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

    # Chi tiết: Buổi này ai đi, ai vắng
    chi_tiet = relationship('ChiTietDiemDanh', backref='buoi_diem_danh', lazy=True)


class ChiTietDiemDanh(db.Model):
    """Trạng thái của 1 học viên trong 1 buổi học"""
    __tablename__ = "chi_tiet_diem_danh"
    ma_diem_danh = Column(Integer, ForeignKey('diem_danh.id'), primary_key=True)
    ma_hoc_vien = Column(String(20), ForeignKey('hoc_vien.ma_nguoi_dung'), primary_key=True)
    trang_thai = Column(Enum(TrangThaiDiemDanhEnum), default=TrangThaiDiemDanhEnum.CO_MAT)
    ghi_chu = Column(String(200))


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

    ds_diem_chi_tiet = relationship('ChiTietDiem', backref='cau_truc_diem', lazy=True)


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

    ds_diem_thanh_phan = relationship('ChiTietDiem', backref='bang_diem', lazy=True)

    # Ràng buộc: 1 Học viên chỉ có 1 Bảng điểm trong 1 Khóa học
    __table_args__ = (UniqueConstraint('ma_khoa_hoc', 'ma_hoc_vien', name='_enrollment_uc'),)

    def lay_chi_tiet_diem(self, list_cau_truc_diem):
        bang_diem = {}
        for ct in list_cau_truc_diem:
            bang_diem[ct.ten_loai_diem] = [None, ct.trong_so]
        for chi_tiet in self.ds_diem_thanh_phan:
            ten_loai = chi_tiet.cau_truc_diem.ten_loai_diem
            if ten_loai in bang_diem:
                bang_diem[ten_loai][0] = chi_tiet.gia_tri_diem
        bang_diem['Tổng kết'] = [self.diem_trung_binh, None]
        bang_diem['Kết quả'] = [self.ket_qua, None]
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


# ==========================================
# 6. TÀI CHÍNH
# ==========================================

class HoaDon(db.Model):
    __tablename__ = "hoa_don"
    ma_hoa_don = Column(Integer, autoincrement=True, primary_key=True)
    ngay_tao = Column(DateTime, default=datetime.now())
    ngay_nop = Column(DateTime, nullable=True)
    so_tien = Column(Float, nullable=False)
    trang_thai = Column(Enum(TrangThaiHoaDonEnum), default=TrangThaiHoaDonEnum.CHUA_THANH_TOAN)

    ma_hoc_vien = Column(String(20), ForeignKey('hoc_vien.ma_nguoi_dung'), nullable=False)
    ma_khoa_hoc = Column(String(20), ForeignKey('khoa_hoc.ma_khoa_hoc'), nullable=False)
    ma_nhan_vien = Column(String(20), ForeignKey('nhan_vien.ma_nguoi_dung'), nullable=True)


def chay_thu_nghiem_truy_van():
    print("\n" + "=" * 40)
    print("DEMO TRUY VẤN DỮ LIỆU TRUNG TÂM")
    print("=" * 40)

    # ---------------------------------------------------------
    # 1. TRUY VẤN NGƯỜI DÙNG (Kế thừa đa hình)
    # ---------------------------------------------------------
    print("\n--- 1. LẤY DANH SÁCH HỌC VIÊN ---")

    # Lệnh này trả về: Một danh sách (List) các object HocVien
    ds_hoc_vien = HocVien.query.all()

    for hv in ds_hoc_vien:
        # Nhờ kế thừa, ta gọi được thuộc tính của bảng cha (ho_va_ten)
        # và bảng con (ngay_sinh) trên cùng 1 object.
        print(f"Học viên: {hv.ho_va_ten} (Mã: {hv.ma_nguoi_dung})")
        print(f" - Email: {hv.email}")
        print(f" - Ngày sinh: {hv.ngay_sinh.strftime('%d/%m/%Y')}")

    # ---------------------------------------------------------
    # 2. TRUY VẤN KHÓA HỌC & GIÁO VIÊN
    # ---------------------------------------------------------
    print("\n--- 2. CHI TIẾT KHÓA HỌC BEG001 ---")

    # Lệnh này trả về: Một Object KhoaHoc duy nhất (hoặc None nếu không tìm thấy)
    # Cách này gọi .get() từ phiên làm việc (session) của Database
    # Cú pháp: db.session.get(Tên_Class, "Khóa_Chính")
    khoa_hoc = db.session.get(KhoaHoc, "BEG001")

    if khoa_hoc:
        print(f"Tên khóa: {khoa_hoc.ten_khoa_hoc}")
        print(f"Học phí: {khoa_hoc.loai_khoa_hoc.hoc_phi:,.0f} VND")  # Relationship sang LoaiKhoaHoc
        print(f"Giáo viên CN: {khoa_hoc.giao_vien.ho_va_ten}")  # Relationship sang GiaoVien

        # Sử dụng Association Proxy để lấy list học viên nhanh
        print(f"Danh sách lớp ({len(khoa_hoc.ds_hoc_vien)} học viên):")
        for hv in khoa_hoc.ds_hoc_vien:
            print(f" -> {hv.ho_va_ten}")

    # ---------------------------------------------------------
    # 3. TRUY VẤN LỊCH HỌC
    # ---------------------------------------------------------
    print("\n--- 3. LỊCH HỌC CỦA LỚP ---")
    # khoa_hoc.lich_hoc trả về một List các object LichHoc
    for lh in khoa_hoc.lich_hoc:
        thu_str = lh.thu.name  # Trả về string 'THU_HAI', 'THU_TU'...
        ca_str = lh.ca_hoc.name  # Trả về string 'CA_SANG'...
        phong = lh.phong_hoc.ten_phong_hoc
        print(f" - {thu_str} | {ca_str} tại phòng {phong}")

    # ---------------------------------------------------------
    # 4. TRUY VẤN BẢNG ĐIỂM ĐỘNG (Phần khó nhất)
    # ---------------------------------------------------------
    print("\n--- 4. BẢNG ĐIỂM CHI TIẾT ---")

    # Lấy bảng điểm của học viên đầu tiên trong danh sách
    hoc_vien_dau_tien = ds_hoc_vien[0]

    # Lấy các lớp học viên này đang học
    # Trả về List các object BangDiem
    cac_lop_dang_hoc = hoc_vien_dau_tien.ds_lop_hoc

    for bang_diem in cac_lop_dang_hoc:
        print(f"Kết quả môn: {bang_diem.khoa_hoc.ten_khoa_hoc}")
        print(f" -> Tổng kết: {bang_diem.diem_trung_binh} (Đậu: {bang_diem.ket_qua})")
        print(" -> Chi tiết điểm thành phần:")

        # Truy cập vào bảng ChiTietDiem
        for diem_ct in bang_diem.ds_diem_thanh_phan:
            # diem_ct.cau_truc_diem giúp ta lấy tên đầu điểm (VD: Giữa kỳ)
            ten_dau_diem = diem_ct.cau_truc_diem.ten_loai_diem
            trong_so = diem_ct.cau_truc_diem.trong_so * 100
            gia_tri = diem_ct.gia_tri_diem

            print(f"    * {ten_dau_diem} ({trong_so}%): {gia_tri} điểm")

    # ---------------------------------------------------------
    # 5. TRUY VẤN ĐIỂM DANH
    # ---------------------------------------------------------
    print("\n--- 5. TÌNH TRẠNG ĐIỂM DANH ---")
    # Lấy buổi điểm danh gần nhất của khóa học
    buoi_dd = DiemDanh.query.filter_by(ma_khoa_hoc="BEG001").first()

    if buoi_dd:
        print(f"Ngày điểm danh: {buoi_dd.ngay_diem_danh.strftime('%d/%m/%Y')}")
        for ct in buoi_dd.chi_tiet:
            ten_hv = ct.hoc_vien.ho_va_ten
            trang_thai = ct.trang_thai.name  # CO_MAT / VANG...
            ghi_chu = f"({ct.ghi_chu})" if ct.ghi_chu else ""
            print(f" - {ten_hv}: {trang_thai} {ghi_chu}")

    # ---------------------------------------------------------
    # 6. TRUY VẤN TÀI CHÍNH (HÓA ĐƠN)
    # ---------------------------------------------------------
    print("\n--- 6. DOANH THU (HÓA ĐƠN) ---")
    ds_hoa_don = HoaDon.query.all()
    tong_tien = 0
    for hd in ds_hoa_don:
        print(f"HĐ #{hd.ma_hoa_don}: {hd.so_tien:,.0f} VND - HV: {hd.hoc_vien.ho_va_ten}")
        tong_tien += hd.so_tien

    print(f"=> TỔNG DOANH THU: {tong_tien:,.0f} VND")


def tao_du_lieu_mau():
    print("--- BẮT ĐẦU TẠO DỮ LIỆU MẪU (NEW SCHEMA) ---")

    # 1. Reset Database
    db.drop_all()
    db.create_all()
    print("-> Đã reset database thành công.")

    # --- 2. TẠO NGƯỜI DÙNG (USERS) ---
    # Giả lập mã hash MD5 cho password '123'
    mat_khau_chung = "202cb962ac59075b964b07152d234b70"

    # 2.1 Quản trị viên
    admin = QuanLy(
        ma_nguoi_dung="QL250001", ten_dang_nhap="admin", mat_khau=mat_khau_chung,
        ho_va_ten="Nguyễn Quản Trị", email="admin@edu.com", so_dien_thoai="0909000111",
        vai_tro=NguoiDungEnum.QUAN_LY
    )

    # 2.2 Nhân viên tư vấn
    nv1 = NhanVien(
        ma_nguoi_dung="NV250001", ten_dang_nhap="thu_ngan", mat_khau=mat_khau_chung,
        ho_va_ten="Lê Thu Ngân", email="thungan@edu.com", so_dien_thoai="0909111222",
        vai_tro=NguoiDungEnum.NHAN_VIEN
    )

    # 2.3 Giáo viên
    gv1 = GiaoVien(
        ma_nguoi_dung="GV250001", ten_dang_nhap="mr_smith", mat_khau=mat_khau_chung,
        ho_va_ten="John Smith", email="john@edu.com", so_dien_thoai="0912333444",
        vai_tro=NguoiDungEnum.GIAO_VIEN, nam_kinh_nghiem=10
    )
    gv2 = GiaoVien(
        ma_nguoi_dung="GV250002", ten_dang_nhap="ms_hien", mat_khau=mat_khau_chung,
        ho_va_ten="Nguyễn Thu Hiền", email="hien@edu.com", so_dien_thoai="0912333555",
        vai_tro=NguoiDungEnum.GIAO_VIEN, nam_kinh_nghiem=5
    )

    # 2.4 Học viên
    hv1 = HocVien(
        ma_nguoi_dung="HV250001", ten_dang_nhap="hv_an", mat_khau=mat_khau_chung,
        ho_va_ten="Phạm Văn An", email="an@edu.com", so_dien_thoai="0987654001",
        vai_tro=NguoiDungEnum.HOC_VIEN, so_dien_thoai_phu_huynh="0911000001",
        ngay_sinh=datetime(2005, 5, 20)
    )
    hv2 = HocVien(
        ma_nguoi_dung="HV250002", ten_dang_nhap="hv_binh", mat_khau=mat_khau_chung,
        ho_va_ten="Lê Thanh Bình", email="binh@edu.com", so_dien_thoai="0987654002",
        vai_tro=NguoiDungEnum.HOC_VIEN, so_dien_thoai_phu_huynh="0911000002",
        ngay_sinh=datetime(2006, 8, 15)
    )

    db.session.add_all([admin, nv1, gv1, gv2, hv1, hv2])
    db.session.commit()
    print("-> Đã tạo xong Users.")

    # --- 3. TẠO LOẠI KHÓA HỌC (THEO CẤP ĐỘ) ---
    # Yêu cầu hình ảnh: Beginner, Intermediate, Advanced
    loai_beg = LoaiKhoaHoc(ma_loai_khoa_hoc="ENG-BEG", ten_loai_khoa_hoc="Tiếng Anh Beginner", hoc_phi=3000000)
    loai_int = LoaiKhoaHoc(ma_loai_khoa_hoc="ENG-INT", ten_loai_khoa_hoc="Tiếng Anh Intermediate", hoc_phi=4500000)
    loai_adv = LoaiKhoaHoc(ma_loai_khoa_hoc="ENG-ADV", ten_loai_khoa_hoc="Tiếng Anh Advanced", hoc_phi=6000000)
    loai_toeic = LoaiKhoaHoc(ma_loai_khoa_hoc="TOEIC", ten_loai_khoa_hoc="Luyện thi TOEIC", hoc_phi=5000000)

    db.session.add_all([loai_beg, loai_int, loai_adv, loai_toeic])
    db.session.commit()
    print("-> Đã tạo xong Loại khóa học (Cấp độ).")

    # --- 4. TẠO PHÒNG HỌC ---
    phongs = [PhongHoc(ten_phong_hoc=f"P{i}") for i in range(101, 106)]
    db.session.add_all(phongs)
    db.session.commit()

    # --- 5. TẠO KHÓA HỌC ---
    today = datetime.now()

    # Khóa 1: Tiếng Anh Beginner (Đang học)
    kh_beg = KhoaHoc(
        ma_khoa_hoc="BEG001",
        ten_khoa_hoc="Tiếng Anh Căn Bản K25",
        ma_loai_khoa_hoc="ENG-BEG",
        ma_giao_vien="GV250001",  # Mr. Smith dạy
        si_so_hien_tai=2, si_so_toi_da=20,
        ngay_bat_dau=today - timedelta(days=30),
        ngay_ket_thuc=today + timedelta(days=60),
        tinh_trang=TinhTrangKhoaHocEnum.DUNG_TUYEN_SINH  # Đã chốt lớp
    )

    # Khóa 2: TOEIC (Sắp mở)
    kh_toeic = KhoaHoc(
        ma_khoa_hoc="TOEIC001",
        ten_khoa_hoc="Luyện giải đề TOEIC 600+",
        ma_loai_khoa_hoc="TOEIC",
        ma_giao_vien="GV250002",  # Ms. Hiền dạy
        si_so_hien_tai=0, si_so_toi_da=25,
        ngay_bat_dau=today + timedelta(days=10),
        ngay_ket_thuc=today + timedelta(days=100),
        tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
    )

    db.session.add_all([kh_beg, kh_toeic])
    db.session.commit()
    print("-> Đã tạo xong Khóa học.")

    # --- 6. TẠO CẤU TRÚC ĐIỂM (YÊU CẦU QUAN TRỌNG) ---
    # Khóa Beginner có 3 cột điểm: Chuyên cần (20%), Giữa kỳ (30%), Cuối kỳ (50%)
    ct1 = CauTrucDiem(ma_khoa_hoc="BEG001", ten_loai_diem="Chuyên cần", trong_so=0.2)
    ct2 = CauTrucDiem(ma_khoa_hoc="BEG001", ten_loai_diem="Giữa kỳ", trong_so=0.3)
    ct3 = CauTrucDiem(ma_khoa_hoc="BEG001", ten_loai_diem="Cuối kỳ", trong_so=0.5)

    # Khóa TOEIC chỉ có 2 cột điểm: Mock Test (40%), Final Test (60%)
    ct4 = CauTrucDiem(ma_khoa_hoc="TOEIC001", ten_loai_diem="Mock Test", trong_so=0.4)
    ct5 = CauTrucDiem(ma_khoa_hoc="TOEIC001", ten_loai_diem="Final Test", trong_so=0.6)

    db.session.add_all([ct1, ct2, ct3, ct4, ct5])
    db.session.commit()
    print("-> Đã tạo cấu trúc điểm động.")

    # --- 7. TẠO LỊCH HỌC ---
    # BEG001: Thứ 2-4-6 Ca Sáng
    for thu in [TuanEnum.THU_HAI, TuanEnum.THU_TU, TuanEnum.THU_SAU]:
        lh = LichHoc(ma_khoa_hoc="BEG001", ma_phong_hoc=1, thu=thu, ca_hoc=CaHocEnum.CA_SANG)
        db.session.add(lh)

    db.session.commit()

    # --- 8. ĐĂNG KÝ HỌC & NHẬP ĐIỂM CHI TIẾT ---

    # 8.1: Đăng ký HV An và HV Bình vào lớp BEG001
    bd_an = BangDiem(ma_khoa_hoc="BEG001", ma_hoc_vien="HV250001")
    bd_binh = BangDiem(ma_khoa_hoc="BEG001", ma_hoc_vien="HV250002")

    db.session.add_all([bd_an, bd_binh])
    db.session.commit()  # Commit để có ID bảng điểm

    # 8.2: Nhập điểm cho HV An (Học giỏi)
    # Lấy ID cấu trúc điểm đã tạo ở trên (ct1, ct2...)
    dt_an_1 = ChiTietDiem(ma_bang_diem=bd_an.id, ma_cau_truc_diem=ct1.id, gia_tri_diem=10.0)  # Chuyên cần
    dt_an_2 = ChiTietDiem(ma_bang_diem=bd_an.id, ma_cau_truc_diem=ct2.id, gia_tri_diem=10.0)  # Giữa kỳ
    # Chưa có cuối kỳ

    # Nhập điểm cho HV Bình (Học yếu)
    dt_binh_1 = ChiTietDiem(ma_bang_diem=bd_binh.id, ma_cau_truc_diem=ct1.id, gia_tri_diem=8.0)  # Chuyên cần
    dt_binh_2 = ChiTietDiem(ma_bang_diem=bd_binh.id, ma_cau_truc_diem=ct2.id, gia_tri_diem=4.0)  # Giữa kỳ

    db.session.add_all([dt_an_1, dt_an_2, dt_binh_1, dt_binh_2])
    db.session.commit()

    # 8.3: Cập nhật điểm tổng kết tự động
    bd_an.cap_nhat_tong_ket()
    bd_binh.cap_nhat_tong_ket()
    db.session.commit()
    print("-> Đã nhập điểm và tính toán kết quả.")

    # --- 9. HÓA ĐƠN ---
    hd1 = HoaDon(
        so_tien=3000000, trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN,
        ma_hoc_vien="HV250001", ma_khoa_hoc="BEG001", ma_nhan_vien="NV250001",
        ngay_nop=datetime.now() - timedelta(days=20)
    )
    db.session.add(hd1)
    db.session.commit()

    # --- 10. ĐIỂM DANH (YÊU CẦU MỚI) ---
    # Tạo 1 buổi điểm danh ngày hôm nay cho lớp BEG001
    dd_buoi_1 = DiemDanh(ma_khoa_hoc="BEG001", ngay_diem_danh=datetime.now())
    db.session.add(dd_buoi_1)
    db.session.commit()

    # Chi tiết: An đi học, Bình vắng
    ctdd_1 = ChiTietDiemDanh(
        ma_diem_danh=dd_buoi_1.id, ma_hoc_vien="HV250001",
        trang_thai=TrangThaiDiemDanhEnum.CO_MAT
    )
    ctdd_2 = ChiTietDiemDanh(
        ma_diem_danh=dd_buoi_1.id, ma_hoc_vien="HV250002",
        trang_thai=TrangThaiDiemDanhEnum.VANG_KHONG_PHEP, ghi_chu="Ngủ quên"
    )

    db.session.add_all([ctdd_1, ctdd_2])
    db.session.commit()
    print("-> Đã tạo dữ liệu điểm danh.")

    print("\n=== HOÀN TẤT TẠO DỮ LIỆU MẪU ===")


if __name__ == "__main__":
    with app.app_context():
        tao_du_lieu_mau()
        chay_thu_nghiem_truy_van()
