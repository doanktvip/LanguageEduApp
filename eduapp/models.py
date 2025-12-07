from datetime import datetime, timedelta
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
    anh_chan_dung = Column(String(100),
                           default='https://res.cloudinary.com/db4bjqp4f/image/upload/v1765002051/hew7wdmqad2sqw3kpixe.png')

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

    @classmethod
    def tao_ma_nguoi_dung(cls):
        prefix_map = {
            "HocVien": "HV",
            "GiaoVien": "GV",
            "NhanVien": "NV",
            "QuanLy": "QL"
        }

        class_name = cls.__name__
        prefix = prefix_map.get(class_name, "ND")
        current_year = datetime.now().strftime('%y')
        last_user = db.session.query(cls.ma_nguoi_dung).filter(cls.ma_nguoi_dung.like(f"{prefix}%")).order_by(
            cls.ma_nguoi_dung.desc()).limit(1).first()
        if last_user:
            last_id = last_user[0]
            last_year = last_id[2:4]
            try:
                last_sequence = int(last_id[4:])
            except ValueError:
                last_sequence = 0
            if last_year == current_year:
                new_sequence = last_sequence + 1
            else:
                new_sequence = 1
        else:
            new_sequence = 1
        new_id = f"{prefix}{current_year}{new_sequence:04d}"
        return new_id


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
    nhung_khoa_hoc = relationship('KhoaHoc', backref='hoc_vien', lazy=True)


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
    ma_nguoi_dung = Column(String(20), ForeignKey(HocVien.ma_nguoi_dung), nullable=False)
    si_so_hien_tai = Column(Integer, default=0)
    si_so_toi_da = Column(Integer, nullable=False)
    ngay_bat_dau = Column(DateTime, nullable=False)
    ngay_ket_thuc = Column(DateTime, nullable=False)
    tinh_trang = Column(Enum(TinhTrangKhoaHocEnum), default=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH)
    ma_giao_vien = Column(String(20), ForeignKey(GiaoVien.ma_nguoi_dung), nullable=False)
    nhung_bang_diem = relationship('BangDiem', backref='khoa_hoc', lazy=True)
    lich_hoc = relationship('LichHoc', backref='khoa_hoc', lazy=True)
    nhung_hoa_don = relationship('HoaDon', backref='khoa_hoc', lazy=True)

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
                        "CA_CHIEU": [None] * 7
                    }
                }
            tuan_map[key]["days"].append(current_date.strftime("%d/%m"))
            if not (current_date < self.ngay_bat_dau or current_date > self.ngay_ket_thuc):
                for lh in self.lich_hoc:
                    ca_key = lh.ca_hoc.name
                    if lh.thu.value == current_date.weekday() is not None and ca_key in tuan_map[key]["schedule"]:
                        tuan_map[key]["schedule"][ca_key][lh.thu.value] = lh
            current_date += timedelta(days=1)
        return list(tuan_map.values())


class PhongHoc(db.Model):
    __tablename__ = "phong_hoc"
    ma_phong_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ten_phong_hoc = Column(String(5), nullable=False)
    nhung_lich_hoc = relationship('LichHoc', backref='phong_hoc', lazy=True)


class LichHoc(db.Model):
    __tablename__ = "lich_hoc"
    ma_lich_hoc = Column(Integer, autoincrement=True, primary_key=True)
    ma_khoa_hoc = Column(String(20), ForeignKey(KhoaHoc.ma_khoa_hoc), nullable=False)
    ma_phong_hoc = Column(Integer, ForeignKey(PhongHoc.ma_phong_hoc), nullable=False)
    thu = Column(Enum(TuanEnum), nullable=False)
    ca_hoc = Column(Enum(CaHocEnum), nullable=False)

    def __init__(self, ca_hoc):
        self.ca_hoc = ca_hoc

    def thoi_gian_theo_ca(self):
        if self.ca_hoc == CaHocEnum.CA_SANG:
            return 7, 11
        return 13, 17


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


