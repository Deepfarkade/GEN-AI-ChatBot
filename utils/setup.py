import os
import vanna as vn
from dotenv import load_dotenv
from vanna.remote import VannaDefault

os.environ['REQUESTS_CA_BUNDLE'] = 'cert.crt'


def setup_connexion():
    
        load_dotenv()
        #api_key = os.environ.get("VANNA_API_KEY")
        api_key = "2e8f6ca84f514b6eab6250c51f6a6d93"
        vanna_model_name = "esp_model"
        vn = VannaDefault(model=vanna_model_name, api_key=api_key)
        

#api_key = # Your API key from https://vanna.ai/account/profile 

#vanna_model_name = # Your model name from https://vanna.ai/account/profile 
#vn = VannaDefault(model=vanna_model_name, api_key=api_key)


