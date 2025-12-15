import hashlib
from datetime import datetime, date
from sqlalchemy import and_, or_, extract
from eduapp import db, app
from eduapp.models import HocVien, GiaoVien, NhanVien, QuanLy, NguoiDungEnum, KhoaHoc, PhongHoc, LoaiKhoaHoc, NguoiDung, \
    BangDiem, CauTrucDiem, TinhTrangKhoaHocEnum, HoaDon, ChiTietDiem, ChiTietDiemDanh, TrangThaiDiemDanhEnum, DiemDanh, \
    TuanEnum, CaHocEnum, LichHoc


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
                elif status_val == 2:
                    row['stats']['present'] += 0.5
        if row['stats']['total'] > 0:
            row['percent'] = int((row['stats']['present'] / row['stats']['total']) * 100)
        else:
            row['percent'] = 0
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


def kiem_tra_trung_lich_hoc_vien(ma_hoc_vien, ma_khoa_hoc_moi):
    kh_moi = KhoaHoc.query.get(ma_khoa_hoc_moi)
    if not kh_moi:
        return False, "Khóa học không tồn tại"
    ds_khoa_hoc_da_dang_ky = KhoaHoc.query.join(BangDiem).filter(
        BangDiem.ma_hoc_vien == ma_hoc_vien,
        KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC
    ).all()
    if not ds_khoa_hoc_da_dang_ky:
        return True, "Lịch trống, có thể đăng ký"
    for kh_cu in ds_khoa_hoc_da_dang_ky:
        if (kh_moi.ngay_bat_dau <= kh_cu.ngay_ket_thuc) and (kh_moi.ngay_ket_thuc >= kh_cu.ngay_bat_dau):
            for lich_moi in kh_moi.lich_hoc:
                for lich_cu in kh_cu.lich_hoc:
                    if (lich_moi.thu == lich_cu.thu) and (lich_moi.ca_hoc == lich_cu.ca_hoc):
                        return False, f"Trùng lịch với khóa {kh_cu.ten_khoa_hoc} ({kh_cu.ma_khoa_hoc}) vào {lich_moi.thu.name} - {lich_moi.ca_hoc.name}"
    return True, "Hợp lệ"


def kiem_tra_xung_dot_lich(form_data, lich_hoc_list):
    try:
        try:
            si_so = int(form_data.get('si_so', 0))
            if si_so < 10 or si_so > 150:
                return False, "Sĩ số phải từ 10 đến 150 học viên."
        except ValueError:
            return False, "Sĩ số không hợp lệ."
        start_str = form_data['ngay_bat_dau']
        end_str = form_data['ngay_ket_thuc']
        ma_gv_dang_chon = form_data['ma_giao_vien']
        start_date = datetime.strptime(start_str, '%Y-%m-%d') if isinstance(start_str, str) else start_str
        end_date = datetime.strptime(end_str, '%Y-%m-%d') if isinstance(end_str, str) else end_str
        if start_date > end_date:
            return False, "Ngày kết thúc phải sau ngày bắt đầu."
        lich_tiem_nang = db.session.query(LichHoc, KhoaHoc).join(KhoaHoc).filter(
            KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC,
            KhoaHoc.ngay_bat_dau <= end_date,
            KhoaHoc.ngay_ket_thuc >= start_date
        ).all()
        map_ban = {}
        for lich, khoa in lich_tiem_nang:
            key = f"{lich.thu.value}-{lich.ca_hoc.value}"
            if key not in map_ban:
                map_ban[key] = {'phong': [], 'gv': []}
            map_ban[key]['phong'].append({
                'ma': str(lich.ma_phong_hoc),
                'ten_lop': khoa.ten_khoa_hoc
            })
            map_ban[key]['gv'].append({
                'ma': str(khoa.ma_giao_vien),
                'ten_lop': khoa.ten_khoa_hoc
            })
        for item in lich_hoc_list:
            thu = str(item['thu'])
            ca = str(item['ca'])
            phong = str(item['ma_phong'])
            check_key = f"{thu}-{ca}"
            if check_key in map_ban:
                data_ban = map_ban[check_key]
                for p in data_ban['phong']:
                    if p['ma'] == phong:
                        thu_text = f"Thứ {int(thu) + 2}"
                        ca_text = "Sáng" if ca == "1" else "Chiều"
                        return False, f"Xung đột PHÒNG: Phòng {phong} đã có lớp '{p['ten_lop']}' học vào {thu_text}, {ca_text}."
                for g in data_ban['gv']:
                    if g['ma'] == ma_gv_dang_chon:
                        thu_text = f"Thứ {int(thu) + 2}"
                        ca_text = "Sáng" if ca == "1" else "Chiều"
                        return False, f"Xung đột GIÁO VIÊN: GV này đang dạy lớp '{g['ten_lop']}' vào {thu_text}, {ca_text}."
        return True, "Hợp lệ"
    except Exception as e:
        print(f"Lỗi check lịch: {str(e)}")
        return False, f"Lỗi hệ thống: {str(e)}"


