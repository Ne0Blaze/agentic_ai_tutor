import React from 'react';
import ReactDOM from 'react-dom/client'; // For React 18+
import './index.css'; // For global styles
import App from './App'; // Import the main App component

const rootElement = document.getElementById('root');
if (rootElement) {
    const root = ReactDOM.createRoot(rootElement);
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
} else {
    console.error("Failed to find the root element. Ensure your public/index.html has an element with id='root'.");
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
// import reportWebVitals from './reportWebVitals'; // Optional
// reportWebVitals();
