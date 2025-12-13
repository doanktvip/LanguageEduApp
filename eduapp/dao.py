import hashlib
from datetime import datetime, date
from eduapp import db
from eduapp.models import HocVien, GiaoVien, NhanVien, QuanLy, NguoiDungEnum, KhoaHoc, PhongHoc, LoaiKhoaHoc, NguoiDung, \
    BangDiem, CauTrucDiem, TinhTrangKhoaHocEnum, HoaDon, ChiTietDiem, ChiTietDiemDanh, TrangThaiDiemDanhEnum, DiemDanh


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


def get_by_course_teacher_id(teacher_id, course_id):
    return KhoaHoc.query.filter_by(ma_khoa_hoc=course_id, ma_giao_vien=teacher_id).first()


def get_by_classroom_id(classroom_id):
    return PhongHoc.query.filter_by(ma_phong_hoc=classroom_id).first()


def get_by_scoreboard_id(student_id, classroom_id):
    return BangDiem.query.filter_by(ma_hoc_vien=student_id, ma_khoa_hoc=classroom_id).first()


def get_cau_truc_diem(course_id):
    return CauTrucDiem.query.filter_by(ma_khoa_hoc=course_id)


def get_chi_tiet_diem(ma_bang_diem, ma_cau_truc_diem):
    return ChiTietDiem.query.filter_by(ma_bang_diem=ma_bang_diem, ma_cau_truc_diem=ma_cau_truc_diem).first()


def lay_khoa_hoc_chua_dang_ky(student_id):
    ds_ma_da_hoc = [bd.ma_khoa_hoc for bd in BangDiem.query.filter_by(ma_hoc_vien=student_id).all()]
    query = KhoaHoc.query.filter(
        KhoaHoc.tinh_trang == TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
    )
    if ds_ma_da_hoc:
        query = query.filter(~KhoaHoc.ma_khoa_hoc.in_(ds_ma_da_hoc))
    return query.all()


def dang_ky_khoa_hoc(ma_hoc_vien, ma_khoa_hoc):
    try:
        khoa_hoc = KhoaHoc.query.get(ma_khoa_hoc)
        if not khoa_hoc:
            return False
        if khoa_hoc.si_so_hien_tai >= khoa_hoc.si_so_toi_da:
            return False
        ghi_danh_moi = BangDiem(
            ma_hoc_vien=ma_hoc_vien,
            ma_khoa_hoc=ma_khoa_hoc,
            diem_trung_binh=None,
            ket_qua=False
        )
        db.session.add(ghi_danh_moi)
        hoc_phi = khoa_hoc.loai_khoa_hoc.hoc_phi
        hoa_don_moi = HoaDon(
            ma_hoc_vien=ma_hoc_vien,
            ma_khoa_hoc=ma_khoa_hoc,
            so_tien=hoc_phi
        )
        db.session.add(hoa_don_moi)
        khoa_hoc.si_so_hien_tai += 1
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()


def update_password(username, new_hashed_password):
    try:
        user = NguoiDung.query.filter_by(ten_dang_nhap=username).first()
        if user:
            user.mat_khau = new_hashed_password
            db.session.commit()
            return True
        else:
            return False
    except Exception:
        db.session.rollback()


def get_attendance_sheet_data(course):
    weeks_data = course.lay_danh_sach_tuan_hoc()
    date_columns = []
    added_dates = set()
    for week in weeks_data:
        year = week['year']
        for i in range(7):
            if week['schedule']['CA_SANG'][i] or week['schedule']['CA_CHIEU'][i]:
                day_str = week['days'][i]
                d, m = map(int, day_str.split('/'))
                try:
                    current_date = date(year, m, d)
                    date_iso = current_date.isoformat()
                    if date_iso not in added_dates:
                        added_dates.add(date_iso)
                        date_columns.append({
                            'value': date_iso,
                            'display': day_str,
                            'weekday': f"T{i + 2}" if i < 6 else "CN",
                            'obj': current_date
                        })
                except ValueError:
                    continue
    date_columns.sort(key=lambda x: x['value'])
    attendance_data = db.session.query(
        DiemDanh.ngay_diem_danh,
        ChiTietDiemDanh.ma_hoc_vien,
        ChiTietDiemDanh.trang_thai
    ).join(ChiTietDiemDanh).filter(
        DiemDanh.ma_khoa_hoc == course.ma_khoa_hoc
    ).all()
    attendance_map = {}
    for ngay, ma_hv, trang_thai in attendance_data:
        ngay_iso = ngay.strftime('%Y-%m-%d')
        if ma_hv not in attendance_map:
            attendance_map[ma_hv] = {}
        attendance_map[ma_hv][ngay_iso] = trang_thai.value
    student_rows = []
    today_iso = date.today().isoformat()
    for enroll in course.ds_dang_ky:
        hv = enroll.hoc_vien
        row = {
            'info': hv,
            'cells': [],
            'stats': {'total': 0, 'present': 0},
            'percent': 0
        }
        for col in date_columns:
            d_val = col['value']
            status_val = attendance_map.get(hv.ma_nguoi_dung, {}).get(d_val, None)
            is_future = (d_val > today_iso)
            if status_val is None and d_val == today_iso:
                status_val = 1
            row['cells'].append({
                'date': d_val,
                'status': status_val,
                'editable': (d_val == today_iso),
                'ửa hôm is_future': is_future
            })
            if not is_future and status_val:
                row['stats']['total'] += 1
                if status_val == 1:
                    row['stats']['present'] += 1
        if row['stats']['total'] > 0:
            row['percent'] = int((row['stats']['present'] / row['stats']['total']) * 100)
        else:
            row['percent'] = 100
        student_rows.append(row)
    return date_columns, student_rows


def save_attendance_sheet(course_id, form_data):
    today = date.today()
    today_str = today.isoformat()
    try:
        buoi_diem_danh = DiemDanh.query.filter_by(
            ma_khoa_hoc=course_id,
        ).filter(db.func.date(DiemDanh.ngay_diem_danh) == today).first()
        if not buoi_diem_danh:
            buoi_diem_danh = DiemDanh(ma_khoa_hoc=course_id, ngay_diem_danh=datetime.now())
            db.session.add(buoi_diem_danh)
            db.session.flush()
        course = KhoaHoc.query.get(course_id)
        if course:
            for enroll in course.ds_dang_ky:
                ma_hv = enroll.hoc_vien.ma_nguoi_dung
                key = f"att_{ma_hv}_{today_str}"
                if key in form_data:
                    try:
                        val = int(form_data.get(key))
                    except ValueError:
                        val = 3
                    if val == 1:
                        status = TrangThaiDiemDanhEnum.CO_MAT
                    elif val == 2:
                        status = TrangThaiDiemDanhEnum.VANG_CO_PHEP
                    else:
                        status = TrangThaiDiemDanhEnum.VANG_KHONG_PHEP
                    detail = ChiTietDiemDanh.query.filter_by(
                        ma_diem_danh=buoi_diem_danh.id,
                        ma_hoc_vien=ma_hv
                    ).first()
                    if detail:
                        detail.trang_thai = status
                    else:
                        detail = ChiTietDiemDanh(
                            ma_diem_danh=buoi_diem_danh.id,
                            ma_hoc_vien=ma_hv,
                            trang_thai=status
                        )
                        db.session.add(detail)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Lỗi khi lưu điểm danh: {e}")
        db.session.rollback()
        return False
