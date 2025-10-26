function togglePassword(inputId) {
    const passwordInput = document.getElementById(inputId);
    const toggleButton = passwordInput.nextElementSibling;
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleButton.textContent = '🙈';
    } else {
        passwordInput.type = 'password';
        toggleButton.textContent = '👁️';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const passwordInputId = document.getElementById('loginForm').querySelector('input[name="password"]').id;
    const passwordInput = document.getElementById(passwordInputId);

    if (passwordInput) {
        const toggleButton = passwordInput.nextElementSibling;
        if (toggleButton && toggleButton.classList.contains('toggle-password')) {
            toggleButton.setAttribute('onclick', `togglePassword('${passwordInputId}')`);
            toggleButton.onclick = () => togglePassword(passwordInputId);
        }
    }
});