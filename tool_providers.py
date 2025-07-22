from datetime import datetime, timedelta, timezone
import random
import uuid
import google.generativeai as genai
from user_data import UserData
from exercise_content import EXERCISE_TOPICS_CONTENT


class OTPToolProvider:
    def __init__(self, user_data: UserData):
        self.user_data = user_data

    def send_otp_tool(self, user_id, phone_number):
        profile = self.user_data.ensure_user_profile_exists(user_id)
        otp = str(random.randint(100000, 999999))
        profile["temp_otp"] = otp
        profile["temp_otp_timestamp"] = datetime.now().isoformat()
        profile["phone_number_raw"] = phone_number
        self.user_data.save_all_data()
        print(f"OTPToolProvider: SIMULATED OTP for {user_id} ({phone_number}): {otp}")
        return {"status": "success", "message": f"OTP 'sent' to {phone_number}."}

    def verify_otp_tool(self, user_id, otp_entered):
        profile = self.user_data.get_user_profile(user_id)
        stored_otp = profile.get("temp_otp")
        otp_timestamp_str = profile.get("temp_otp_timestamp")
        if otp_timestamp_str:
            otp_timestamp = datetime.fromisoformat(otp_timestamp_str)
            if datetime.now() - otp_timestamp > timedelta(minutes=5):
                return {"status": "failure", "message": "OTP expired."}
        if stored_otp and stored_otp == otp_entered:
            profile["phone_verified"] = "true"
            profile["onboarding_status"] = "OTP_VERIFIED_PENDING_MCQ"
            if "temp_otp" in profile:
                del profile["temp_otp"]
            if "temp_otp_timestamp" in profile:
                del profile["temp_otp_timestamp"]
            self.user_data.save_all_data()
            return {"status": "success", "message": "OTP verified successfully."}
        else:
            return {"status": "failure", "message": "Invalid OTP."}


class ExerciseToolProvider:
    def __init__(self, user_data: UserData):
        self.user_data = user_data
        self.exercise_content = EXERCISE_TOPICS_CONTENT

    def start_mcq_exercise_tool(self, user_id, topic="basic_grammar_warmup"):
        profile = self.user_data.ensure_user_profile_exists(user_id)
        questions_to_use = self.exercise_content.get(
            topic, self.exercise_content.get("basic_grammar_warmup", [])
        )
        if not questions_to_use:
            return {"status": "error", "message": f"No MCQs for topic '{topic}'."}

        exercise_id = f"mcq_{topic.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}"
        profile.update(
            {
                "current_exercise_id": exercise_id,
                "current_exercise_topic": topic,
                "current_exercise_questions": questions_to_use,
                "current_exercise_answers": [],
                "current_exercise_question_index": 0,
                "onboarding_status": "IN_MCQ_EXERCISE",
                "current_activity_state": "IN_MCQ_EXERCISE",
                "current_active_agent_name": "QuizMasterSubAgent",
            }
        )
        print(
            f"ExerciseToolProvider: User '{user_id}' starting MCQ on '{topic}'. Active agent -> QuizMasterSubAgent."
        )
        self.user_data.save_all_data()
        first_q = questions_to_use[0]
        return {
            "status": "first_question",
            "exercise_id": exercise_id,
            "exercise_prompt": f"Question 1 of {len(questions_to_use)}: {first_q['question']}",
            "options": first_q["options"],
            "question_number": 1,
            "total_questions": len(questions_to_use),
        }

    def process_mcq_answer_and_get_next_question_tool(self, user_id, user_answer_index):
        profile = self.user_data.get_user_profile(user_id)
        if not (
            profile
            and profile.get("current_active_agent_name") == "QuizMasterSubAgent"
            and profile.get("current_activity_state") == "IN_MCQ_EXERCISE"
        ):
            return {"status": "error", "message": "Not in active MCQ or wrong agent."}

        try:
            processed_answer_index = int(float(str(user_answer_index)))
            print(
                f"DEBUG: Processed user_answer_index from '{user_answer_index}' (type: {type(user_answer_index)}) to '{processed_answer_index}' (type: {type(processed_answer_index)})"
            )
        except ValueError:
            print(
                f"ERROR: Could not convert user_answer_index '{user_answer_index}' to an integer."
            )
            return {
                "status": "error",
                "message": "Invalid answer format. Please provide a number for your choice.",
            }

        q_idx = profile.get("current_exercise_question_index", 0)
        questions = profile.get("current_exercise_questions", [])
        if q_idx >= len(questions):
            return {"status": "error", "message": "Exercise already completed."}

        current_q = questions[q_idx]
        is_correct = processed_answer_index == current_q["correct_index"]
        profile.setdefault("current_exercise_answers", []).append(
            {
                "question_id": current_q["id"],
                "user_answer_index": processed_answer_index,
                "correct_answer_index": current_q["correct_index"],
                "is_correct": is_correct,
            }
        )
        profile["current_exercise_question_index"] = q_idx + 1
        self.user_data.save_all_data()

        was_correct = is_correct
        correct_text = current_q["options"][current_q["correct_index"]]
        explanation = current_q.get("explanation", "")

        if profile["current_exercise_question_index"] < len(questions):
            next_q = questions[profile["current_exercise_question_index"]]
            return {
                "status": "next_question",
                "exercise_prompt": f"Q {profile['current_exercise_question_index'] + 1}/{len(questions)}: {next_q['question']}",
                "options": next_q["options"],
                "question_number": profile["current_exercise_question_index"] + 1,
                "total_questions": len(questions),
                "was_previous_answer_correct": was_correct,
                "correct_answer_text": correct_text,
                "explanation": explanation,
            }
        else:
            correct_c = sum(
                ans["is_correct"] for ans in profile["current_exercise_answers"]
            )
            score = f"{correct_c}/{len(questions)}"
            improve = [
                q.get("explanation", q["question"][:30])
                for i, (ans, q) in enumerate(
                    zip(profile["current_exercise_answers"], questions)
                )
                if not ans["is_correct"]
            ]
            return {
                "status": "exercise_complete",
                "exercise_id": profile["current_exercise_id"],
                "exercise_type": profile.get("current_exercise_topic", "MCQ"),
                "score": score,
                "correct_answers": correct_c,
                "total_questions": len(questions),
                "improvement_areas": list(set(improve)),
                "was_previous_answer_correct": was_correct,
                "correct_answer_text": correct_text,
                "explanation": explanation,
            }


