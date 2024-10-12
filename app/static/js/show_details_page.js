document.addEventListener('DOMContentLoaded', async function() {
    const comment_template = document.getElementById('comment-template');
    const comment_container = document.getElementById('comments-container');
    const show_id = comment_container.getAttribute('data-showid');
    const no_comments_label = document.getElementById('no-comments-label');
    const comment_textarea = document.getElementById('comment-textarea');
    const post_comment_button = document.getElementById('comment-button');
    const loading_container = document.getElementById('loading-container');
    const comment_error_label = document.getElementById('comment-error-text');
    const replying_info_label = document.getElementById('replying-info-label');
    const replying_username_label = document.getElementById('replying-username');
    const cancel_reply_button = document.getElementById('cancel-reply-button');
    const current_user_id = Number(this.body.getAttribute('data-authenticated-user-id'));

    var selected_comment = null;

    async function buildComment( comment_data, parent_element ) {
        if ( document.getElementById(`comment-${comment_data.id}`) ) {
            return;
        }
        const new_comment = comment_template.cloneNode(true);
        new_comment.id = `comment-${comment_data.id}`;
        new_comment.querySelector('.comment-username-label').innerText = comment_data.user.username;
        new_comment.querySelector('.comment-text').innerText = comment_data.content;
        new_comment.querySelector('.comment-datetime').date = comment_data.created_at;
        new_comment.querySelector('.comment-avatar').image = `https://www.gravatar.com/avatar/${ comment_data.user.gravatar_hash }&d=retro`
        const reply_button = new_comment.querySelector('.comment-reply-button');
        const delete_button = new_comment.querySelector('.comment-delete-button');
        if ( comment_data.user.id != current_user_id ) {
            delete_button.style.display = 'none';
        }
        if ( current_user_id < 1 ) {
            reply_button.style.display = 'none';
            delete_button.style.display = 'none';
        }
        new_comment.addEventListener('sl-lazy-load', async function() {
            const response = await fetch(`/api/get_comments/${show_id}/${comment_data.id}`);
            if (response.status !== 200) {
                return;
            }
            const replies_data = await response.json();
            for (let reply_data of replies_data['comments']) {
                await buildComment(reply_data, new_comment);
            }
            new_comment.lazy = false;
        });
        if ( comment_data.total_children > 0 ) {
            new_comment.lazy = true;
        }
        new_comment.style.display = 'block';
        if ( current_user_id > 0 ) {
            reply_button.addEventListener('click', function() {
                if ( selected_comment == comment_data.id ) {
                    selected_comment = null;
                    replying_info_label.style.display = 'none';
                    return;
                }
                selected_comment = comment_data.id;
                replying_username_label.innerText = `@${comment_data.user.username}`;
                replying_info_label.style.display = 'block';
            });
        }
        if ( comment_data.user.id == current_user_id ) {
            delete_button.addEventListener('click', async function() {
                const response = await fetch(`/api/delete_comment/${comment_data.id}`, {
                    method: 'DELETE',
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

        parent_element.appendChild(new_comment);
    }

    async function fetch_show_comments() {
        const response = await fetch(`/api/get_comments/${show_id}`);
        if (response.status !== 200) {
            return;
        }
        const comments_data = await response.json();
        for (let comment_data of comments_data['comments']) {
            await buildComment(comment_data, comment_container);
        }
        if (comments_data['comments'].length === 0) {
            no_comments_label.style.display = 'block';
        }
    }
    fetch_show_comments();

    if ( post_comment_button && comment_textarea ) {
        post_comment_button.addEventListener('click', async function() {
            if (comment_textarea.value === '') {
                comment_error_label.innerText = 'Please enter a comment';
                comment_error_label.style.display = 'block';
                return;
            }
            if (comment_textarea.value.length > 1024 || comment_textarea.value.length < 10) {
                comment_error_label.innerText = 'Comment must be between 10 and 1024 characters long';
                comment_error_label.style.display = 'block';
                return;
            }
            comment_error_label.style.display = 'none';
            loading_container.style.display = 'block';
            post_comment_button.disabled = true;

            var response
            if ( !selected_comment ) {
                response = await fetch(`/api/post_comment/${show_id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        content: comment_textarea.value,
                    }),
                });
            } else {
                response = await fetch(`/api/post_comment/${show_id}/${selected_comment}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        content: comment_textarea.value,
                    }),
                });
            }
            if (response.status === 200) {
                comment_textarea.value = '';
                comment_container.innerHTML = '';
                await fetch_show_comments();
            } else {
                const data = await response.json();
                comment_error_label.innerText = data.error;
                comment_error_label.style.display = 'block';
            }
            loading_container.style.display = 'none';
            post_comment_button.disabled = false;
        });

        cancel_reply_button.addEventListener('click', function() {
            selected_comment = null;
            replying_info_label.style.display = 'none';
        });
    }
});