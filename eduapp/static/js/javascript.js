function setupPasswordToggle(triggerId, inputId, iconId) {
        const trigger = document.getElementById(triggerId);
        const input = document.getElementById(inputId);
        const icon = document.getElementById(iconId);
        if (trigger && input && icon) {
            trigger.addEventListener("click", function () {
                const currentType = input.getAttribute("type");
                const newType = currentType === "password" ? "text" : "password";
                input.setAttribute("type", newType);
                if(newType === 'text'){
                    icon.classList.remove("bi-eye-slash");
                    icon.classList.add("bi-eye");
                    trigger.classList.add("text-primary");
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
    if (input && preview) {
        input.addEventListener('change', function (evt) {
            const tgt = evt.target || window.event.srcElement;
            const files = tgt.files;
            if (FileReader && files && files.length) {
                const fr = new FileReader();
                fr.onload = function () {
                    preview.src = fr.result;
                }
                fr.readAsDataURL(files[0]);
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    var dropdownToggles = document.querySelectorAll('.js-dropdown-fixed');
    dropdownToggles.forEach(function(toggle) {
        if (typeof bootstrap !== 'undefined') {
            var instance = bootstrap.Dropdown.getInstance(toggle);
            if (instance) {
                instance.dispose();
            }
            new bootstrap.Dropdown(toggle, {
                popperConfig: function(defaultConfig) {
                    var newConfig = Object.assign({}, defaultConfig);
                    newConfig.strategy = 'fixed';
                    return newConfig;
                }
            });
        }
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const loader = document.getElementById('loading-overlay');
    const showLoader = () => {
        if (loader) {
            loader.classList.remove('d-none');
            loader.classList.add('d-flex');
        }
    };
    const hideLoader = () => {
        if (loader) {
            loader.classList.add('d-none');
            loader.classList.remove('d-flex');
        }
    };
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const action = form.getAttribute('action') || "";
            if (action.includes('export')) return;
            if (form.checkValidity() && !form.target) {
                showLoader();
            }
        });
    });
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const target = this.getAttribute('target');
            if (href) {
                const lowerHref = href.toLowerCase();
                if (lowerHref.includes('export') ||
                    lowerHref.includes('download') ||
                    lowerHref.includes('.csv') ||
                    lowerHref.includes('.xlsx')) {
                    return;
                }
            }

            if (href &&
                !href.startsWith('#') &&
                !href.startsWith('javascript:') &&
                target !== '_blank') {
                showLoader();
            }
        });
    });
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            hideLoader();
        }
    });
});

function chuyenCheDoVaMoModal(event) {
    if (event) event.preventDefault();
    var toggleBtn = document.getElementById('sidebarToggle');
    var isExpanded = toggleBtn && toggleBtn.getAttribute('aria-expanded') === 'true';
    if (isExpanded) {
        toggleBtn.click();
    }
    setTimeout(function() {
        var modalElement = document.getElementById('modalCheckPin');
        var bsModal = bootstrap.Modal.getInstance(modalElement);
        if (!bsModal) {
            bsModal = new bootstrap.Modal(modalElement);
        }
        bsModal.show();
    }, 350);
}

let mybutton = document.getElementById("btn-back-to-top");
window.onscroll = function () {
    scrollFunction();
};

function scrollFunction() {
    if (document.body.scrollTop > 100 || document.documentElement.scrollTop > 100) {
        mybutton.style.display = "block";
    } else {
        mybutton.style.display = "none";
    }
}

mybutton.addEventListener("click", backToTop);

function backToTop() {
    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}