def tao_khoa_hoc_moi(data, lich_hoc_list):
    try:
        ma_moi = KhoaHoc.tao_ma_khoa_hoc_moi(data['ma_loai_khoa_hoc'])
        new_kh = KhoaHoc(
            ma_khoa_hoc=ma_moi,
            ten_khoa_hoc=data['ten_khoa_hoc'],
            ma_loai_khoa_hoc=data['ma_loai_khoa_hoc'],
            ma_giao_vien=data['ma_giao_vien'],
            si_so_toi_da=data['si_so'],
            ngay_bat_dau=datetime.strptime(data['ngay_bat_dau'], '%Y-%m-%d'),
            ngay_ket_thuc=datetime.strptime(data['ngay_ket_thuc'], '%Y-%m-%d'),
            tinh_trang=TinhTrangKhoaHocEnum.DANG_TUYEN_SINH
        )
        db.session.add(new_kh)
        for item in lich_hoc_list:
            new_lich = LichHoc(
                ma_khoa_hoc=ma_moi,
                ma_phong_hoc=item['ma_phong'],
                thu=TuanEnum(int(item['thu'])),
                ca_hoc=CaHocEnum(int(item['ca']))
            )
            db.session.add(new_lich)
        db.session.commit()
        return True, "Tạo khóa học thành công!"
    except Exception as e:
        db.session.rollback()
        return False, str(e)


def tao_cau_truc_diem(ma_khoa_hoc, ds_ten, ds_trong_so):
    try:
        if not ds_ten or len(ds_ten) != len(ds_trong_so):
            return False, "Dữ liệu cấu trúc không hợp lệ."
        tong_trong_so = sum([float(ts) for ts in ds_trong_so])
        if tong_trong_so != 100:
            return False, f"Tổng trọng số phải là 100% (Hiện tại: {tong_trong_so}%)"
        for i in range(len(ds_ten)):
            new_struct = CauTrucDiem(
                ma_khoa_hoc=ma_khoa_hoc,
                ten_loai_diem=ds_ten[i].strip(),
                trong_so=float(ds_trong_so[i]) / 100.0
            )
            db.session.add(new_struct)
        db.session.commit()
        return True, "Tạo cấu trúc điểm thành công!"
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi DAO tao_cau_truc_diem: {str(e)}")
        return False, str(e)


def luu_bang_diem(ma_khoa_hoc, form_data, is_save_draft):
    try:
        count_changes = 0
        for key, value in form_data.items():
            if key.startswith('diem_') and value.strip() != '':
                parts = key.split('_')
                if len(parts) == 3:
                    bd_id = int(parts[1])
                    ct_id = int(parts[2])
                    try:
                        diem_val = float(value)
                    except ValueError:
                        continue
                    if 0 <= diem_val <= 10:
                        chi_tiet = ChiTietDiem.query.filter_by(
                            ma_bang_diem=bd_id,
                            ma_cau_truc_diem=ct_id
                        ).first()
                        if chi_tiet and is_save_draft and chi_tiet.ban_nhap == False:
                            continue
                        if chi_tiet:
                            if chi_tiet.gia_tri_diem != diem_val or chi_tiet.ban_nhap != is_save_draft:
                                chi_tiet.gia_tri_diem = diem_val
                                chi_tiet.ban_nhap = is_save_draft
                                count_changes += 1
                        else:
                            new_score = ChiTietDiem(
                                ma_bang_diem=bd_id,
                                ma_cau_truc_diem=ct_id,
                                gia_tri_diem=diem_val,
                                ban_nhap=is_save_draft
                            )
                            db.session.add(new_score)
                            count_changes += 1
        if not is_save_draft:
            db.session.commit()
            ds_bang_diem = BangDiem.query.filter_by(ma_khoa_hoc=ma_khoa_hoc).all()
            for bd in ds_bang_diem:
                bd.cap_nhat_tong_ket()
        db.session.commit()
        return True, f"Đã cập nhật {count_changes} điểm số."
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi DAO luu_bang_diem: {str(e)}")
        return False, str(e)


