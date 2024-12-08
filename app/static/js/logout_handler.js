document.addEventListener('DOMContentLoaded', async function() {
    const logout_button = document.getElementById('logout-button');

    async function logout_handler() {
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            // Successfully logged out, redirect to home or login page
            window.location.href = '/';  // Change this to your desired redirect page
        } else {
            const data = await response.json();
            alert("Logout failed: " + (data.error || "Unknown error")); // Optional: Show an error message
        }
    }

    if (logout_button) {
        logout_button.addEventListener('click', async function() {
            console.log("Logout button clicked");
            const response = await fetch('/api/logout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            
            console.log("Logout response status:", response.status);
            
            if (response.ok) {
                window.location.href = '/';
            } else {
                const data = await response.json();
                alert("Logout failed: " + (data.error || "Unknown error"));
            }
        });
    }
});