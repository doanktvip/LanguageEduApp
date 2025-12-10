import hashlib
import time
import random
import math
import datetime
from collections import defaultdict

import cloudinary.uploader
from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user
from flask_mail import Message
from eduapp import app, dao, login_manager, mail
from eduapp.models import HocVien, NguoiDungEnum, HoaDon, KhoaHoc


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    err_msg = None
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = dao.login(username, password)
        if user:
            login_user(user)
            return redirect('/')
        else:
            err_msg = 'Tài khoản không chính xác'
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
    err_msg = None
    data = {}
    show_step2 = False
    if 'register_info' in session:
        data = session['register_info']
    if request.method == 'POST':
        step = request.form.get('step')
        form_data = request.form.to_dict()
        data.update(form_data)
        if step == '1':
            password = data.get('password')
            re_enter_password = data.get('re_enter_password')
            username = data.get('username')
            if not password or password != re_enter_password:
                err_msg = 'Mật khẩu nhập lại không chính xác'
            elif dao.get_by_username(username):
                err_msg = 'Tài khoản đã tồn tại'
            else:
                session['register_info'] = {
                    'name': data.get('name'),
                    'username': username,
                    'password': password,
                    're_enter_password': re_enter_password
                }
                show_step2 = True
        elif step == '2':
            step1_data = session.get('register_info')
            if not step1_data:
                return redirect(url_for('register'))
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
                        pass
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
                        ho_va_ten=step1_data.get('name'),
                        ten_dang_nhap=step1_data.get('username'),
                        mat_khau=step1_data.get('password'),
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
    return render_template("register.html", err_msg=err_msg, data=data, show_step2=show_step2)


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == "GET":
        session.pop('otp_code', None)
        session.pop('reset_email', None)
        session.pop('reset_username', None)
        return render_template("forgot_password.html", show_step2=False)
    step = request.form.get("step")
    if step == "resend":
        session.pop('otp_code', None)
        step = "1"
    if step == "1":
        username = request.form.get("username") or session.get('reset_username')
        email = request.form.get("email") or session.get('reset_email')
        user = dao.get_by_username_email(username, email)
        if not user:
            return render_template("forgot_password.html", show_step2=False,
                                   err_msg='Tài khoản hoặc email không chính xác.')
        if not session.get('otp_code'):
            otp_code = str(random.randint(0, 999999)).zfill(6)
            session['otp_code'] = otp_code
            session['reset_username'] = username
            session['reset_email'] = email
            # msg = Message(
            #     subject="Mã xác nhận đổi mật khẩu",
            #     sender=app.config.get('MAIL_USERNAME'),
            #     recipients=[session.get('reset_email')]
            # )
            # msg.body = f"Mã xác nhận đổi mật khẩu của bạn là: {session.get('otp_code')}.\nLưu ý: Mã chỉ sử dụng trong vòng 1 lần nhập (nhập sai hay đúng đều mất hiệu lực khi nhập)."
            # mail.send(msg)
        return render_template("forgot_password.html", show_step2=True, err_msg=None, has_otp=True)
    if step == "2":
        real_otp = session.get('otp_code')
        new_password = request.form.get("new_password")
        re_enter_password = request.form.get("re_enter_password")
        if new_password != re_enter_password:
            return render_template("forgot_password.html", show_step2=True,
                                   err_msg='Mật khẩu nhập lại không khớp!', has_otp=True)
        user_otp = request.form.get("verify")
        if not real_otp or user_otp != real_otp:
            session.pop('otp_code', None)
            return render_template("forgot_password.html", show_step2=True,
                                   err_msg='Mã xác nhận sai hoặc đã bị hủy. Vui lòng nhấn "Gửi lại mã".',
                                   has_otp=False)
        # dao.update_password(saved_username, new_password)
        session.pop('otp_code', None)
        session.pop('reset_username', None)
        session.pop('reset_email', None)
        return redirect('/')
    return redirect('/forgot_password')


@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        data = request.form.to_dict()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        re_enter_password = data.get('re_enter_password')
        old_password = str(hashlib.md5(old_password.encode('utf-8')).hexdigest())
        if old_password != current_user.mat_khau:
            err_msg = "Mật khẩu cũ không chính xác!"
            return render_template("change_password.html", err_msg=err_msg)
        if new_password != re_enter_password:
            err_msg = "Mật khẩu nhập lại không chính xác!"
            return render_template("change_password.html", err_msg=err_msg)
        # update
        return redirect('/')
    return render_template("change_password.html")


