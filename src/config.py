import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")

DATA_DIR = "./data"
DB_DIR = "./vector_store"
LOG_DIR = "./logs"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

TOP_K = 15
CONFIDENCE_THRESHOLD = 0.55  # Cosine distance above this = warn mechanic
HISTORY_WINDOW = 2           # Number of past exchanges to keep in context