import google.generativeai as genai
import traceback
from config import API_KEY
from user_data import UserData


# --- Generic Agent Class (as defined in the previous response) ---
class Agent:
    def __init__(
        self,
        name,
        model_name,
        instruction,
        tools_schemas=None,  # List of tool schema dicts
        description="",
        before_model_callback=None,  # Not used in this simplified version yet
        before_tool_callback=None,
    ):  # Not used in this simplified version yet
        self.name = name
        self.model_name = model_name
        self.instruction = instruction
        self.description = description
        self.tools_schemas = tools_schemas or []  # Schemas of tools this agent can use
        self.genai_model_instance = None
        self._initialize_model()

    def _initialize_model(self):
        if (
            not self.model_name
            or not API_KEY
            or API_KEY == "YOUR_DEFAULT_API_KEY_HERE_PLEASE_REPLACE"
        ):
            print(
                f"Agent '{self.name}': Model not initialized (missing model_name or API key)."
            )
            return

        try:
            self.genai_model_instance = genai.GenerativeModel(
                self.model_name,
                system_instruction=self.instruction,
                tools=self.tools_schemas,
            )
            print(
                f"Agent '{self.name}' initialized with model '{self.model_name}' and {len(self.tools_schemas)} tools."
            )
        except Exception as e:
            print(
                f"Agent '{self.name}': Error initializing Gemini model '{self.model_name}': {e}"
            )
            traceback.print_exc()
            self.genai_model_instance = None

    def invoke(
        self,
        user_id: str,
        user_message_text: str,
        chat_session: genai.ChatSession,
        tool_implementations_map: dict,
        user_data_agent_ref: "UserData",  # Direct reference for callbacks/state
    ):
        if not self.genai_model_instance:
            print(f"Agent '{self.name}': Cannot invoke, model not initialized.")
            return (
                {
                    "text": "I'm sorry, I'm having a technical issue (model). Please try again later.",
                    "status": "ERROR_MODEL_NOT_INIT",
                },
                None,
                None,
            )

        print(
            f"Agent '{self.name}' (UID: {user_id}) invoking model with: '{user_message_text[:100]}...'"
        )
        try:
            llm_response = chat_session.send_message([{"text": str(user_message_text)}])
        except Exception as e:
            print(f"Agent '{self.name}': Error sending message to Gemini: {e}")
            traceback.print_exc()
            if "ChatSession" in str(type(e.__cause__)) or "Chat" in str(
                type(e.__cause__)
            ):
                print(
                    f"Agent '{self.name}': Attempting to reset chat session for user '{user_id}' due to send_message error."
                )
            return (
                {
                    "text": "I encountered an issue communicating. Please try again.",
                    "status": "ERROR_GEMINI_SEND",
                },
                None,
                None,
            )

        bot_text_reply = ""
        frontend_exercise_data = None
        frontend_exercise_feedback = None
        MAX_FUNCTION_CALL_LOOPS = 7
        loop_count = 0

        while loop_count < MAX_FUNCTION_CALL_LOOPS:
            loop_count += 1
            if (
                not llm_response.candidates
                or not llm_response.candidates[0].content
                or not llm_response.candidates[0].content.parts
            ):
                print(
                    f"Agent '{self.name}': Model response has no parts on loop {loop_count}."
                )
                break

            # >>> START OF ENHANCED LOGGING <<<
            print(
                f"--- Agent '{self.name}' - Turn {loop_count} - Raw LLM Response Parts ---"
            )
            for i, part_debug in enumerate(llm_response.candidates[0].content.parts):
                if hasattr(part_debug, "text") and part_debug.text:
                    print(f"  Part {i} (Text): {part_debug.text}")
                elif (
                    hasattr(part_debug, "function_call")
                    and part_debug.function_call.name
                ):
                    fc_debug = part_debug.function_call
                    args_debug = dict(fc_debug.args) if fc_debug.args else {}
                    print(
                        f"  Part {i} (FunctionCall): Name='{fc_debug.name}', Args={args_debug}"
                    )
                    # Print type of each argument
                    for arg_name, arg_val in args_debug.items():
                        print(
                            f"    Arg '{arg_name}': Value='{arg_val}', Type={type(arg_val)}"
                        )
                else:
                    print(f"  Part {i} (Other): {part_debug}")
            print(f"--- End of Raw LLM Response Parts for Turn {loop_count} ---")
            # >>> END OF ENHANCED LOGGING <<<

            function_call_parts_from_llm = [
                p
                for p in llm_response.candidates[0].content.parts
                if hasattr(p, "function_call") and p.function_call.name
            ]

            for item_part in llm_response.candidates[0].content.parts:
                if hasattr(item_part, "text") and item_part.text:
                    bot_text_reply += item_part.text

            if not function_call_parts_from_llm:
                break

            tool_responses_for_llm = []
            for fc_part in function_call_parts_from_llm:
                fc = fc_part.function_call
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                tool_args["user_id"] = user_id

                if tool_name in tool_implementations_map:
                    try:
                        print(
                            f"Agent '{self.name}' calling tool: {tool_name} with args: {tool_args}"
                        )
                        api_response_data = tool_implementations_map[tool_name](
                            **tool_args
                        )
                        tool_responses_for_llm.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name, response=api_response_data
                                )
                            )
                        )
                        if (
                            tool_name == "start_mcq_exercise"
                            and api_response_data.get("status") == "first_question"
                        ):
                            frontend_exercise_data = api_response_data.copy()
                            if "status" in frontend_exercise_data:
                                del frontend_exercise_data["status"]
                        elif tool_name == "process_mcq_answer_and_get_next_question":
                            if api_response_data.get("status") == "next_question":
                                frontend_exercise_data = api_response_data.copy()
                                if "status" in frontend_exercise_data:
                                    del frontend_exercise_data["status"]
                            elif api_response_data.get("status") == "exercise_complete":
                                frontend_exercise_feedback = api_response_data.copy()
                                if "status" in frontend_exercise_feedback:
                                    del frontend_exercise_feedback["status"]
                                frontend_exercise_data = None
                    except Exception as e_tool:
                        print(
                            f"Agent '{self.name}': Error executing tool {tool_name} for user '{user_id}': {e_tool}"
                        )
                        traceback.print_exc()
                        tool_responses_for_llm.append(
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={
                                        "error": str(e_tool),
                                        "message": f"Tool {tool_name} execution failed.",
                                    },
                                )
                            )
                        )
                else:
                    print(f"Agent '{self.name}': Unknown tool '{tool_name}' requested.")
                    tool_responses_for_llm.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={
                                    "error": "Unknown function",
                                    "message": f"Function {tool_name} is not defined.",
                                },
                            )
                        )
                    )

            if not tool_responses_for_llm:
                break
            bot_text_reply = ""
            print(
                f"Agent '{self.name}': Sending {len(tool_responses_for_llm)} tool response(s) to Gemini."
            )
            try:
                llm_response = chat_session.send_message(tool_responses_for_llm)
            except Exception as e_send_tool_resp:
                print(
                    f"Agent '{self.name}': Error sending tool responses to Gemini: {e_send_tool_resp}"
                )
                traceback.print_exc()
                bot_text_reply = (
                    "I had an issue processing that. Let's try something else."
                )
                break

        response_package = {
            "text": bot_text_reply.strip(),
            "status": "SUCCESS",
        }  # Changed from "success"
        return response_package, frontend_exercise_data, frontend_exercise_feedback
