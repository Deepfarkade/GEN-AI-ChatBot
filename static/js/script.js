document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM content loaded. Executing JavaScript...');
  const chatForm = document.getElementById('chat-form');
  const chatHistory = document.querySelector('.chat-history');

  chatForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    // Get user input
    const userInput = document.getElementById('user_input').value.trim();
    document.getElementById('user_input').value = '';
    if (userInput === '') return; // Ignore empty input

    

    // Add user message to chat history
    appendMessage('user', userInput);

    // Display loading message
    const loadingMessage = appendLoadingMessage();

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_input: userInput })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      console.log('Server response:', data); // Log the entire response object
      
      // Add bot response to chat history
      appendMessage('bot', data.output);

      // Check if there is a prompted question and display it
      const nextQuestion = data.next_question;
      if (nextQuestion) {
        const promptMessage = "I think you'd like to ask:";
        const clickableQuestion = `<a href="#" class="prompted-question">${nextQuestion}</a>`;
        appendMessage('bot', `Bot: ${promptMessage} ${clickableQuestion}`);
      }

      // Auto-scroll to the bottom of the chat history
      chatHistory.scrollTop = chatHistory.scrollHeight;
    } catch (error) {
      console.error('Error:', error);
    } finally {
      // Remove loading message
      if (loadingMessage) {
        loadingMessage.remove();
      }
    }
  });

  // Event delegation for handling click on prompted questions
  chatHistory.addEventListener('click', function(event) {
    if (event.target.classList.contains('prompted-question')) {
      event.preventDefault();
      // Get the text of the clicked question
      const questionText = event.target.textContent;
      // Fill the input field with the clicked question text
      document.getElementById('user_input').value = questionText;
    }
  });

  function appendLoadingMessage() {
    const loadingMessage = document.createElement('div');
    loadingMessage.classList.add('message2', 'bot', 'loading');
    loadingMessage.innerHTML = `<div class="loading-spinner"></div> Please wait while we are fetching your answer...`;
    chatHistory.appendChild(loadingMessage);
    return loadingMessage;
  }

  function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    // Use innerHTML instead of textContent to render HTML
    messageElement.innerHTML = message;
    chatHistory.appendChild(messageElement);
  }

});
