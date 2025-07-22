import google.generativeai as genai
import traceback
from user_data import UserData
from agent import Agent


class ChatSessionManager:
    def __init__(self, user_data_ref: UserData):
        # Store: { user_id: (session_object, agent_name_string) }
        self.active_chat_sessions: dict[str, tuple[genai.ChatSession, str]] = {}
        self.user_data_ref = user_data_ref

    def get_session(self, user_id: str, agent: Agent) -> genai.ChatSession | None:
        current_session_tuple = self.active_chat_sessions.get(user_id)

        if current_session_tuple:
            session_object, associated_agent_name = current_session_tuple
            if associated_agent_name == agent.name:
                # Session exists and is for the correct agent type
                print(
                    f"ChatSessionManager: Reusing existing session for user '{user_id}', agent '{agent.name}'."
                )
                return session_object
            else:
                # Session exists but is for a *different* agent type. It's stale.
                print(
                    f"ChatSessionManager: Stale session detected for user '{user_id}'. Old agent: '{associated_agent_name}', New agent: '{agent.name}'. Will create new session."
                )
                # Fall through to create a new session.

        # No session, or stale session, create a new one
        if not agent.genai_model_instance:
            print(
                f"ChatSessionManager: Cannot create session for user '{user_id}', agent '{agent.name}' model not initialized."
            )
            return None

        # Pass agent.name for potential history filtering/preparation if needed in the future
        sdk_history = self.user_data_ref.get_sdk_compatible_session_history(
            user_id, for_agent_name=agent.name
        )
        try:
            print(
                f"ChatSessionManager: Starting new chat session for user '{user_id}', agent '{agent.name}' with {len(sdk_history)} history turns."
            )
            new_session_object = agent.genai_model_instance.start_chat(
                history=sdk_history
            )
            self.active_chat_sessions[user_id] = (
                new_session_object,
                agent.name,
            )  # Store with agent name
            return new_session_object
        except Exception as e:
            print(
                f"ChatSessionManager: Error starting chat for user '{user_id}', agent '{agent.name}': {e}"
            )
            traceback.print_exc()
            # Clean up if creation failed partially
            if user_id in self.active_chat_sessions:
                del self.active_chat_sessions[user_id]
            return None

    def reset_chat_session(self, user_id: str):
        if user_id in self.active_chat_sessions:
            del self.active_chat_sessions[user_id]
            print(
                f"ChatSessionManager: Chat session explicitly reset for user '{user_id}'. New session will be created by get_session on next need."
            )
