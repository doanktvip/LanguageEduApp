import time
import random
import math
from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user
from flask_mail import Message
from eduapp import app, dao, login_manager, mail
from eduapp.models import NguoiDungEnum


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
    err_msg = None
    data = {}
    if current_user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        #  name,username, password, re_enter_password, image, phone_number, email
        data = request.form.to_dict()
        username = data.get('username')
        password = data.get('password')
        re_enter_password = data.get('re_enter_password')
        # image = request.files.get('image') lấy ảnh bằng các này
        image_file = request.files.get('image')
        user = dao.get_by_username(username)
        if user:
            err_msg = 'Tài khoản đã tồn tại'
            data['username'] = ''
        elif password != re_enter_password:
            err_msg = 'Mật khẩu nhập lại không chính xác'
            data['password'] = ''
            data['re_enter_password'] = ''
        if not err_msg:
            dao.add_image(image_file)

            return redirect(url_for('login'))
    return render_template("register.html", err_msg=err_msg, data=data)


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
            msg = Message(
                subject="Mã xác nhận đổi mật khẩu",
                sender=app.config.get('MAIL_USERNAME'),
                recipients=[session.get('reset_email')]
            )
            msg.body = f"Mã xác nhận đổi mật khẩu của bạn là: {session.get('otp_code')}.\nLưu ý: Mã chỉ sử dụng trong vòng 1 lần nhập (nhập sai hay đúng đều mất hiệu lực khi nhập)."
            # mail.send(msg)
        return render_template("forgot_password.html", show_step2=True, err_msg=None, has_otp=True)
    if step == "2":
        user_otp = request.form.get("verify")
        new_password = request.form.get("new_password")
        re_enter_password = request.form.get("re_enter_password")
        real_otp = session.get('otp_code')
        if new_password != re_enter_password:
            return render_template("forgot_password.html", show_step2=True,
                                   err_msg='Mật khẩu nhập lại không khớp!', has_otp=True)
        if not real_otp or user_otp != real_otp:
            session.pop('otp_code', None)
            return render_template("forgot_password.html", show_step2=True,
                                   err_msg='Mã xác nhận sai hoặc đã bị hủy. Vui lòng nhấn "Gửi lại mã".',
                                   has_otp=False)
        # 3. Thành công -> Đổi pass -> Xóa session
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
        if old_password != current_user.mat_khau:
            err_msg = "Mật khẩu cũ không chính xác!"
            return render_template("change_password.html", err_msg=err_msg)
        if new_password != re_enter_password:
            err_msg = "Mật khẩu nhập lại không chính xác!"
            return render_template("change_password.html", err_msg=err_msg)

        return redirect('/')
    return render_template("change_password.html")


otp_storage = {}


@app.route('/verify', methods=['GET', 'POST'])
def verify_page():
    if not current_user.is_authenticated:
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
            msg = Message(
                subject="Mã xác nhận email",
                sender=app.config.get('MAIL_USERNAME'),
                recipients=[nguoi_nhan]
            )
            msg.body = f"Mã xác nhận của bạn là: {new_otp}. Mã có hiệu lực trong {otp_lifetime} giây."
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


if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True)
