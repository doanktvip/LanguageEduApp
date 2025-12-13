import hashlib
import time
import random
import math
import datetime
import cloudinary.uploader
from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user
from eduapp import app, dao, login_manager, mail, db
from eduapp.models import NguoiDungEnum, ChiTietDiem
from flask_mail import Message


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    err_msg = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.login(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or '/')
        else:
            err_msg = 'Tên tài khoản hoặc mật khẩu không chính xác.'
    return render_template("login.html", err_msg=err_msg)


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@login_manager.user_loader
def load_user(user_id):
    return dao.get_by_id(user_id)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'GET':
        session.pop('register_info', None)
        return render_template("register.html", data={}, show_step2=False)
    err_msg = None
    show_step2 = False
    focus_field = None
    data = session.get('register_info', {})
    form_data = request.form.to_dict()
    data.update(form_data)
    session['register_info'] = data
    if 'back_to_step1' in request.form:
        return render_template("register.html", err_msg=None, data=data, show_step2=False)
    step = request.form.get('step')
    if step == '1':
        password = data.get('password')
        re_enter_password = data.get('re_enter_password')
        username = data.get('username')
        if dao.get_by_username(username):
            err_msg = 'Tài khoản đã tồn tại'
            data['username'] = ''
            focus_field = 'username'
        elif not password or password != re_enter_password:
            err_msg = 'Mật khẩu nhập lại không chính xác'
            data['password'] = ''
            data['re_enter_password'] = ''
            focus_field = 'password'
        else:
            show_step2 = True
    elif step == '2':
        email = data.get('email')
        user_check = dao.get_by_email(email)
        if user_check:
            err_msg = 'Email này đã được sử dụng bởi tài khoản khác!'
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
            if data.get('dob'):
                try:
                    dob_val = datetime.datetime.strptime(data.get('dob'), '%Y-%m-%d')
                except ValueError:
                    err_msg = "Định dạng ngày sinh không hợp lệ."
                    show_step2 = True
            if not err_msg:
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
                    return redirect(url_for('login'))
                else:
                    err_msg = 'Đã có lỗi hệ thống xảy ra, vui lòng thử lại sau.'
                    show_step2 = True
    return render_template("register.html", err_msg=err_msg, data=data, show_step2=show_step2, focus_field=focus_field)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == "GET":
        session.pop('reset_info', None)
        return render_template("forgot_password.html", show_step2=False, data={})
    err_msg = None
    show_step2 = False
    reset_info = session.get('reset_info', {})
    step = request.form.get("step")
    if step == "1":
        username = request.form.get("username")
        email = request.form.get("email")
        user = dao.get_by_username_email(username, email)
        if not user:
            err_msg = 'Tên tài khoản hoặc Email không chính xác.'
            reset_info = {'username': username, 'email': email}
        else:
            otp_code = str(random.randint(0, 999999)).zfill(6)
            reset_info = {
                'username': username,
                'email': email,
                'otp_code': otp_code
            }
            session['reset_info'] = reset_info
            # chức năng gửi mail
            # msg = Message(
            #     subject="Xin chào từ Flask!",
            #     recipients=[email],
            #     html=f"""<p>Xin chào {username},</p>
            #     <p>Cảm ơn bạn đã tham gia cùng chúng tôi! Để kích hoạt tài khoản, vui lòng nhập mã xác thực bên dưới:</p>
            #     <p style="font-size: 24px;"><b>{otp_code}</b></p>
            #     <p>Mã này sẽ hết hạn sau 10 phút. Hẹn gặp bạn bên trong ứng dụng nhé!</p>
            #     <p>Thân mến,<br>Đội ngũ [Tên_App]</p>"""
            # )
            # mail.send(msg)
            print(otp_code)
            show_step2 = True
    elif step == "resend":
        if not reset_info: return redirect(url_for('forgot_password'))
        new_otp = str(random.randint(0, 999999)).zfill(6)
        reset_info['otp_code'] = new_otp  # Cấp mã mới
        session['reset_info'] = reset_info
        # chức năng gửi mail
        # msg = Message(
        #     subject="Xin chào từ Flask!",
        #     recipients=[email],
        #     html=f"""<p>Xin chào {username},</p>
        #     <p>Cảm ơn bạn đã tham gia cùng chúng tôi! Để kích hoạt tài khoản, vui lòng nhập mã xác thực bên dưới:</p>
        #     <p style="font-size: 24px;"><b>{otp_code}</b></p>
        #     <p>Mã này sẽ hết hạn sau 10 phút. Hẹn gặp bạn bên trong ứng dụng nhé!</p>
        #     <p>Thân mến,<br>Đội ngũ [Tên_App]</p>"""
        # )
        # mail.send(msg)
        print(f"DEBUG NEW OTP: {new_otp}")
        err_msg = "Mã xác nhận mới đã được gửi."
        show_step2 = True
    elif step == "2":
        if not reset_info: return redirect(url_for('forgot_password'))
        user_otp = request.form.get("verify")
        new_password = request.form.get("new_password")
        re_password = request.form.get("re_enter_password")
        real_otp = reset_info.get('otp_code')
        saved_username = reset_info.get('username')
        if not real_otp or user_otp != real_otp:
            reset_info.pop('otp_code', None)
            session['reset_info'] = reset_info
            err_msg = 'Mã xác nhận không chính xác. Mã này đã bị vô hiệu hóa.'
            show_step2 = True
        elif new_password != re_password:
            err_msg = 'Mật khẩu xác nhận không khớp.'
            show_step2 = True
        else:
            hashed_pass = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
            if dao.update_password(saved_username, hashed_pass):
                session.pop('reset_info', None)
                return redirect('/login')
            else:
                err_msg = "Lỗi hệ thống."
                show_step2 = True
    return render_template("forgot_password.html", show_step2=show_step2, err_msg=err_msg, data=reset_info)


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    err_msg = None
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        re_enter_password = request.form.get('re_enter_password')
        hashed_old_input = str(hashlib.md5(old_password.encode('utf-8')).hexdigest())
        if hashed_old_input != current_user.mat_khau:
            err_msg = "Mật khẩu cũ không chính xác!"
        elif new_password != re_enter_password:
            err_msg = "Mật khẩu xác nhận không trùng khớp!"
        else:
            try:
                hashed_new_password = str(hashlib.md5(new_password.encode('utf-8')).hexdigest())
                current_user.mat_khau = hashed_new_password
                db.session.commit()
                return redirect('/')
            except Exception as e:
                db.session.rollback()
                print(f"Lỗi đổi pass: {e}")
                err_msg = "Lỗi hệ thống, vui lòng thử lại sau."
    return render_template("change_password.html", err_msg=err_msg)


