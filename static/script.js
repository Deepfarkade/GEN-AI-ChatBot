document.addEventListener('DOMContentLoaded', function() {
    const chatHistory = document.getElementById('chat-history');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');

    // Function to scroll to the bottom of the chat history
    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    // Function to handle sending user messages
    function sendMessage() {
        const userMessage = userInput.value;
        chatHistory.innerHTML += `<p class="user-message">You: ${userMessage}</p>`;
        scrollToBottom();

        // Fetch the bot response from the server
        fetch('/chatbot', {
            method: 'POST',
            body: new URLSearchParams({ user_input: userMessage }),
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        })
        .then((response) => response.json())
        .then((data) => {
            const botResponse = data.bot_response;
            chatHistory.innerHTML += `<p class="bot-message">${botResponse}</p>`;

            // Check if there is a prompted question and display it
            const promptedQuestion = data.prompted_question;
            if (promptedQuestion) {
                chatHistory.innerHTML += `<p class="bot-message">Bot: ${promptedQuestion}</p>`;
                scrollToBottom();  // Scroll to the bottom after displaying the prompted question
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });

        userInput.value = ''; // Clear the user input field
    }

    // Event listener for the send button click
    sendButton.addEventListener('click', function (e) {
        e.preventDefault();
        sendMessage();
    });

    // Event listener for the Enter key press in the user input field
    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // Function to display the conversation history received from the server
    function displayServerConversationHistory(conversationHistory) {
        for (const message of conversationHistory) {
            const role = message.role;
            const content = message.content;

            if (role === 'user') {
                chatHistory.innerHTML += `<p class="user-message">User: ${content}</p>`;
            } else if (role === 'assistant') {
                chatHistory.innerHTML += `<p class="bot-message">Bot: ${content}</p>`;
            }
        }
        scrollToBottom();
    }

    // Display the welcome message if available
    function displayWelcomeMessage() {
        fetch('/get_welcome_message')  // Add a new route to retrieve the welcome message
            .then((response) => response.json())
            .then((data) => {
                const botResponse = data.bot_response;
                chatHistory.innerHTML += `<p class="bot-message">${botResponse}</p>`;
                scrollToBottom();
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    }



    // Display the welcome message on page load
    displayWelcomeMessage();
});
