import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("BRIEFF_CHAT_MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("BRIEFF_IMAGE_MODEL", "gpt-image-1")
IMAGE_GEN_SIZE = "1536x1024"
FINAL_ASPECT_RATIO = (4, 3)
FINAL_SIZE = (1920, 1440)
