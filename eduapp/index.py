import re
import time
import random
import math
from datetime import timedelta, date
import datetime
import admin
import cloudinary.uploader
import json
from flask import render_template, redirect, request, url_for, session, jsonify, flash
from flask_login import current_user, login_user, logout_user
from eduapp import app, dao, login_manager
from eduapp.decorators import anonymous_required, giao_vien_required, hoc_vien_required, \
    giao_vien_hoac_hoc_vien_required, tinh_trang_xac_nhan_email_required, login_user_required, quan_ly_required, \
    quan_ly_hoac_nhan_vien_required, hoc_vien_hoac_nhan_vien_required, bat_buoc_xac_minh_email
from eduapp.models import NguoiDungEnum, TinhTrangKhoaHocEnum, CaHocEnum, TrangThaiHoaDonEnum


@app.context_processor
def common_attribute():
    return {
        "categories": dao.load_categories(),
        "contact_email": app.config.get('MAIL_USERNAME'),
        "hotline": dao.lay_thong_tin_quan_ly_chinh()
    }


@app.route('/')
def index():
    return render_template("index.html")


@app.errorhandler(404)
def page_not_found(e):
    current_path = request.path
    if current_path.startswith('/admin'):
        return redirect('/admin')
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.login(username, password)

        if user:
            if not user.tinh_trang_hoat_dong:
                msg = f"Tài khoản bị khóa! Liên hệ: {app.config.get('MAIL_USERNAME')}."
                flash(msg, "danger")
                return redirect(url_for('login'))
            session.permanent = True
            login_user(user)

            next_page = request.args.get('next')
            flash(f"Chào mừng {user.ho_va_ten} đã quay trở lại!", "success")
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash("Tên tài khoản hoặc mật khẩu không chính xác.", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/logout')
def logout():
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('login'))


@login_manager.user_loader
def load_user(user_id):
    return dao.get_by_id(user_id)


@app.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    if request.method == 'GET':
        session.pop('register_info', None)
        return render_template("register.html", data={}, show_step2=False)

    show_step2 = False
    focus_field = None
    data = session.get('register_info', {})
    form_data = request.form.to_dict()
    data.update(form_data)
    session['register_info'] = data

    if 'back_to_step1' in request.form:
        return render_template("register.html", data=data, show_step2=False)

    step = request.form.get('step')

    if step == '1':
        password = data.get('password')
        re_enter_password = data.get('re_enter_password')
        username = data.get('username')

        if dao.get_by_username(username):
            flash('Tài khoản đã tồn tại!', 'danger')
            data['username'] = ''
            focus_field = 'username'
        elif not password or password != re_enter_password:
            flash('Mật khẩu xác nhận không chính xác!', 'danger')
            data['password'] = ''
            data['re_enter_password'] = ''
            focus_field = 'password'
        else:
            show_step2 = True

    elif step == '2':
        email = data.get('email')
        if dao.get_by_email(email):
            flash('Email này đã được sử dụng bởi tài khoản khác!', 'danger')
            data['email'] = ''
            show_step2 = True
        else:
            image_file = request.files.get('image')
            path_image = "https://res.cloudinary.com/db4bjqp4f/image/upload/v1765436438/shtnr60mecp057e2uctk.jpg"
            if image_file and image_file.filename != '':
                try:
                    res = cloudinary.uploader.upload(image_file)
                    path_image = res['secure_url']
                except Exception as ex:
                    print(f"Lỗi upload: {ex}")

            dob_val = None
            try:
                if data.get('dob'):
                    dob_val = datetime.datetime.strptime(data.get('dob'), '%Y-%m-%d')
            except ValueError:
                flash("Định dạng ngày sinh không hợp lệ.", "danger")
                show_step2 = True

            if dob_val:
                is_success = dao.add_user(
                    NguoiDungEnum.HOC_VIEN,
                    ho_va_ten=data.get('name'),
                    ten_dang_nhap=data.get('username'),
                    mat_khau=data.get('password'),
                    so_dien_thoai=data.get('phone_number'),
                    email=email,
                    anh_chan_dung=path_image,
                    ngay_sinh=dob_val
                )
                if is_success:
                    session.pop('register_info', None)
                    flash("Đăng ký tài khoản thành công! Vui lòng đăng nhập.", "success")
                    return redirect(url_for('login'))
                else:
                    flash('Đã có lỗi hệ thống xảy ra, vui lòng thử lại sau.', 'danger')
                    show_step2 = True

    return render_template("register.html", data=data, show_step2=show_step2, focus_field=focus_field)


@app.route('/forgot_password', methods=['GET', 'POST'])
@anonymous_required
def forgot_password():
    if request.method == "GET":
        session.pop('reset_info', None)
        return render_template("forgot_password.html", show_step2=False, data={})

    show_step2 = False
    reset_info = session.get('reset_info', {})
    step = request.form.get("step")

    if step == "1":
        username = request.form.get("username")
        email = request.form.get("email")
        user = dao.get_by_username_email(username, email)

        if not user:
            flash('Tên tài khoản hoặc Email không chính xác.', 'danger')
            reset_info = {'username': username, 'email': email}
        else:
            if not user.tinh_trang_hoat_dong:
                msg = f"Tài khoản đã bị khóa! Liên hệ: {app.config['MAIL_USERNAME']} để được hỗ trợ."
                flash(msg, "danger")
                return redirect(url_for('forgot_password'))

            otp_code = str(random.randint(0, 999999)).zfill(6)
            reset_info = {
                'username': username,
                'email': email,
                'otp_code': otp_code,
                'name': user.ho_va_ten
            }
            session['reset_info'] = reset_info

            if dao.send_otp_email_forgot_password(email, user.ho_va_ten, otp_code):
                flash(f"Mã xác nhận đã được gửi đến email {email}", "success")
                show_step2 = True
            else:
                flash("Lỗi gửi email. Vui lòng thử lại sau.", "danger")

    elif step == "resend":
        if not reset_info:
            return redirect(url_for('forgot_password'))

        new_otp = str(random.randint(0, 999999)).zfill(6)
        reset_info['otp_code'] = new_otp
        session['reset_info'] = reset_info

        if dao.send_otp_email_forgot_password(reset_info.get('email'), reset_info.get('name'), new_otp):
            flash("Mã xác nhận mới đã được gửi vào email của bạn.", "info")
        else:
            flash("Lỗi hệ thống khi gửi lại mã.", "danger")
        show_step2 = True

    elif step == "2":
        if not reset_info:
            return redirect(url_for('forgot_password'))

        user_otp = request.form.get("verify")
        new_password = request.form.get("new_password")
        re_password = request.form.get("re_enter_password")
        real_otp = reset_info.get('otp_code')
        saved_username = reset_info.get('username')

        if not real_otp or user_otp != real_otp:
            reset_info.pop('otp_code', None)
            session['reset_info'] = reset_info
            flash('Mã xác nhận không chính xác. Mã này đã bị vô hiệu hóa.', 'danger')
            show_step2 = True
        elif new_password != re_password:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
            show_step2 = True
        else:
            if dao.update_password(saved_username, new_password):
                session.pop('reset_info', None)
                flash("Đổi mật khẩu thành công! Vui lòng đăng nhập lại.", "success")
                return redirect(url_for('login'))
            else:
                flash("Lỗi hệ thống khi cập nhật mật khẩu.", "danger")
                show_step2 = True

    return render_template("forgot_password.html", show_step2=show_step2, data=reset_info)


