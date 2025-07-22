tools_schema = [
    {
        "name": "get_user_attribute",
        "description": "Retrieves user attributes (e.g., name, onboarding_status, phone_number_raw).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "attribute_name": {
                    "type": "STRING",
                    "nullable": True,
                    "description": "e.g. 'name', 'onboarding_status'. Can be a single string or a list of strings. If null, returns all attributes.",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "save_user_attribute",
        "description": "Saves/updates user attributes.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "attribute_name": {"type": "STRING"},
                "attribute_value": {"type": "STRING"},
            },
            "required": ["user_id", "attribute_name", "attribute_value"],
        },
    },
    {
        "name": "send_otp",
        "description": "Sends OTP to user's phone.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "phone_number": {"type": "STRING"},
            },
            "required": ["user_id", "phone_number"],
        },
    },
    {
        "name": "verify_otp",
        "description": "Verifies OTP.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "otp_entered": {"type": "STRING"},
            },
            "required": ["user_id", "otp_entered"],
        },
    },
    {
        "name": "get_conversation_history",
        "description": "Retrieves conversation history. Use sparingly.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "limit": {"type": "INTEGER", "nullable": True},
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "check_activity_status",
        "description": "Checks user activity status for session resumption.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"user_id": {"type": "STRING"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "record_exercise_result",
        "description": "Records MCQ results.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_id": {"type": "STRING"},
                "exercise_id": {"type": "STRING"},
                "exercise_type": {"type": "STRING"},
                "score": {"type": "STRING"},
                "correct_answers": {"type": "INTEGER"},
                "total_questions": {"type": "INTEGER"},
                "improvement_areas": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"},
                    "nullable": True,
                },
            },
            "required": [
                "user_id",
                "exercise_id",
                "exercise_type",
                "score",
                "correct_answers",
                "total_questions",
            ],
        },
    },
    {
        "name": "start_mcq_exercise",
        "description": "Initiates an MCQ exercise.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"user_id": {"type": "STRING"}, "topic": {"type": "STRING"}},
            "required": ["user_id", "topic"],
        },
    },
    {
        "name": "process_mcq_answer_and_get_next_question",
        "description": "Processes user's MCQ answer index. Returns feedback, and the next question or exercise completion status.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "user_answer_index": {
                    "type": "INTEGER",
                    "description": "The 0-based integer index of the user's selected answer option. This value MUST be a whole number (integer), not a decimal/float or a string.",
                },
            },
            "required": ["user_answer_index"],
        },
    },
    {
        "name": "direct_to_premium_checkout",
        "description": "Directs to premium checkout.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"user_id": {"type": "STRING"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "analyze_user_mood",
        "description": "Analyzes the user's mood and engagement.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"user_id": {"type": "STRING"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "get_previous_session_summary",
        "description": "Generates and retrieves a summary of previous sessions.",
        "parameters": {
            "type": "OBJECT",
            "properties": {"user_id": {"type": "STRING"}},
            "required": ["user_id"],
        },
    },
]
