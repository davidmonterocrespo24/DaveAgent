const vscode = acquireVsCodeApi();

const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');

let isProcessing = false;

window.addEventListener('message', event => {
    const message = event.data;

    switch (message.type) {
        case 'processStarted':
            setRunningState(true);
            addSystemMessage("Agent started.");
            break;

        case 'processExited':
            setRunningState(false);
            addSystemMessage(`Agent exited (Code: ${message.code || 0})`);
            break;

        case 'agentEvent':
            handleAgentEvent(message.data);
            break;

        case 'log':
            console.log(message.value);
            break;
    }
});

function handleAgentEvent(data) {
    const type = data.type;
    const content = data.data; // Wrapper logic in VSCodeInterface puts actual data here? 
    // Wait, let's check VSCodeInterface _emit_event:
    // "type": event_type, "data": data

    // Some events put text directly in 'data' dictionary under 'content' key
    // e.g. "agent_message" -> { "agent": "...", "content": "..." }

    const payload = data.data; // This is the inner dict

    switch (type) {
        case 'agent_message':
            addAgentMessage(payload.content, payload.agent);
            break;
        case 'thought':
            addThought(payload.content);
            break;
        case 'task_start':
            addSystemMessage(`⚡ Task: ${payload.title}`);
            break;
        case 'task_complete':
            addSystemMessage(`✓ Completed: ${payload.title}`);
            break;
        case 'request_input':
            // Re-enable input if it was disabled? 
            // Actually we keep it enabled usually, but maybe focus it.
            messageInput.focus();
            break;
        case 'stop_thinking':
            // Maybe hide spinner
            break;
        case 'error':
            addMessage(payload.content, 'error');
            break;
        // ... handle others
    }

    // Auto scroll
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setRunningState(running) {
    if (running) {
        startBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
        messageInput.disabled = false;
        sendBtn.disabled = false;
    } else {
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        messageInput.disabled = true;
        sendBtn.disabled = true;
    }
}

function addMessage(text, className) {
    const div = document.createElement('div');
    div.className = `message ${className}`;

    // Simple markdown rendering could go here
    // For now, simple text with basic formatting
    div.innerText = text;

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addSystemMessage(text) {
    addMessage(text, 'system');
}

function addAgentMessage(text, agentName) {
    const div = document.createElement('div');
    div.className = 'message agent';
    const strong = document.createElement('strong');
    strong.innerText = agentName + ": ";
    div.appendChild(strong);

    const contentSpan = document.createElement('span');
    contentSpan.innerText = text; // Should be markdown rendered
    div.appendChild(contentSpan);

    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addThought(text) {
    addMessage(text, 'thought');
}

startBtn.addEventListener('click', () => {
    vscode.postMessage({ type: 'startAgent' });
});

stopBtn.addEventListener('click', () => {
    vscode.postMessage({ type: 'killAgent' });
});

sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    vscode.postMessage({ type: 'userInput', value: text });
    addMessage(text, 'user');
    messageInput.value = '';
}
