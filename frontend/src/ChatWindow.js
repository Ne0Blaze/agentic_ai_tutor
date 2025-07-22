import React, { useEffect, useRef } from 'react';
import Message from './Message';
import './ChatWindow.css';

function ChatWindow({ messages, isLoading }) {
    const chatEndRef = useRef(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="chat-window">
            {messages.map((msg, index) => (
                <Message
                    key={index}
                    sender={msg.sender}
                    text={msg.text}
                    timestamp={msg.timestamp}
                />
            ))}
            {isLoading && (
                <div className="message bot-message typing-indicator">
                    <span>Typing...</span>
                </div>
            )}
            <div ref={chatEndRef} />
        </div>
    );
}

export default ChatWindow; 