def tao_du_lieu_mau():
    print("--- BẮT ĐẦU TẠO DỮ LIỆU MẪU ---")

    # 1. Xóa dữ liệu cũ và tạo lại bảng (Cẩn thận khi dùng trên production)
    db.drop_all()
    db.create_all()
    print("-> Đã reset database.")

    # --- 2. TẠO NGƯỜI DÙNG (USERS) ---
    # Password hash cho '123': 202cb962ac59075b964b07152d234b70
    mat_khau_chung = "202cb962ac59075b964b07152d234b70"

    # Quản trị viên
    admin = QuanLy(
        ma_nguoi_dung="QL250001", ten_dang_nhap="admin", mat_khau=mat_khau_chung,
        ho_va_ten="Nguyễn Quản Trị", email="admin@edu.com", so_dien_thoai="0909000111",
        vai_tro=NguoiDungEnum.QUAN_LY
    )

    # Nhân viên (2 người)
    nv1 = NhanVien(
        ma_nguoi_dung="NV250001", ten_dang_nhap="thu_ngan", mat_khau=mat_khau_chung,
        ho_va_ten="Lê Thu Ngân", email="thungan@edu.com", so_dien_thoai="0909111222",
        vai_tro=NguoiDungEnum.NHAN_VIEN
    )
    nv2 = NhanVien(
        ma_nguoi_dung="NV250002", ten_dang_nhap="tu_van", mat_khau=mat_khau_chung,
        ho_va_ten="Trần Tư Vấn", email="tuvan@edu.com", so_dien_thoai="0909111333",
        vai_tro=NguoiDungEnum.NHAN_VIEN
    )

    # Giáo viên (2 người)
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

    # Học viên (3 người)
    hv1 = HocVien(
        ma_nguoi_dung="HV250001", ten_dang_nhap="hv_an", mat_khau=mat_khau_chung,
        ho_va_ten="Phạm Văn An", email="an@edu.com", so_dien_thoai="0987654001",
        vai_tro=NguoiDungEnum.HOC_VIEN, so_dien_thoai_phu_huynh="0911000001",
        ngay_sinh=datetime(2005, 5, 20), tinh_trang_xac_nhan_email=True
    )
    hv2 = HocVien(
        ma_nguoi_dung="HV250002", ten_dang_nhap="hv_binh", mat_khau=mat_khau_chung,
        ho_va_ten="Lê Thanh Bình", email="binh@edu.com", so_dien_thoai="0987654002",
        vai_tro=NguoiDungEnum.HOC_VIEN, so_dien_thoai_phu_huynh="0911000002",
        ngay_sinh=datetime(2006, 8, 15), tinh_trang_xac_nhan_email=True
    )
    hv3 = HocVien(  # Học viên chưa đóng tiền
        ma_nguoi_dung="HV250003", ten_dang_nhap="hv_cuong", mat_khau=mat_khau_chung,
        ho_va_ten="Đỗ Mạnh Cường", email="cuong@edu.com", so_dien_thoai="0987654003",
        vai_tro=NguoiDungEnum.HOC_VIEN, so_dien_thoai_phu_huynh="0911000003",
        ngay_sinh=datetime(2005, 2, 10), tinh_trang_xac_nhan_email=False
    )

    db.session.add_all([admin, nv1, nv2, gv1, gv2, hv1, hv2, hv3])
    db.session.commit()
    print("-> Đã tạo xong Users.")

    # --- 3. TẠO DANH MỤC (PHÒNG HỌC & LOẠI KHÓA HỌC) ---
    phongs = [PhongHoc(ten_phong_hoc=f"P{i}") for i in range(101, 106)]  # P101 -> P105

    loai_toeic = LoaiKhoaHoc(ma_loai_khoa_hoc="TOEIC", ten_loai_khoa_hoc="Luyện thi TOEIC", hoc_phi=4500000)
    loai_ielts = LoaiKhoaHoc(ma_loai_khoa_hoc="IELTS", ten_loai_khoa_hoc="Luyện thi IELTS", hoc_phi=8500000)
    loai_gt = LoaiKhoaHoc(ma_loai_khoa_hoc="GIAOTIEP", ten_loai_khoa_hoc="Tiếng Anh Giao Tiếp", hoc_phi=3000000)

    db.session.add_all(phongs)
    db.session.add_all([loai_toeic, loai_ielts, loai_gt])
    db.session.commit()
    print("-> Đã tạo xong Phòng học & Loại khóa học.")

    # --- 4. TẠO KHÓA HỌC ---
    # Lưu ý: Theo schema của bạn, khoá học cần ma_nguoi_dung (HocVien).
    # Logic này hơi lạ (thường Nhân viên tạo), nhưng mình sẽ dùng 'HV250001' làm người đại diện tạo.

    today = datetime.now()

    # Khóa TOEIC 550+ (Đã bắt đầu)
    kh1 = KhoaHoc(
        ma_khoa_hoc="TOEIC001", ma_loai_khoa_hoc="TOEIC", ma_nguoi_dung="HV250001", ma_giao_vien="GV250001",
        si_so_hien_tai=2, si_so_toi_da=20,
        ngay_bat_dau=today - timedelta(days=15),  # Đã học 2 tuần
        ngay_ket_thuc=today + timedelta(days=45),
        tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
    )

    # Khóa IELTS 6.5 (Sắp mở)
    kh2 = KhoaHoc(
        ma_khoa_hoc="IELTS001", ma_loai_khoa_hoc="IELTS", ma_nguoi_dung="HV250001", ma_giao_vien="GV250002",
        si_so_hien_tai=0, si_so_toi_da=10,
        ngay_bat_dau=today + timedelta(days=7),  # 1 tuần nữa học
        ngay_ket_thuc=today + timedelta(days=97),
        tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
    )

    db.session.add_all([kh1, kh2])
    db.session.commit()
    print("-> Đã tạo xong Khóa học.")

    # --- 5. TẠO LỊCH HỌC ---
    # TOEIC001: Học Thứ 2 - Thứ 4 - Thứ 6 (Ca Sáng, P101)
    lh1 = LichHoc(ca_hoc=CaHocEnum.CA_SANG)
    lh1.ma_khoa_hoc = "TOEIC001"
    lh1.ma_phong_hoc = 1  # ID của P101
    lh1.thu = TuanEnum.THU_HAI

    lh2 = LichHoc(ca_hoc=CaHocEnum.CA_SANG)
    lh2.ma_khoa_hoc = "TOEIC001"
    lh2.ma_phong_hoc = 1
    lh2.thu = TuanEnum.THU_TU

    lh3 = LichHoc(ca_hoc=CaHocEnum.CA_SANG)
    lh3.ma_khoa_hoc = "TOEIC001"
    lh3.ma_phong_hoc = 1
    lh3.thu = TuanEnum.THU_SAU

    # IELTS001: Học Thứ 3 - Thứ 5 (Ca Chiều, P102)
    lh4 = LichHoc(ca_hoc=CaHocEnum.CA_CHIEU)
    lh4.ma_khoa_hoc = "IELTS001"
    lh4.ma_phong_hoc = 2
    lh4.thu = TuanEnum.THU_BA

    lh5 = LichHoc(ca_hoc=CaHocEnum.CA_CHIEU)
    lh5.ma_khoa_hoc = "IELTS001"
    lh5.ma_phong_hoc = 2
    lh5.thu = TuanEnum.THU_NAM

    db.session.add_all([lh1, lh2, lh3, lh4, lh5])
    db.session.commit()
    print("-> Đã tạo xong Lịch học.")

    # --- 6. ĐĂNG KÝ HỌC (BẢNG ĐIỂM) & HÓA ĐƠN ---

    # HV1 (An) đăng ký TOEIC001, đã trả tiền, đã có điểm giữa kỳ
    bd1 = BangDiem(
        ma_khoa_hoc="TOEIC001", ma_hoc_vien="HV250001",
        diem_giua_ky=7.5, diem_chuyen_can=10.0, ket_qua=False  # Chưa kết thúc
    )
    hd1 = HoaDon(
        ma_hoa_don=1001, so_tien=4500000, trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN,
        ma_hoc_vien="HV250001", ma_khoa_hoc="TOEIC001", ma_nhan_vien="NV250001",
        ngay_nop=datetime.now() - timedelta(days=10)
    )

    # HV2 (Bình) đăng ký TOEIC001, đã trả tiền, học yếu
    bd2 = BangDiem(
        ma_khoa_hoc="TOEIC001", ma_hoc_vien="HV250002",
        diem_giua_ky=4.0, diem_chuyen_can=8.0, ket_qua=False
    )
    hd2 = HoaDon(
        ma_hoa_don=1002, so_tien=4500000, trang_thai=TrangThaiHoaDonEnum.DA_THANH_TOAN,
        ma_hoc_vien="HV250002", ma_khoa_hoc="TOEIC001", ma_nhan_vien="NV250001",
        ngay_nop=datetime.now() - timedelta(days=12)
    )

    # HV3 (Cường) đăng ký IELTS001, CHƯA trả tiền (Chưa có bảng điểm vì chưa học)
    hd3 = HoaDon(
        ma_hoa_don=1003, so_tien=8500000, trang_thai=TrangThaiHoaDonEnum.CHUA_THANH_TOAN,
        ma_hoc_vien="HV250003", ma_khoa_hoc="IELTS001", ma_nhan_vien="NV250002",
        ngay_nop=datetime.now()  # Vừa tạo
    )
    # Lưu ý: Thường thì có hóa đơn mới tạo bảng điểm, hoặc ngược lại tùy logic.
    # Ở đây mình giả định chưa đóng tiền thì chưa vào danh sách lớp (chưa có BangDiem).

    db.session.add_all([bd1, bd2, hd1, hd2, hd3])
    db.session.commit()
    print("-> Đã tạo xong Bảng điểm & Hóa đơn.")
    print("\n=== HOÀN TẤT QUÁ TRÌNH TẠO DỮ LIỆU ===")


if __name__ == "__main__":
    with app.app_context():
        tao_du_lieu_mau()
