from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import pyodbc
import pandas as pd
import spacy
from fuzzywuzzy import fuzz
from typing import Optional
from collections import Counter
import string
import openai
import random
import os

# Disable SSL warnings
import requests
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

os.environ['REQUESTS_CA_BUNDLE'] = 'cert.crt'

# Replace "YOUR_API_KEY" with your actual OpenAI API key
openai.api_key = "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"

app = Flask(__name__)


# Generate a secure random key using os.urandom
secret_key = os.urandom(24)
app.secret_key = secret_key

# Path to the user database JSON file
USER_DATABASE_PATH = 'user_database.json'

# Load user database from JSON file
def load_user_database():
    if os.path.exists(USER_DATABASE_PATH):
        with open(USER_DATABASE_PATH, 'r') as file:
            user_database = json.load(file)
        return user_database
    else:
        return {"users": []}

# Save user database to JSON file
def save_user_database(user_database):
    with open(USER_DATABASE_PATH, 'w') as file:
        json.dump(user_database, file, indent=2)
        



CONVERSATION_HISTORY_FILE = 'conversation_history.json'

def load_user_conversation_history(user_id):
    # Load user-specific conversation history from the JSON file
    try:
        with open(CONVERSATION_HISTORY_FILE, 'r') as file:
            conversations = json.load(file).get("conversations", [])
            user_history = next((conv for conv in conversations if conv["user_id"] == user_id), {"questions": [], "prompted_question": None})
            return user_history["questions"]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_user_conversation_history(user_id, user_history, prompted_question=None):
    # Load existing conversations or initialize an empty list
    try:
        with open(CONVERSATION_HISTORY_FILE, 'r') as file:
            conversations = json.load(file).get("conversations", [])
    except (FileNotFoundError, json.JSONDecodeError):
        conversations = []

    # Check if there's an existing conversation for the user
    existing_user_conversation = next((conv for conv in conversations if conv["user_id"] == user_id), None)

    if existing_user_conversation:
        # Update the existing user's conversation history with the new question
        update_existing_question(existing_user_conversation, user_history[-1]["content"])
        existing_user_conversation["prompted_question"] = prompted_question
    else:
        # Create a new entry for the user
        new_user_conversation = {
            "user_id": user_id,
            "questions": [{"content": user_history[-1]["content"], "count": 1}],  # Create a list with only the latest question
            "prompted_question": prompted_question
        }
        conversations.append(new_user_conversation)

    # Save updated conversations to the JSON file
    with open(CONVERSATION_HISTORY_FILE, 'w') as file:
        json.dump({"conversations": conversations}, file, indent=2)

    # Invoke generate_user_prompted_question for dynamic generation
    generate_user_prompted_question(user_id, user_history)


def update_existing_question(existing_user_conversation, question_content):
    # Update the count if the question already exists
    for question in existing_user_conversation["questions"]:
        if question["content"] == question_content:
            question["count"] += 1
            return

    # If the question is new, add it with count 1
    existing_user_conversation["questions"].append({"content": question_content, "count": 1})






def analyze_user_history(user_history):
    tokens = []
    for conversation in user_history:
        if "questions" in conversation and isinstance(conversation["questions"], list):
            for message in conversation["questions"]:
                if isinstance(message, dict) and "content" in message:
                    tokens.extend(word.strip(string.punctuation).lower() for word in message["content"].split())
    word_counts = Counter(tokens)
    return word_counts

import random