otp_storage = {}


@app.route('/verify', methods=['GET', 'POST'])
def verify_page():
    if not current_user.is_authenticated or \
            current_user.vai_tro != NguoiDungEnum.HOC_VIEN or \
            current_user.tinh_trang_xac_nhan_email:
        return redirect('/')
    email = current_user.email
    current_time = time.time()
    otp_lifetime = app.config.get("OTP_LIFETIME", 60)
    max_resend_limit = app.config.get("MAX_RESEND_LIMIT", 5)
    resend_block_time = app.config.get("RESEND_BLOCK_TIME", 300)
    user_otp_data = otp_storage.get(email, {})
    blocked_until = user_otp_data.get('blocked_until', 0)
    if current_time < blocked_until:
        if request.args.get('action') == 'resend':
            return redirect(url_for('verify_page'))
        wait_time_left = math.ceil(blocked_until - current_time)
        return render_template("verify.html", block_time=wait_time_left, is_blocked=True,
                               max_resend_limit=max_resend_limit)
    if request.method == 'POST':
        user_input_otp = request.form.get('verify')
        if not user_otp_data:
            return render_template("verify.html", wait_time=0, warn_msg="Vui lòng yêu cầu gửi mã mới.")
        last_sent = user_otp_data.get('last_sent', 0)
        elapsed_time = current_time - last_sent
        if elapsed_time > otp_lifetime:
            otp_storage.pop(email, None)
            return render_template("verify.html", wait_time=0)
        saved_otp = user_otp_data.get('otp')
        if user_input_otp == saved_otp:
            try:
                current_user.tinh_trang_xac_nhan_email = True
                db.session.commit()
                otp_storage.pop(email, None)  # Xóa OTP
                return redirect('/')
            except Exception as e:
                db.session.rollback()
                return render_template("verify.html", wait_time=0, warn_msg="Lỗi hệ thống khi kích hoạt.")
        else:
            wait_time_left = math.ceil(otp_lifetime - elapsed_time)
            return render_template("verify.html", wait_time=wait_time_left, warn_msg="Mã xác nhận không chính xác.")
    wait_time = 0
    can_resend = True
    last_sent = user_otp_data.get('last_sent', 0)
    if current_time - last_sent < otp_lifetime:
        wait_time = math.ceil(otp_lifetime - (current_time - last_sent))
        can_resend = False
    action = request.args.get('action')
    if action == 'resend' and not can_resend:
        return redirect(url_for('verify_page'))
    if action == 'resend' and can_resend:
        current_attempts = user_otp_data.get('attempts', 0)
        if current_attempts >= max_resend_limit:
            user_otp_data['blocked_until'] = current_time + resend_block_time
            user_otp_data['attempts'] = 0
            otp_storage[email] = user_otp_data
            return render_template("verify.html", block_time=resend_block_time, is_blocked=True,
                                   max_resend_limit=max_resend_limit)
        try:
            new_otp = str(random.randint(0, 999999)).zfill(6)
            otp_storage[email] = {
                'otp': new_otp,
                'last_sent': current_time,
                'attempts': current_attempts + 1,
                'blocked_until': 0
            }
            # chức năng gửi mail
            # msg = Message(
            #     subject="Xin chào từ Flask!",
            #     recipients=[email],
            #     html=f"""<p>Xin chào {username},</p>
            #     <p>Cảm ơn bạn đã tham gia cùng chúng tôi! Để kích hoạt tài khoản, vui lòng nhập mã xác thực bên dưới:</p>
            #     <p style="font-size: 24px;"><b>{otp_code}</b></p>
            #     <p>Mã này sẽ hết hạn sau 10 phút. Hẹn gặp bạn bên trong ứng dụng nhé!</p>
            #     <p>Thân mến,<br>Đội ngũ [Tên_App]</p>"""
            # )
            # mail.send(msg)
            print(f"DEBUG OTP: {new_otp}")
            return redirect(url_for('verify_page'))
        except Exception as e:
            return str(e)
    return render_template("verify.html", wait_time=wait_time)


