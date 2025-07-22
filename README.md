# Dr. Dic Tionary AI Tutor

This project is a sophisticated, modular AI-powered English tutor named "Dr. Dic Tionary". It leverages Google's Gemini Pro model to create an interactive and personalized learning experience. The application is built with a Python Flask backend and a React frontend.

## Features

- **Modular, State-Driven Agent Architecture**: The backend uses a multi-agent system where a root orchestrator directs tasks to specialized sub-agents (e.g., Onboarding, Quiz, General Conversation) based on the user's current state.
- **Interactive Onboarding Flow**: A detailed, multi-step process to gather user information and personalize the learning experience.
- **Dynamic MCQ Exercises**: The tutor can conduct multiple-choice question (MCQ) exercises on various topics to test and improve the user's grammar and vocabulary.
- **Personalized & Context-Aware Conversations**: The tutor remembers user details, conversation history, and even analyzes user mood to provide a tailored and empathetic experience.
- **Persistent User Sessions & History**: Each user has a distinct chat session, and their profile, progress, and conversation history are saved across sessions.
- **Tool-Enabled Functionality**: Agents use a variety of tools to perform actions like sending OTPs for verification, managing user data, conducting exercises, and summarizing past conversations.

## Architecture Overview

The backend operates as a **state machine** orchestrated by the `RootAgent`.

1.  **State Management**: The core of the application is the user's state, which is stored in `user_data.json`. Key fields like `onboarding_status` and `current_activity_state` dictate the application's flow.
2.  **Orchestration**: When a user sends a message, the `RootAgent` in `orchestrator.py` first determines the user's current state.
3.  **Delegation**: Based on this state, it delegates the task to the appropriate specialized sub-agent (e.g., `OnboardingSubAgent`, `QuizMasterSubAgent`).
4.  **Agent Execution**: Each sub-agent is a generic `Agent` instance configured with a specific system prompt (from `prompts.py`) and a set of tools (from `tool_schema.py`). The agent invokes the Gemini model to get a response, which might include text or a request to call a tool.
5.  **Tool Implementation**: The actual logic for the tools is implemented in `tool_providers.py` and `user_data.py`. These tools can read or modify the user's state, advancing the state machine.
6.  **Session Context**: The `ChatSessionManager` ensures that the conversational history is correctly loaded for the currently active sub-agent, allowing for seamless transitions between states (e.g., from general chat to a quiz).

## Project Structure

The project is organized into a backend and a frontend directory.

### Backend (`agentic_ai_tutor/`)

```
agentic_ai_tutor/
│
├── main.py                     # Main application entry point (Flask server)
├── orchestrator.py             # The "brain": RootAgent that directs traffic to sub-agents
├── agent.py                    # Core 'Agent' class definition
├── session_manager.py          # Manages user chat sessions and context
├── user_data.py                # Handles user profile, history, and data persistence
│
├── tool_providers.py           # Implementation of tools (OTP, Exercises, Mood Analysis)
├── tool_schema.py              # Schema definitions for all agent tools
├── prompts.py                  # The heart of the AI: System prompts defining agent behavior
├── exercise_content.py         # Content for the learning exercises
│
├── config.py                   # Configuration loader (e.g., API keys from .env)
├── .env                        # Local environment variables (e.g., API_KEY) - You create this
│
├── *.json                      # Data files (user data, history, logs) - excluded by .gitignore
└── .gitignore                  # Specifies files to be ignored by version control
```

**Key Modules:**

-   `main.py`: Initializes the Flask application, sets up global instances of agents and tools, and defines the API endpoints (`/api/init`, `/api/chat`).
-   `orchestrator.py`: The "brain" of the application. Contains the `RootAgent` which acts as a state machine controller, delegating tasks to the appropriate sub-agent based on user state stored in `user_data.json`.
-   `agent.py`: Contains the generic `Agent` class, which is the base for all specialized agents. It handles model initialization and the core `invoke` logic for interacting with the Gemini API.
-   `session_manager.py`: Manages Google Generative AI chat sessions for each user. Crucially, it creates new sessions with the correct history when the active sub-agent changes.
-   `user_data.py`: The data persistence layer. Manages reading from and writing to JSON files that store user profiles, conversation histories, and exercise logs. It also provides several tool implementations that modify user state directly.
-   `tool_providers.py`: Contains classes that bundle and implement the logic for tools like `send_otp`, `start_mcq_exercise`, and `analyze_user_mood`.
-   `prompts.py`: **The heart of the AI's personality and logic.** Contains detailed system prompts that dictate the strict operational flow for each sub-agent (e.g., the multi-step onboarding protocol).
-   `tool_schema.py`: Defines the function signatures (schemas) for all tools available to the AI agents, which are passed to the Gemini model.
-   `exercise_content.py`: Stores the content (questions, answers, explanations) for all MCQ exercises.
-   `config.py`: Loads configuration variables from the `.env` file.

### Frontend (`agentic_ai_tutor/frontend/`)

The frontend is a standard React application. For detailed information on its structure and how to run it, please refer to the `agentic_ai_tutor/frontend/README.md` file.

## Setup and Running the Application

### Backend

1.  **Navigate to the project directory:**
    ```bash
    cd agentic_ai_tutor
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    A `requirements.txt` file is included.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the API Key:**
    The application loads the Google Gemini API key from an environment file.
    a. Create a new file named `.env` in the `agentic_ai_tutor/` directory.
    b. Add the following line to the `.env` file, replacing `YOUR_API_KEY_HERE` with your actual Google AI API key:
    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

5.  **Run the Flask server:**
    ```bash
    python main.py
    ```
    The backend server will start on `http://127.0.0.1:5001`.

### Frontend

Please follow the instructions in `agentic_ai_tutor/frontend/README.md` to install dependencies and start the React development server. 
