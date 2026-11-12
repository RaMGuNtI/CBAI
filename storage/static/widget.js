(function() {
    const script = document.currentScript;
    const botId = script.getAttribute('data-bot-id');
    const color = script.getAttribute('data-color') || '#4F46E5';

    // Create launcher button
    const btn = document.createElement('div');
    btn.id = 'custombot-launcher';
    btn.innerHTML = '💬';
    btn.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: ${color};
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        z-index: 999999;
        transition: transform 0.2s ease;
    `;

    // Create Chat Container
    const container = document.createElement('div');
    container.id = 'custombot-container';
    container.style.cssText = `
        position: fixed;
        bottom: 96px;
        right: 24px;
        width: 380px;
        height: 520px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.18);
        display: none;
        flex-direction: column;
        overflow: hidden;
        z-index: 999999;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    `;

    container.innerHTML = `
        <div style="background:${color}; color:white; padding:16px; font-weight:600; display:flex; justify-content:space-between; align-items:center;">
            <span>CustomBot AI</span>
            <span id="custombot-close" style="cursor:pointer; font-size:20px;">&times;</span>
        </div>
        <div id="custombot-messages" style="flex:1; padding:16px; overflow-y:auto; display:flex; flex-direction:column; gap:10px; font-size:14px; background:#f9fafb;">
            <div style="background:#e5e7eb; padding:8px 12px; border-radius:8px; align-self:flex-start; max-width:80%;">
                Connecting to assistant...
            </div>
        </div>
        <div style="padding:12px; border-top:1px solid #e5e7eb; display:flex; gap:8px;">
            <input id="custombot-input" type="text" placeholder="Type your inquiry..." style="flex:1; padding:8px 12px; border:1px solid #d1d5db; border-radius:6px; outline:none; font-size:14px;" />
            <button id="custombot-send" style="background:${color}; color:white; border:none; border-radius:6px; padding:8px 14px; cursor:pointer; font-weight:600;">Send</button>
        </div>
    `;

    document.body.appendChild(btn);
    document.body.appendChild(container);

    let isOpen = false;
    btn.onclick = () => {
        isOpen = !isOpen;
        container.style.display = isOpen ? 'flex' : 'none';
        btn.innerHTML = isOpen ? '✕' : '💬';
    };

    document.getElementById('custombot-close').onclick = () => {
        isOpen = false;
        container.style.display = 'none';
        btn.innerHTML = '💬';
    };

    // Load initial bot details
    const apiBase = script.src.split('/static/')[0];
    const messagesEl = document.getElementById('custombot-messages');
    const inputEl = document.getElementById('custombot-input');
    const sendBtn = document.getElementById('custombot-send');

    fetch(`${apiBase}/api/public/chatbots/${botId}`)
        .then(res => res.json())
        .then(data => {
            messagesEl.innerHTML = `
                <div style="background:#e5e7eb; padding:10px 14px; border-radius:8px; align-self:flex-start; max-width:85%;">
                    ${data.welcome_message || 'Hello! How can I help you today?'}
                </div>
            `;
        })
        .catch(() => {
            messagesEl.innerHTML = `<div style="color:red; font-size:12px;">Failed to load chatbot.</div>`;
        });

    const sendMessage = () => {
        const text = inputEl.value.trim();
        if (!text) return;
        inputEl.value = '';

        // Add user bubble
        const userMsg = document.createElement('div');
        userMsg.style.cssText = `background:${color}; color:white; padding:10px 14px; border-radius:8px; align-self:flex-end; max-width:85%;`;
        userMsg.textContent = text;
        messagesEl.appendChild(userMsg);

        // Loading bubble
        const loader = document.createElement('div');
        loader.style.cssText = `background:#e5e7eb; padding:8px 12px; border-radius:8px; align-self:flex-start; font-style:italic; font-size:12px;`;
        loader.textContent = 'Thinking...';
        messagesEl.appendChild(loader);
        messagesEl.scrollTop = messagesEl.scrollHeight;

        fetch(`${apiBase}/api/public/chatbots/${botId}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text, session_id: 'embed_' + Math.random().toString(36).substring(7) })
        })
        .then(res => res.json())
        .then(data => {
            loader.remove();
            const botMsg = document.createElement('div');
            botMsg.style.cssText = `background:#e5e7eb; padding:10px 14px; border-radius:8px; align-self:flex-start; max-width:85%; line-height:1.4;`;
            botMsg.textContent = data.answer;
            messagesEl.appendChild(botMsg);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        })
        .catch(err => {
            loader.remove();
            const errMsg = document.createElement('div');
            errMsg.style.cssText = `color:red; font-size:12px; align-self:flex-start;`;
            errMsg.textContent = 'Error getting response.';
            messagesEl.appendChild(errMsg);
        });
    };

    sendBtn.onclick = sendMessage;
    inputEl.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
})();

