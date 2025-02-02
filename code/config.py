from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv('token')
OWM_API = os.getenv('OWM_API')