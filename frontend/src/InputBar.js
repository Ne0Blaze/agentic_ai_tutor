import React, { useState, forwardRef } from 'react';
import './InputBar.css';

// Wrap InputBar with forwardRef to accept a ref and forward it to the DOM input element
const InputBar = forwardRef(({ onSendMessage, isLoading }, ref) => {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (inputValue.trim() && !isLoading) {
            onSendMessage(inputValue);
            setInputValue('');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="input-bar">
            <input
                ref={ref} // Attach the forwarded ref here
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !inputValue.trim()}>
                {isLoading ? 'Sending...' : 'Send'}
            </button>
        </form>
    );
});

export default InputBar; 