@app.route('/change_password', methods=['GET', 'POST'])
@login_user_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        re_enter_password = request.form.get('re_enter_password')

        if dao.hash_password(old_password) != current_user.mat_khau:
            flash("Mật khẩu cũ không chính xác!", "danger")
            return redirect(url_for('change_password'))

        elif new_password != re_enter_password:
            flash("Mật khẩu xác nhận không trùng khớp!", "danger")
            return redirect(url_for('change_password'))

        else:
            if dao.update_password(current_user.ten_dang_nhap, new_password):
                flash("Đổi mật khẩu thành công!", "success")
                return redirect('/')
            else:
                flash("Lỗi hệ thống, vui lòng thử lại sau.", "danger")
                return redirect(url_for('change_password'))

    return render_template("change_password.html")


@app.route('/verify', methods=['GET', 'POST'])
@login_user_required
@hoc_vien_required
@tinh_trang_xac_nhan_email_required
def verify_page():
    email = current_user.email
    current_uid = str(current_user.ma_nguoi_dung)
    current_time = time.time()

    otp_lifetime = app.config.get("OTP_LIFETIME", 60)
    max_resend_limit = app.config.get("MAX_RESEND_LIMIT", 5)
    resend_block_time = app.config.get("RESEND_BLOCK_TIME", 300)

    user_otp_data = session.get('otp_data', {})

    if str(user_otp_data.get('user_id', '')) != current_uid:
        user_otp_data = {}
        session.pop('otp_data', None)

    blocked_until = user_otp_data.get('blocked_until', 0)

    if current_time < blocked_until:
        if request.args.get('action') == 'resend':
            flash("Bạn đang bị tạm khóa gửi mã. Vui lòng đợi.", "warning")
            return redirect(url_for('verify_page'))
        wait_time_left = math.ceil(blocked_until - current_time)
        return render_template("verify.html", block_time=wait_time_left, is_blocked=True)

    if request.method == 'POST':
        user_input_otp = request.form.get('verify', '').strip()

        if not user_otp_data:
            flash("Vui lòng yêu cầu gửi mã mới.", "danger")
            return redirect(url_for('verify_page'))

        last_sent = user_otp_data.get('last_sent', 0)
        if (current_time - last_sent) > otp_lifetime:
            session.pop('otp_data', None)
            flash("Mã xác nhận đã hết hạn.", "warning")
            return redirect(url_for('verify_page'))

        if user_input_otp == user_otp_data.get('otp'):
            if dao.update_tinh_trang_email(current_user.ten_dang_nhap):
                session.pop('otp_data', None)
                flash("Xác minh thành công!", "success")
                return redirect('/')

        flash("Mã xác nhận không chính xác.", "danger")
        return redirect(url_for('verify_page'))

    wait_time = 0
    last_sent = user_otp_data.get('last_sent', 0)
    if user_otp_data and (current_time - last_sent < otp_lifetime):
        wait_time = math.ceil(otp_lifetime - (current_time - last_sent))

    action = request.args.get('action')
    if (action == 'resend' and wait_time == 0) or (not user_otp_data and action != 'resend'):
        current_attempts = user_otp_data.get('attempts', 0) if user_otp_data else 0

        if current_attempts >= max_resend_limit:
            user_otp_data['blocked_until'] = current_time + resend_block_time
            user_otp_data['user_id'] = current_uid
            session['otp_data'] = user_otp_data
            flash("Yêu cầu quá nhiều lần. Bạn bị tạm chặn.", "error")
            return redirect(url_for('verify_page'))

        new_otp = str(random.randint(0, 999999)).zfill(6)
        session['otp_data'] = {
            'user_id': current_uid, 'otp': new_otp,
            'last_sent': current_time, 'attempts': current_attempts + 1,
            'blocked_until': 0
        }
        if dao.send_verification_email(email, current_user.ho_va_ten, new_otp):
            flash(f"Mã mới đã gửi tới {email}", "info")
            return redirect(url_for('verify_page'))
        flash("Lỗi gửi mail.", "danger")

    return render_template("verify.html", wait_time=wait_time)


@app.route('/update-email-verify', methods=['POST'])
@login_user_required
def update_email_verify():
    new_email = request.form.get('new_email', '').strip()

    if not new_email:
        flash("Vui lòng nhập địa chỉ email hợp lệ.", "warning")
        return redirect(url_for('verify_page'))

    existing_user = dao.get_by_email(email=new_email)
    if existing_user and existing_user.ma_nguoi_dung != current_user.ma_nguoi_dung:
        flash("Email này đã được sử dụng bởi một tài khoản khác.", "danger")
        return redirect(url_for('verify_page'))

    if dao.update_email(current_user.ten_dang_nhap, new_email):
        flash("Cập nhật email thành công! Mã xác minh mới đã được gửi.", "success")
        return redirect(url_for('verify_page', action='resend'))
    else:
        flash("Lỗi hệ thống: Không thể cập nhật email lúc này.", "danger")
        return redirect(url_for('verify_page'))


