from user_data import UserData
from session_manager import ChatSessionManager
from agent import Agent
from tool_schema import tools_schema
from prompts import (
    SYSTEM_PROMPT_ONBOARDING,
    SYSTEM_PROMPT_POST_ONBOARDING,
    SYSTEM_PROMPT_QUIZ_MASTER,
)


class RootAgent:
    def __init__(
        self,
        user_data_provider: UserData,
        tool_implementations: dict,
        chat_manager: ChatSessionManager,
    ):
        self.user_data = user_data_provider
        self.tool_map = tool_implementations
        self.chat_manager = chat_manager

        onboarding_tools = [
            s
            for s in tools_schema
            if s["name"]
            in [
                "get_user_attribute",
                "save_user_attribute",
                "send_otp",
                "verify_otp",
                "start_mcq_exercise",
                "direct_to_premium_checkout",
            ]
        ]
        quiz_tools = [
            s
            for s in tools_schema
            if s["name"]
            in [
                "process_mcq_answer_and_get_next_question",
                "record_exercise_result",
                "get_user_attribute",
            ]
        ]
        post_onboarding_tools = [
            s
            for s in tools_schema
            if s["name"]
            in [
                "get_user_attribute",
                "save_user_attribute",
                "analyze_user_mood",
                "check_activity_status",
                "get_conversation_history",
                "get_previous_session_summary",
                "start_mcq_exercise",
                "direct_to_premium_checkout",
            ]
        ]

        self.onboarding_agent = Agent(
            name="OnboardingSubAgent",
            model_name="gemini-2.0-flash-001",
            instruction=SYSTEM_PROMPT_ONBOARDING,
            tools_schemas=onboarding_tools,
        )
        self.quiz_master_agent = Agent(
            name="QuizMasterSubAgent",
            model_name="gemini-2.0-flash-001",
            instruction=SYSTEM_PROMPT_QUIZ_MASTER,
            tools_schemas=quiz_tools,
        )
        self.post_onboarding_agent = Agent(
            name="PostOnboardingSubAgent",
            model_name="gemini-2.0-flash-001",
            instruction=SYSTEM_PROMPT_POST_ONBOARDING,
            tools_schemas=post_onboarding_tools,
        )

        self.sub_agents_map = {
            "OnboardingSubAgent": self.onboarding_agent,
            "QuizMasterSubAgent": self.quiz_master_agent,
            "PostOnboardingSubAgent": self.post_onboarding_agent,
        }
        print("Dr. Dic TionaryRootAgent: All sub-agents initialized.")

    def _determine_active_agent(self, user_id: str) -> Agent:
        profile = self.user_data.ensure_user_profile_exists(user_id)

        active_agent_name_from_profile = profile.get("current_active_agent_name")

        onboarding_status = profile.get("onboarding_status")
        current_activity_state = profile.get("current_activity_state")

        determined_agent_name_by_logic = ""
        if current_activity_state == "IN_MCQ_EXERCISE":
            determined_agent_name_by_logic = "QuizMasterSubAgent"
        elif onboarding_status != "ONBOARDING_COMPLETE":
            determined_agent_name_by_logic = "OnboardingSubAgent"
        elif onboarding_status == "ONBOARDING_COMPLETE":
            determined_agent_name_by_logic = "PostOnboardingSubAgent"
        else:
            print(
                f"Dr. Dic TionaryRootAgent: WARNING - Unhandled state for user '{user_id}'. OS: {onboarding_status}, CAS: {current_activity_state}. Defaulting to PostOnboardingSubAgent."
            )
            determined_agent_name_by_logic = "PostOnboardingSubAgent"
            if (
                profile.get("onboarding_status") != "ONBOARDING_COMPLETE"
                or profile.get("current_activity_state") == "IN_MCQ_EXERCISE"
            ):
                profile["onboarding_status"] = "ONBOARDING_COMPLETE"
                profile["current_activity_state"] = "GENERAL_CHAT"
                # No need to self.user_data.save_all_data() here if it's saved below or elsewhere

        if determined_agent_name_by_logic != active_agent_name_from_profile:
            print(
                f"Dr. Dic TionaryRootAgent: Agent Profile Outdated for user '{user_id}'. Profile had: '{active_agent_name_from_profile}', logic now expects: '{determined_agent_name_by_logic}'. Updating profile."
            )
            profile["current_active_agent_name"] = determined_agent_name_by_logic
            self.user_data.save_all_data()  # Save this change
            # Explicit reset is still okay, get_session() will also ensure correctness.
            self.chat_manager.reset_chat_session(user_id)

        selected_agent = self.sub_agents_map.get(determined_agent_name_by_logic)

        if not selected_agent:
            print(
                f"Dr. Dic TionaryRootAgent: CRITICAL ERROR - Determined agent name '{determined_agent_name_by_logic}' not in sub_agents_map. Defaulting to PostOnboardingSubAgent and fixing profile."
            )
            profile["current_active_agent_name"] = "PostOnboardingSubAgent"
            profile["onboarding_status"] = "ONBOARDING_COMPLETE"
            profile["current_activity_state"] = "GENERAL_CHAT"
            self.user_data.user_data[user_id] = profile  # Ensure in-memory is updated
            self.user_data.save_all_data()
            self.chat_manager.reset_chat_session(
                user_id
            )  # Reset for the fallback agent
            return self.post_onboarding_agent  # Return the fallback agent instance

        return selected_agent

    def handle_user_message(self, user_id: str, user_message_text: str):
        active_agent = self._determine_active_agent(user_id)
        chat_session = self.chat_manager.get_session(user_id, active_agent)

        if not chat_session:
            print(
                f"Dr. Dic TionaryRootAgent: CRITICAL - Could not get chat session for agent {active_agent.name}, user {user_id}. Agent model might be uninitialized."
            )
            return (
                {
                    "text": "I'm having trouble initializing our conversation. Please try again in a moment.",
                    "status": "ERROR_CHAT_SESSION_INIT",
                },
                None,
                None,
            )

        self.user_data.add_turn_to_history(
            user_id,
            "user",
            [{"text": user_message_text}],
            handler_agent_name=active_agent.name,
        )
        profile = self.user_data.get_user_profile(user_id)
        profile["last_user_message_text_for_mood"] = user_message_text
        self.user_data.save_all_data()

        response_package, fe_exercise_data, fe_exercise_feedback = active_agent.invoke(
            user_id, user_message_text, chat_session, self.tool_map, self.user_data
        )

        self.user_data.add_turn_to_history(
            user_id,
            "model",
            [{"text": response_package["text"]}],
            handler_agent_name=active_agent.name,
        )

        updated_profile = self.user_data.get_user_profile(user_id)
        final_response_to_frontend = {
            "response_text": response_package["text"],
            "onboarding_status": updated_profile.get("onboarding_status"),
            "current_activity_state": updated_profile.get("current_activity_state"),
            "active_agent_for_turn": active_agent.name,
        }
        if response_package.get("status") != "SUCCESS":  # Check against ALL CAPS
            final_response_to_frontend["error_detail"] = response_package.get("status")

        if fe_exercise_data:
            final_response_to_frontend["exercise_data"] = fe_exercise_data
        elif fe_exercise_feedback:  # If exercise is complete, fe_exercise_data is None
            final_response_to_frontend["exercise_data"] = (
                fe_exercise_feedback  # Use "exercise_data" for consistency
            )

        return final_response_to_frontend, fe_exercise_data, fe_exercise_feedback