@app.route('/update_avatar', methods=['POST'])
def update_avatar():
    avatar = request.files.get('avatar')
    if avatar:
        try:
            res = cloudinary.uploader.upload(avatar)
            avatar_url = res.get('secure_url')
            current_user.anh_chan_dung = avatar_url
            db.session.commit()
        except Exception as e:
            print(e)
    return redirect(url_for('profile'))


@app.route('/update_parent_phone', methods=['POST'])
def update_parent_phone():
    parent_phone = request.form.get('parent_phone')
    target_user_id = request.form.get('user_id')
    if current_user.ma_nguoi_dung != target_user_id and current_user.vai_tro.name != 'QUAN_LY':
        return redirect(url_for('profile', user_id=target_user_id, status='denied'))
    user_to_update = dao.get_by_id(target_user_id)
    if user_to_update:
        try:
            user_to_update.so_dien_thoai_phu_huynh = parent_phone
            db.session.commit()
            return redirect(url_for('profile', user_id=target_user_id, status='success'))
        except Exception as e:
            db.session.rollback()
            print(e)
            return redirect(url_for('profile', user_id=target_user_id, status='failed'))
    return redirect(url_for('profile', user_id=target_user_id))


@app.route('/profile', defaults={'user_id': None})
@app.route('/profile/<user_id>')
def profile(user_id):
    if user_id:
        user_to_show = dao.get_by_id(user_id)
        if not user_to_show:
            return redirect('/')
    else:
        user_to_show = current_user
    return render_template("profile.html", user=user_to_show)