@app.route('/update_avatar', methods=['POST'])
@login_user_required
def update_avatar():
    avatar = request.files.get('avatar')
    if avatar:
        if dao.update_avatar(current_user.ten_dang_nhap, avatar):
            flash("Cập nhật ảnh đại diện thành công!", "success")
        else:
            flash("Lỗi khi cập nhật ảnh đại diện.", "danger")
    return redirect(url_for('profile', user_id=current_user.ma_nguoi_dung))


@app.route('/update_parent_phone', methods=['POST'])
@login_user_required
def update_parent_phone():
    parent_phone = request.form.get('parent_phone')
    target_user_id = request.form.get('user_id')

    if current_user.ma_nguoi_dung != target_user_id and current_user.vai_tro.name != 'QUAN_LY':
        flash("Bạn không có quyền thực hiện thay đổi này.", "warning")
        return redirect(url_for('profile', user_id=target_user_id))

    if dao.update_parent_phone(target_user_id, parent_phone):
        flash("Cập nhật số điện thoại phụ huynh thành công!", "success")
    else:
        flash("Cập nhật thất bại. Vui lòng thử lại.", "danger")

    return redirect(url_for('profile', user_id=target_user_id))


@app.route('/profile', defaults={'user_id': None})
@app.route('/profile/<user_id>')
@login_user_required
def profile(user_id):
    if user_id:
        user_to_show = dao.get_by_id(user_id)
        if not user_to_show:
            return redirect('/')
    else:
        user_to_show = current_user
    return render_template("profile.html", user=user_to_show)


@app.route('/schedule', methods=['GET'])
@login_user_required
@giao_vien_hoac_hoc_vien_required
@bat_buoc_xac_minh_email
def schedule():
    cac_thu = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    ds_khoa_hoc = []
    is_teacher = False
    if current_user.vai_tro == NguoiDungEnum.HOC_VIEN:
        ds_khoa_hoc = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    elif current_user.vai_tro == NguoiDungEnum.GIAO_VIEN:
        ds_khoa_hoc = current_user.nhung_khoa_hoc
        is_teacher = True
    try:
        offset = int(request.args.get('offset', 0))
    except ValueError:
        offset = 0
    today = datetime.datetime.now()
    start_of_week_current = today - timedelta(days=today.weekday())
    start_of_target_week = start_of_week_current + timedelta(weeks=offset)
    target_year, target_week_iso, _ = start_of_target_week.isocalendar()
    tuan_hien_thi = {
        "week": target_week_iso,
        "year": target_year,
        "days": [],
        "full_dates": [],
        "schedule": {
            "CA_SANG": [[] for _ in range(7)],
            "CA_CHIEU": [[] for _ in range(7)]
        }
    }
    for i in range(7):
        current_date = start_of_target_week + timedelta(days=i)
        tuan_hien_thi["days"].append(current_date.strftime("%d/%m"))
        tuan_hien_thi["full_dates"].append(current_date)
    for khoa_hoc in ds_khoa_hoc:
        ngay_cuoi_tuan_target = start_of_target_week + timedelta(days=6)
        if khoa_hoc.ngay_bat_dau.date() <= ngay_cuoi_tuan_target.date() and khoa_hoc.ngay_ket_thuc.date() >= start_of_target_week.date():
            for lich in khoa_hoc.lich_hoc:
                day_index = lich.thu.value
                specific_date_of_week = tuan_hien_thi["full_dates"][day_index]
                if khoa_hoc.ngay_bat_dau.date() <= specific_date_of_week.date() <= khoa_hoc.ngay_ket_thuc.date():
                    ca_key = lich.ca_hoc.name
                    buoi_hoc_info = {
                        "khoa_hoc": khoa_hoc,
                        "phong_hoc": lich.phong_hoc,
                        "gio_bat_dau": 7 if lich.ca_hoc == CaHocEnum.CA_SANG else 13,
                        "gio_ket_thuc": 11 if lich.ca_hoc == CaHocEnum.CA_SANG else 17
                    }
                    tuan_hien_thi["schedule"][ca_key][day_index].append(buoi_hoc_info)
    today_index = -1
    if offset == 0:
        today_index = today.weekday()
    return render_template('schedule.html', cac_thu=cac_thu, tuan_hien_thi=tuan_hien_thi, offset=offset,
                           is_teacher=is_teacher, today_index=today_index)


@app.route('/scoreboard', methods=['GET'])
@login_user_required
@hoc_vien_required
@bat_buoc_xac_minh_email
def scoreboard():
    ds_khoa_hoc_cua_hv = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    if not ds_khoa_hoc_cua_hv:
        return render_template('student/scoreboard.html', ma_khoa_hoc_hien_tai=None, ds_khoa_hoc=[])
    ma_khoa_hoc_dang_chon = request.args.get('course_id')
    ds_ma_hop_le = [kh.ma_khoa_hoc for kh in ds_khoa_hoc_cua_hv]
    if not ma_khoa_hoc_dang_chon or ma_khoa_hoc_dang_chon not in ds_ma_hop_le:
        ma_mac_dinh = ds_khoa_hoc_cua_hv[0].ma_khoa_hoc
        return redirect(url_for('scoreboard', course_id=ma_mac_dinh))
    course = dao.get_by_course_id(ma_khoa_hoc_dang_chon)
    list_bang_diem = {}
    if course:
        cau_truc_diem = dao.get_cau_truc_diem(course.ma_khoa_hoc)
        bang_diem = dao.get_by_scoreboard_id(current_user.ma_nguoi_dung, course.ma_khoa_hoc)
        if cau_truc_diem and bang_diem:
            list_bang_diem = bang_diem.lay_chi_tiet_diem(cau_truc_diem)
    return render_template("student/scoreboard.html", ma_khoa_hoc_hien_tai=ma_khoa_hoc_dang_chon,
                           ds_khoa_hoc=ds_khoa_hoc_cua_hv, list_bang_diem=list_bang_diem)


