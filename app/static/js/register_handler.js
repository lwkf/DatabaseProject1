document.addEventListener('DOMContentLoaded', async function() {
    const username_input = document.getElementById('username-input');
    const email_input = document.getElementById('email-input');
    const password_input = document.getElementById('password-input');
    const register_button = document.getElementById('register-button');
    const error_message_label = document.getElementById('register-error-text');

    const loading_container = document.getElementById('loading-container');
    async function validate_input() {
        if (username_input.value === '' || email_input.value === '' || password_input.value === '') {
            error_message_label.innerText = 'Please fill in all fields';
            error_message_label.style.display = 'block';
            return false;
        }
        if ( username_input.value.length < 4 || username_input.value.length > 20) {
            error_message_label.innerText = 'Username must be between 4 and 20 characters long';
            error_message_label.style.display = 'block';
            return false;
        }
        if (!username_input.value.match(/^[a-zA-Z0-9]+$/)) {
            error_message_label.innerText = 'Username must contain only letters and numbers';
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

    async function register_handler() {
        if (!await validate_input()) {
            return;
        }
        loading_container.style.display = 'block';
        register_button.disabled = true;

        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username_input.value,
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
        register_button.disabled = false;  
    }

    register_button.addEventListener('click', register_handler);
});