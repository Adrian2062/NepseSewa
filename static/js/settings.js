// Settings Page Logic

document.addEventListener('DOMContentLoaded', () => {
    // Demo save button (replace with form submit)
    const saveBtn = document.getElementById('saveAllBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            saveBtn.innerHTML = '<i class="fas fa-check me-2"></i>Saved';
            saveBtn.classList.remove('btn-success');
            saveBtn.classList.add('btn-outline-success');
            setTimeout(() => {
                saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Changes';
                saveBtn.classList.remove('btn-outline-success');
                saveBtn.classList.add('btn-success');
            }, 1400);
        });
    }

    // Password demo validation
    const changeBtn = document.getElementById('changePasswordBtn');
    const passMsg = document.getElementById('passMsg');
    if (changeBtn) {
        changeBtn.addEventListener('click', () => {
            const form = document.getElementById('passwordForm');
            const newP = form?.querySelector('[name="new_password"]')?.value || '';
            const conf = form?.querySelector('[name="confirm_password"]')?.value || '';

            if (!passMsg) return;

            if (newP.length < 6) {
                passMsg.textContent = '❌ Password must be at least 6 characters.';
                passMsg.style.color = '#ef4444';
                return;
            }
            if (newP !== conf) {
                passMsg.textContent = '❌ New password and confirm password do not match.';
                passMsg.style.color = '#ef4444';
                return;
            }
            passMsg.textContent = '✅ Password looks valid (demo). Connect backend to update.';
            passMsg.style.color = '#059669';
        });
    }

    // Delete confirm input
    const delInput = document.getElementById('deleteConfirmInput');
    const delBtn = document.getElementById('confirmDeleteBtn');
    const delMsg = document.getElementById('deleteMsg');
    if (delInput && delBtn) {
        delInput.addEventListener('input', () => {
            const ok = delInput.value.trim().toUpperCase() === 'DELETE';
            delBtn.disabled = !ok;
            if (delMsg) {
                delMsg.textContent = ok ? 'Ready to delete (demo).' : '';
                delMsg.style.color = ok ? '#059669' : '#6b7280';
            }
        });
    }

    // Reset demo
    const resetBtn = document.getElementById('confirmResetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            resetBtn.innerHTML = '<i class="fas fa-check me-2"></i>Reset Done';
            resetBtn.classList.add('disabled');
        });
    }
});
