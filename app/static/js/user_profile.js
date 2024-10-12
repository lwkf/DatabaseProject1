document.addEventListener('DOMContentLoaded', async function() {
    document.getElementById('profile-button').addEventListener('click', function(event) {
        event.preventDefault(); // Prevent the default anchor click behavior
        // Logic to display user profile, e.g., opening a modal or redirecting
        window.location.href = '/profile'; // Redirect to the profile page
    });

    const delete_button = new_comment.querySelector('.comment-delete-button');
    if ( comment_data.user.id != current_user_id ) {
        delete_button.style.display = 'none';
    }
    if ( current_user_id < 1 ) {
        reply_button.style.display = 'none';
        delete_button.style.display = 'none';
    }
    if ( comment_data.user.id == current_user_id ) {
        delete_button.addEventListener('click', async function() {
            const response = await fetch(`/api/delete_comment/${comment_data.id}`, {
                method: 'UPDATE',
            });
            if (response.status === 200) {
                new_comment.remove();
            } else {
                const data = await response.json();
                comment_error_label.innerText = data.error;
                comment_error_label.style.display = 'block';
            }
        });
    }
    if ( comment.is_deleted == "TRUE" ) {
        delete_button.style.display = 'none';
    }
});