@app.route('/course_fee')
@login_user_required
@hoc_vien_required
@bat_buoc_xac_minh_email
def course_fee():
    ds_hoa_don = list(current_user.nhung_hoa_don)
    ds_hoa_don.sort(key=lambda x: x.ngay_tao, reverse=True)
    tong_tien = sum(hd.so_tien for hd in ds_hoa_don if hd.trang_thai.value == 2)
    return render_template('student/course_fee.html', ds_hoa_don=ds_hoa_don, tong_tien=tong_tien,
                           now=datetime.datetime.now())


@app.route("/register_course", methods=['GET', 'POST'])
@bat_buoc_xac_minh_email
def register_course():
    list_thong_bao = []

    if current_user.is_authenticated:
        ma_hv_target = request.args.get('ma_hoc_vien')
        if ma_hv_target and current_user.user_role == NguoiDungEnum.NHAN_VIEN:
            target_user = dao.get_by_id(ma_hv_target)
        else:
            target_user = current_user
    else:
        target_user = None

    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.url))

        ds_ma_khoa_hoc = request.form.getlist('course_ids')
        if ds_ma_khoa_hoc and target_user:
            for ma_kh in ds_ma_khoa_hoc:
                kh_obj = dao.get_by_course_id(ma_kh)
                ten_khoa = kh_obj.ten_khoa_hoc if kh_obj else ma_kh

                hop_le, ly_do = dao.kiem_tra_trung_lich_hoc_vien(target_user.ma_nguoi_dung, ma_kh)
                if hop_le:
                    kq = dao.dang_ky_khoa_hoc(target_user.ma_nguoi_dung, ma_kh)
                    if kq:
                        list_thong_bao.append({'type': 'success', 'content': f"Khóa '{ten_khoa}': Đăng ký thành công!"})
                    else:
                        list_thong_bao.append({'type': 'danger', 'content': f"Khóa '{ten_khoa}': Lỗi hệ thống."})
                else:
                    list_thong_bao.append({'type': 'warning', 'content': f"Khóa '{ten_khoa}': {ly_do}"})
        else:
            list_thong_bao.append({'type': 'warning', 'content': "Bạn chưa chọn khóa học nào!"})

    kw = request.args.get('kw')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    cate_id = request.args.get('cate_id')

    student_id = target_user.ma_nguoi_dung if target_user else None

    ds_khoa_hoc = dao.lay_khoa_hoc_chua_dang_ky(
        ma_nguoi_dung=student_id,
        kw=kw,
        from_date=from_date,
        to_date=to_date,
        ma_loai=cate_id
    )

    return render_template("student/register_course.html", ds_khoa_hoc=ds_khoa_hoc, thong_bao=list_thong_bao,
                           target_user=target_user)


@app.route('/grading', methods=['GET', 'POST'])
@login_user_required
@giao_vien_required
def grading():
    ds_khoa_hoc = current_user.nhung_khoa_hoc
    selected_course_id = request.args.get('course_id') or request.form.get('course_id')

    if not selected_course_id and ds_khoa_hoc:
        selected_course_id = ds_khoa_hoc[0].ma_khoa_hoc

    if request.method == 'POST' and selected_course_id:
        action = request.form.get('action_type')
        success = False
        message = ""

        if action == 'create_structure':
            ds_ten = request.form.getlist('ten_thanh_phan[]')
            ds_trong_so = request.form.getlist('trong_so[]')
            success, message = dao.tao_cau_truc_diem(selected_course_id, ds_ten, ds_trong_so)
        elif action in ['save_draft', 'publish']:
            is_draft = (action == 'save_draft')
            success, message = dao.luu_bang_diem(selected_course_id, request.form, is_draft)

        category = 'success' if success else 'danger'
        flash(message, category)

        return redirect(url_for('grading', course_id=selected_course_id))

    selected_course = None
    cau_truc_diem = []
    bang_diem_data = []

    if selected_course_id:
        selected_course = dao.get_by_course_teacher_id(current_user.ma_nguoi_dung, selected_course_id)
        if selected_course:
            cau_truc_diem = selected_course.cau_truc_diem
            if cau_truc_diem:
                for bd in selected_course.ds_dang_ky:
                    chi_tiet = bd.lay_chi_tiet_diem(cau_truc_diem)
                    bang_diem_data.append({'hoc_vien': bd.hoc_vien, 'ma_bang_diem': bd.id, 'diem_so': chi_tiet})

    return render_template("teacher/grading.html", ds_khoa_hoc=ds_khoa_hoc, selected_course=selected_course,
                           cau_truc_diem=cau_truc_diem, bang_diem_data=bang_diem_data)


@app.route('/attendance', methods=['GET', 'POST'])
@login_user_required
@giao_vien_required
def attendance():
    ds_khoa_hoc = getattr(current_user, 'nhung_khoa_hoc', [])
    ds_khoa_hoc = sorted(ds_khoa_hoc, key=lambda x: x.ngay_bat_dau, reverse=True)

    course_id = request.args.get('course_id') or request.form.get('course_id')

    if not course_id and ds_khoa_hoc:
        course_id = ds_khoa_hoc[0].ma_khoa_hoc

    course = None
    if course_id:
        course = dao.get_by_course_id(course_id)

    if request.method == 'POST' and course:
        if dao.save_attendance_sheet(course.ma_khoa_hoc, request.form):
            flash('Đã lưu điểm danh thành công!', 'success')
            return redirect(url_for('attendance', course_id=course_id))
        else:
            flash('Lỗi khi lưu dữ liệu.', 'danger')

    sessions = []
    student_rows = []
    target_session_id = ""
    today_str = date.today().strftime('%Y-%m-%d')

    if course:
        sessions, student_rows, target_session_id = dao.get_attendance_sheet_data(course)

    return render_template('teacher/attendance.html', ds_khoa_hoc=ds_khoa_hoc, course=course, sessions=sessions,
                           student_rows=student_rows, target_session_id=target_session_id, today_str=today_str)


