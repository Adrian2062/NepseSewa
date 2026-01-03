function showLogin() {
    hideAll();
    const el = document.getElementById('loginForm');
    if (el) el.classList.add('active');
}

function showRegister() {
    hideAll();
    const el = document.getElementById('registerForm');
    if (el) el.classList.add('active');
}

function hideAll() {
    document.querySelectorAll('.form-container').forEach(f => f.classList.remove('active'));
}
