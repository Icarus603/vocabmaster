# utils/api_config.py

# WARNING: This file contains sensitive information (API keys).
# It SHOULD BE ADDED to your .gitignore file to prevent it from being committed to version control.

import os
from dotenv import load_dotenv
load_dotenv()

# Netease Youdao API Key for SiliconFlow Embedding service
NETEASE_API_KEY = os.getenv("NETEASE_API_KEY", "")
