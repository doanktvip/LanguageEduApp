import hashlib
import cloudinary.uploader
from datetime import datetime, date
from sqlalchemy import or_, extract, func, case, desc
from eduapp import db, app, mail
from eduapp.models import HocVien, GiaoVien, NhanVien, QuanLy, NguoiDungEnum, KhoaHoc, PhongHoc, LoaiKhoaHoc, NguoiDung, \
    BangDiem, CauTrucDiem, TinhTrangKhoaHocEnum, HoaDon, ChiTietDiem, ChiTietDiemDanh, TrangThaiDiemDanhEnum, DiemDanh, \
    TuanEnum, CaHocEnum, LichHoc, TrangThaiHoaDonEnum
from flask_mail import Message


def send_otp_email_forgot_password(user_email, user_name, otp_code):
    try:
        msg = Message(
            subject="Simple Talk: Yêu cầu đặt lại mật khẩu",
            recipients=[user_email],
            html=f"""
            <!doctype html>
            <html>
            <body style="background-color: #f8f9fa; padding: 20px; font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #0d6efd; color: #ffffff; text-align: center; padding: 20px;">
                        <h3 style="margin: 0; text-transform: uppercase; letter-spacing: 1px;">SIMPLE TALK</h3>
                    </div>
                    <div style="padding: 30px;">
                        <h4 style="color: #0d6efd; margin-top: 0;">Xin chào {user_name},</h4>
                        <p style="line-height: 1.6;">Chúng mình vừa nhận được tín hiệu cần hỗ trợ đổi mật khẩu từ bạn.</p>
                        <p style="line-height: 1.6;">Đừng lo lắng nhé, hãy sử dụng mã xác nhận dưới đây để tiếp tục hành trình chinh phục ngoại ngữ của mình:</p>
                        <div style="background-color: #f1f3f5; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center;">
                            <span style="font-size: 14px; color: #6c757d; display: block; margin-bottom: 10px;">Mã xác nhận bảo mật của bạn:</span>
                            <strong style="font-size: 36px; color: #212529; letter-spacing: 8px; display: block;">{otp_code}</strong>
                        </div>
                        <p style="text-align: center; font-size: 14px; color: #dc3545; background-color: #fff5f5; padding: 10px; border-radius: 4px; border: 1px dashed #dc3545;">
                            ⚠️ <b>Lưu ý quan trọng:</b> Mã này không giới hạn thời gian, nhưng sẽ bị <b>vô hiệu hóa ngay lập tức</b> nếu bạn nhập sai!
                        </p>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="font-size: 14px; color: #6c757d; text-align: center; margin-bottom: 0;">
                            Cảm ơn bạn đã đồng hành cùng Simple Talk.<br>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"DEBUG OTP sent to {user_email}: {otp_code}")
        return True
    except Exception as e:
        print(f"Lỗi gửi mail: {e}")
        return False


def send_course_registration_email(user_email, user_name, course_list):
    try:
        html_danh_sach_khoa = "".join(
            [f"<li style='margin-bottom: 8px;'>✅ {ten}</li>" for ten in course_list]
        )

        count = len(course_list)

        msg = Message(
            subject=f"Simple Talk: Xác nhận đăng ký thành công {count} khóa học",
            recipients=[user_email],
            html=f"""
            <!doctype html>
            <html>
            <body style="background-color: #f8f9fa; padding: 20px; font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">

                    <div style="background-color: #0d6efd; color: #ffffff; text-align: center; padding: 20px;">
                        <h3 style="margin: 0; text-transform: uppercase; letter-spacing: 1px;">SIMPLE TALK</h3>
                    </div>

                    <div style="padding: 30px;">
                        <h4 style="color: #0d6efd; margin-top: 0;">Xin chào {user_name},</h4>

                        <p style="line-height: 1.6;">Chúc mừng bạn! Chúng mình xác nhận bạn đã đăng ký thành công các khóa học sau:</p>

                        <div style="background-color: #f1f3f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <ul style="margin: 0; padding-left: 20px; font-weight: bold; color: #212529; list-style-type: none;">
                                {html_danh_sach_khoa}
                            </ul>
                        </div>

                        <p style="line-height: 1.6;">Hành trình chinh phục kiến thức mới đã sẵn sàng. Hãy bắt đầu ngay hôm nay nhé!</p>

                        <div style="text-align: center; margin-top: 30px; margin-bottom: 10px;">
                            <a href="http://127.0.0.1:5000/" style="background-color: #0d6efd; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                                ▶️ Vào lớp ngay
                            </a>
                        </div>

                        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

                        <p style="font-size: 14px; color: #6c757d; text-align: center; margin-bottom: 0;">
                            Cảm ơn bạn đã lựa chọn Simple Talk.<br>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"DEBUG: Gửi mail đăng ký thành công cho {user_email}")
        return True
    except Exception as e:
        print(f"Lỗi gửi email đăng ký khóa học: {e}")
        return False


