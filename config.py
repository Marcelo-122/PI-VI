# config.py
import os
from dotenv import load_dotenv

class Config:
    def __init__(self):

        load_dotenv()
        
        self.API_KEY = os.getenv("API_KEY")

cfg = Config()