def generate_user_prompted_question(user_id, user_history):
    if not user_history:
        # If the user has no conversation history, provide random questions from the knowledge base
        available_questions = [q["question"] for q in knowledge_base["questions"]]
        random_questions = random.sample(available_questions, min(4, len(available_questions)))
        formatted_questions = "\n".join([f"{i + 1}) {question}" for i, question in enumerate(random_questions)])
        prompted_question = f"Do you want to know more about:\n{formatted_questions}?"
        print(f"Dynamic Prompted Question for {user_id}:\n{formatted_questions}")
        return prompted_question

    # Extract user's questions from conversation history
    user_questions = [message["content"] for message in user_history]

    # Find the top 4 most asked questions in the user's conversation history that are also in the knowledge base
    question_counts = Counter(user_questions)
    most_asked_questions = [question for question, _ in question_counts.most_common(4)]

    valid_most_asked_questions = []
    for user_question in most_asked_questions:
        matching_questions = [kb_q["question"] for kb_q in knowledge_base["questions"] if user_question.lower() in kb_q["question"].lower()]
        if matching_questions:
            valid_most_asked_questions.append(matching_questions[0])

    # If there are not enough valid most asked questions, fill in the rest randomly
    available_questions = [q["question"] for q in knowledge_base["questions"]]
    remaining_questions = random.sample([q for q in available_questions if q not in valid_most_asked_questions], min(4 - len(valid_most_asked_questions), len(available_questions)))
    all_prompted_questions = valid_most_asked_questions + remaining_questions

    formatted_questions = "\n".join([f"{i + 1}) {question}" for i, question in enumerate(all_prompted_questions)])
    prompted_question = f"Do you want to know more about:\n{formatted_questions}?"
    print(f"Prompted Question for {user_id}:\n{formatted_questions}")
    return prompted_question



# Function to execute an SQL query and return a DataFrame
def execute_sql_query(query):
    try:
        # Establish a connection to SQL Server
        connection = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=IN3269974W2;DATABASE=GEN_AI;Trusted_Connection=yes')

        # Execute the SQL query
        df = pd.read_sql(query, connection)

        # Close the database connection
        connection.close()

        return df
    except pyodbc.Error as e:
        return None

# Load the spaCy language model
#nlp = spacy.load(r"C:\Users\JC421PR\OneDrive - EY\Desktop\Learnings\GEN AI\en_core_web_sm-3.7.0\en_core_web_sm\en_core_web_sm-3.7.0")
nlp = spacy.load("./en_core_web_sm-3.7.0/en_core_web_sm/en_core_web_sm-3.7.0")

# Load the knowledge base from a JSON file
def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

# Save the knowledge base to a JSON file
def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

# Find the best match for a user question in the knowledge base
def find_best_match(user_question: str, questions: list[str], threshold: float) -> Optional[str]:
    best_score = 0
    best_match = None

    # Preprocess user input and known questions to lowercase
    user_question = user_question.lower()
    questions = [q.lower() for q in questions]

    # Find the best match in the knowledge base
    user_question_doc = nlp(user_question)
    for question in questions:
        question_doc = nlp(question)
        similarity = user_question_doc.similarity(question_doc)
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = question

    # If a good match found, return it directly
    if best_match and best_score >= threshold:
        return best_match
    else:
        return None  # Indicate that no good match was found in the knowledge base


# Get the answer for a matched question
def get_answer_for_question(question: str, knowledge_base: dict) -> Optional[str]:
    for q in knowledge_base["questions"]:
        if q["question"].lower() == question:
            return q.get("answer")

# Get response from GPT-3.5-turbo model
def get_response_from_model(user_input):
    # Use GPT-3.5-turbo for prediction
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a chatbot."},
            {"role": "user", "content": user_input},
        ],
        temperature=0.7
    )
    # Extract the assistant's reply content
    assistant_reply = response['choices'][0]['message']['content']
    
    # Log the OpenAI API response
    print("OpenAI API Response:", response)

    return assistant_reply




# Add the route for the root URL to redirect to the login page
@app.route('/')
def index():
    return redirect(url_for('login'))


# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        user_database = load_user_database()

        # Check if user ID and password match
        for user in user_database["users"]:
            if user["id"] == user_id and user["password"] == password:
                # Store the user's ID and name in the session
                session['user_id'] = user_id
                session['user_name'] = user.get('name', '')  # Retrieve the user's name
                print("User logged in successfully. User ID:", user_id)
                return redirect(url_for('chatbot'))
        return render_template('login.html', message='Invalid credentials. Please try again or create a new account.')

    return render_template('login.html', message='')

