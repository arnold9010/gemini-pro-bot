# site.py
import os
import json
from flask import Flask, request, jsonify, render_template_string, Response, stream_with_context
from logic import get_gemini_response_stream
from models import WORKING_MODELS

app = Flask(__name__)

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>AI Hub Advanced</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap" rel="stylesheet">
    
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

    <style>
        /* CSS Variables & Themes */
        :root, [data-theme="black"] {
            --bg-main: #131314; --bg-sidebar: #1e1f22; --bg-input: #1e1f22;
            --bg-user-msg: #303134; --bg-code: #1e1f22; --bg-modal: #282a2c;
            --text-primary: #e3e3e3; --text-secondary: #c4c7c5;
            --accent-color: #a8c7fa; --border-color: #444746; --bg-dropdown: #282a2c;
        }
        
        [data-theme="white"] {
            --bg-main: #f0f4f9; --bg-sidebar: #ffffff; --bg-input: #ffffff;
            --bg-user-msg: #e3e3e3; --bg-code: #f6f8fa; --bg-modal: #ffffff;
            --text-primary: #1f1f1f; --text-secondary: #444746;
            --accent-color: #0b57d0; --border-color: #e0e0e0; --bg-dropdown: #ffffff;
        }

        [data-theme="blue"] {
            --bg-main: #0b141a; --bg-sidebar: #111b21; --bg-input: #2a3942;
            --bg-user-msg: #005c4b; --bg-code: #111b21; --bg-modal: #233138;
            --text-primary: #e9edef; --text-secondary: #8696a0;
            --accent-color: #53bdeb; --border-color: #2a3942; --bg-dropdown: #233138;
        }

        [data-theme="red"] {
            --bg-main: #1a0b0b; --bg-sidebar: #221010; --bg-input: #2a1515;
            --bg-user-msg: #4a1515; --bg-code: #150a0a; --bg-modal: #2a1515;
            --text-primary: #f2e6e6; --text-secondary: #b39b9b;
            --accent-color: #ff6b6b; --border-color: #3d2222; --bg-dropdown: #2a1515;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Google Sans', sans-serif; }
        body { background-color: var(--bg-main); color: var(--text-primary); display: flex; height: 100vh; overflow: hidden; transition: background 0.3s, color 0.3s; }
        
        /* Sidebar & Topbar */
        .sidebar { width: 280px; background-color: var(--bg-sidebar); display: flex; flex-direction: column; padding: 16px; border-right: 1px solid var(--border-color); z-index: 10;}
        .sidebar-header { font-size: 18px; font-weight: 500; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;}
        .new-chat-btn { background: transparent; color: var(--text-primary); border: 1px solid var(--border-color); padding: 10px 15px; border-radius: 20px; cursor: pointer; display: flex; align-items: center; gap: 10px; font-size: 14px; margin-bottom: 20px; transition: background 0.2s; }
        .new-chat-btn:hover { background-color: rgba(128,128,128,0.1); }
        .history-list { flex-grow: 1; overflow-y: auto; margin-bottom: 10px; }
        .history-item { padding: 10px; border-radius: 8px; color: var(--text-secondary); font-size: 14px; cursor: pointer; margin-bottom: 5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .history-item:hover, .history-item.active { background-color: rgba(128, 128, 128, 0.15); color: var(--text-primary); }
        .main-content { flex-grow: 1; display: flex; flex-direction: column; position: relative; }
        .top-bar { height: 64px; display: flex; justify-content: space-between; align-items: center; padding: 0 24px; position: relative; z-index: 50; }
        .top-actions { display: flex; gap: 10px; }
        .icon-btn { background: transparent; border: none; color: var(--text-secondary); cursor: pointer; padding: 8px; border-radius: 50%; display: flex; align-items: center; transition: 0.2s;}
        .icon-btn:hover { background: rgba(128,128,128,0.1); color: var(--text-primary); }
        .delete-btn:hover { background: rgba(255, 107, 107, 0.1); color: #ff6b6b; }
        
        /* Custom Dropdown */
        .model-selector-container { position: relative; }
        .model-btn { background: transparent; border: none; color: var(--text-primary); font-size: 18px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; transition: background 0.2s;}
        .model-btn:hover { background: rgba(128,128,128,0.1); }
        .model-dropdown { position: absolute; top: 50px; left: 0; background: var(--bg-dropdown); border-radius: 16px; width: 340px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); border: 1px solid var(--border-color); display: none; flex-direction: column; padding: 8px; max-height: 70vh; overflow-y: auto; }
        .model-dropdown.show { display: flex; }
        .model-item { padding: 12px 16px; border-radius: 8px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; transition: background 0.1s;}
        .model-item:hover { background: rgba(128,128,128,0.1); }
        .model-item.selected { background: rgba(168, 199, 250, 0.08); border-color: rgba(168, 199, 250, 0.2); }
        .model-info { display: flex; flex-direction: column; gap: 4px; }
        .model-title { font-size: 15px; font-weight: 500; color: var(--text-primary); }
        .model-desc { font-size: 13px; color: var(--text-secondary); }
        .check-icon { color: var(--accent-color); display: none; }
        .model-item.selected .check-icon { display: block; }

        /* Chat */
        .chat-container { flex-grow: 1; overflow-y: auto; padding: 20px 15%; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth;}
        .greeting { font-size: 44px; font-weight: 500; margin-top: 10vh; margin-bottom: 40px; }
        .greeting span { background: linear-gradient(74deg, var(--accent-color), #9b72cb, #d96570); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .message { display: flex; gap: 16px; max-width: 100%; }
        .user-message { justify-content: flex-end; }
        .message-content { padding: 12px 16px; border-radius: 12px; font-size: 16px; line-height: 1.5; word-wrap: break-word; overflow-x: hidden; width: 100%; }
        .user-message .message-content { background-color: var(--bg-user-msg); border-top-right-radius: 4px; max-width: 80%; width: auto; }
        
        /* Advanced Code Blocks */
        .custom-code-block { background: #0d1117; border: 1px solid var(--border-color); border-radius: 8px; margin: 16px 0; overflow: hidden; color: #e3e3e3;}
        .code-header { background: rgba(255,255,255,0.05); padding: 8px 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; }
        .code-lang { font-size: 12px; color: #888; font-family: monospace; text-transform: uppercase; }
        .code-actions { display: flex; gap: 8px; }
        .code-btn { background: transparent; border: 1px solid #444; color: #aaa; border-radius: 4px; padding: 4px 8px; font-size: 12px; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 4px;}
        .code-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .code-btn.preview-btn { color: var(--accent-color); border-color: var(--accent-color); }
        .code-body { padding: 16px; overflow-x: auto; font-size: 14px; background: #0d1117;}
        .code-footer { background: rgba(255,255,255,0.02); padding: 8px 16px; border-top: 1px dashed #333; display: flex; justify-content: flex-end;}

        /* Input */
        .input-wrapper { padding: 0 15% 24px 15%; width: 100%; }
        .input-box { background-color: var(--bg-input); border-radius: 24px; padding: 12px 20px; display: flex; align-items: flex-end; gap: 10px; border: 1px solid transparent; transition: 0.3s;}
        .input-box:focus-within { border-color: var(--border-color); box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        textarea { flex-grow: 1; background: transparent; border: none; color: var(--text-primary); font-size: 16px; resize: none; outline: none; max-height: 200px; padding: 4px 0; }
        .send-btn { background: transparent; border: none; color: var(--text-secondary); cursor: pointer; padding: 8px; }
        .send-btn.active { color: var(--accent-color); }
        
        /* Modals */
        .overlay { display: none; position: absolute; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.7); z-index: 1000; justify-content: center; align-items: center; }
        .modal { background: var(--bg-modal); padding: 24px; border-radius: 16px; width: 400px; border: 1px solid var(--border-color); color: var(--text-primary);}
        .modal h2 { margin-bottom: 20px; font-size: 20px; }
        .setting-group { margin-bottom: 16px; display: flex; flex-direction: column; gap: 8px; }
        .setting-group label { font-size: 14px; color: var(--text-secondary); }
        .setting-group select { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border-color); padding: 8px 10px; border-radius: 8px; outline: none; }
        .setting-group input[type="range"] { width: 100%; }
        .modal-btns { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
        .btn-primary { background: var(--accent-color); color: #000; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-weight: 500; }
        .btn-secondary { background: transparent; color: var(--text-primary); border: 1px solid var(--border-color); padding: 8px 16px; border-radius: 20px; cursor: pointer; }
        
        .preview-modal { width: 90vw; height: 90vh; display: flex; flex-direction: column; padding: 0; overflow: hidden;}
        .preview-header { padding: 16px 24px; background: #1e1f22; border-bottom: 1px solid #444; display: flex; justify-content: space-between; align-items: center; color: white;}
        .preview-iframe { flex-grow: 1; border: none; width: 100%; background: #fff; }

        ::-webkit-scrollbar { width: 8px; height: 8px;}
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #888; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--accent-color); }

        /* ИСКРА / АНИМАЦИЯ ЗАГРУЗКИ */
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes pulse-glow { 
            0%, 100% { opacity: 0.6; filter: drop-shadow(0 0 2px var(--accent-color)); } 
            50% { opacity: 1; filter: drop-shadow(0 0 8px var(--accent-color)); } 
        }
    </style>
</head>
<body data-theme="black">

    <aside class="sidebar">
        <div class="sidebar-header">AI Hub</div>
        <button class="new-chat-btn" onclick="createNewChat()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"></path></svg>
            New chat
        </button>
        <div class="history-list" id="history-list"></div>
        
        <button class="new-chat-btn" onclick="clearAllChats()" style="border-color: #ff6b6b; color: #ff6b6b; justify-content: center; margin-bottom: 0;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path></svg>
            Clear All
        </button>
    </aside>

    <main class="main-content">
        <header class="top-bar">
            <div class="model-selector-container">
                <button class="model-btn" id="model-trigger" onclick="toggleDropdown(event)">
                    <span id="current-model-name">Loading...</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"></path></svg>
                </button>
                <div class="model-dropdown" id="model-dropdown"></div>
            </div>

            <div class="top-actions">
                <button class="icon-btn delete-btn" onclick="deleteCurrentChat()" title="Delete Current Chat">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path></svg>
                </button>

                <button class="icon-btn" onclick="toggleSettings(true)" title="Settings">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                </button>
            </div>
        </header>

        <div class="chat-container" id="chat-container">
            <div class="greeting" id="greeting">
                <span>Hello!</span><br>What's on your mind?
            </div>
        </div>

        <div class="input-wrapper">
            <div class="input-box">
                <textarea id="prompt" placeholder="Ask anything..." rows="1" oninput="autoResize(this)" onkeydown="handleEnter(event)"></textarea>
                <button class="send-btn" id="send-btn" onclick="send()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"></path></svg>
                </button>
            </div>
        </div>

        <div class="overlay" id="settings-modal">
            <div class="modal">
                <h2>Settings</h2>
                
                <div class="setting-group">
                    <label>Theme</label>
                    <select id="theme-select">
                        <option value="black">Dark (Default)</option>
                        <option value="white">Light</option>
                        <option value="blue">Deep Blue</option>
                        <option value="red">Crimson</option>
                    </select>
                </div>

                <div class="setting-group">
                    <label>Response Language</label>
                    <select id="lang-select">
                        <option value="English">English</option>
                        <option value="Russian" selected>Russian</option>
                        <option value="Ukrainian">Ukrainian</option>
                    </select>
                </div>
                <div class="setting-group">
                    <label>Memory Limit (Messages: <span id="mem-val">15</span>)</label>
                    <input type="range" id="memory-slider" min="1" max="300" value="15" oninput="document.getElementById('mem-val').innerText = this.value">
                </div>
                <div class="modal-btns">
                    <button class="btn-secondary" onclick="toggleSettings(false)">Cancel</button>
                    <button class="btn-primary" onclick="saveSettings()">Save</button>
                </div>
            </div>
        </div>

        <div class="overlay" id="preview-modal">
            <div class="modal preview-modal">
                <div class="preview-header">
                    <h2 style="margin:0; font-size:18px;">Live Preview</h2>
                    <button class="icon-btn" onclick="closePreview()">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"></path></svg>
                    </button>
                </div>
                <iframe id="preview-frame" class="preview-iframe"></iframe>
            </div>
        </div>
    </main>

    <script>
        let currentChatId = null;
        let chatHistoryDB = JSON.parse(localStorage.getItem('ai_chats')) || {};
        let settings = JSON.parse(localStorage.getItem('ai_settings')) || { lang: 'Russian', memory: 15, theme: 'black' };
        let activeModelId = localStorage.getItem('active_model') || '';

        // Override Marked.js renderer
        const renderer = new marked.Renderer();
        renderer.code = function(code, language) {
            const validLang = !!(language && hljs.getLanguage(language));
            const highlighted = validLang ? hljs.highlight(code, { language }).value : hljs.highlightAuto(code).value;
            const langLabel = language ? language : 'text';
            const isPreviewable = ['html', 'css', 'javascript', 'js'].includes(langLabel.toLowerCase());
            const previewBtn = isPreviewable ? `<button class="code-btn preview-btn" onclick="openPreview(this, '${langLabel}')">▶ Preview</button>` : '';
            const safeCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');

            return `
            <div class="custom-code-block">
                <div class="code-header">
                    <span class="code-lang">${langLabel}</span>
                    <div class="code-actions">
                        ${previewBtn}
                        <button class="code-btn" onclick="copyCode(this)">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy
                        </button>
                    </div>
                </div>
                <div class="code-body hljs"><pre><code data-raw="${safeCode}">${highlighted}</code></pre></div>
                <div class="code-footer">
                    <button class="code-btn" onclick="copyCode(this)">Copy code</button>
                </div>
            </div>`;
        };
        marked.setOptions({ renderer: renderer });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.model-selector-container')) {
                document.getElementById('model-dropdown').classList.remove('show');
            }
        });

        function applyTheme() { document.body.setAttribute('data-theme', settings.theme || 'black'); }

        function initApp() {
            document.getElementById('theme-select').value = settings.theme || 'black';
            document.getElementById('lang-select').value = settings.lang || 'Russian';
            document.getElementById('memory-slider').value = settings.memory || 15;
            document.getElementById('mem-val').innerText = settings.memory || 15;
            
            applyTheme();
            renderSidebar();
            
            if(Object.keys(chatHistoryDB).length > 0) {
                loadChat(Object.keys(chatHistoryDB)[Object.keys(chatHistoryDB).length - 1]);
            } else { createNewChat(); }
        }

        function toggleDropdown() { document.getElementById('model-dropdown').classList.toggle('show'); }
        function toggleSettings(show) { document.getElementById('settings-modal').style.display = show ? 'flex' : 'none'; }
        
        function selectModel(modelId, modelName) {
            activeModelId = modelId; localStorage.setItem('active_model', activeModelId);
            document.getElementById('current-model-name').innerText = modelName;
            document.getElementById('model-dropdown').classList.remove('show'); renderDropdown(window.availableModels);
        }

        function renderDropdown(models) {
            const container = document.getElementById('model-dropdown'); container.innerHTML = '';
            models.forEach(m => {
                let cleanName = m.split('/').pop().replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                let isSelected = m === activeModelId;
                if (isSelected) document.getElementById('current-model-name').innerText = cleanName;
                
                const div = document.createElement('div');
                div.className = `model-item ${isSelected ? 'selected' : ''}`;
                div.onclick = () => selectModel(m, cleanName);
                div.innerHTML = `<div class="model-info"><span class="model-title">${cleanName}</span><span class="model-desc">${m}</span></div>
                    <svg class="check-icon" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"></path></svg>`;
                container.appendChild(div);
            });
        }

        function saveSettings() {
            settings.theme = document.getElementById('theme-select').value;
            settings.lang = document.getElementById('lang-select').value;
            settings.memory = document.getElementById('memory-slider').value;
            localStorage.setItem('ai_settings', JSON.stringify(settings)); 
            applyTheme();
            toggleSettings(false);
        }

        /* CHAT MANAGEMENT FUNCTIONS */
        function createNewChat() {
            currentChatId = 'chat_' + Date.now();
            chatHistoryDB[currentChatId] = { title: "New Chat", messages: [] };
            saveDB(); renderSidebar();
            document.getElementById('chat-container').innerHTML = `<div class="greeting" id="greeting"><span>Hello!</span><br>What's on your mind?</div>`;
        }

        function deleteCurrentChat() {
            if(!currentChatId || !chatHistoryDB[currentChatId]) return;
            if(!confirm("Вы уверены, что хотите удалить этот чат?")) return;
            
            delete chatHistoryDB[currentChatId];
            saveDB();
            
            if(Object.keys(chatHistoryDB).length > 0) {
                loadChat(Object.keys(chatHistoryDB)[Object.keys(chatHistoryDB).length - 1]);
            } else {
                createNewChat();
            }
        }

        function clearAllChats() {
            if(!confirm("ВНИМАНИЕ: Это удалит всю историю чатов навсегда. Вы уверены?")) return;
            chatHistoryDB = {};
            saveDB();
            createNewChat();
        }

        function loadChat(id) {
            currentChatId = id; renderSidebar();
            const cont = document.getElementById('chat-container'); cont.innerHTML = '';
            if(chatHistoryDB[id].messages.length === 0) {
                cont.innerHTML = `<div class="greeting" id="greeting"><span>Hello!</span><br>What's on your mind?</div>`;
            } else {
                chatHistoryDB[id].messages.forEach(msg => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = `message ${msg.role === 'user' ? 'user-message' : 'ai-message'}`;
                    msgDiv.innerHTML = `<div class="message-content">${msg.role === 'user' ? msg.text.replace(/\n/g, '<br>') : marked.parse(msg.text)}</div>`;
                    cont.appendChild(msgDiv);
                });
                cont.scrollTop = cont.scrollHeight;
            }
        }

        function renderSidebar() {
            const list = document.getElementById('history-list'); list.innerHTML = '';
            Object.keys(chatHistoryDB).reverse().forEach(id => {
                const div = document.createElement('div');
                div.className = `history-item ${id === currentChatId ? 'active' : ''}`;
                div.innerText = chatHistoryDB[id].title; div.onclick = () => loadChat(id);
                list.appendChild(div);
            });
        }

        function saveDB() { localStorage.setItem('ai_chats', JSON.stringify(chatHistoryDB)); }
        function autoResize(ta) { ta.style.height = 'auto'; ta.style.height = ta.scrollHeight + 'px'; document.getElementById('send-btn').classList.toggle('active', ta.value.trim() !== ''); }
        function handleEnter(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }

        /* Actions: Copy & Preview */
        function copyCode(btn) {
            const block = btn.closest('.custom-code-block');
            const codeRaw = block.querySelector('code').getAttribute('data-raw');
            const txt = document.createElement('textarea'); txt.innerHTML = codeRaw;
            navigator.clipboard.writeText(txt.value);
            const orig = btn.innerHTML; btn.innerHTML = 'Copied!';
            setTimeout(() => btn.innerHTML = orig, 2000);
        }

        function openPreview(btn, lang) {
            const block = btn.closest('.custom-code-block');
            const codeRaw = block.querySelector('code').getAttribute('data-raw');
            const txt = document.createElement('textarea'); txt.innerHTML = codeRaw;
            let code = txt.value;
            
            let htmlContent = code;
            if(lang === 'css') htmlContent = `<style>${code}</style><h1>CSS Preview Area</h1><div class="test-div" style="padding:20px; background:#f0f0f0;">Test Element</div>`;
            if(lang === 'javascript' || lang === 'js') htmlContent = `<h1>Check console or interactions</h1><script>${code}<\/script>`;

            document.getElementById('preview-frame').srcdoc = htmlContent;
            document.getElementById('preview-modal').style.display = 'flex';
        }
        function closePreview() { 
            document.getElementById('preview-modal').style.display = 'none'; 
            document.getElementById('preview-frame').srcdoc = ''; 
        }

        async function send() {
            const inp = document.getElementById('prompt');
            const val = inp.value.trim();
            if(!val || !activeModelId) return;

            inp.value = ''; autoResize(inp);
            const g = document.getElementById('greeting'); if(g) g.style.display = 'none';
            const cont = document.getElementById('chat-container');

            // Add User Msg
            const uMsg = document.createElement('div'); uMsg.className = 'message user-message';
            uMsg.innerHTML = `<div class="message-content">${val.replace(/\n/g, '<br>')}</div>`;
            cont.appendChild(uMsg);

            if(chatHistoryDB[currentChatId].messages.length === 0) {
                chatHistoryDB[currentChatId].title = val.substring(0, 25) + "..."; renderSidebar();
            }
            chatHistoryDB[currentChatId].messages.push({role: 'user', text: val}); saveDB();

            // Создаем сообщение от ИИ с крутящейся анимацией Искры
            const aiMsg = document.createElement('div'); aiMsg.className = 'message ai-message';
            const aiContent = document.createElement('div'); aiContent.className = 'message-content';
            
            aiContent.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px; color: var(--accent-color); animation: pulse-glow 2s infinite;">
                    <svg style="animation: spin 3s linear infinite;" width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M12 0L14.59 9.41L24 12L14.59 14.59L12 24L9.41 14.59L0 12L9.41 9.41L12 0Z" fill="currentColor"/>
                    </svg>
                    <span style="font-weight: 500; font-size: 15px;">Думаю...</span>
                </div>
            `;
            
            aiMsg.appendChild(aiContent); cont.appendChild(aiMsg);
            cont.scrollTop = cont.scrollHeight;
            
            let fullAiResponse = "";

            const fd = new FormData();
            fd.append('prompt', val); fd.append('model', activeModelId);
            fd.append('chat_id', currentChatId); fd.append('memory', settings.memory); fd.append('lang', settings.lang);

            try {
                // Streaming Fetch
                const res = await fetch('/api/send_stream', { method: 'POST', body: fd });
                const reader = res.body.getReader();
                const decoder = new TextDecoder("utf-8");

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, {stream: true});
                    fullAiResponse += chunk;
                    
                    // Render markdown live (Анимация удалится при первом же тексте)
                    aiContent.innerHTML = marked.parse(fullAiResponse);
                    cont.scrollTop = cont.scrollHeight;
                }
                
                chatHistoryDB[currentChatId].messages.push({role: 'model', text: fullAiResponse}); saveDB();

            } catch(e) { 
                aiContent.innerHTML = "<span style='color:red'>Ошибка соединения.</span>"; 
            }
        }

        window.onload = async () => {
            initApp();
            try {
                // INSTANT LOAD FROM BACKEND
                const res = await fetch('/api/init'); const data = await res.json();
                window.availableModels = data.models;
                if(!activeModelId && window.availableModels.length > 0) activeModelId = window.availableModels[0];
                renderDropdown(window.availableModels);
            } catch(e) { document.getElementById('current-model-name').innerText = "Load failed"; }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/init')
def init():
    # THIS INSTANTLY RETURNS YOUR MODELS. IF IT'S SLOW, HARD REFRESH BROWSER CACHE.
    return jsonify({"models": WORKING_MODELS})

@app.route('/api/send_stream', methods=['POST'])
def send_stream():
    p = request.form.get('prompt')
    m = request.form.get('model')
    chat_id = request.form.get('chat_id') or 'default'
    mem = request.form.get('memory') or 15
    lang = request.form.get('lang') or 'Russian'
    
    def generate():
        for chunk_text in get_gemini_response_stream(m, p, chat_id=chat_id, memory_size=mem, language=lang):
            yield chunk_text

    return Response(stream_with_context(generate()), mimetype='text/plain')

if __name__ == '__main__':
    print("[*] Starting UI...")
    # Берем порт от хостинга, а если запускаем на компе - используем 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)