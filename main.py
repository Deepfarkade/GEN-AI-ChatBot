import json
from difflib import get_close_matches
import pyodbc
import pandas as pd

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
        print("An error occurred:", e)
        return None

def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, 'r') as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: list[str]) -> str | None:
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]

def chat_bot():
    knowledge_base: dict = load_knowledge_base("knowledge_base.json")
    
    while True:
        user_input: str = input('You: ')
        
        if user_input.lower() == 'quit':
            break
        
        best_match: str | None = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])
        
        if best_match:
            answer: str = get_answer_for_question(best_match, knowledge_base)
            
            # Check if the answer starts with "Running the query:" to indicate a query execution.
            if answer.startswith("Running the query:"):
                query_to_execute = answer.replace("Running the query: ", "")
                df = execute_sql_query(query_to_execute)
                if df is not None and not df.empty:
                    print('Bot: Here are the results of the query:')
                    print(df)
                else:
                    print('Bot: An error occurred while executing the query.')
            else:
                print(f'Bot: {answer}')
        else:
            print('Bot: I don\'t know the answer. Can you teach me?')
            new_answer = input('Type the answer or "Skip" to Skip: ')
            
            if new_answer.lower() != 'Skip':
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                save_knowledge_base('knowledge_base.json', knowledge_base)
                print('Bot: Thank you! I learned a new response!')

if __name__ == '__main__':
    chat_bot()
