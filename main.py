import google.generativeai as genai
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import atexit
import traceback

from config import (
    API_KEY,
    USER_DATA_FILE,
    CONVERSATION_HISTORY_FILE,
    EXERCISE_LOGS_FILE,
)
from user_data import UserData
from tool_providers import (
    OTPToolProvider,
    ExerciseToolProvider,
    MiscToolProvider,
)
from session_manager import ChatSessionManager
from orchestrator import RootAgent


# --- Flask App Setup & Global Instances ---
app = Flask(__name__)
CORS(app)

user_data_global = UserData(
    USER_DATA_FILE, CONVERSATION_HISTORY_FILE, EXERCISE_LOGS_FILE
)
otp_tools_global = OTPToolProvider(user_data_global)
exercise_tools_global = ExerciseToolProvider(user_data_global)
misc_tools_global = MiscToolProvider(user_data_global, API_KEY)

tool_implementations_map_global = {
    "get_user_attribute": user_data_global.get_user_attribute_tool,
    "save_user_attribute": user_data_global.save_user_attribute_tool,
    "get_conversation_history": user_data_global.get_conversation_history_tool,
    "record_exercise_result": user_data_global.record_exercise_result_tool,
    "check_activity_status": user_data_global.check_activity_status_tool,
    "direct_to_premium_checkout": user_data_global.direct_to_premium_checkout_tool,
    "send_otp": otp_tools_global.send_otp_tool,
    "verify_otp": otp_tools_global.verify_otp_tool,
    "start_mcq_exercise": exercise_tools_global.start_mcq_exercise_tool,
    "process_mcq_answer_and_get_next_question": exercise_tools_global.process_mcq_answer_and_get_next_question_tool,
    "analyze_user_mood": misc_tools_global.analyze_user_mood_tool,
    "get_previous_session_summary": misc_tools_global.get_previous_session_summary_tool,
}

chat_session_manager_global = ChatSessionManager(user_data_global)
Dr_Dic_Tionary_root_agent_global = RootAgent(
    user_data_global, tool_implementations_map_global, chat_session_manager_global
)

atexit.register(user_data_global.save_all_data)


@app.route("/api/init", methods=["POST"])
def init_chat_endpoint():
    data = request.json
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    try:
        profile = user_data_global.ensure_user_profile_exists(user_id)
        active_agent_for_init = (
            Dr_Dic_Tionary_root_agent_global._determine_active_agent(user_id)
        )
        if not active_agent_for_init.genai_model_instance:
            print(
                f"Init Error: Agent {active_agent_for_init.name} model not initialized."
            )
            return jsonify(
                {
                    "error": f"Service initialization error for {active_agent_for_init.name}. Please try again."
                }
            ), 500
        chat_session_manager_global.get_session(user_id, active_agent_for_init)
    except Exception as e:
        print(f"Error during /api/init for user {user_id}: {e}")
        traceback.print_exc()
        return jsonify(
            {"error": "Could not initialize chat session.", "detail": str(e)}
        ), 500

    response_payload = {
        "welcome_message": "Welcome to Dr. Dic Tionary!",
        "onboarding_status": profile.get("onboarding_status"),
        "current_activity_state": profile.get("current_activity_state"),
        "active_agent_name": profile.get("current_active_agent_name"),
        "history": [],
    }
    raw_history = user_data_global.conversation_history.get(user_id, [])[-20:]
    for entry in raw_history:
        sender = "user" if entry.get("role") == "user" else "bot"
        text_content = ""
        for part_item in entry.get("parts", []):
            if isinstance(part_item, dict) and part_item.get("text"):
                text_content += part_item.get("text") + " "
        if text_content.strip():
            response_payload["history"].append(
                {
                    "sender": sender,
                    "text": text_content.strip(),
                    "timestamp": entry.get("timestamp", datetime.now().isoformat()),
                }
            )

    if profile.get("current_activity_state") == "IN_MCQ_EXERCISE":
        current_q_idx = profile.get("current_exercise_question_index", 0)
        questions = profile.get("current_exercise_questions", [])
        if questions and 0 <= current_q_idx < len(questions):
            current_q_data = questions[current_q_idx]
            response_payload["exercise_data"] = {
                "exercise_id": profile.get("current_exercise_id"),
                "exercise_prompt": f"Question {current_q_idx + 1} of {len(questions)}: {current_q_data['question']}",
                "options": current_q_data["options"],
                "question_number": current_q_idx + 1,
                "total_questions": len(questions),
            }
    return jsonify(response_payload)


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.json
    user_id = data.get("userId")
    user_message_text = data.get("message")
    if not user_id or user_message_text is None:
        return jsonify({"error": "userId and message are required"}), 400

    try:
        response_data, fe_exercise_data, fe_exercise_feedback = (
            Dr_Dic_Tionary_root_agent_global.handle_user_message(
                user_id, user_message_text
            )
        )
        if fe_exercise_data:
            response_data["exercise_data"] = fe_exercise_data
        if fe_exercise_feedback:
            response_data["exercise_feedback"] = fe_exercise_feedback
        print(
            f"Dr. Dic Tionary Flask: Responding for user '{user_id}': '{response_data.get('response_text', '')[:100]}...' (Agent: {response_data.get('active_agent_for_turn')})"
        )
        return jsonify(response_data)
    except Exception as e:
        print(
            f"Dr. Dic Tionary Flask: UNEXPECTED FATAL error in chat endpoint for user '{user_id}': {e}"
        )
        traceback.print_exc()
        return jsonify(
            {
                "error": "A critical server error occurred. Please try again later.",
                "detail": str(e),
            }
        ), 500


if __name__ == "__main__":
    print(
        "Dr. Dic Tionary AI Tutor (Simplified Sub-Agent Architecture) backend starting..."
    )
    if not API_KEY or API_KEY == "YOUR_DEFAULT_API_KEY_HERE_PLEASE_REPLACE":
        print(
            "CRITICAL: GOOGLE_API_KEY is not set or is using the default placeholder."
        )
    else:
        try:
            genai.configure(api_key=API_KEY)
            print("GenAI configured successfully with API Key.")
        except Exception as e:
            print(f"Failed to configure GenAI globally: {e}")
            traceback.print_exc()
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
