function xuLyKiemTraPin() {
    const pinInput = document.getElementById('verify');
    const errorMsg = document.getElementById('pinErrorMsg');
    const pinValue = pinInput.value;
    if (!pinValue || pinValue.length < 6) {
        errorMsg.innerText = "Vui lòng nhập đủ 6 số";
        errorMsg.classList.remove('d-none');
        pinInput.focus();
        return;
    }
    fetch('/api/kiem-tra-pin-admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pin: pinValue })
    }).then(response => response.json()).then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            errorMsg.innerText = data.message;
            errorMsg.classList.remove('d-none');
            pinInput.value = '';
            pinInput.focus();
        }
        pinInput.value = '';
    }).catch(error => {
        console.error('Lỗi:', error);
        alert("Lỗi kết nối server!");
    });
}