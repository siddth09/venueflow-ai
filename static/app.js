document.addEventListener('DOMContentLoaded', () => {
    
    const ui = {
        chatInput: document.getElementById('chat-input'),
        sendBtn: document.getElementById('send-btn'),
        chatWindow: document.getElementById('chat-window'),
        recsContainer: document.getElementById('recs-container'),
        heatmapList: document.getElementById('heatmap-list')
    };

    // Load Initial Data
    fetchRecommendations();
    fetchHeatmap();

    // Set polling for realtime dynamic feel
    setInterval(fetchHeatmap, 15000);

    // Event Listeners
    ui.sendBtn.addEventListener('click', sendMessage);
    ui.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function sendMessage() {
        const text = ui.chatInput.value.trim();
        if (!text) return;

        appendMessage(text, 'sent');
        ui.chatInput.value = '';

        // Show typing indicator
        const typingId = showTypingIndicator();

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator(typingId);
            const formattedResponse = formatBotResponse(data);
            appendMessage(formattedResponse, 'received', true);
            ui.chatWindow.scrollTo({top: ui.chatWindow.scrollHeight, behavior: 'smooth'});
        })
        .catch(err => {
            console.error('Error:', err);
            removeTypingIndicator(typingId);
            appendMessage("⚠️ Error reaching the assistant backend.", 'received');
        });
    }

    function appendMessage(content, type, isHtml=false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content;
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-timestamp';
        timeDiv.textContent = timestamp;

        msgDiv.appendChild(contentDiv);
        msgDiv.appendChild(timeDiv);

        ui.chatWindow.appendChild(msgDiv);
        ui.chatWindow.scrollTo({top: ui.chatWindow.scrollHeight, behavior: 'smooth'});
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `message received`;
        msgDiv.id = id;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<i>Processing request...</i>';
        
        msgDiv.appendChild(contentDiv);
        ui.chatWindow.appendChild(msgDiv);
        ui.chatWindow.scrollTo({top: ui.chatWindow.scrollHeight, behavior: 'smooth'});
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    // Advanced Formatting for specific Intents
    function formatBotResponse(data) {
        if (!data) return "Empty response.";
        
        if (data.query_type === 'navigation') {
            let html = `<strong>📍 Navigation Route Calculation:</strong><br><br>`;
            data.route.route_steps.forEach((step, idx) => {
                html += `• ${step}<br>`;
            });
            html += `<br><span style="color:var(--primary-color)">Ext. Arrival Time: ${data.estimated_arrival}</span>`;
            return html;
        }
        
        if (data.query_type === 'facility_info') {
            let html = `<strong>The nearest ${data.facility}s:</strong><br><br>`;
            data.nearest_locations.forEach(loc => {
                html += `• ${loc.location} (Wait: ${loc.wait_time} mins, Accessible: ${loc.accessible ? 'Yes':'No'})<br>`;
            });
            html += `<br>Current crowd level: <span style="text-transform:capitalize;">${data.current_status.crowd_level}</span>`;
            if (data.prediction) {
                 html += `<br><br>💡 Prediction: ${data.prediction.recommendation}`;
            }
            return html;
        }

        if (data.query_type === 'wait_times') {
            let html = `<strong>Predicted Wait Times:</strong><br><br>`;
            for (const [area, info] of Object.entries(data.predictions)) {
                html += `• ${area.charAt(0).toUpperCase() + area.slice(1)}: ${info.predicted_wait_minutes} min (Cur: ${info.current_wait_minutes} min)<br>`;
            }
            html += `<br><em>Best Option: ${data.best_option}</em>`;
            return html;
        }

        if (data.immediate_actions) {
            let html = `<strong>💡 Smart Recommendations:</strong><br><br>`;
            data.immediate_actions.forEach(action => {
                html += `• ${action.action} <span style="color:var(--text-secondary)">(${action.reason || action.details})</span><br>`;
            });
            return html;
        }

        // Fallback generic format
        return `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }

    function fetchRecommendations() {
        fetch('/api/recommendations')
        .then(res => res.json())
        .then(data => {
            ui.recsContainer.innerHTML = '<h3>Smart Recommendations</h3>';
            if(data.immediate_actions && data.immediate_actions.length > 0) {
                data.immediate_actions.forEach(act => {
                    const colorMap = {"high": "var(--danger-color)", "medium": "var(--warning-color)", "low": "var(--success-color)"};
                    const color = colorMap[act.priority] || "var(--primary-color)";
                    
                    const el = document.createElement('div');
                    el.className = 'rec-card';
                    el.style.borderLeftColor = color;
                    el.innerHTML = `
                        <span class="rec-title">${act.action}</span>
                        <span class="rec-reason">${act.reason || act.details || ''}</span>
                    `;
                    ui.recsContainer.appendChild(el);
                });
            } else {
                ui.recsContainer.innerHTML += '<p style="color:var(--text-secondary); font-size:0.8rem;">No immediate actions needed.</p>';
            }
        }).catch(err => console.error("Recommendations error:", err));
    }

    function fetchHeatmap() {
        fetch('/api/heatmap')
        .then(res => res.json())
        .then(data => {
            ui.heatmapList.innerHTML = '';
            
            // Sort by crowd level severity for nice presentation
            const severityLevel = {"critical": 4, "high": 3, "moderate": 2, "low": 1};
            const sortedAreas = data.areas.sort((a,b) => severityLevel[b.crowd_level] - severityLevel[a.crowd_level]);

            sortedAreas.forEach(area => {
                const el = document.createElement('div');
                el.className = 'heatmap-card';
                
                el.innerHTML = `
                    <div class="heatmap-info">
                        <span class="heatmap-area">${area.area.replace('_', ' ')}</span>
                        <span class="heatmap-wait">Wait: ${area.wait_time} min</span>
                    </div>
                    <div class="heatmap-indicator" style="background-color: ${area.color_code}40; color: ${area.color_code}; border: 1px solid ${area.color_code}">
                        ${area.crowd_level}
                    </div>
                `;
                ui.heatmapList.appendChild(el);
            });
        }).catch(err => console.error("Heatmap error:", err));
    }

});
