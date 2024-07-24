document.addEventListener("DOMContentLoaded", function() {
    const chatContainer = document.querySelector('.chat-container');
    const chatInput = document.querySelector('#chat-input');
    const sendBtn = document.querySelector('#send-btn');
    const themeBtn = document.querySelector('#theme-btn');
    const deleteBtn = document.querySelector('#delete-btn');

    function appendChatMessage(message, type = 'outgoing') {
        const chatElement = document.createElement('div');
        chatElement.classList.add('chat', type);

        const chatContent = document.createElement('div');
        chatContent.classList.add('chat-content');

        const chatDetails = document.createElement('div');
        chatDetails.classList.add('chat-details');

        const chatParagraph = document.createElement('p');
        chatParagraph.textContent = message;
        chatDetails.appendChild(chatParagraph);

        chatContent.appendChild(chatDetails);
        chatElement.appendChild(chatContent);
        chatContainer.appendChild(chatElement);

        chatContainer.scrollTop = chatContainer.scrollHeight; // Scroll to the bottom
    }

    function sendMessage() {
        const query = chatInput.value.trim();
        if (query) {
            appendChatMessage(query, 'outgoing');
            chatInput.value = ''; // Clear input

            fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    query: query
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    appendChatMessage(data.response, 'incoming');
                } else {
                    appendChatMessage(data.response, 'incoming');
                }
            })
            .catch(error => {
                appendChatMessage('An error occurred. Please try again later.', 'incoming');
                console.error('Error:', error);
            });
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    themeBtn.addEventListener('click', function() {
        document.body.classList.toggle('light-mode');
        const currentTheme = document.body.classList.contains('light-mode') ? 'light' : 'dark';
        themeBtn.textContent = currentTheme === 'light' ? 'dark_mode' : 'light_mode';
    });

    deleteBtn.addEventListener('click', function() {
        chatContainer.innerHTML = ''; // Clear chat
    });
});
