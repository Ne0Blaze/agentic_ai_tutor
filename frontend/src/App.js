import React, { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import ChatWindow from './ChatWindow';
import InputBar from './InputBar';
import ExercisePage from './ExercisePage';

// Function to generate a simple UUID (re-added as it was removed in the revert)
function generateUUID() {
    return 'xxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function App() {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    // userId will be set after the initial screen
    const [userId, setUserId] = useState('');
    const [currentOnboardingStatus, setCurrentOnboardingStatus] = useState('');
    const [currentExerciseData, setCurrentExerciseData] = useState(null);

    // New state for the User ID input screen
    const [userIdInput, setUserIdInput] = useState('');
    const [isUserIdScreenVisible, setIsUserIdScreenVisible] = useState(true);

    const inputBarRef = useRef(null);

    const handleApiResponse = useCallback((data) => {
        // This function will process the API response and update state accordingly.
        // It centralizes the logic for handling text responses, onboarding status, and exercise data.

        // Handle exercise feedback when exercise is complete
        // The agent sets onboarding_status to MCQ_COMPLETED_PENDING_UPSELL (or similar)
        // and the feedback should be in response_text or a dedicated field.
        if (data.exercise_feedback) {
            // The agent's main feedback might be in response_text.
            // Additional structured feedback can be appended or formatted.
            let feedbackText = `Exercise Complete! Score: ${data.exercise_feedback.score}. ${data.exercise_feedback.feedback_summary}`;
            if (data.exercise_feedback.improvement_areas && data.exercise_feedback.improvement_areas.length > 0) {
                feedbackText += '\nAreas for improvement:\n' + data.exercise_feedback.improvement_areas.join('\n');
            }
            const feedbackMessage = { sender: 'bot', text: feedbackText, timestamp: new Date() };
            setMessages(prevMessages => [...prevMessages, feedbackMessage]);
            // After feedback, currentExerciseData should be null (handled by status change)
        }

        if (data.response_text) {
            const botMessage = { sender: 'bot', text: data.response_text, timestamp: new Date() };
            setMessages(prevMessages => [...prevMessages, botMessage]);
        }

        if (data.onboarding_status) {
            setCurrentOnboardingStatus(data.onboarding_status);

            if (data.onboarding_status === 'IN_MCQ_EXERCISE' && data.exercise_data) {
                setCurrentExerciseData(data.exercise_data);
            } else if (data.onboarding_status !== 'IN_MCQ_EXERCISE') {
                // If no longer in exercise, clear exercise data
                // This also handles the case where an exercise finishes
                setCurrentExerciseData(null);
            }
        }
    }, []);

    const sendMessage = useCallback(async (text, type = 'chat_message', payload = {}) => {
        if (!userId) {
            alert("User ID not set. Please start a session.");
            return;
        }
        if (!text && type === 'chat_message') return; // Allow empty text for non-chat messages like exercise submissions if needed

        const userMessageDisplay = type === 'exercise_answer'
            // ? { sender: 'user', text: `(Selected answer for exercise)`, timestamp: new Date() }
            ? {}
            : { sender: 'user', text: text, timestamp: new Date() };

        // Display user's chat message or a placeholder for exercise answer submission
        if (type !== 'internal_call') { // internal_call might be used if we don't want to show user message
            setMessages(prevMessages => [...prevMessages, userMessageDisplay]);
        }

        setIsLoading(true);

        let apiPayload;
        if (type === 'exercise_answer') {
            // Backend expects user_id and message. Agent will interpret message as answer_index.
            // The agent prompt guides it to call process_mcq_answer_and_get_next_question
            // with the user_answer_index it extracts from the message.
            apiPayload = { userId: userId, message: text, onboarding_status: currentOnboardingStatus };
        } else {
            apiPayload = { userId: userId, message: text, onboarding_status: currentOnboardingStatus, ...payload };
        }

        try {
            const response = await fetch('http://127.0.0.1:5001/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(apiPayload),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            handleApiResponse(data);

        } catch (error) {
            console.error("Failed to send message:", error);
            const errorMessage = { sender: 'bot', text: 'Sorry, I encountered an error. Please try again.', timestamp: new Date() };
            setMessages(prevMessages => [...prevMessages, errorMessage]);
        } finally {
            setIsLoading(false);
            // Focus input after message sending cycle is complete, only if not in exercise mode
            // This will be handled by the useEffect below for robustness
        }
    }, [userId, currentOnboardingStatus, handleApiResponse]);

    // Specific function for submitting exercise answers
    const submitExerciseAnswer = useCallback(async (answerIndex) => {
        // The agent is expecting the answer index as part of the user's "message".
        // The system prompt will guide the agent to interpret this message as an answer
        // and call `process_mcq_answer_and_get_next_question` with it.
        // We send the index as a string, as all messages are text.
        await sendMessage(String(answerIndex), 'exercise_answer');
    }, [sendMessage]);

    useEffect(() => {
        const fetchInitialData = async () => {
            if (!userId || isUserIdScreenVisible) return; // Don't fetch if no userId or screen is visible

            console.log(`Initializing chat for user ID: ${userId}`);
            setIsLoading(true);
            try {
                const response = await fetch('http://127.0.0.1:5001/api/init', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ userId })
                });
                if (!response.ok) throw new Error('Failed to initialize chat');
                const data = await response.json();

                let initialMessages = [];
                if (data.welcome_message) {
                    initialMessages.push({ sender: 'bot', text: data.welcome_message, timestamp: new Date() });
                }
                if (data.history) {
                    const formattedHistory = data.history.map(m => ({
                        ...m,
                        timestamp: new Date(m.timestamp || Date.now())
                    }));
                    // Filter out any potential welcome message from history if already added
                    const uniqueHistory = formattedHistory.filter(histMsg => histMsg.text !== data.welcome_message);
                    initialMessages = [...initialMessages, ...uniqueHistory];
                }
                setMessages(initialMessages);

                // Handle initial state from /api/init, which might include ongoing exercise
                handleApiResponse(data);

            } catch (error) {
                console.error("Initialization error:", error);
                // Display a generic welcome or error if init fails, and allow retrying User ID
                setMessages([{ sender: 'bot', text: 'Error initializing session. Please check User ID or try a new one.', timestamp: new Date() }]);
                setIsUserIdScreenVisible(true); // Show User ID screen again on error
                setUserId(''); // Clear faulty userId
            } finally {
                setIsLoading(false);
            }
        };

        fetchInitialData();
    }, [userId, isUserIdScreenVisible, handleApiResponse]);

    // Determine if in exercise mode
    const isInExerciseMode = currentOnboardingStatus === 'IN_MCQ_EXERCISE' && currentExerciseData != null;

    // Effect to focus input bar after messages change and not in exercise mode
    useEffect(() => {
        if (!isInExerciseMode && inputBarRef.current) {
            // Adding a slight delay can sometimes help ensure the element is fully ready for focus after UI updates.
            setTimeout(() => {
                inputBarRef.current.focus();
            }, 0);
        }
    }, [messages, isInExerciseMode]); // Rerun when messages change or exercise mode toggles

    const handleUserIdSubmit = () => {
        let idToUse = userIdInput.trim();
        if (!idToUse) {
            idToUse = generateUUID();
            console.log('No User ID entered, generated new User ID:', idToUse);
        }
        setUserId(idToUse); // This will trigger the fetchInitialData useEffect
        setIsUserIdScreenVisible(false);
        setMessages([]); // Clear any previous messages (e.g. from a failed init attempt)
        setCurrentExerciseData(null); // Clear any previous exercise data
    };

    if (isUserIdScreenVisible) {
        return (
            <div className="App userId-prompt">
                <h1>Welcome to a class with Dr. Dic Tionary</h1>
                <input
                    type="text"
                    value={userIdInput}
                    onChange={(e) => setUserIdInput(e.target.value)}
                    placeholder="Enter User ID (or leave blank for new)"
                />
                <button onClick={handleUserIdSubmit}>Start Session</button>
                <p>If you are a new user or want a new session, leave the User ID blank and click "Start Session".</p>
                {messages.map((msg, index) => (
                    msg.text.startsWith("Error initializing session") && <p key={index} style={{ color: 'red' }}>{msg.text}</p>
                ))}
            </div>
        );
    }

    return (
        <div className="App">
            <header className="App-header">
                <h1>Dr.Dic Tionary(User: {userId})</h1>
            </header>
            {isInExerciseMode ? (
                <ExercisePage
                    userId={userId}
                    exerciseData={currentExerciseData}
                    onSubmitAnswer={submitExerciseAnswer}
                    onLoadingChange={setIsLoading} // Pass setIsLoading to ExercisePage
                />
            ) : (
                <>
                    <ChatWindow messages={messages} isLoading={isLoading} />
                    <InputBar ref={inputBarRef} onSendMessage={sendMessage} isLoading={isLoading} />
                </>
            )}
        </div>
    );
}

export default App; 