otp_storage = {}


@app.route('/verify', methods=['GET', 'POST'])
def verify_page():
    if not current_user.is_authenticated or current_user.vai_tro.value != 1 or current_user.tinh_trang_xac_nhan_email == True:
        return redirect('/')
    nguoi_nhan = current_user.email
    otp_lifetime = app.config.get("OTP_LIFETIME")
    max_resend_limit = app.config.get("MAX_RESEND_LIMIT")
    resend_block_time = app.config.get("RESEND_BLOCK_TIME")
    current_time = time.time()
    user_otp_data = otp_storage.get(nguoi_nhan, {})
    blocked_until = user_otp_data.get('blocked_until', 0)
    action = request.args.get('action')
    if current_time < blocked_until:
        if action == 'resend':
            return redirect(url_for('verify_page'))
        wait_time_left = math.ceil(blocked_until - current_time)
        return render_template("verify.html", block_time=wait_time_left, is_blocked=True,
                               max_resend_limit=max_resend_limit)
    if request.method == 'POST':
        user_input_otp = request.form.get('verify')
        if not user_otp_data:
            return render_template("verify.html", wait_time=0)
        last_sent = user_otp_data.get('last_sent', 0)
        elapsed_time = current_time - last_sent
        if elapsed_time > otp_lifetime:
            otp_storage.pop(nguoi_nhan, None)
            return render_template("verify.html", wait_time=0)
        saved_otp = user_otp_data.get('otp')
        if user_input_otp == saved_otp:
            # update
            otp_storage.pop(nguoi_nhan, None)
            return redirect('/')
        else:
            wait_time_left = math.ceil(otp_lifetime - elapsed_time)
            warn_msg = "Mã xác nhận không chính xác."
            return render_template("verify.html", wait_time=wait_time_left, warn_msg=warn_msg)
    wait_time = 0
    can_resend = True
    last_sent = user_otp_data.get('last_sent', 0)
    if current_time - last_sent < otp_lifetime:
        wait_time = math.ceil(otp_lifetime - (current_time - last_sent))
        can_resend = False
    if action == 'resend' and not can_resend:
        return redirect(url_for('verify_page'))
    should_send = (action == 'resend') and can_resend
    if should_send:
        current_attempts = user_otp_data.get('attempts', 0)
        if current_attempts >= max_resend_limit:
            user_otp_data['blocked_until'] = current_time + resend_block_time
            user_otp_data['attempts'] = 0
            otp_storage[nguoi_nhan] = user_otp_data
            return render_template("verify.html", block_time=resend_block_time, is_blocked=True,
                                   max_resend_limit=max_resend_limit)
        try:
            new_otp = str(random.randint(0, 999999)).zfill(6)
            otp_storage[nguoi_nhan] = {
                'otp': new_otp,
                'last_sent': current_time,
                'attempts': current_attempts + 1,
                'blocked_until': 0
            }
            # msg = Message(
            #     subject="Mã xác nhận email",
            #     sender=app.config.get('MAIL_USERNAME'),
            #     recipients=[nguoi_nhan]
            # )
            # msg.body = f"Mã xác nhận của bạn là: {new_otp}. Mã có hiệu lực trong {otp_lifetime} giây."
            # mail.send(msg)
            return redirect(url_for('verify_page'))
        except Exception as e:
            return str(e)
    return render_template("verify.html", wait_time=wait_time)


@app.route('/profile')
def profile():
    if not current_user.is_authenticated:
        return redirect('/')
    return render_template("profile.html")


