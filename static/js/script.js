document.addEventListener('DOMContentLoaded', function() {
  const chatForm = document.getElementById('chat-form');
  const chatHistory = document.querySelector('.chat-history');
  const nextQuestionElement = document.querySelector('.next-question p');
  const topQuestionsContainer = document.querySelector('.top-questions');

  chatForm.addEventListener('submit', async function(event) {
    event.preventDefault();
    // Get user input
    const userInput = document.getElementById('user_input').value.trim();
    document.getElementById('user_input').value = '';
    if (userInput === '') return; // Ignore empty input

    topQuestionsContainer.style.display = 'none';


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
      // Add bot response to chat history
      appendMessage('bot', data.output);

      document.querySelectorAll(".table-responsive th").forEach(headerCell=>{
        headerCell.addEventListener("click",()=>{
          const tableElement = headerCell.parentElement.parentElement.parentElement;
          const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
          const currentIsAscending = headerCell.classList.contains("th-sort-asc");
          sortTableByColumn(tableElement,headerIndex,!currentIsAscending); 
        });
      });      

      // Update next question, if available
      const nextQuestion = data.next_question;
      if (nextQuestion) {
        const promptMessage = "I think you'd like to ask:";
        const clickableQuestion = `<a href="#" class="prompted-question">${nextQuestion}</a>`;
        appendMessage('bot', `${promptMessage} ${clickableQuestion}`);
      }
    
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
  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('prompted-question')) {
      event.preventDefault();
      // Get the text of the clicked question
      const questionText = event.target.textContent;
      // Fill the input field with the clicked question text
      document.getElementById('user_input').value = questionText;
    }
  });

  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('suggestion')) {
      event.preventDefault();
      // Get the text of the clicked question
      const questionText = event.target.textContent;
      // Fill the input field with the clicked question text
      document.getElementById('user_input').value = questionText;
    }
  });

  function appendLoadingMessage() {
    const loadingMessage = document.createElement('div');
    loadingMessage.classList.add('message', 'bot', 'loading');
    loadingMessage.innerHTML = `<div class="loading-spinner"></div><div style="padding: 10px;">Please wait while we are fetching your answer...</div>`;
    chatHistory.appendChild(loadingMessage);
    return loadingMessage;
  }

  function copyToClipboard() {
    var tableHtml = document.querySelector('.table-responsive').innerHTML;
    var tempInput = document.createElement('textarea');
    tempInput.value = tableHtml;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand('copy');
    document.body.removeChild(tempInput);
    alert('Table copied to clipboard!');
  }


  function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);

    const iconElement = document.createElement('div');
    iconElement.classList.add(sender === 'user' ? 'user-icon' : 'bot-icon');
    iconElement.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    messageElement.appendChild(iconElement);

    const contentElement = document.createElement('div');
    contentElement.classList.add('message-content');
    contentElement.innerHTML = message; // Use innerHTML to render HTML content
    messageElement.appendChild(contentElement);

    chatHistory.appendChild(messageElement);
  }
});

function sortTableByColumn(table, column, asc = true) {
  const dirModifier = asc ? 1 : -1;
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.querySelectorAll("tr"));

  // Sort each row
  const sortedRows = rows.sort((a, b) => {
    const aColText = a.querySelector(`td:nth-child(${column + 1})`).textContent;
    const bColText = b.querySelector(`td:nth-child(${column + 1})`).textContent;

    // Check if it's a date
    const isDate = !isNaN(Date.parse(aColText)) && !isNaN(Date.parse(bColText));
    const isNumber = !isNaN(parseFloat(aColText)) && !isNaN(parseFloat(bColText));
    // If it's a date, convert to Date object for comparison
    if (isDate) {
      const dateA = new Date(aColText);
      const dateB = new Date(bColText);
      return (dateA - dateB) * dirModifier;
    } else if (isNumber) {
      const aValue = parseFloat(aColText);
      const bValue = parseFloat(bColText);
      return (aValue - bValue) * dirModifier;
    } else {
      // If not a date, compare as text
      return aColText.localeCompare(bColText) * dirModifier;
    }
  });

  // Remove all existing TRs from the table
  while (tbody.firstChild) {
    tbody.removeChild(tbody.firstChild);
  }

  // Readd the sorted rows
  tbody.append(...sortedRows);

  // Remove existing sorting icons
  table.querySelectorAll("th").forEach(th => {
    th.classList.remove("th-sort-asc", "th-sort-desc");
    th.querySelector('.fa-sort-up')?.remove();
    th.querySelector('.fa-sort-down')?.remove();
  });

  // Add sorting icon to the clicked column header
  const header = table.querySelector(`th:nth-child(${column + 1})`);
  if (asc) {
    header.classList.add("th-sort-asc");
    header.innerHTML += '<i class="fas fa-sort-up"></i> ';
  } else {
    header.classList.add("th-sort-desc");
    header.innerHTML += '<i class="fas fa-sort-down"></i> ';
  }
}