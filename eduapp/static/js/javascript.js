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
            icon.classList.toggle("bi-eye");
            icon.classList.toggle("bi-eye-slash");
        });
    }
}