@app.route('/schedule', methods=['GET'])
def schedule():
    tuan_duoc_chon = None
    cac_thu = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]
    ma_khoa_hoc_dang_chon = request.args.get('course_id')
    ds_khoa_hoc_cua_hv = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    ds_ma_hop_le = [kh.ma_khoa_hoc for kh in ds_khoa_hoc_cua_hv]
    if not ma_khoa_hoc_dang_chon or ma_khoa_hoc_dang_chon not in ds_ma_hop_le:
        if ds_khoa_hoc_cua_hv:
            ma_mac_dinh = ds_khoa_hoc_cua_hv[0].ma_khoa_hoc
            return redirect(url_for('schedule', course_id=ma_mac_dinh))
        return render_template('schedule.html', course_id=None, ds_khoa_hoc=ds_khoa_hoc_cua_hv)
    course = dao.get_by_course_id(ma_khoa_hoc_dang_chon)
    current_index = 0
    tong_so_tuan = 0
    if course:
        danh_sach_hoc = course.lay_danh_sach_tuan_hoc()
        tong_so_tuan = len(danh_sach_hoc)
        if danh_sach_hoc:
            index_tham_so = request.args.get('index', type=int)
            if index_tham_so is not None:
                current_index = max(0, min(index_tham_so, tong_so_tuan - 1))
            else:
                today = datetime.datetime.now()
                nam_hien_tai, tuan_hien_tai, _ = today.isocalendar()
                found = False
                for i, tuan in enumerate(danh_sach_hoc):
                    if tuan['week'] == tuan_hien_tai and tuan['year'] == nam_hien_tai:
                        current_index = i
                        found = True
                        break
                if not found:
                    current_index = 0
            tuan_duoc_chon = danh_sach_hoc[current_index]
    return render_template('schedule.html', ma_khoa_hoc_hien_tai=ma_khoa_hoc_dang_chon, cac_thu=cac_thu,
                           tuan_duoc_chon=tuan_duoc_chon, current_index=current_index, tong_so_tuan=tong_so_tuan,
                           ds_khoa_hoc=ds_khoa_hoc_cua_hv)


@app.route('/scoreboard', methods=['GET'])
def scoreboard():
    if not current_user.is_authenticated:
        return redirect('/')
    ma_khoa_hoc_dang_chon = request.args.get('course_id')
    ds_khoa_hoc_cua_hv = [bd.khoa_hoc for bd in current_user.ds_lop_hoc]
    ds_ma_hop_le = [kh.ma_khoa_hoc for kh in ds_khoa_hoc_cua_hv]
    if not ma_khoa_hoc_dang_chon or ma_khoa_hoc_dang_chon not in ds_ma_hop_le:
        if ds_khoa_hoc_cua_hv:
            ma_mac_dinh = ds_khoa_hoc_cua_hv[0].ma_khoa_hoc
            return redirect(url_for('scoreboard', course_id=ma_mac_dinh))
        return render_template('scoreboard.html', course_id=None, ds_khoa_hoc=ds_khoa_hoc_cua_hv)
    course = dao.get_by_course_id(ma_khoa_hoc_dang_chon)
    list_bang_diem = {}
    if course:
        cau_truc_diem = dao.get_cau_truc_diem(course.ma_khoa_hoc)
        bang_diem = dao.get_by_scoreboard_id(current_user.ma_nguoi_dung, course.ma_khoa_hoc)
        if cau_truc_diem:
            list_bang_diem = bang_diem.lay_chi_tiet_diem(cau_truc_diem)
    return render_template("scoreboard.html", ma_khoa_hoc_hien_tai=ma_khoa_hoc_dang_chon,
                           ds_khoa_hoc=ds_khoa_hoc_cua_hv, list_bang_diem=list_bang_diem)


@app.route('/course_fee')
def course_fee():
    if not current_user.is_authenticated:
        return redirect('/')
    danh_sach = current_user.nhung_hoa_don
    if not danh_sach:
        return render_template('course_fee.html', ds_hoa_don=None)
    ds_hoa_don = HoaDon.chuyen_danh_sach_sang_dict(danh_sach)
    tong_tien = 0
    for i in ds_hoa_don:
        for j in ds_hoa_don[i]:
            if j == 'Trạng thái' and ds_hoa_don[i][j] == 2:
                tong_tien += ds_hoa_don[i]['Số tiền']
    return render_template('course_fee.html', ds_hoa_don=ds_hoa_don, tong_tien=tong_tien)


@app.route("/register_course", methods=['GET', 'POST'])
def register_course():
    if not current_user.is_authenticated:
        return redirect('/')
    khoa_hoc_dao_chua_dang_ky = dao.lay_khoa_hoc_chua_dang_ky(current_user.ma_nguoi_dung)
    if request.method == 'POST':
        ds_khoa_hoc = request.form.getlist('register_course')
        if ds_khoa_hoc:
            print(ds_khoa_hoc)
    if not khoa_hoc_dao_chua_dang_ky:
        return render_template("register_course.html", khoa_hoc_dao_chua_dang_ky=None)
    danh_sach = KhoaHoc.chuyen_danh_sach_sang_dict(khoa_hoc_dao_chua_dang_ky)
    print(danh_sach)
    return render_template("register_course.html", khoa_hoc_dao_chua_dang_ky=khoa_hoc_dao_chua_dang_ky,
                           danh_sach=danh_sach)


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
