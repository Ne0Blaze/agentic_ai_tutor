import React from 'react';
import './Message.css';

function Message({ sender, text, timestamp }) {
    const messageClass = sender === 'user' ? 'user-message' : 'bot-message';

    // Function to format timestamp (optional)
    const formatTime = (date) => {
        if (!date) return '';
        return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div className={`message ${messageClass}`}>
            <div className="message-content">
                <p>{text}</p>
            </div>
            {timestamp && <span className="message-timestamp">{formatTime(timestamp)}</span>}
        </div>
    );
}

export default Message; 
