import os
import json
import pandas as pd
import spacy
from flask import Response
from flask import Flask, request, session, redirect, url_for, render_template
from utils.setup import setup_connexion
from utils.vanna_calls import generate_sql_cached, run_sql_cached
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import AIMessage
from flask import jsonify
from jinja2 import Environment, FileSystemLoader


app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Set a secret key for session management

os.environ['REQUESTS_CA_BUNDLE'] = 'cert.crt'
setup_connexion()

TF_ENABLE_ONEDNN_OPTS = 0

# Load spaCy model
nlp = spacy.load("en_core_web_lg")

def find_similar_question(query, user_role):
    predefined_questions_file = f"{user_role.lower().replace(' ', '_')}_predefined_questions.json"

    # Load predefined questions from JSON file
    with open(predefined_questions_file, 'r') as f:
        predefined_questions = json.load(f)

    # Iterate through predefined questions to find the most similar one
    max_similarity = 0
    similar_question = None
    for question in predefined_questions:
        similarity = nlp(question).similarity(nlp(query))
        if similarity > max_similarity:
            max_similarity = similarity
            similar_question = question
    
    return similar_question

def prompt_next_question(query, user_role):
    similar_question = find_similar_question(query, user_role)
    if similar_question:
        predefined_questions_file = f"{user_role.lower().replace(' ', '_')}_Predefined_questions.json"
        
        # Check if the predefined questions file exists
        if os.path.exists(predefined_questions_file):
            # Load predefined questions from the appropriate JSON file
            with open(predefined_questions_file, 'r') as f:
                predefined_questions = json.load(f)
            
            # Find the index of the similar question
            index = predefined_questions.index(similar_question)
            
            # Get the next question in the sequence
            if index + 1 < len(predefined_questions):
                next_question = predefined_questions[index + 1]
            else:
                # Loop back to the first question if the prompted question is the last question
                next_question = predefined_questions[0]
            
            return next_question
    return None


def save_context(self, input_str, output_str):
    self.chat_memory.add_ai_message(output_str)

def save_user_question(question, user_role):
    user_role_file_path = f"{user_role.lower().replace(' ', '_')}_questions.json"

    # Load existing questions from file if it exists
    if os.path.exists(user_role_file_path):
        with open(user_role_file_path, "r") as f:
            user_questions = json.load(f)
    else:
        user_questions = {}

    # Update count or add new question
    user_questions[question] = user_questions.get(question, 0) + 1

    # Save updated questions to file
    with open(user_role_file_path, "w") as f:
        json.dump(user_questions, f, indent=2)  # Write dictionary with indentation for readability

def load_user_questions(user_role):
    user_role_file_path = f"{user_role.lower().replace(' ', '_')}_questions.json"

    if os.path.exists(user_role_file_path):
        with open(user_role_file_path, "r") as f:
            return json.load(f)
    else:
        return {}  # Return an empty dictionary if file doesn't exist

def get_top_5_questions(user_role):
    user_questions = load_user_questions(user_role)

    # Sort questions by count in descending order
    sorted_questions = sorted(user_questions.items(), key=lambda x: x[1], reverse=True)

    # Return the top 5 questions
    top_5_questions = [question for question, count in sorted_questions[:5]]
    return top_5_questions

# Initialize conversation history
memory = ConversationBufferWindowMemory(memory_key="chat_history", k=4, return_messages=True)

# Check if users.json file exists, if not, create an empty one
USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

# Load existing users from the JSON file
try:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
except json.JSONDecodeError:
    users = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]["password"] == password:
            session['logged_in'] = True
            session['username'] = username
            session['user_role'] = users[username]["user_role"]
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_role = request.form['user_role']
        if username not in users:
            users[username] = {"password": password, "user_role": user_role}
            with open(USERS_FILE, "w") as f:
                json.dump(users, f)
            return redirect(url_for('login'))
        else:
            return render_template('signup.html', error='Username already exists')
    return render_template('signup.html')

def process_and_display_sql(question, user_role):
    sql = generate_sql_cached(question=question)
    if sql:
        try:
            df = run_sql_cached(sql=sql)
            if not df.empty:
                # Convert DataFrame to an HTML table with proper formatting
                table_html = generate_responsive_table(df)
                #output = f'Bot: Here are the results of the query:<br>{table_html}'
                output = f'<div class="qtext">Bot: Here are the results of the query:</div><br>{table_html}'
            else:
                output = "Bot: No data found for the given query."
        except Exception as e:
            output = f"Bot: Error executing SQL query: {str(e)}"
    else:
        output = "Bot: Sorry, I couldn't generate a valid SQL query for your question."

    # Save to memory
    memory.save_context({"input": question}, {"output": str(output)})
    # Save user's question to user role-specific file
    save_user_question(question, user_role)
    return output, table_html

def generate_responsive_table(df):
    table_html = df.to_html(index=False, escape=False)
    table_html = table_html.replace('<table', 
    '<table style="font-size: 12px;text-align:center;border:0;"')
    table_html = table_html.replace('<tr', 
    '<tr style="padding:10px; text-align: center; text-transform:uppercase;"')
    table_html = table_html.replace('<td', '<td style="padding:10px;text-align: center"')
    # Add responsive table styles
    table_html = f"""
    <div class="table-responsive" style="max-height: 350px;">
        {table_html}
    </div>
    """
    return table_html





@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        if 'logged_in' in session and session['logged_in']:
            top_5_questions = get_top_5_questions(session.get('user_role', ''))
            return render_template('chatbot.html', top_5_questions=top_5_questions)
        else:
            return redirect(url_for('login'))
    elif request.method == 'POST':
        data = request.json
        user_input = data['user_input']
        user_role = session.get('user_role', '')
        output, table_html = process_and_display_sql(user_input, user_role)

        next_question = prompt_next_question(user_input, user_role)

        return jsonify({'output': output, 'table_html': table_html, 'next_question': next_question})


@app.route('/logout')
def logout():
    # Clear session_state variables related to chat history
    session.pop('past', None)
    session.pop('generated', None)
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_role', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)