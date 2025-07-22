# --- CONSTANTS ---
from dotenv import dotenv_values

config = dotenv_values(".env")

GRPC_OTP_ERROR_MESSAGE = "OTP service is currently unavailable. Please try again later."
USER_DATA_FILE = "user_data.json"
CONVERSATION_HISTORY_FILE = "conversation_history.json"
EXERCISE_LOGS_FILE = "exercise_logs.json"
API_KEY = config["GEMINI_API_KEY"]

if API_KEY == "":
    print(
        "WARNING: GEMINI_API_KEY is not set or uses a placeholder. Application may not function."
    )
