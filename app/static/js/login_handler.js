document.addEventListener('DOMContentLoaded', async function() {
    const email_input = document.getElementById('email-input');
    const password_input = document.getElementById('password-input');
    const login_button = document.getElementById('login-button');
    const error_message_label = document.getElementById('login-error-text');

    const loading_container = document.getElementById('loading-container');
    async function validate_input() {
        if (email_input.value === '' || password_input.value === '') {
            error_message_label.innerText = 'Please fill in all fields';
            error_message_label.style.display = 'block';
            return false;
        }
        if (password_input.value.length < 8) {
            error_message_label.innerText = 'Password must be at least 8 characters long';
            error_message_label.style.display = 'block';
            return false;
        }
        if (!email_input.value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
            error_message_label.innerText = 'Invalid email address';
            error_message_label.style.display = 'block';
            return false;
        }
        error_message_label.style.display = 'none';
        return true;
    }

    async function login_handler() {
        if (!await validate_input()) {
            return;
        }
        loading_container.style.display = 'block';
        login_button.disabled = true;

        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email_input.value,
                password: password_input.value,
            }),
        });
        if (response.status === 200) {
            window.location.href = '/';
            return;
        } else {
            const data = await response.json();
            error_message_label.innerText = data.error;
            error_message_label.style.display = 'block';
        }
        loading_container.style.display = 'none';
        login_button.disabled = false;  
    }

    login_button.addEventListener('click', login_handler);
});