class MiscToolProvider:
    def __init__(self, user_data: UserData, api_key):
        self.user_data = user_data
        self.api_key = api_key
        self.mood_model = None
        self.summary_model = None
        if self.api_key and self.api_key != "YOUR_DEFAULT_API_KEY_HERE_PLEASE_REPLACE":
            try:
                self.mood_model = genai.GenerativeModel("gemini-2.0-flash-001")
                self.summary_model = genai.GenerativeModel("gemini-2.0-flash-001")
            except Exception as e:
                print(f"MiscToolProvider: Error initializing utility models: {e}")

    def analyze_user_mood_tool(self, user_id, current_user_message_text=None):
        if not self.mood_model:
            return {
                "user_id": user_id,
                "detected_mood": "NEUTRAL",
                "disengagement_strikes": 0,
            }
        profile = self.user_data.ensure_user_profile_exists(user_id)
        session_history = self.user_data.get_sdk_compatible_session_history(user_id)
        recent_msgs = []
        for entry in reversed(session_history):
            if entry.get("role") == "user":
                text_parts = [
                    p.get("text") for p in entry.get("parts", []) if p.get("text")
                ]
                if text_parts:
                    recent_msgs.append(" ".join(text_parts))
            if len(recent_msgs) >= 4:
                break
        recent_msgs.reverse()
        if current_user_message_text:
            recent_msgs.append(current_user_message_text)
        elif not recent_msgs and profile.get("last_user_message_text_for_mood"):
            recent_msgs.append(profile["last_user_message_text_for_mood"])
        if not recent_msgs:
            return {
                "user_id": user_id,
                "detected_mood": "NEUTRAL",
                "disengagement_strikes": profile.get("disengagement_strikes", 0),
            }

        mood_analysis_prompt = """You are a mood analysis expert.
Analyze only the user's messages provided below from the current interaction to assess their current engagement level.
Respond with ONE of these labels and nothing else: ACTIVE_PARTICIPATION, DISINTERESTED, MILDLY_FRUSTRATED, REPETITIVE_ANSWERS, NEUTRAL.

User messages from current session (most recent is last):"""

        for i, msg in enumerate(recent_msgs):
            mood_analysis_prompt += f"- Message {i + 1}: {msg}\n"

        mood_analysis_prompt += "\nEngagement Level:"
        try:
            resp = self.mood_model.generate_content(mood_analysis_prompt)
            mood = resp.text.strip()
            if mood not in [
                "ACTIVE_PARTICIPATION",
                "DISINTERESTED",
                "MILDLY_FRUSTRATED",
                "REPETITIVE_ANSWERS",
                "NEUTRAL",
            ]:
                mood = "NEUTRAL"
        except Exception as e:
            print(f"Mood tool error: {e}")
            mood = "NEUTRAL"
        profile["current_mood"] = mood
        if mood in ["DISINTERESTED", "REPETITIVE_ANSWERS"]:
            profile["disengagement_strikes"] = (
                profile.get("disengagement_strikes", 0) + 1
            )
        elif mood == "MILDLY_FRUSTRATED":
            profile["disengagement_strikes"] = 0
        else:
            profile["disengagement_strikes"] = 0
        self.user_data.save_all_data()
        print(f"Analyze_user_mood_tool: User '{user_id}' mood: {mood}")
        print(
            f"Analyze_user_mood_tool: User '{user_id}' disengagement_strikes: {profile['disengagement_strikes']}"
        )
        return {
            "user_id": user_id,
            "detected_mood": mood,
            "disengagement_strikes": profile["disengagement_strikes"],
        }

    def get_previous_session_summary_tool(self, user_id):
        if not self.summary_model:
            return {
                "user_id": user_id,
                "summary": "Summary service unavailable.",
                "error": True,
            }
        profile = self.user_data.ensure_user_profile_exists(user_id)
        current_session_start_iso = profile.get("current_session_start_timestamp")
        if not current_session_start_iso:
            return {
                "user_id": user_id,
                "summary": "Cannot determine current session start.",
                "error": True,
            }
        try:
            current_session_start_dt = datetime.fromisoformat(
                current_session_start_iso
            ).replace(
                tzinfo=timezone.utc
                if datetime.fromisoformat(current_session_start_iso).tzinfo is None
                else None
            )
        except:
            return {
                "user_id": user_id,
                "summary": "Error parsing session start timestamp.",
                "error": True,
            }

        all_history = self.user_data.conversation_history.get(user_id, [])
        prev_msgs = []
        for entry in all_history:
            entry_ts_str = entry.get("timestamp")
            if not entry_ts_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(
                    entry_ts_str.replace("Z", "+00:00")
                ).replace(
                    tzinfo=timezone.utc
                    if datetime.fromisoformat(
                        entry_ts_str.replace("Z", "+00:00")
                    ).tzinfo
                    is None
                    else None
                )
                if entry_dt < current_session_start_dt:
                    role = entry.get("role", "unknown")
                    text_parts = [
                        part.get("text")
                        for part in entry.get("parts", [])
                        if isinstance(part, dict) and part.get("text")
                    ]
                    if text_parts:
                        prev_msgs.append(f"{role.capitalize()}: {' '.join(text_parts)}")
            except:
                continue
        if not prev_msgs:
            profile["previous_sessions_summary"] = "No previous session history."
            self.user_data.save_all_data()
            return {"user_id": user_id, "summary": "No previous session history."}

        convo_to_sum = "\n".join(prev_msgs[-100:])
        prompt = f"Summarize this conversation (<150 words):\n{convo_to_sum}\nSummary:"
        try:
            resp = self.summary_model.generate_content(prompt)
            summary = resp.text.strip()
            profile["previous_sessions_summary"] = summary
            self.user_data.save_all_data()
            return {"user_id": user_id, "summary": summary}
        except Exception as e:
            print(f"Summary tool error: {e}")
            err_sum = f"Error summarizing: {e}"
            profile["previous_sessions_summary"] = err_sum
            self.user_data.save_all_data()
            return {"user_id": user_id, "summary": err_sum, "error": True}
