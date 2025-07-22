# Dr. Dic Tionary AI Tutor

This project is a sophisticated, modular AI-powered English tutor named "Dr. Dic Tionary". It leverages Google's Gemini Pro model to create an interactive and personalized learning experience. The application is built with a Python Flask backend and a React frontend.

## Features

- **Modular Agent-based Architecture**: The backend is built using a multi-agent system, where different agents handle specific tasks like onboarding, quizzes, and general conversation.
- **Interactive Exercises**: The tutor can conduct multiple-choice question (MCQ) exercises to test and improve the user's grammar and vocabulary.
- **Personalized Learning**: The tutor remembers user details and conversation history to provide a tailored experience.
- **Session Management**: Each user has a distinct chat session, and their progress is tracked across sessions.
- **Tool-based Functionality**: The agents can use a variety of tools to perform actions like sending an OTP for verification, managing user data, and conducting exercises.

## Project Structure

The project is organized into a backend and a frontend directory.

### Backend (`agentic_ai_tutor/`)

The backend is a collection of Python modules designed for a scalable and maintainable agentic AI system.

```
agentic_ai_tutor/
│
├── main.py                     # Main application entry point (Flask server)
├── agent.py                    # Core 'Agent' class definition
├── orchestrator.py             # RootAgent that directs traffic to sub-agents
├── session_manager.py          # Manages user chat sessions
├── user_data.py                # Handles user profile and conversation history data
├── tool_providers.py           # Implementation of tools available to the agents
│
├── config.py                   # Configuration for API keys and file paths
├── prompts.py                  # System prompts for the different AI agents
├── tool_schema.py              # Schema definitions for the agent tools
├── exercise_content.py         # Content for the learning exercises
│
├── *.json                      # Data files (user data, history, logs) - excluded by .gitignore
└── .gitignore                  # Specifies files to be ignored by version control
```

**Key Modules:**

-   `main.py`: Initializes the Flask application, sets up global instances of agents and tools, and defines the API endpoints (`/api/init`, `/api/chat`).
-   `agent.py`: Contains the generic `Agent` class, which is the base for all specialized agents. It handles model initialization and the core `invoke` logic.
-   `orchestrator.py`: Defines the `RootAgent`, which is responsible for determining the appropriate sub-agent (e.g., Onboarding, Quiz, General) to handle a user's message based on their current state.
-   `session_manager.py`: Manages Google Generative AI chat sessions for each user, ensuring conversation context is maintained.
-   `user_data.py`: The `UserData` class provides an abstraction layer for reading from and writing to JSON files that store user profiles, conversation histories, and exercise logs.
-   `tool_providers.py`: Contains classes that bundle and implement related tools, such as `OTPToolProvider` for phone verification and `ExerciseToolProvider` for managing quizzes.
-   `config.py`, `prompts.py`, `tool_schema.py`, `exercise_content.py`: These files externalize the configuration, prompts, tool definitions, and exercise content, making the system easier to manage and modify.

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
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    A `requirements.txt` file is included.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure the API Key:**
    Open `agentic_ai_tutor/config.py` and replace `"YOUR_DEFAULT_API_KEY_HERE_PLEASE_REPLACE"` with your actual Google AI API key.

5.  **Run the Flask server:**
    ```bash
    python main.py
    ```
    The backend server will start on `http://127.0.0.1:5001`.

### Frontend

Please follow the instructions in `agentic_ai_tutor/frontend/README.md` to install dependencies and start the React development server. 