@app.route('/schedule', methods=['GET'])
def schedule():
    cac_thu = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    ds_khoa_hoc = []
    is_teacher = False
    if current_user.vai_tro == NguoiDungEnum.HOC_VIEN:
        ds_khoa_hoc = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    elif current_user.vai_tro == NguoiDungEnum.GIAO_VIEN:
        ds_khoa_hoc = current_user.nhung_khoa_hoc
        is_teacher = True
    ds_ma_hop_le = [kh.ma_khoa_hoc for kh in ds_khoa_hoc]
    ma_khoa_hoc_dang_chon = request.args.get('course_id')
    if not ma_khoa_hoc_dang_chon or ma_khoa_hoc_dang_chon not in ds_ma_hop_le:
        if ds_khoa_hoc:
            ma_mac_dinh = ds_khoa_hoc[0].ma_khoa_hoc
            return redirect(url_for('schedule', course_id=ma_mac_dinh))
        else:
            return render_template('schedule.html', ma_khoa_hoc_hien_tai=None, ds_khoa_hoc=[], is_teacher=is_teacher)
    course = next((kh for kh in ds_khoa_hoc if kh.ma_khoa_hoc == ma_khoa_hoc_dang_chon), None)
    tuan_duoc_chon = None
    current_index = 0
    tong_so_tuan = 0
    today_index = -1
    if course:
        danh_sach_hoc = course.lay_danh_sach_tuan_hoc()
        tong_so_tuan = len(danh_sach_hoc)
        if danh_sach_hoc:
            today = datetime.datetime.now()
            nam_hien_tai, tuan_hien_tai, thu_hien_tai = today.isocalendar()
            index_tham_so = request.args.get('index', type=int)
            if index_tham_so is not None:
                current_index = max(0, min(index_tham_so, tong_so_tuan - 1))
            else:
                found = False
                for i, tuan in enumerate(danh_sach_hoc):
                    if tuan['week'] == tuan_hien_tai and tuan['year'] == nam_hien_tai:
                        current_index = i
                        found = True
                        break
                if not found:
                    current_index = 0
            tuan_duoc_chon = danh_sach_hoc[current_index]
            if tuan_duoc_chon['week'] == tuan_hien_tai and tuan_duoc_chon['year'] == nam_hien_tai:
                today_index = thu_hien_tai - 1
    return render_template('schedule.html', ma_khoa_hoc_hien_tai=ma_khoa_hoc_dang_chon, cac_thu=cac_thu,
                           tuan_duoc_chon=tuan_duoc_chon, current_index=current_index, tong_so_tuan=tong_so_tuan,
                           ds_khoa_hoc=ds_khoa_hoc, is_teacher=is_teacher, today_index=today_index)


@app.route('/scoreboard', methods=['GET'])
def scoreboard():
    ds_khoa_hoc_cua_hv = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    if not ds_khoa_hoc_cua_hv:
        return render_template('scoreboard.html', ma_khoa_hoc_hien_tai=None, ds_khoa_hoc=[])
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
    return render_template("scoreboard.html", ma_khoa_hoc_hien_tai=ma_khoa_hoc_dang_chon,
                           ds_khoa_hoc=ds_khoa_hoc_cua_hv, list_bang_diem=list_bang_diem)


@app.route('/course_fee')
def course_fee():
    ds_hoa_don = list(current_user.nhung_hoa_don)
    ds_hoa_don.sort(key=lambda x: x.ngay_tao, reverse=True)
    tong_tien = sum(hd.so_tien for hd in ds_hoa_don if hd.trang_thai.value == 2)
    return render_template('course_fee.html', ds_hoa_don=ds_hoa_don, tong_tien=tong_tien)


