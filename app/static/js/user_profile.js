document.addEventListener('DOMContentLoaded', async function() {
    const comments = document.getElementsByClassName('comment');

    for(let comment of comments) {
        const delete_button = comment.getElementsByClassName('comment-delete-button');
        if (delete_button.length > 0) {
            delete_button[0].addEventListener('click', async function() {
                console.log(comment.getAttribute('data-commentID'));
                const response = await fetch(`/api/delete_comment/${comment.getAttribute('data-commentID')}`, {
                    method: 'UPDATE',
                });
                if (response.status === 200) {
                    comment.remove();
                    location.reload();
                } else {
                    const data = await response.json();
                    comment.getElementsByClassName('comment-error-label')[0].innerText = data.error;
                    comment.getElementsByClassName('comment-error-label')[0].style.display = 'block';
                }
            });
        }
    }
});