# Route for creating a new account
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        # Retrieve user details from the form
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        user_name = request.form.get('user_name')
        user_surname = request.form.get('user_surname')

        user_database = load_user_database()

        # Check if user ID already exists
        for user in user_database["users"]:
            if user["id"] == user_id:
                return render_template('create_account.html', message='User ID already exists. Please choose a different one.')
        
        # Add new user to the database
        user_database["users"].append({
        "id": user_id,
        "password": password,
        "name": user_name,
        "surname": user_surname
        })
        save_user_database(user_database)

        # Redirect to the login page after creating an account
        return redirect(url_for('login'))

    return render_template('create_account.html', message='')

# Add a new route to get the welcome message
@app.route('/get_welcome_message')
def get_welcome_message():
    user_id = session.get('user_id', '')
    user_name = session.get('user_name', '')
    welcome_message = f'Hey {user_name}, Nice to see you again. How may I assist you today?'
    return jsonify({'bot_response': welcome_message})



# Route for the chatbot page
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    # Check if the user is authenticated
    if 'user_id' not in session:
        # User is not authenticated, redirect to the login page
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_input = request.form.get('user_input')

        if user_input is not None:
            response = {
                'user_input': user_input,
                'bot_response': '',
                'prompted_question': ''
            }

            if user_input.lower() == 'quit':
                response['bot_response'] = 'Bot: Goodbye!'
            else:
                user_id = session['user_id']

                # Load user-specific conversation history
                user_history = load_user_conversation_history(user_id)

                # Add the user's input to the conversation history
                user_history.append({'role': 'user', 'content': user_input})
                
                # Save user-specific conversation history
                save_user_conversation_history(user_id, user_history)

                # Analyze user's conversation history to generate prompted questions
                prompted_question = generate_user_prompted_question(user_id, user_history)
                response['prompted_question'] = prompted_question

                # Debug: Print prompted question
                print(f"Prompted Question for {user_id}: {prompted_question}")
                

                # Use prompted question as bot's response
                prompted_question = generate_user_prompted_question(user_id, user_history)
                response['bot_response'] = f'Bot: {prompted_question}'

                # Adjust the threshold as needed (0.7 for demonstration)
                best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]], threshold=0.7)

                if best_match:
                    answer = get_answer_for_question(best_match, knowledge_base)

                    if answer and answer.startswith("Running the query:"):
                        query_to_execute = answer.replace("Running the query: ", "")
                        df = execute_sql_query(query_to_execute)
                        if df is not None and not df.empty:
                            # Add a flag to indicate whether there are more rows
                            has_more_rows = len(df) > 10

                            table_html = df.to_html(classes='table table-bordered custom-table', index=False, escape=False).replace('class="dataframe ', 'class="')
                            table_html = table_html.replace('<table', f'<table style="font-size: 12px; max-width: 100%;" data-has-more-rows="{has_more_rows}"')
                            table_html = table_html.replace('<th', '<th style="padding: 10px; background-color: #3498db; color: #fff;"')
                            table_html = table_html.replace('<td', '<td style="padding: 8px;"')
                            response['bot_response'] = f'Bot: Here are the results of the query:<br>{table_html}'
                        else:
                            response['bot_response'] = 'Bot: An error occurred while executing the query.'
                    elif answer:
                        answer = answer.replace("\n", "<br>")
                        response['bot_response'] = 'Bot: ' + answer
                else:
                    # If no match found in the knowledge base, use GPT-3.5-turbo for prediction
                    response_from_model = get_response_from_model(user_input)

                    response['bot_response'] = 'Bot: ' + response_from_model

            return jsonify(response)

    return render_template('chatbot.html')  # Adjust the template name as needed
knowledge_base = load_knowledge_base("knowledge_base.json")    
#if __name__ == '__main__':
#    knowledge_base = load_knowledge_base("knowledge_base.json")
#   app.run(debug=False)
