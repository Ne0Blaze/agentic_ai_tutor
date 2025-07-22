import React, { useState, useEffect } from 'react';
import './ExercisePage.css';

function ExercisePage({ userId, exerciseData, onSubmitAnswer, onLoadingChange }) {
    const [selectedOption, setSelectedOption] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Reset selected option when question changes
    useEffect(() => {
        setSelectedOption(null);
    }, [exerciseData?.exercise_prompt]);

    const handleOptionChange = (index) => {
        setSelectedOption(index);
    };

    const handleSubmit = async () => {
        if (selectedOption === null) {
            alert("Please select an answer.");
            return;
        }
        setIsSubmitting(true);
        if (onLoadingChange) onLoadingChange(true); // Notify App.js about loading state

        // The onSubmitAnswer prop will handle the API call and subsequent state updates in App.js
        await onSubmitAnswer(selectedOption);

        setIsSubmitting(false);
        if (onLoadingChange) onLoadingChange(false);
        // No need to reset selectedOption here, useEffect above handles it when exerciseData changes
    };

    if (!exerciseData || !exerciseData.exercise_prompt) {
        return <div className="exercise-container"><p>Loading exercise...</p></div>;
    }

    return (
        <div className="exercise-container">
            <div className="exercise-card">
                <h2>Grammar Exercise</h2>
                <p className="exercise-question">{exerciseData.exercise_prompt}</p>
                <div className="exercise-options">
                    {exerciseData.options && exerciseData.options.map((option, index) => (
                        <button
                            key={index}
                            className={`option-button ${selectedOption === index ? 'selected' : ''}`}
                            onClick={() => handleOptionChange(index)}
                            disabled={isSubmitting}
                        >
                            {option}
                        </button>
                    ))}
                </div>
                <button
                    className="submit-button"
                    onClick={handleSubmit}
                    disabled={selectedOption === null || isSubmitting}
                >
                    {isSubmitting ? 'Submitting...' : 'Submit Answer'}
                </button>
                {exerciseData.question_number && exerciseData.total_questions && (
                    <p className="progress-text">
                        Question {exerciseData.question_number} of {exerciseData.total_questions}
                    </p>
                )}
            </div>
        </div>
    );
}

export default ExercisePage; 