def send_verification_email(user_email, user_name, otp_code):
    try:
        msg = Message(
            subject="Simple Talk: Mã xác nhận tài khoản",
            recipients=[user_email],
            html=f"""
            <!doctype html>
            <html>
            <body style="background-color: #f8f9fa; padding: 20px; font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">
                    <div style="background-color: #0d6efd; color: #ffffff; text-align: center; padding: 20px;">
                        <h3 style="margin: 0; text-transform: uppercase; letter-spacing: 1px;">SIMPLE TALK</h3>
                    </div>

                    <div style="padding: 30px;">
                        <h4 style="color: #0d6efd; margin-top: 0;">Xin chào {user_name},</h4>
                        <p style="line-height: 1.6;">Chúng mình vừa nhận được yêu cầu xác nhận email từ bạn.</p>
                        <p style="line-height: 1.6;">Để tiếp tục hành trình chinh phục ngoại ngữ, hãy nhập mã xác nhận dưới đây:</p>

                        <div style="background-color: #f1f3f5; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center;">
                            <span style="font-size: 14px; color: #6c757d; display: block; margin-bottom: 10px;">Mã xác nhận của bạn là:</span>
                            <strong style="font-size: 36px; color: #212529; letter-spacing: 8px; display: block;">{otp_code}</strong>
                        </div>

                        <p style="text-align: center; font-size: 14px; color: #dc3545; background-color: #fff5f5; padding: 10px; border-radius: 4px; border: 1px dashed #dc3545;">
                            ⚠️ <b>Lưu ý:</b> Mã này chỉ có hiệu lực trong vòng <b>1 phút</b>!
                        </p>

                        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">

                        <p style="font-size: 14px; color: #6c757d; text-align: center; margin-bottom: 0;">
                            Cảm ơn bạn đã đồng hành cùng Simple Talk.<br>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
        )
        mail.send(msg)
        print(f"DEBUG OTP Verify cho {user_name}: {otp_code}")
        return True
    except Exception as e:
        print(f"Lỗi gửi email verify: {e}")
        return False


def get_by_scoreboard_id(student_id, classroom_id):
    return BangDiem.query.filter_by(ma_hoc_vien=student_id, ma_khoa_hoc=classroom_id).first()


def get_cau_truc_diem(course_id):
    return CauTrucDiem.query.filter_by(ma_khoa_hoc=course_id)


def get_chi_tiet_diem(ma_bang_diem, ma_cau_truc_diem):
    return ChiTietDiem.query.filter_by(ma_bang_diem=ma_bang_diem, ma_cau_truc_diem=ma_cau_truc_diem).first()


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
    today = datetime.now()
    active_courses = KhoaHoc.query.filter(
        KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC,
        KhoaHoc.ngay_ket_thuc >= today
    ).all()

    result = []
    for kh in active_courses:
        for lh in kh.lich_hoc:
            result.append({
                'start': kh.ngay_bat_dau.strftime('%Y-%m-%d'),
                'end': kh.ngay_ket_thuc.strftime('%Y-%m-%d'),
                'thu': lh.thu.value,  # 0-6
                'ca': lh.ca_hoc.value,  # 1-2
                'phong': str(lh.ma_phong_hoc),
                'gv': kh.ma_giao_vien
            })
    return result


def cap_nhat_si_so_toi_da(ma_khoa_hoc, si_so_moi):
    try:
        kh = get_by_course_id(ma_khoa_hoc)
        if kh:
            kh.si_so_toi_da = si_so_moi
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e


def cap_nhat_hoc_phi(ma_khoa_hoc, hoc_phi_moi):
    try:
        kh = get_by_course_id(ma_khoa_hoc)
        if kh:
            kh.hoc_phi = hoc_phi_moi
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e


def lay_si_so_hien_tai_lon_nhat():
    max_val = db.session.query(func.max(KhoaHoc.si_so_hien_tai)).filter(
        KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC).scalar()
    return max_val if max_val else 0


def cap_nhat_si_so_toan_bo(si_so_moi):
    try:
        KhoaHoc.query.filter(KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC).update(
            {KhoaHoc.si_so_toi_da: si_so_moi}, synchronize_session=False)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def cap_nhat_hoc_phi_theo_phan_tram(phan_tram_giam):
    try:
        he_so = 1.0 - (phan_tram_giam / 100.0)
        KhoaHoc.query.filter(KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC).update(
            {KhoaHoc.hoc_phi: KhoaHoc.hoc_phi * he_so}, synchronize_session=False)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def xoa_khoa_hoc_dao(ma_kh):
    try:
        kh = get_by_course_id(ma_kh)
        if kh:
            db.session.delete(kh)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Lỗi khi xóa khóa học: {e}")
        db.session.rollback()
        return False


def cap_nhat_database_tinh_trang_khoa_hoc():
    khoa_hocs = KhoaHoc.query.filter(KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC).all()
    so_luong_thay_doi = 0
    for kh in khoa_hocs:
        trang_thai_cu = kh.tinh_trang
        kh.cap_nhat_tinh_trang_tu_dong()
        if kh.tinh_trang != trang_thai_cu:
            so_luong_thay_doi += 1
    try:
        if so_luong_thay_doi > 0:
            db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi cập nhật database: {e}")
        return False


def thong_ke_hoc_vien_va_ket_qua():
    return db.session.query(
        KhoaHoc.ten_khoa_hoc,
        func.count(BangDiem.id).label('tong_hv'),
        func.sum(case((BangDiem.ket_qua == True, 1), else_=0)).label('so_dat'),
        func.sum(case((BangDiem.diem_trung_binh == None, 1), else_=0)).label('chua_co_diem')
    ).outerjoin(BangDiem, KhoaHoc.ma_khoa_hoc == BangDiem.ma_khoa_hoc) \
        .group_by(KhoaHoc.ma_khoa_hoc).all()


def thong_ke_doanh_thu_theo_nam(nam):
    return db.session.query(
        func.extract('month', HoaDon.ngay_nop).label('thang'),
        func.sum(HoaDon.so_tien).label('tong_tien')
    ).filter(
        HoaDon.trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN,
        func.extract('year', HoaDon.ngay_nop) == nam
    ).group_by(func.extract('month', HoaDon.ngay_nop)).all()


def get_ds_nam_co_hoa_don():
    query = db.session.query(
        func.extract('year', HoaDon.ngay_nop).label('nam')
    ).filter(
        HoaDon.trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN,
        HoaDon.ngay_nop.isnot(None)
    ).distinct().order_by(desc('nam')).all()
    return [int(r.nam) for r in query]


def get_so_luong_hoc_vien_theo_khoa():
    return db.session.query(
        KhoaHoc.ten_khoa_hoc,
        func.count(BangDiem.ma_hoc_vien).label('so_luong')
    ).join(BangDiem, KhoaHoc.ma_khoa_hoc == BangDiem.ma_khoa_hoc) \
        .group_by(KhoaHoc.ma_khoa_hoc, KhoaHoc.ten_khoa_hoc) \
        .order_by(desc('so_luong')).all()


def get_du_lieu_ty_le_dau():
    return db.session.query(
        KhoaHoc.ten_khoa_hoc,
        func.count(BangDiem.id).label('tong_so'),
        func.sum(case((BangDiem.ket_qua == True, 1), else_=0)).label('so_dau')
    ).join(BangDiem, KhoaHoc.ma_khoa_hoc == BangDiem.ma_khoa_hoc) \
        .group_by(KhoaHoc.ma_khoa_hoc, KhoaHoc.ten_khoa_hoc).all()


def hash_password(password):
    return str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())


def login(username, password):
    password = hash_password(password)
    return NguoiDung.query.filter_by(ten_dang_nhap=username, mat_khau=password).first()


def add_user(loai_nguoi_dung, **kwargs):
    map_model = {
        NguoiDungEnum.HOC_VIEN: HocVien,
        NguoiDungEnum.NHAN_VIEN: NhanVien,
        NguoiDungEnum.GIAO_VIEN: GiaoVien,
    }
    ModelClass = map_model.get(loai_nguoi_dung)
    if not ModelClass:
        return False

    try:
        if 'ma_nguoi_dung' not in kwargs:
            kwargs['ma_nguoi_dung'] = NguoiDung.tao_ma_nguoi_dung(loai_nguoi_dung)

        if 'mat_khau' in kwargs:
            kwargs['mat_khau'] = hash_password(kwargs['mat_khau'])

        kwargs['vai_tro'] = loai_nguoi_dung
        nguoi_dung_moi = ModelClass(**kwargs)
        db.session.add(nguoi_dung_moi)
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        print(f"Lỗi add_user: {ex}")
        return False


def get_by_id(user_id):
    return NguoiDung.query.get(user_id)


def get_by_username(username):
    return NguoiDung.query.filter_by(ten_dang_nhap=username).first()


def get_by_username_email(username, email):
    return NguoiDung.query.filter_by(ten_dang_nhap=username, email=email).first()


def get_by_email(email):
    return NguoiDung.query.filter_by(email=email).first()


def update_password(username, new_plain_password):
    try:
        user = get_by_username(username=username)
        if user:
            user.mat_khau = hash_password(new_plain_password)
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False


def check_admin_pin(user, pin_input):
    if not isinstance(user, QuanLy):
        return False
    return str(user.ma_pin) == hash_password(pin_input)


def update_tinh_trang_email(username):
    try:
        user = get_by_username(username=username)
        if user:
            user.tinh_trang_xac_nhan_email = True
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False


def update_email(username, new_email):
    try:
        user = get_by_username(username=username)
        if user:
            user.email = new_email
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False


def update_avatar(username, new_avatar_url):
    try:
        user = get_by_username(username=username)
        if user:
            if not isinstance(new_avatar_url, str):
                res = cloudinary.uploader.upload(new_avatar_url)
                new_avatar_url = res.get('secure_url')

            user.anh_chan_dung = new_avatar_url
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False


def update_parent_phone(username, parent_phone):
    try:
        user = get_by_username(username=username)
        if user:
            user.so_dien_thoai_phu_huynh = parent_phone
            db.session.commit()
            return True
        return False
    except Exception:
        db.session.rollback()
        return False


def update_trang_thai_nguoi_dung(ma_nd):
    try:
        user = get_by_id(ma_nd)
        if user:
            user.tinh_trang_hoat_dong = not user.tinh_trang_hoat_dong
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        return False


def get_by_course_id(course_id):
    return KhoaHoc.query.get(course_id)


def get_by_course_category(course_category):
    return LoaiKhoaHoc.query.get(course_category)


def get_by_course_teacher_id(teacher_id, course_id):
    return KhoaHoc.query.filter_by(ma_khoa_hoc=course_id, ma_giao_vien=teacher_id).first()


def get_by_classroom_id(classroom_id):
    return PhongHoc.query.get(classroom_id)


def get_all_loai_khoa_hoc():
    return LoaiKhoaHoc.query.all()


def get_all_giao_vien():
    return GiaoVien.query.all()


def get_all_phong_hoc():
    return PhongHoc.query.all()


def tra_cuu_khoa_hoc(params=None, page=1, page_size=app.config["PAGE_SIZE"]):
    if params is None: params = {}
    query = KhoaHoc.query

    if kw := params.get('kw'):
        query = query.filter(or_(
            KhoaHoc.ma_khoa_hoc.ilike(f"%{kw}%"),
            KhoaHoc.ten_khoa_hoc.ilike(f"%{kw}%")
        ))

    if status := params.get('status'):
        try:
            query = query.filter(KhoaHoc.tinh_trang == TinhTrangKhoaHocEnum(int(status)))
        except:
            pass

    if from_date := params.get('from_date'):
        query = query.filter(KhoaHoc.ngay_bat_dau >= from_date)

    if to_date := params.get('to_date'):
        query = query.filter(KhoaHoc.ngay_bat_dau <= to_date)

    return query.order_by(KhoaHoc.ngay_bat_dau.desc()).paginate(page=page, per_page=page_size, error_out=False)


def lay_khoa_hoc_chua_dang_ky(student_id):
    subquery = db.session.query(BangDiem.ma_khoa_hoc).filter(BangDiem.ma_hoc_vien == student_id)
    return KhoaHoc.query.filter(
        KhoaHoc.tinh_trang == TinhTrangKhoaHocEnum.DANG_TUYEN_SINH,
        ~KhoaHoc.ma_khoa_hoc.in_(subquery)
    ).all()


def _base_user_query(ModelClass, kw=None, status=None):
    query = ModelClass.query
    if kw:
        query = query.filter(or_(
            ModelClass.ho_va_ten.ilike(f"%{kw}%"),
            ModelClass.ma_nguoi_dung.ilike(f"%{kw}%"),
            ModelClass.email.ilike(f"%{kw}%"),
            ModelClass.so_dien_thoai.ilike(f"%{kw}%")
        ))
    if status is not None and status != '':
        is_active = (str(status) == '1')
        query = query.filter(ModelClass.tinh_trang_hoat_dong == is_active)
    return query


def lay_danh_sach_hoc_vien(kw=None, status=None, nam_sinh=None, page=1, per_page=app.config["PAGE_SIZE"]):
    query = _base_user_query(HocVien, kw, status)
    if nam_sinh:
        try:
            query = query.filter(extract('year', HocVien.ngay_sinh) == int(nam_sinh))
        except:
            pass
    return query.order_by(HocVien.ngay_tao.desc()).paginate(page=page, per_page=per_page)


def lay_danh_sach_nhan_vien(kw=None, status=None, from_date=None, to_date=None, page=1,
                            per_page=app.config["PAGE_SIZE"]):
    query = _base_user_query(NhanVien, kw, status)
    if from_date: query = query.filter(NhanVien.ngay_tao >= from_date)
    if to_date: query = query.filter(NhanVien.ngay_tao <= to_date)
    return query.order_by(NhanVien.ngay_tao.desc()).paginate(page=page, per_page=per_page)


def lay_danh_sach_giao_vien(kw=None, status=None, from_date=None, to_date=None, page=1,
                            page_size=app.config["PAGE_SIZE"]):
    query = _base_user_query(GiaoVien, kw, status)
    if from_date: query = query.filter(GiaoVien.ngay_tao >= from_date)
    if to_date: query = query.filter(
        GiaoVien.ngay_tao <= to_date)
    return query.order_by(GiaoVien.ngay_tao.desc()).paginate(page=page, per_page=page_size)


def lay_ds_hoc_vien_cua_khoa(ma_khoa_hoc, page=1, page_size=app.config["PAGE_SIZE"], tu_khoa=None, ket_qua=None,
                             nam_sinh=None):
    query = BangDiem.query.join(HocVien).filter(BangDiem.ma_khoa_hoc == ma_khoa_hoc)
    if tu_khoa:
        query = query.filter(or_(HocVien.ho_va_ten.ilike(f"%{tu_khoa}%"), HocVien.ma_nguoi_dung.ilike(f"%{tu_khoa}%")))
    if nam_sinh:
        query = query.filter(extract('year', HocVien.ngay_sinh) == int(nam_sinh))
    if ket_qua:
        if ket_qua == 'dau':
            query = query.filter(BangDiem.ket_qua == True)
        elif ket_qua == 'rot':
            query = query.filter(BangDiem.ket_qua == False, BangDiem.diem_trung_binh != None)
        elif ket_qua == 'chua_xet':
            query = query.filter(BangDiem.diem_trung_binh == None)
    return query.paginate(page=page, per_page=page_size)


def dang_ky_khoa_hoc(ma_hoc_vien, ma_khoa_hoc):
    try:
        khoa_hoc = KhoaHoc.query.get(ma_khoa_hoc)
        if not khoa_hoc or khoa_hoc.si_so_hien_tai >= khoa_hoc.si_so_toi_da:
            return False
        ghi_danh = BangDiem(ma_hoc_vien=ma_hoc_vien, ma_khoa_hoc=ma_khoa_hoc)
        hoa_don = HoaDon(ma_hoc_vien=ma_hoc_vien, ma_khoa_hoc=ma_khoa_hoc, so_tien=khoa_hoc.hoc_phi)
        db.session.add_all([ghi_danh, hoa_don])
        khoa_hoc.si_so_hien_tai += 1
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def kiem_tra_trung_lich_hoc_vien(ma_hoc_vien, ma_khoa_hoc_moi):
    kh_moi = get_by_course_id(ma_khoa_hoc_moi)
    if not kh_moi: return False, "Khóa học không tồn tại"
    ds_khoa_hoc_da_dang_ky = KhoaHoc.query.join(BangDiem).filter(
        BangDiem.ma_hoc_vien == ma_hoc_vien,
        KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC
    ).all()
    if not ds_khoa_hoc_da_dang_ky: return True, "Hợp lệ"
    for kh_cu in ds_khoa_hoc_da_dang_ky:
        if (kh_moi.ngay_bat_dau <= kh_cu.ngay_ket_thuc) and (kh_moi.ngay_ket_thuc >= kh_cu.ngay_bat_dau):
            for lich_moi in kh_moi.lich_hoc:
                for lich_cu in kh_cu.lich_hoc:
                    if (lich_moi.thu == lich_cu.thu) and (lich_moi.ca_hoc == lich_cu.ca_hoc):
                        return False, f"Trùng lịch với {kh_cu.ten_khoa_hoc} ({lich_moi.thu.name}-{lich_moi.ca_hoc.name})"
    return True, "Hợp lệ"


def kiem_tra_xung_dot_lich(form_data, lich_hoc_list):
    try:
        si_so = int(form_data.get('si_so', 0))
        if not (10 <= si_so <= 100): return False, "Sĩ số 10-100."
        start_date = datetime.strptime(form_data['ngay_bat_dau'], '%Y-%m-%d')
        end_date = datetime.strptime(form_data['ngay_ket_thuc'], '%Y-%m-%d')
        if start_date > end_date: return False, "Ngày kết thúc lỗi."

        ma_gv = str(form_data['ma_giao_vien'])
        lich_tiem_nang = db.session.query(LichHoc, KhoaHoc).join(KhoaHoc).filter(
            KhoaHoc.tinh_trang != TinhTrangKhoaHocEnum.DA_KET_THUC,
            KhoaHoc.ngay_bat_dau <= end_date,
            KhoaHoc.ngay_ket_thuc >= start_date
        ).all()
        map_ban = {}
        for lich, khoa in lich_tiem_nang:
            key = f"{lich.thu.value}-{lich.ca_hoc.value}"
            if key not in map_ban: map_ban[key] = {'phong': [], 'gv': []}
            map_ban[key]['phong'].append(str(lich.ma_phong_hoc))
            map_ban[key]['gv'].append(str(khoa.ma_giao_vien))

        for item in lich_hoc_list:
            check_key = f"{item['thu']}-{item['ca']}"
            if check_key in map_ban:
                if str(item['ma_phong']) in map_ban[check_key]['phong']:
                    return False, f"Phòng {item['ma_phong']} đã bận vào Thứ {int(item['thu']) + 2}."
                if ma_gv in map_ban[check_key]['gv']:
                    return False, f"Giáo viên đã bận vào Thứ {int(item['thu']) + 2}."
        return True, "Hợp lệ"
    except Exception as e:
        return False, str(e)


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
            hoc_phi=float(data.get('hoc_phi', 0))
        )
        db.session.add(new_kh)

        for item in lich_hoc_list:
            db.session.add(LichHoc(
                ma_khoa_hoc=ma_moi,
                ma_phong_hoc=item['ma_phong'],
                thu=TuanEnum(int(item['thu'])),
                ca_hoc=CaHocEnum(int(item['ca']))
            ))
        db.session.commit()
        return True, "Thành công"
    except Exception as e:
        db.session.rollback()
        return False, str(e)
