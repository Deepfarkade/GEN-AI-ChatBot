document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatHistory = document.querySelector('.chat-history');
    const nextQuestionElement = document.querySelector('.next-question p');
  
    chatForm.addEventListener('submit', async function(event) {
      event.preventDefault();
      // Get user input
      const userInput = document.getElementById('user_input').value.trim();
      document.getElementById('user_input').value = '';
      if (userInput === '') return; // Ignore empty input
  
      // Add user message to chat history
      appendMessage('user', userInput);
  
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
        // Add bot response to chat history
        appendMessage('bot', data.output);
  
        // Update next question, if available
        if (nextQuestionElement) {
          nextQuestionElement.textContent = data.next_question || '';
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  
    function appendMessage(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender);
        // Use innerHTML instead of textContent to render HTML
        messageElement.innerHTML = message;
        chatHistory.appendChild(messageElement);
      }
  });