@app.route('/manager/profile/<string:ma_nguoi_dung>', methods=['GET'])
@login_user_required
@quan_ly_hoac_nhan_vien_required
def manager_profile_user(ma_nguoi_dung):
    user_to_show = dao.get_by_id(ma_nguoi_dung)
    if not user_to_show:
        return redirect('/')
    if user_to_show.vai_tro != NguoiDungEnum.HOC_VIEN and current_user.vai_tro == NguoiDungEnum.NHAN_VIEN:
        return redirect(url_for('manager_student_list'))
    return render_template('manager/profile_user.html', user=user_to_show)


@app.route('/manager/reset_password/<ma_nguoi_dung>', methods=['GET', 'POST'])
@login_user_required
@quan_ly_required
def manager_reset_password_page(ma_nguoi_dung):
    user = dao.get_by_id(ma_nguoi_dung)
    if not user:
        flash("Người dùng không tồn tại!", "danger")
        return redirect(url_for('manager_course_list'))

    if request.method == 'GET':
        back_url = request.referrer or url_for('manager_course_list')
    else:
        back_url = request.form.get('back_url')

    if request.method == 'POST':
        mat_khau_moi = request.form.get('new_password')
        xac_nhan_mk = request.form.get('re_enter_password')

        if not mat_khau_moi or len(mat_khau_moi) < 6:
            flash("Mật khẩu phải từ 6 ký tự trở lên.", "danger")
        elif mat_khau_moi != xac_nhan_mk:
            flash("Mật khẩu xác nhận không khớp.", "danger")
        else:
            if dao.update_password(user.ten_dang_nhap, mat_khau_moi):
                flash(f"Đã đặt lại mật khẩu cho {user.ho_va_ten} thành công!", "success")
                return redirect(back_url)
            else:
                flash("Có lỗi xảy ra trong quá trình cập nhật mật khẩu.", "danger")

    return render_template('manager/reset_password.html', user=user, back_url=back_url)


