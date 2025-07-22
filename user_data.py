import os
import json
from datetime import datetime, timezone


class UserData:
    def __init__(self, user_data_file, convo_history_file, exercise_logs_file):
        self.user_data_file = user_data_file
        self.convo_history_file = convo_history_file
        self.exercise_logs_file = exercise_logs_file
        self.user_data = {}
        self.conversation_history = {}
        self.exercise_logs = {}
        self.load_all_data()

    def load_all_data(self):
        for path, attr_name in [
            (self.user_data_file, "user_data"),
            (self.convo_history_file, "conversation_history"),
            (self.exercise_logs_file, "exercise_logs"),
        ]:
            try:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        setattr(self, attr_name, json.load(f))
            except Exception as e:
                print(
                    f"UserData: Error loading {attr_name} from {path}: {e}. Starting empty."
                )
                setattr(self, attr_name, {})

    def save_all_data(self):
        for path, data_dict in [
            (self.user_data_file, self.user_data),
            (self.convo_history_file, self.conversation_history),
            (self.exercise_logs_file, self.exercise_logs),
        ]:
            try:
                with open(path, "w") as f:
                    json.dump(data_dict, f, indent=4)
            except Exception as e:
                print(f"UserData: Error saving to {path}: {e}")

    def get_user_profile(self, user_id):
        return self.user_data.get(user_id, {})

    def ensure_user_profile_exists(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "last_interaction_timestamp": datetime.now().isoformat(),
                "onboarding_status": "NEEDS_ONBOARDING",
                "is_new_session_flag": "true",
                "current_mood": "NEUTRAL",
                "disengagement_strikes": 0,
                "current_session_start_timestamp": datetime.now().isoformat(),
                "current_active_agent_name": "OnboardingSubAgent",
                "current_activity_state": "ONBOARDING",  # CHANGED
            }
            print(f"UserData: Created new profile for user '{user_id}'.")
            self.save_all_data()

        profile = self.user_data[user_id]
        if "current_active_agent_name" not in profile:
            if profile.get("onboarding_status") == "ONBOARDING_COMPLETE":
                profile["current_active_agent_name"] = "PostOnboardingSubAgent"
                profile["current_activity_state"] = "GENERAL_CHAT"  # CHANGED
                if profile.get("onboarding_status") == "IN_MCQ_EXERCISE":
                    profile["current_active_agent_name"] = "QuizMasterSubAgent"
                    profile["current_activity_state"] = "IN_MCQ_EXERCISE"  # CHANGED
            else:
                profile["current_active_agent_name"] = "OnboardingSubAgent"
                profile["current_activity_state"] = "ONBOARDING"  # CHANGED
            self.save_all_data()
        if "current_activity_state" not in profile:
            profile["current_activity_state"] = (
                "GENERAL_CHAT"
                if profile.get("onboarding_status") == "ONBOARDING_COMPLETE"
                else "ONBOARDING"
            )  # CHANGED
            self.save_all_data()
        return self.user_data[user_id]

    def get_user_attribute_tool(self, user_id, attribute_name=None):
        profile = self.ensure_user_profile_exists(user_id)
        is_new_user_check = profile.get(
            "onboarding_status"
        ) == "NEEDS_ONBOARDING" and not profile.get("name")
        if (
            isinstance(attribute_name, str)
            and attribute_name.startswith("[")
            and attribute_name.endswith("]")
        ):
            try:
                attribute_name = json.loads(attribute_name.replace("'", '"'))
            except:
                pass
        if not attribute_name:
            return profile.copy()
        if isinstance(attribute_name, list):
            result = {}
            for attr_key in attribute_name:
                value = profile.get(attr_key)
                if value is not None:
                    result[attr_key] = value
                elif is_new_user_check and attr_key == "onboarding_status":
                    result["onboarding_status"] = "NEEDS_ONBOARDING"
                else:
                    result[attr_key] = None
            if (
                is_new_user_check
                and "onboarding_status" in attribute_name
                and result.get("onboarding_status") is None
            ):
                result["onboarding_status"] = "NEEDS_ONBOARDING"
            return result
        if isinstance(attribute_name, str):
            value = profile.get(attribute_name)
            if value is not None:
                return {attribute_name: value}
            elif is_new_user_check and attribute_name == "onboarding_status":
                return {"onboarding_status": "NEEDS_ONBOARDING"}
            else:
                return {attribute_name: None}
        return profile.copy()

    def serialize_part(part):
        if hasattr(part, "text") and part.text is not None:
            return {"text": part.text}
        elif hasattr(part, "function_call") and part.function_call.name:
            fc = part.function_call
            return {
                "function_call": {
                    "name": fc.name,
                    "args": dict(fc.args) if fc.args else {},
                }
            }
        elif hasattr(part, "function_response") and part.function_response.name:
            fr = part.function_response
            # Ensure fr.response is serializable (it should be if tools return dicts)
            response_content = {}
            if fr.response:
                try:
                    # Attempt to convert proto message to dict if necessary
                    # This is a bit of a guess, as fr.response should ideally be a dict
                    # from our tool_implementations_map.
                    response_content = dict(fr.response)
                except:  # If it's already a dict or fails
                    response_content = (
                        {"raw_response_data": str(fr.response)} if fr.response else {}
                    )

            return {
                "function_response": {"name": fr.name, "response": response_content}
            }
        return {"unknown_part_type": str(part)}

    def get_sdk_compatible_session_history(self, user_id, for_agent_name=None):
        profile = self.ensure_user_profile_exists(user_id)
        session_start_ts_str = profile.get("current_session_start_timestamp")
        if not session_start_ts_str:
            return []
        try:
            session_start_dt = datetime.fromisoformat(session_start_ts_str)
            if session_start_dt.tzinfo is None:
                session_start_dt = session_start_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return []

        all_user_history = self.conversation_history.get(user_id, [])
        sdk_history = []
        for entry in all_user_history:
            entry_ts_str = entry.get("timestamp")
            if not entry_ts_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=timezone.utc)

                if entry_dt >= session_start_dt:
                    serialized_parts_for_sdk = []
                    raw_parts = entry.get("parts", [])
                    if isinstance(raw_parts, list):  # Ensure it's a list
                        for p_item in raw_parts:
                            if isinstance(
                                p_item, dict
                            ):  # Already a dict, assume serializable
                                # Further check common structures from serialize_part
                                if "text" in p_item:
                                    serialized_parts_for_sdk.append(
                                        {"text": str(p_item["text"])}
                                    )  # Ensure text
                                elif "function_call" in p_item and isinstance(
                                    p_item["function_call"], dict
                                ):
                                    # Ensure args are dict
                                    fc_args = p_item["function_call"].get("args", {})
                                    if not isinstance(fc_args, dict):
                                        fc_args = {"data": str(fc_args)}
                                    serialized_parts_for_sdk.append(
                                        {
                                            "function_call": {
                                                "name": str(
                                                    p_item["function_call"].get("name")
                                                ),
                                                "args": fc_args,
                                            }
                                        }
                                    )
                                elif "function_response" in p_item and isinstance(
                                    p_item["function_response"], dict
                                ):
                                    fr_resp = p_item["function_response"].get(
                                        "response", {}
                                    )
                                    if not isinstance(fr_resp, dict):
                                        fr_resp = {"data": str(fr_resp)}
                                    serialized_parts_for_sdk.append(
                                        {
                                            "function_response": {
                                                "name": str(
                                                    p_item["function_response"].get(
                                                        "name"
                                                    )
                                                ),
                                                "response": fr_resp,
                                            }
                                        }
                                    )
                                else:  # Unknown dict structure, try to force string
                                    serialized_parts_for_sdk.append(
                                        {"text": json.dumps(p_item, default=str)}
                                    )

                            elif hasattr(p_item, "text"):  # It's a Part object
                                serialized_parts_for_sdk.append(
                                    {"text": str(p_item.text)}
                                )
                            # Add more robust serialization for other Part types if necessary
                            # This is mainly defensive if bad data got into history.

                    if serialized_parts_for_sdk:
                        sdk_history.append(
                            {
                                "role": entry.get("role"),
                                "parts": serialized_parts_for_sdk,
                            }
                        )
            except ValueError:
                # print(f"UserData: Skipping history entry due to timestamp parse error: {entry_ts_str}")
                continue
            except Exception as e_hist_ser:
                print(
                    f"UserData: Error serializing history part for SDK: {e_hist_ser} - Entry: {entry}"
                )
                continue
        return sdk_history

    def save_user_attribute_tool(self, user_id, attribute_name, attribute_value):
        profile = self.ensure_user_profile_exists(user_id)

        # Ensure state values being saved are ALL CAPS if they are known states
        known_onboarding_states_to_capitalize = [
            "pending_reason",
            "pending_native_language",
            "pending_english_level",
            "pending_phone_number",
            "pending_otp",
            "needs_onboarding",
            "otp_verified_pending_mcq",
            "in_mcq_exercise",
            "mcq_completed_pending_upsell",
            "onboarding_complete",
        ]
        known_activity_states_to_capitalize = [
            "general_chat",
            "in_mcq_exercise",
            "onboarding",
            "onboarding_pending_mcq_ack",
        ]

        if (
            attribute_name == "onboarding_status"
            and attribute_value.lower() in known_onboarding_states_to_capitalize
        ):
            attribute_value = attribute_value.upper()
        elif (
            attribute_name == "current_activity_state"
            and attribute_value.lower() in known_activity_states_to_capitalize
        ):
            attribute_value = attribute_value.upper()

        profile[attribute_name] = attribute_value
        profile["last_interaction_timestamp"] = datetime.now().isoformat()
        if attribute_name == "phone_number":
            profile["phone_number_raw"] = attribute_value

        if attribute_name == "onboarding_status":
            if attribute_value == "ONBOARDING_COMPLETE":
                profile["current_active_agent_name"] = "PostOnboardingSubAgent"
                profile["current_activity_state"] = "GENERAL_CHAT"
                print(
                    f"UserData: User '{user_id}' onboarding complete. Active agent -> PostOnboardingSubAgent"
                )
            elif attribute_value == "IN_MCQ_EXERCISE":
                pass
            elif attribute_value == "OTP_VERIFIED_PENDING_MCQ":
                profile["current_activity_state"] = "ONBOARDING_PENDING_MCQ_ACK"
        self.save_all_data()
        return {"status": "success", "message": f"Attribute '{attribute_name}' saved."}

    def get_conversation_history_tool(self, user_id, limit=None):
        history = self.conversation_history.get(user_id, [])
        formatted_history = []
        for entry in history[-limit:] if limit else history:
            text = ""
            if entry.get("role") and entry.get("parts"):
                for part in entry["parts"]:
                    if isinstance(part, dict) and part.get("text"):
                        text += part["text"] + " "
                if text:
                    formatted_history.append(
                        f"{entry['role'].capitalize()}: {text.strip()}"
                    )
        return {
            "history_summary": "\n".join(formatted_history),
            "history_raw": history[-limit:] if limit else history,
        }

    def get_sdk_compatible_session_history(self, user_id, for_agent_name=None):
        profile = self.ensure_user_profile_exists(user_id)
        session_start_ts_str = profile.get("current_session_start_timestamp")
        if not session_start_ts_str:
            return []
        try:
            session_start_dt = datetime.fromisoformat(session_start_ts_str)
            if session_start_dt.tzinfo is None:
                session_start_dt = session_start_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return []

        all_user_history = self.conversation_history.get(user_id, [])
        sdk_history = []
        for entry in all_user_history:
            entry_ts_str = entry.get("timestamp")
            if not entry_ts_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(entry_ts_str.replace("Z", "+00:00"))
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=timezone.utc)
                if entry_dt >= session_start_dt:
                    sdk_parts = []
                    for p_item in entry.get("parts", []):
                        if isinstance(p_item, dict) and "text" in p_item:
                            sdk_parts.append({"text": p_item["text"]})
                        elif isinstance(p_item, dict) and "function_call" in p_item:
                            sdk_parts.append({"function_call": p_item["function_call"]})
                        elif isinstance(p_item, dict) and "function_response" in p_item:
                            sdk_parts.append(
                                {"function_response": p_item["function_response"]}
                            )
                    if sdk_parts:
                        sdk_history.append(
                            {"role": entry.get("role"), "parts": sdk_parts}
                        )
            except ValueError:
                continue
        return sdk_history

    def add_turn_to_history(self, user_id, role, parts_list, handler_agent_name=None):
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        history_entry = {
            "role": role,
            "parts": parts_list,
            "timestamp": datetime.now().isoformat(),
        }
        if handler_agent_name:
            history_entry["handler_agent_name"] = handler_agent_name
        self.conversation_history[user_id].append(history_entry)
        self.save_all_data()

    def record_exercise_result_tool(
        self,
        user_id,
        exercise_id,
        exercise_type,
        score,
        correct_answers,
        total_questions,
        improvement_areas=None,
    ):
        print(
            f"UserData: record_exercise_result_tool for user '{user_id}', exercise '{exercise_id}'"
        )
        profile = self.ensure_user_profile_exists(user_id)
        if user_id not in self.exercise_logs:
            self.exercise_logs[user_id] = []
        result = {
            "exercise_id": exercise_id,
            "exercise_type": exercise_type,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "improvement_areas": improvement_areas or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.exercise_logs[user_id].append(result)
        profile["last_interaction_timestamp"] = datetime.now().isoformat()
        profile["current_activity_state"] = "GENERAL_CHAT"
        profile["current_active_agent_name"] = "PostOnboardingSubAgent"
        for key in [
            "current_exercise_id",
            "current_exercise_topic",
            "current_exercise_questions",
            "current_exercise_answers",
            "current_exercise_question_index",
        ]:
            if key in profile:
                del profile[key]
        if profile.get("onboarding_status") == "IN_MCQ_EXERCISE":
            profile["onboarding_status"] = "MCQ_COMPLETED_PENDING_UPSELL"
        print(
            f"UserData: Exercise result recorded. Active agent -> {profile['current_active_agent_name']}"
        )
        self.save_all_data()
        return {"status": "success", "message": "Exercise result recorded."}

    def check_activity_status_tool(self, user_id):
        profile = self.ensure_user_profile_exists(user_id)
        last_activity_description = "your English practice"
        if profile.get("current_activity_state") == "IN_MCQ_EXERCISE":  # CHANGED
            last_activity_description = (
                f"the '{profile.get('current_exercise_topic', 'quiz')}'"
            )
        elif (
            profile.get("current_activity_state")
            and profile.get("current_activity_state") != "GENERAL_CHAT"
        ):  # CHANGED
            last_activity_description = (
                f"your '{profile.get('current_activity_state')}' session"
            )
        return {
            "status": "active",
            "user_name": profile.get("name", "User"),
            "last_activity": last_activity_description,
        }

    def direct_to_premium_checkout_tool(self, user_id):
        profile = self.ensure_user_profile_exists(user_id)
        profile.update(
            {
                "last_premium_pitch_timestamp": datetime.now().isoformat(),
                "onboarding_status": "ONBOARDING_COMPLETE",
                "current_active_agent_name": "PostOnboardingSubAgent",
                "current_activity_state": "GENERAL_CHAT",  # CHANGED
            }
        )
        self.save_all_data()
        return {
            "status": "success",
            "message": f"User {user_id} being directed to premium.",
            "checkout_url": "https://example.com/Dr. Dic Tionary/premium",
        }