def lay_tat_ca_lich_ban():
    try:
        results = db.session.query(
            LichHoc.ma_phong_hoc,
            LichHoc.thu,
            LichHoc.ca_hoc,
            KhoaHoc.ngay_bat_dau,
            KhoaHoc.ngay_ket_thuc,
            KhoaHoc.ma_giao_vien
        ).join(KhoaHoc).filter(
            KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC
        ).all()
        lich_ban = []
        for r in results:
            lich_ban.append({
                "phong": r.ma_phong_hoc,
                "thu": r.thu.value,
                "ca": r.ca_hoc.value,
                "start": r.ngay_bat_dau.strftime('%Y-%m-%d'),
                "end": r.ngay_ket_thuc.strftime('%Y-%m-%d'),
                "gv": r.ma_giao_vien
            })
        return lich_ban
    except Exception as e:
        print(f"Lỗi lấy lịch bận: {e}")
        return []


def tra_cuu_khoa_hoc(params=None, page=1, page_size=app.config["PAGE_SIZE"]):
    if params is None:
        params = {}
    query = KhoaHoc.query
    kw = params.get('kw')
    if kw:
        query = query.filter(or_(
            KhoaHoc.ma_khoa_hoc.ilike(f"%{kw}%"),
            KhoaHoc.ten_khoa_hoc.ilike(f"%{kw}%")
        ))
    status = params.get('status')
    if status:
        try:
            query = query.filter(KhoaHoc.tinh_trang == TinhTrangKhoaHocEnum(int(status)))
        except:
            pass
    from_date = params.get('from_date')
    if from_date:
        try:
            if isinstance(from_date, str):
                d_from = datetime.strptime(from_date, '%Y-%m-%d')
            else:
                d_from = from_date
            query = query.filter(KhoaHoc.ngay_bat_dau >= d_from)
        except:
            pass
    to_date = params.get('to_date')
    if to_date:
        try:
            if isinstance(to_date, str):
                d_to = datetime.strptime(to_date, '%Y-%m-%d')
            else:
                d_to = to_date
            query = query.filter(KhoaHoc.ngay_bat_dau <= d_to)
        except:
            pass
    query = query.order_by(KhoaHoc.ngay_bat_dau.desc())
    return query.paginate(page=page, per_page=page_size, error_out=False)


def lay_ds_hoc_vien_cua_khoa(ma_khoa_hoc, page=1, page_size=app.config["PAGE_SIZE"], tu_khoa=None, ket_qua=None,
                             nam_sinh=None):
    query = BangDiem.query.join(HocVien).filter(BangDiem.ma_khoa_hoc == ma_khoa_hoc)
    if tu_khoa:
        search_term = f"%{tu_khoa}%"
        query = query.filter(or_(
            HocVien.ho_va_ten.ilike(search_term),
            HocVien.ma_nguoi_dung.ilike(search_term)
        ))
    if nam_sinh:
        try:
            nam = int(nam_sinh)
            query = query.filter(extract('year', HocVien.ngay_sinh) == nam)
        except ValueError:
            pass
    if ket_qua:
        if ket_qua == 'dau':
            query = query.filter(BangDiem.ket_qua == True)
        elif ket_qua == 'rot':
            query = query.filter(BangDiem.ket_qua == False, BangDiem.diem_trung_binh != None)
        elif ket_qua == 'chua_xet':
            query = query.filter(BangDiem.diem_trung_binh == None)
    return query.paginate(page=page, per_page=page_size)