@app.route('/manager/courses', methods=['GET'])
@login_user_required
@quan_ly_required
def manager_course_list():
    dao.cap_nhat_database_tinh_trang_khoa_hoc()
    page = request.args.get('page', 1, type=int)
    search_params = {
        'kw': request.args.get('kw', '').strip(),
        'status': request.args.get('status'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date')}
    pagination = dao.tra_cuu_khoa_hoc(search_params, page=page, page_size=app.config["PAGE_SIZE"])
    return render_template('manager/course_list.html', pagination=pagination, TinhTrangKhoaHocEnum=TinhTrangKhoaHocEnum)


@app.route('/manager/course/<string:ma_khoa_hoc>', methods=['GET'])
@login_user_required
@quan_ly_required
def manager_course_detail(ma_khoa_hoc):
    khoa_hoc = dao.get_by_course_id(ma_khoa_hoc)
    if not khoa_hoc:
        return redirect(url_for('manager_course_list', error_msg=f"Không tìm thấy khóa học {ma_khoa_hoc}"))
    page = request.args.get('page', 1, type=int)
    tu_khoa = request.args.get('tu_khoa', '')
    nam_sinh = request.args.get('nam_sinh', '')
    ket_qua = request.args.get('ket_qua', '')
    pagination = dao.lay_ds_hoc_vien_cua_khoa(
        ma_khoa_hoc,
        page=page,
        page_size=app.config["PAGE_SIZE"],
        tu_khoa=tu_khoa,
        nam_sinh=nam_sinh,
        ket_qua=ket_qua)
    return render_template('manager/course_detail.html', khoa_hoc=khoa_hoc, pagination=pagination, tu_khoa=tu_khoa,
                           nam_sinh=nam_sinh, ket_qua=ket_qua)


@app.route('/manager/create_course', methods=['GET', 'POST'])
@login_user_required
@quan_ly_required
def manager_create_course():
    form_data = {}
    old_lich_hoc = []
    lich_ban_data = dao.lay_tat_ca_lich_ban()

    if request.method == 'POST':
        try:
            raw_hoc_phi = request.form.get('hoc_phi', '0').replace('.', '').replace(',', '')
            form_data = {
                'ten_khoa_hoc': request.form.get('ten_khoa_hoc', ''),
                'ma_loai_khoa_hoc': request.form.get('ma_loai_khoa_hoc', ''),
                'hoc_phi': raw_hoc_phi,
                'ma_giao_vien': request.form.get('ma_giao_vien', ''),
                'si_so': request.form.get('si_so', '30'),
                'thoi_luong': request.form.get('thoi_luong', '0'),
                'ngay_bat_dau': request.form.get('ngay_bat_dau', ''),
                'ngay_ket_thuc': request.form.get('ngay_ket_thuc', '')
            }

            ds_thu = request.form.getlist('thu[]')
            ds_ca = request.form.getlist('ca[]')
            ds_phong = request.form.getlist('phong[]')

            lich_hoc_list = []
            seen_slots = set()
            for i in range(len(ds_thu)):
                item = {'thu': ds_thu[i], 'ca': ds_ca[i], 'ma_phong': ds_phong[i]}
                old_lich_hoc.append(item)
                if not ds_thu[i] or not ds_ca[i] or not ds_phong[i]: continue

                slot_key = f"{ds_thu[i]}-{ds_ca[i]}"
                if slot_key in seen_slots: continue
                seen_slots.add(slot_key)
                lich_hoc_list.append(item)

            so_buoi = len(lich_hoc_list)
            if so_buoi < 3:
                flash(f"Vui lòng thêm ít nhất 3 buổi học (Hiện tại: {so_buoi}).", "warning")
            else:
                is_valid, message = dao.kiem_tra_xung_dot_lich(form_data, lich_hoc_list)
                if is_valid:
                    res, dao_msg = dao.tao_khoa_hoc_moi(form_data, lich_hoc_list)
                    if res:
                        flash(dao_msg, "success")
                        # Chuyển hướng sau khi thành công để reset form
                        return redirect(url_for('manager_create_course'))
                    else:
                        flash(f"Lỗi hệ thống: {dao_msg}", "danger")
                else:
                    flash(message, "warning")
        except Exception as e:
            flash(f"Lỗi dữ liệu: {str(e)}", "danger")

    ds_loai = dao.get_all_loai_khoa_hoc()
    ds_gv = dao.get_all_giao_vien()
    ds_phong = dao.get_all_phong_hoc()

    return render_template('manager/create_course.html', loai_kh=ds_loai, ds_gv=ds_gv, ds_phong=ds_phong,
                           form_data=form_data, old_lich_hoc=old_lich_hoc,
                           lich_ban_json=json.dumps(lich_ban_data, default=str))


@app.route('/manager/employees', methods=['GET'])
@login_user_required
@quan_ly_required
def manager_employee_list():
    page = request.args.get('page', 1, type=int)
    kw = request.args.get('kw')
    status = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    pagination = dao.lay_danh_sach_nhan_vien(
        kw=kw,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page
    )
    return render_template('manager/employee_list.html', pagination=pagination)


@app.route('/manager/students', methods=['GET'])
@login_user_required
@quan_ly_hoac_nhan_vien_required
def manager_student_list():
    kw = request.args.get('kw', '')
    status = request.args.get('status')
    nam_sinh = request.args.get('nam_sinh')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    pagination = dao.lay_danh_sach_hoc_vien(
        kw=kw,
        status=status,
        nam_sinh=nam_sinh,
        page=page
    )
    return render_template('manager/student_list.html', pagination=pagination)


@app.route('/manager/teachers', methods=['GET'])
@login_user_required
@quan_ly_required
def manager_teacher_list():
    kw = request.args.get('kw', '')
    status = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    page = request.args.get('page', 1, type=int)
    pagination = dao.lay_danh_sach_giao_vien(
        kw=kw,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page
    )
    return render_template('manager/teacher_list.html', pagination=pagination)


@app.route('/manager/edit_enrollment/<ma_khoa_hoc>', methods=['GET', 'POST'])
@login_user_required
@quan_ly_required
def manager_edit_enrollment(ma_khoa_hoc):
    kh = None
    if ma_khoa_hoc == 'ALL':
        min_limit = dao.lay_si_so_hien_tai_lon_nhat()
    else:
        kh = dao.get_by_course_id(ma_khoa_hoc)
        if not kh:
            flash("Không tìm thấy khóa học", "danger")
            return redirect(url_for('manager_course_list'))
        min_limit = kh.si_so_hien_tai

    if request.method == 'POST':
        try:
            new_si_so = int(request.form.get('si_so_toi_da'))

            if new_si_so < min_limit:
                flash(f"Lỗi: Không thể thiết lập thấp hơn {min_limit} (Do sĩ số thực tế đang học).", "warning")
            else:
                if ma_khoa_hoc == 'ALL':
                    dao.cap_nhat_si_so_toan_bo(new_si_so)
                    flash(f"Đã đồng bộ sĩ số tối đa thành {new_si_so} cho TẤT CẢ khóa học.", "success")
                else:
                    dao.cap_nhat_si_so_toi_da(ma_khoa_hoc, new_si_so)
                    flash(f"Đã cập nhật sĩ số thành {new_si_so} cho khóa học {kh.ten_khoa_hoc}.", "success")

                return redirect(url_for('manager_course_list'))

        except ValueError:
            flash("Lỗi: Vui lòng nhập một số nguyên hợp lệ.", "danger")
        except Exception as e:
            flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return render_template('manager/edit_enrollment.html', khoa_hoc=kh, min_limit=min_limit)


@app.route('/manager/edit_tuition/<ma_khoa_hoc>', methods=['GET', 'POST'])
@login_user_required
@quan_ly_required
def manager_edit_tuition(ma_khoa_hoc):
    kh = None
    if ma_khoa_hoc == 'ALL':
        if request.method == 'POST':
            try:
                percent = float(request.form.get('percent_value', 0))
                if percent <= 0 or percent > 100:
                    flash("Lỗi: Phần trăm giảm giá không hợp lệ.", "danger")
                else:
                    dao.cap_nhat_hoc_phi_theo_phan_tram(percent)
                    flash(f"Đã áp dụng giảm giá {int(percent)}% cho TOÀN BỘ khóa học đang hoạt động.", "success")
                    return redirect(url_for('manager_course_list'))
            except ValueError:
                flash("Lỗi dữ liệu nhập.", "danger")
            except Exception as e:
                flash(f"Lỗi hệ thống: {str(e)}", "danger")
    else:
        kh = dao.get_by_course_id(ma_khoa_hoc)
        if not kh:
            flash("Không tìm thấy khóa học", "danger")
            return redirect(url_for('manager_course_list'))

        if request.method == 'POST':
            try:
                new_hoc_phi = float(request.form.get('hoc_phi_moi'))
                if new_hoc_phi < 0:
                    flash("Lỗi: Học phí không được là số âm.", "danger")
                else:
                    dao.cap_nhat_hoc_phi(ma_khoa_hoc, new_hoc_phi)
                    flash(f"Đã cập nhật học phí thành {int(new_hoc_phi):,} VND.", "success")
                    return redirect(url_for('manager_course_list'))
            except ValueError:
                flash("Lỗi: Dữ liệu nhập vào không hợp lệ.", "danger")
            except Exception as e:
                flash(f"Lỗi hệ thống: {str(e)}", "danger")

    return render_template('manager/edit_tuition.html', khoa_hoc=kh)


@app.route('/manager/add_user/<role_type>', methods=['GET', 'POST'])
@login_user_required
@quan_ly_hoac_nhan_vien_required
def manager_add_user(role_type):
    if current_user.vai_tro == NguoiDungEnum.NHAN_VIEN and role_type != 'HOC_VIEN':
        return redirect(url_for('manager_add_user', role_type='HOC_VIEN'))

    ROLE_MAP = {
        'HOC_VIEN': {'enum': NguoiDungEnum.HOC_VIEN, 'title': 'Thêm Học Viên Mới',
                     'list_route': 'manager_student_list'},
        'GIAO_VIEN': {'enum': NguoiDungEnum.GIAO_VIEN, 'title': 'Thêm Giáo Viên Mới',
                      'list_route': 'manager_teacher_list'},
        'NHAN_VIEN': {'enum': NguoiDungEnum.NHAN_VIEN, 'title': 'Thêm Nhân Viên Mới',
                      'list_route': 'manager_employee_list'},
    }

    config = ROLE_MAP.get(role_type)
    if not config:
        flash("Loại tài khoản không hợp lệ", "danger")
        return redirect(url_for('index'))

    back_url = url_for(config['list_route'])
    session_key = f'manager_add_user_{role_type}'

    if request.method == 'GET':
        session.pop(session_key, None)
        return render_template("manager/add_user.html", data={}, show_step2=False,
                               role_title=config['title'], role_name=role_type, back_url=back_url)

    show_step2 = False
    data = session.get(session_key, {})
    form_data = request.form.to_dict()
    data.update(form_data)
    session[session_key] = data

    if 'back_to_step1' in request.form:
        return render_template("manager/add_user.html", data=data, show_step2=False,
                               role_title=config['title'], role_name=role_type, back_url=back_url)

    step = request.form.get('step')
    if step == '1':
        password = data.get('password')
        re_enter_password = data.get('re_enter_password')
        username = data.get('username')

        if dao.get_by_username(username):
            flash('Tên đăng nhập đã tồn tại!', 'warning')
            data['username'] = ''
        elif not password or password != re_enter_password:
            flash('Mật khẩu xác nhận không khớp!', 'warning')
        else:
            show_step2 = True

    elif step == '2':
        email = data.get('email')
        if dao.get_by_email(email):
            flash('Email này đã được sử dụng!', 'warning')
            show_step2 = True
        else:
            image_file = request.files.get('image')
            path_image = None
            if image_file and image_file.filename != '':
                try:
                    res = cloudinary.uploader.upload(image_file)
                    path_image = res['secure_url']
                except Exception as ex:
                    print(f"Lỗi upload ảnh: {ex}")

            dob_val = None
            if role_type == 'HOC_VIEN':
                dob_str = data.get('dob')
                if dob_str:
                    try:
                        dob_val = datetime.datetime.strptime(dob_str, '%Y-%m-%d')
                    except ValueError:
                        flash("Ngày sinh không hợp lệ.", "danger")
                        show_step2 = True

            if not session.get('_flashes'):
                user_params = {
                    'ho_va_ten': data.get('name'),
                    'ten_dang_nhap': data.get('username'),
                    'mat_khau': data.get('password'),
                    'so_dien_thoai': data.get('phone_number'),
                    'email': email,
                    'anh_chan_dung': path_image
                }
                if role_type == 'HOC_VIEN' and dob_val:
                    user_params['ngay_sinh'] = dob_val
                elif role_type == 'GIAO_VIEN':
                    user_params['nam_kinh_nghiem'] = data.get('exp')

                is_success = dao.add_user(config['enum'], **user_params)
                if is_success:
                    session.pop(session_key, None)
                    flash(f"Đã thêm tài khoản cho {data.get('name')} thành công!", "success")
                    return redirect(back_url)
                else:
                    flash(is_success if isinstance(is_success, str) else 'Lỗi hệ thống.', 'danger')
                    show_step2 = True

    return render_template("manager/add_user.html", data=data, show_step2=show_step2,
                           role_title=config['title'], role_name=role_type, back_url=back_url)


@app.route('/thay_doi_trang_thai/<string:ma_nd>')
@login_user_required
@quan_ly_required
def thay_doi_trang_thai(ma_nd):
    user = dao.get_by_id(ma_nd)

    if user:
        ten_nd = user.ho_va_ten
        dang_hoat_dong = user.tinh_trang_hoat_dong
        thanh_cong = dao.update_trang_thai_nguoi_dung(ma_nd)
        if thanh_cong:
            if dang_hoat_dong:
                flash(f"Đã khóa tài khoản của học viên {ten_nd} thành công!", "success")
            else:
                flash(f"Đã kích hoạt lại tài khoản cho học viên {ten_nd} thành công!", "success")
        else:
            flash("Lỗi hệ thống: Không thể cập nhật trạng thái vào cơ sở dữ liệu.", "danger")
    else:
        flash("Lỗi: Không tìm thấy thông tin người dùng này.", "danger")
    next_url = request.referrer or url_for('manager_student_list')
    return redirect(next_url)


@app.route('/manager/course/delete/<string:ma_kh>')
@login_user_required
@quan_ly_required
def delete_course(ma_kh):
    if dao.xoa_khoa_hoc_dao(ma_kh):
        flash(f"Đã xóa khóa học {ma_kh} thành công!", "success")
    else:
        flash("Lỗi hệ thống: Không thể xóa được khóa học này.", "danger")
    return redirect(request.referrer or url_for('manager_course_list'))


@app.route('/admin/exit')
def exit_admin():
    session.pop('admin_unlocked', None)
    return redirect('/')


@app.route('/api/kiem-tra-pin-admin', methods=['POST'])
def kiem_tra_pin_admin():
    data = request.get_json()
    pin_nhap = data.get('pin')
    if dao.check_admin_pin(current_user, pin_nhap):
        session['admin_unlocked'] = True
        return jsonify({'success': True, 'redirect_url': '/admin'})
    else:
        return jsonify({'success': False, 'message': 'Mã PIN không chính xác.'}), 200


@app.route('/manager/stats')
@login_user_required
@quan_ly_hoac_nhan_vien_required
def stats_view():
    raw_data_khoa_hoc = dao.thong_ke_hoc_vien_va_ket_qua()
    du_lieu_khoa_hoc_full = []
    for item in raw_data_khoa_hoc:
        ten = item.ten_khoa_hoc
        tong = float(item.tong_hv or 0)
        dat = float(item.so_dat or 0)
        chua_co_diem = float(item.chua_co_diem or 0)
        rot = tong - dat - chua_co_diem
        if tong > 0:
            ty_le_dat = round(dat / tong * 100, 2)
            ty_le_chua_kq = round(chua_co_diem / tong * 100, 2)
            ty_le_rot = round(100 - ty_le_dat - ty_le_chua_kq, 2)
        else:
            ty_le_dat = 0
            ty_le_rot = 0
            ty_le_chua_kq = 0
        du_lieu_khoa_hoc_full.append({
            'ten_khoa_hoc': ten,
            'so_luong_hv': int(tong),
            'ty_le_dat': ty_le_dat,
            'ty_le_rot': ty_le_rot,
            'ty_le_chua_kq': ty_le_chua_kq
        })
    current_year = datetime.datetime.now().year
    ds_nam = dao.get_ds_nam_co_hoa_don()

    if current_year not in ds_nam:
        ds_nam.insert(0, current_year)

    raw_data_doanh_thu = dao.thong_ke_doanh_thu_theo_nam(current_year)
    data_doanh_thu = [0] * 12
    for item in raw_data_doanh_thu:
        data_doanh_thu[int(item.thang) - 1] = float(item.tong_tien or 0)

    tong_doanh_thu_nam = sum(data_doanh_thu)
    tong_hoc_vien_he_thong = sum(item['so_luong_hv'] for item in du_lieu_khoa_hoc_full)

    return render_template(
        'manager/stats.html',
        du_lieu_khoa_hoc_full=du_lieu_khoa_hoc_full,
        data_doanh_thu=data_doanh_thu,
        tong_doanh_thu_nam=tong_doanh_thu_nam,
        tong_hoc_vien_he_thong=tong_hoc_vien_he_thong,
        current_year=current_year,
        ds_nam=ds_nam
    )


@app.route('/api/revenue-chart')
def revenue_chart_api():
    try:
        selected_year = request.args.get('year', default=datetime.datetime.now().year, type=int)

        raw_data = dao.thong_ke_doanh_thu_theo_nam(selected_year)

        data_response = [0] * 12
        for item in raw_data:
            data_response[int(item.thang) - 1] = float(item.tong_tien or 0)

        return jsonify({
            'status': 'success',
            'data': data_response,
            'total': sum(data_response),
            'formatted_total': "{:,.0f}".format(sum(data_response)).replace(",", ".")  # Format sẵn từ server
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/staff/payment/<ma_hoc_vien>', methods=['GET'])
@login_user_required
def staff_student_payment(ma_hoc_vien):
    if current_user.vai_tro != NguoiDungEnum.NHAN_VIEN:
        return redirect(url_for('home'))

    hoc_vien = dao.get_by_id(ma_hoc_vien)

    ds_hoa_don = dao.get_ds_hoa_don_by_hoc_vien(ma_hoc_vien)

    return render_template('staff/payment_detail.html', hoc_vien=hoc_vien, ds_hoa_don=ds_hoa_don)


@app.route('/staff/payment/confirm/<int:ma_hoa_don>', methods=['POST'])
@login_user_required
def confirm_payment(ma_hoa_don):
    if current_user.vai_tro != NguoiDungEnum.NHAN_VIEN:
        return redirect(url_for('home'))

    ket_qua, hoa_don = dao.xac_nhan_thanh_toan(ma_hoa_don, current_user.ma_nguoi_dung)

    if ket_qua:
        flash(f'Đã xác nhận thanh toán thành công cho hóa đơn #{ma_hoa_don}.', 'success')
    else:
        flash('Thanh toán thất bại. Hóa đơn không tồn tại hoặc đã được thanh toán.', 'danger')

    if not hoa_don:
        return redirect("/")

    return redirect(url_for('staff_student_payment', ma_hoc_vien=hoa_don.ma_hoc_vien))


@app.route('/pay/<int:bill_id>', methods=['GET'])
@login_user_required
def pay_page(bill_id):
    hd = dao.get_hoa_don_by_id(bill_id)

    if not hd or hd.ma_hoc_vien != current_user.ma_nguoi_dung:
        flash('Không tìm thấy hóa đơn hoặc bạn không có quyền truy cập!', 'danger')
        return redirect(url_for('course_fee'))

    if hd.trang_thai == 2:
        flash('Hóa đơn này đã được thanh toán hoàn tất.', 'success')
        return redirect(url_for('course_fee'))

    memo = f"HOC PHI {hd.ma_hoa_don}"

    qr_url = (
        f"https://img.vietqr.io/image/{app.config.get('BANK_ID')}-{app.config.get('ACCOUNT_NO')}-compact2.png"
        f"?amount={int(hd.so_tien)}"
        f"&addInfo={memo}"
        f"&accountName={app.config.get('ACCOUNT_NAME')}"
    )

    return render_template('student/pay.html', hoa_don=hd, qr_url=qr_url, memo=memo,
                           bank_info={'bank': app.config.get('BANK_ID'), 'account': app.config.get('ACCOUNT_NO'),
                                      'name': app.config.get('ACCOUNT_NAME')})


@app.route('/api/check_payment_status/<int:bill_id>', methods=['GET'])
def check_payment_status(bill_id):
    hd = dao.get_hoa_don_by_id(bill_id)
    if hd and hd.trang_thai == TrangThaiHoaDonEnum.DA_THANH_TOAN:
        return jsonify({'paid': True})
    return jsonify({'paid': False})


@app.route('/api/webhook/payment', methods=['POST'])
def webhook_payment():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data'}), 400

    content = data.get('content', '').upper()
    amount = data.get('amount', 0)

    match = re.search(r'HOC PHI\s*(\d+)', content)

    if match:
        bill_id = match.group(1)
        hd = dao.get_hoa_don_by_id(bill_id)

        if hd and hd.trang_thai != 2 and float(amount) >= float(hd.so_tien):

            if dao.xac_nhan_thanh_toan(bill_id):
                return jsonify({'success': True, 'message': 'Confirmed'})
            else:
                return jsonify({'success': False, 'message': 'Update failed'}), 500

    return jsonify({'success': False, 'message': 'Ignored'})


# curl -X POST http://127.0.0.1:5000/api/webhook/payment -H "Content-Type: application/json" -d "{\"content\": \"HOC PHI 37\", \"amount\": 5000000}"

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
