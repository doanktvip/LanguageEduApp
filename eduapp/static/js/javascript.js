function demNguocGiay(tongGiay, elementId, alertBoxId, messenger, callback) {
    let thoiGianConLai = tongGiay;
    const element = document.getElementById(elementId);
    const box = document.getElementById(alertBoxId);
    let thoiDiemTatThongBao = -999;
    let noiDungThongBao = "";
    if (!element || !box) return;
    function hienThi() {
        if (thoiGianConLai > thoiDiemTatThongBao && noiDungThongBao !== "") {
            element.innerHTML = `${noiDungThongBao}`;
            box.classList.remove("alert-warning");
            box.classList.add("alert-danger");
        } else {
            const phut = Math.floor(thoiGianConLai / 60);
            const giay = thoiGianConLai % 60;
            const phutString = phut < 10 ? "0" + phut : phut;
            const giayString = giay < 10 ? "0" + giay : giay;
            element.innerHTML = `${messenger} ${phutString}:${giayString}`;
            box.classList.add("alert-warning");
            box.classList.remove("alert-danger");
        }
    }
    hienThi();
    const boDem = setInterval(function() {
        thoiGianConLai--;
        if (thoiGianConLai < 1) {
            clearInterval(boDem);
            if (typeof callback === 'function') {
                callback();
            }
            return;
        }
        hienThi();
    }, 1000);
    return {
        kichHoatThongBao: function(msg, soGiayHienThi) {
            noiDungThongBao = msg;
            thoiDiemTatThongBao = thoiGianConLai - soGiayHienThi;
            hienThi();
        }
    };
}

function formAlert(alertId, alert, alertBox) {
    document.getElementById(alertId).innerHTML = `${alert}`;
    var alertBox = document.getElementById(alertBox);
    alertBox.classList.remove("alert-warning");
    alertBox.classList.add("alert-danger");
}

function setupPasswordToggle(triggerId, inputId, iconId) {
        const trigger = document.getElementById(triggerId);
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        if (trigger && input && icon) {
            trigger.addEventListener("click", function () {
                const currentType = input.getAttribute("type");
                const newType = currentType === "password" ? "text" : "password";
                input.setAttribute("type", newType);

                // Toggle icon class
                if(newType === 'text'){
                    icon.classList.remove("bi-eye-slash");
                    icon.classList.add("bi-eye");
                    trigger.classList.add("text-primary"); // Thêm màu xanh cho đẹp
                } else {
                    icon.classList.remove("bi-eye");
                    icon.classList.add("bi-eye-slash");
                    trigger.classList.remove("text-primary");
                }
            });
        }
    }
    function setupImagePreview(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    // Chỉ chạy khi cả 2 thẻ đều tồn tại trên trang
    if (input && preview) {
        input.addEventListener('change', function (evt) {
            const tgt = evt.target || window.event.srcElement;
            const files = tgt.files;

            // Kiểm tra FileReader và file đã chọn
            if (FileReader && files && files.length) {
                const fr = new FileReader();

                fr.onload = function () {
                    // Cập nhật src của ảnh
                    preview.src = fr.result;
                }

                // Đọc file
                fr.readAsDataURL(files[0]);
            }
        });
    }
}