@app.route("/register_course", methods=['GET', 'POST'])
def register_course():
    if not current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        ds_ma_khoa_hoc = request.form.getlist('course_ids')
        if ds_ma_khoa_hoc:
            count = 0
            for ma_kh in ds_ma_khoa_hoc:
                ket_qua = dao.dang_ky_khoa_hoc(current_user.ma_nguoi_dung, ma_kh)
                if ket_qua: count += 1
        return redirect(url_for('register_course'))
    ds_khoa_hoc_chua_dang_ky = dao.lay_khoa_hoc_chua_dang_ky(current_user.ma_nguoi_dung)
    return render_template("register_course.html", ds_khoa_hoc=ds_khoa_hoc_chua_dang_ky)


@app.route('/grading', methods=['GET', 'POST'])
def grading():
    if not current_user.is_authenticated or current_user.vai_tro != NguoiDungEnum.GIAO_VIEN:
        return redirect('/')
    ds_khoa_hoc = current_user.nhung_khoa_hoc
    selected_course_id = request.args.get('course_id') or request.form.get('course_id')
    if not selected_course_id and ds_khoa_hoc:
        selected_course_id = ds_khoa_hoc[0].ma_khoa_hoc
    if request.method == 'POST' and selected_course_id:
        try:
            form_data = request.form.to_dict()
            action = request.form.get('action_type')
            is_draft_target = True if action == 'save_draft' else False
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
                            chi_tiet = dao.get_chi_tiet_diem(bd_id, ct_id)
                            if chi_tiet:
                                if is_draft_target and chi_tiet.ban_nhap == False:
                                    continue
                                chi_tiet.gia_tri_diem = diem_val
                                chi_tiet.ban_nhap = is_draft_target
                            else:
                                new_score = ChiTietDiem(
                                    ma_bang_diem=bd_id,
                                    ma_cau_truc_diem=ct_id,
                                    gia_tri_diem=diem_val,
                                    ban_nhap=is_draft_target)
                                db.session.add(new_score)
            if not is_draft_target:
                db.session.commit()
                course = dao.get_by_course_teacher_id(current_user.ma_nguoi_dung, selected_course_id)
                if course:
                    for bd in course.ds_dang_ky:
                        bd.cap_nhat_tong_ket()
            db.session.commit()
            return redirect(url_for('grading', course_id=selected_course_id))
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi: {e}")
    selected_course = None
    cau_truc_diem = []
    bang_diem_data = []
    if selected_course_id:
        selected_course = dao.get_by_course_teacher_id(current_user.ma_nguoi_dung, selected_course_id)
        if selected_course:
            cau_truc_diem = selected_course.cau_truc_diem
            for bd in selected_course.ds_dang_ky:
                chi_tiet = bd.lay_chi_tiet_diem(cau_truc_diem)
                bang_diem_data.append({
                    'hoc_vien': bd.hoc_vien,
                    'ma_bang_diem': bd.id,
                    'diem_so': chi_tiet})
    return render_template("grading.html", ds_khoa_hoc=ds_khoa_hoc, selected_course=selected_course,
                           cau_truc_diem=cau_truc_diem, bang_diem_data=bang_diem_data)


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if current_user.vai_tro != NguoiDungEnum.GIAO_VIEN:
        return redirect('/')
    ds_khoa_hoc_raw = current_user.nhung_khoa_hoc
    ds_khoa_hoc = sorted(ds_khoa_hoc_raw, key=lambda x: x.ngay_bat_dau, reverse=True)
    course_id = request.args.get('course_id') or request.form.get('course_id')
    if not course_id and ds_khoa_hoc:
        course_id = ds_khoa_hoc[0].ma_khoa_hoc
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    course = None
    date_columns = []
    student_rows = []
    if course_id:
        valid_ids = [k.ma_khoa_hoc for k in ds_khoa_hoc]
        if course_id in valid_ids:
            course = dao.get_by_course_id(course_id)
    if request.method == 'POST' and course:
        if dao.save_attendance_sheet(course_id, request.form):
            return redirect(url_for('attendance', course_id=course_id, status='success'))
        else:
            return redirect(url_for('attendance', course_id=course_id, status='failed'))
    if course:
        date_columns, student_rows = dao.get_attendance_sheet_data(course)
    return render_template('attendance.html', ds_khoa_hoc=ds_khoa_hoc, course=course, date_columns=date_columns,
                           student_rows=student_rows, today_str=today_str)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
