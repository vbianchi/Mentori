import { render } from 'preact'
import { App } from './App'
import './index.css'

// Inject the Google Font link into the head
const fontLink = document.createElement('link');
fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
fontLink.rel = 'stylesheet';
document.head.appendChild(fontLink);

// --- NEW: Inject the Marked.js library for Markdown parsing ---
const markedScript = document.createElement('script');
markedScript.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
markedScript.onload = () => {
    // Once the script is loaded, render the app.
    render(<App />, document.getElementById('app'));
};
document.head.appendChild(markedScript);
