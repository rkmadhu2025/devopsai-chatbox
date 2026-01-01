"""
LinkedEye-FinSpot Style Dashboard UI for DevOps GenAI Chatbot
Professional enterprise design with AI assistant panel
"""

def get_dashboard_html() -> str:
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevOps AI Assistant | LinkedEye-FinSpot</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --primary-navy: #0f1c3f;
            --primary-blue: #2563eb;
            --primary-blue-light: #3b82f6;
            --sidebar-width: 260px;
            --header-height: 56px;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --purple: #8b5cf6;
            --pink: #ec4899;
            --bg-body: #f4f6f9;
            --bg-card: #ffffff;
            --text-primary: #0f1c3f;
            --text-secondary: #6b7785;
            --border-color: #e5e8eb;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg-body); color: var(--text-primary); font-size: 13px; }

        /* Sidebar */
        .sidebar { position: fixed; top: 0; left: 0; width: var(--sidebar-width); height: 100vh; background: var(--primary-navy); z-index: 200; }
        .sidebar-header { padding: 16px 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .sidebar-logo { width: 40px; height: 40px; background: linear-gradient(135deg, var(--primary-blue-light), var(--purple)); border-radius: 10px; display: flex; align-items: center; justify-content: center; }
        .sidebar-logo i { color: #fff; font-size: 20px; }
        .sidebar-brand { color: #fff; }
        .sidebar-brand h1 { font-size: 16px; font-weight: 700; }
        .sidebar-brand span { font-size: 10px; color: rgba(255,255,255,0.6); }
        .sidebar-nav { padding: 16px 12px; overflow-y: auto; height: calc(100vh - 140px); }
        .nav-section { margin-bottom: 20px; }
        .nav-section-title { font-size: 10px; font-weight: 700; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 1px; padding: 0 12px 8px; }
        .nav-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; color: rgba(255,255,255,0.7); text-decoration: none; border-radius: 8px; transition: all 0.2s; margin-bottom: 2px; cursor: pointer; }
        .nav-item:hover { background: rgba(255,255,255,0.08); color: #fff; }
        .nav-item.active { background: linear-gradient(135deg, var(--primary-blue), #1d4ed8); color: #fff; }
        .nav-item i { width: 20px; text-align: center; }
        .nav-item .nav-badge { background: var(--success); color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 10px; margin-left: auto; }
        .sidebar-footer { position: absolute; bottom: 0; left: 0; right: 0; padding: 16px; border-top: 1px solid rgba(255,255,255,0.1); }
        .env-selector { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 10px 12px; display: flex; align-items: center; gap: 10px; color: #fff; font-size: 12px; }
        .env-dot { width: 10px; height: 10px; background: var(--success); border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        /* Header */
        .header { position: fixed; top: 0; left: var(--sidebar-width); right: 0; height: var(--header-height); background: var(--bg-card); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; z-index: 100; }
        .header-left { display: flex; align-items: center; gap: 16px; }
        .header-title h1 { font-size: 16px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
        .header-title h1 i { color: var(--purple); }
        .header-right { display: flex; align-items: center; gap: 8px; }
        .header-btn { padding: 8px 16px; border: 1px solid var(--border-color); background: #fff; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 500; display: flex; align-items: center; gap: 6px; transition: all 0.2s; }
        .header-btn:hover { background: #f9fafb; border-color: var(--primary-blue); color: var(--primary-blue); }
        .header-btn.primary { background: linear-gradient(135deg, var(--primary-blue), #1d4ed8); color: #fff; border: none; }
        .header-btn.danger { background: var(--danger); color: #fff; border: none; }
        .user-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, var(--primary-blue), var(--purple)); display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 600; font-size: 12px; }

        /* Main Content */
        .main-content { margin-left: var(--sidebar-width); margin-top: var(--header-height); padding: 24px; min-height: calc(100vh - var(--header-height)); }

        /* Grid Layout */
        .detail-grid { display: grid; grid-template-columns: 1fr 400px; gap: 24px; }

        /* Card */
        .card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 24px; }
        .card-header { padding: 16px 20px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
        .card-title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 10px; }
        .card-title i { color: var(--primary-blue); }
        .card-body { padding: 20px; }

        /* AI Panel - Main Chat Area */
        .ai-panel { background: linear-gradient(135deg, #0f1c3f 0%, #1e3a5f 100%); border-radius: 12px; padding: 20px; color: #fff; margin-bottom: 24px; }
        .ai-panel-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .ai-icon { width: 48px; height: 48px; background: linear-gradient(135deg, var(--purple), var(--pink)); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
        .ai-panel-header h3 { font-size: 16px; font-weight: 600; }
        .ai-panel-header p { font-size: 11px; opacity: 0.7; }

        /* Chat Messages */
        .chat-messages { max-height: 500px; overflow-y: auto; margin-bottom: 16px; padding-right: 8px; }
        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 3px; }
        .message { display: flex; gap: 12px; margin-bottom: 16px; }
        .message.user { flex-direction: row-reverse; }
        .message-avatar { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
        .message.user .message-avatar { background: linear-gradient(135deg, var(--primary-blue), var(--purple)); }
        .message.assistant .message-avatar { background: linear-gradient(135deg, var(--purple), var(--pink)); }
        .message-content { background: rgba(255,255,255,0.1); padding: 14px 16px; border-radius: 12px; max-width: 85%; font-size: 13px; line-height: 1.6; }
        .message.user .message-content { background: rgba(59, 130, 246, 0.3); }
        .message-content pre { background: rgba(0,0,0,0.3); padding: 12px; border-radius: 8px; overflow-x: auto; margin: 10px 0; }
        .message-content code { font-family: 'Consolas', monospace; font-size: 12px; }
        .message-content code:not(pre code) { background: rgba(139, 92, 246, 0.3); padding: 2px 6px; border-radius: 4px; }
        .message-meta { font-size: 10px; opacity: 0.6; margin-top: 6px; }

        /* Chat Input */
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input { flex: 1; padding: 14px 16px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: #fff; font-size: 13px; outline: none; resize: none; font-family: inherit; }
        .chat-input::placeholder { color: rgba(255,255,255,0.5); }
        .chat-input:focus { border-color: var(--purple); background: rgba(255,255,255,0.15); }
        .send-btn { width: 48px; height: 48px; border-radius: 10px; background: linear-gradient(135deg, var(--purple), var(--pink)); border: none; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.2s; }
        .send-btn:hover { transform: scale(1.05); box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); }

        /* Quick Actions */
        .quick-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
        .quick-action { padding: 8px 14px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; font-size: 11px; color: #fff; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
        .quick-action:hover { background: rgba(255,255,255,0.2); border-color: var(--purple); }
        .quick-action i { font-size: 12px; }

        /* Typing Indicator */
        .typing-indicator { display: flex; gap: 4px; padding: 14px 16px; }
        .typing-indicator span { width: 8px; height: 8px; background: var(--purple); border-radius: 50%; animation: bounce 1.4s infinite; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-8px); } }

        /* Stats Cards */
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px; display: flex; align-items: center; gap: 14px; }
        .stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .stat-icon.agents { background: linear-gradient(135deg, var(--purple), var(--pink)); color: #fff; }
        .stat-icon.queries { background: linear-gradient(135deg, var(--primary-blue), #1d4ed8); color: #fff; }
        .stat-icon.tools { background: linear-gradient(135deg, var(--success), #059669); color: #fff; }
        .stat-icon.uptime { background: linear-gradient(135deg, var(--warning), #d97706); color: #fff; }
        .stat-info h3 { font-size: 20px; font-weight: 700; }
        .stat-info p { font-size: 11px; color: var(--text-secondary); }

        /* Agent List */
        .agent-list { display: flex; flex-direction: column; gap: 8px; max-height: 400px; overflow-y: auto; }
        .agent-item { padding: 12px 14px; background: #f9fafb; border-radius: 8px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 12px; }
        .agent-item:hover { background: #f3f4f6; border-left: 3px solid var(--primary-blue); }
        .agent-item.active { background: rgba(37, 99, 235, 0.1); border-left: 3px solid var(--primary-blue); }
        .agent-item-icon { width: 36px; height: 36px; border-radius: 8px; background: linear-gradient(135deg, var(--primary-navy), #1e3a5f); display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .agent-item-info { flex: 1; }
        .agent-item-name { font-weight: 600; font-size: 13px; margin-bottom: 2px; }
        .agent-item-status { font-size: 10px; color: var(--success); display: flex; align-items: center; gap: 4px; }
        .agent-item-status::before { content: ''; width: 6px; height: 6px; background: var(--success); border-radius: 50%; }

        /* Recent Activity */
        .activity-item { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border-color); }
        .activity-item:last-child { border-bottom: none; }
        .activity-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
        .activity-icon.query { background: rgba(59, 130, 246, 0.1); color: var(--info); }
        .activity-icon.success { background: rgba(16, 185, 129, 0.1); color: var(--success); }
        .activity-content { flex: 1; }
        .activity-title { font-size: 12px; font-weight: 500; margin-bottom: 2px; }
        .activity-time { font-size: 10px; color: var(--text-secondary); }

        /* Responsive */
        @media (max-width: 1400px) { .detail-grid { grid-template-columns: 1fr 360px; } .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 1200px) { .detail-grid { grid-template-columns: 1fr; } }
        @media (max-width: 992px) { .sidebar { width: 60px; } .sidebar-brand, .nav-item span, .nav-badge, .nav-section-title { display: none; } .header { left: 60px; } .main-content { margin-left: 60px; } }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <aside class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo"><i class="fas fa-eye"></i></div>
            <div class="sidebar-brand"><h1>LinkedEye</h1><span>FinSpot Enterprise</span></div>
        </div>
        <nav class="sidebar-nav">
            <div class="nav-section">
                <div class="nav-section-title">Main</div>
                <a href="#" class="nav-item active"><i class="fas fa-robot"></i><span>AI Assistant</span></a>
                <a href="#" class="nav-item"><i class="fas fa-chart-line"></i><span>Dashboard</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">DevOps</div>
                <a href="#" class="nav-item" onclick="askAgent('kubernetes')"><i class="fas fa-dharmachakra"></i><span>Kubernetes</span><span class="nav-badge">42</span></a>
                <a href="#" class="nav-item" onclick="askAgent('docker')"><i class="fab fa-docker"></i><span>Docker</span></a>
                <a href="#" class="nav-item" onclick="askAgent('jenkins')"><i class="fas fa-cogs"></i><span>CI/CD</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Cloud</div>
                <a href="#" class="nav-item" onclick="askAgent('aws')"><i class="fab fa-aws"></i><span>AWS</span></a>
                <a href="#" class="nav-item" onclick="askAgent('azure')"><i class="fab fa-microsoft"></i><span>Azure</span></a>
                <a href="#" class="nav-item" onclick="askAgent('terraform')"><i class="fas fa-cloud"></i><span>Terraform</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Monitoring</div>
                <a href="#" class="nav-item" onclick="askAgent('prometheus')"><i class="fas fa-chart-area"></i><span>Prometheus</span></a>
                <a href="#" class="nav-item" onclick="askAgent('grafana')"><i class="fas fa-chart-bar"></i><span>Grafana</span></a>
            </div>
            <div class="nav-section">
                <div class="nav-section-title">Infrastructure</div>
                <a href="#" class="nav-item" onclick="askAgent('vmware')"><i class="fas fa-server"></i><span>VMware</span></a>
                <a href="#" class="nav-item" onclick="askAgent('networking')"><i class="fas fa-network-wired"></i><span>Networking</span></a>
            </div>
        </nav>
        <div class="sidebar-footer">
            <div class="env-selector"><div class="env-dot"></div><span>Claude Opus 4.5</span></div>
        </div>
    </aside>

    <!-- Header -->
    <header class="header">
        <div class="header-left">
            <div class="header-title">
                <h1><i class="fas fa-robot"></i> DevOps AI Assistant</h1>
            </div>
        </div>
        <div class="header-right">
            <button class="header-btn" onclick="clearChat()"><i class="fas fa-trash"></i> Clear</button>
            <button class="header-btn"><i class="fas fa-download"></i> Export</button>
            <button class="header-btn primary"><i class="fas fa-cog"></i> Settings</button>
            <div class="user-avatar">RM</div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon agents"><i class="fas fa-robot"></i></div>
                <div class="stat-info"><h3>42+</h3><p>AI Agents</p></div>
            </div>
            <div class="stat-card">
                <div class="stat-icon queries"><i class="fas fa-comments"></i></div>
                <div class="stat-info"><h3 id="queryCount">0</h3><p>Queries Today</p></div>
            </div>
            <div class="stat-card">
                <div class="stat-icon tools"><i class="fas fa-tools"></i></div>
                <div class="stat-info"><h3>100+</h3><p>Tools Supported</p></div>
            </div>
            <div class="stat-card">
                <div class="stat-icon uptime"><i class="fas fa-clock"></i></div>
                <div class="stat-info"><h3>24/7</h3><p>Available</p></div>
            </div>
        </div>

        <div class="detail-grid">
            <!-- Left Column - AI Chat Panel -->
            <div class="left-column">
                <div class="ai-panel">
                    <div class="ai-panel-header">
                        <div class="ai-icon"><i class="fas fa-robot"></i></div>
                        <div>
                            <h3>AI DevOps Assistant</h3>
                            <p>Powered by Claude Opus 4.5 - 42+ specialized agents</p>
                        </div>
                    </div>

                    <div class="chat-messages" id="chatMessages">
                        <div class="message assistant">
                            <div class="message-avatar">🤖</div>
                            <div class="message-content">
                                <strong>Welcome to LinkedEye DevOps AI Assistant!</strong><br><br>
                                I'm here to help you with:
                                <ul style="margin: 10px 0 0 20px;">
                                    <li>Kubernetes deployments & troubleshooting</li>
                                    <li>Docker containerization</li>
                                    <li>AWS/Azure cloud infrastructure</li>
                                    <li>CI/CD pipelines (Jenkins, ArgoCD)</li>
                                    <li>Monitoring (Prometheus, Grafana)</li>
                                    <li>VMware & networking</li>
                                </ul>
                                <div class="message-meta">Just now</div>
                            </div>
                        </div>
                    </div>

                    <div class="chat-input-area">
                        <textarea class="chat-input" id="chatInput" placeholder="Ask about DevOps, Kubernetes, Docker, AWS, CI/CD..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
                        <button class="send-btn" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button>
                    </div>

                    <div class="quick-actions">
                        <span class="quick-action" onclick="sendQuickQuery('Create a Kubernetes deployment with HPA')"><i class="fas fa-dharmachakra"></i> K8s Deploy</span>
                        <span class="quick-action" onclick="sendQuickQuery('Write a multi-stage Dockerfile')"><i class="fab fa-docker"></i> Dockerfile</span>
                        <span class="quick-action" onclick="sendQuickQuery('Create Terraform AWS module')"><i class="fas fa-cloud"></i> Terraform</span>
                        <span class="quick-action" onclick="sendQuickQuery('Write PromQL query for high CPU')"><i class="fas fa-chart-line"></i> PromQL</span>
                        <span class="quick-action" onclick="sendQuickQuery('Create Jenkins CI/CD pipeline')"><i class="fas fa-cogs"></i> Jenkins</span>
                    </div>
                </div>
            </div>

            <!-- Right Column -->
            <div class="right-column">
                <!-- Available Agents -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-robot"></i> Available Agents</span>
                    </div>
                    <div class="card-body">
                        <div class="agent-list" id="agentList">
                            <div class="agent-item" onclick="selectAgent('kubernetes')">
                                <div class="agent-item-icon">☸️</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Kubernetes</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('docker')">
                                <div class="agent-item-icon">🐳</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Docker</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('prometheus')">
                                <div class="agent-item-icon">📊</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Prometheus</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('aws')">
                                <div class="agent-item-icon">☁️</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">AWS Cloud</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('terraform')">
                                <div class="agent-item-icon">🔧</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Terraform</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('jenkins')">
                                <div class="agent-item-icon">⚙️</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Jenkins CI/CD</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('grafana')">
                                <div class="agent-item-icon">📈</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">Grafana</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                            <div class="agent-item" onclick="selectAgent('vmware')">
                                <div class="agent-item-icon">🖥️</div>
                                <div class="agent-item-info">
                                    <div class="agent-item-name">VMware</div>
                                    <div class="agent-item-status">Ready</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="card">
                    <div class="card-header">
                        <span class="card-title"><i class="fas fa-history"></i> Recent Activity</span>
                    </div>
                    <div class="card-body" id="recentActivity">
                        <div class="activity-item">
                            <div class="activity-icon success"><i class="fas fa-check"></i></div>
                            <div class="activity-content">
                                <div class="activity-title">System initialized</div>
                                <div class="activity-time">Just now</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        let sessionId = 'session_' + Date.now();
        let isLoading = false;
        let queryCount = 0;

        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message || isLoading) return;

            addMessage(message, 'user');
            input.value = '';
            isLoading = true;
            showTyping();
            queryCount++;
            document.getElementById('queryCount').textContent = queryCount;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, session_id: sessionId })
                });
                const data = await response.json();
                hideTyping();
                addMessage(data.response, 'assistant', data.agent_icon, data.agent_name);
                addActivity(data.agent_name + ' responded', 'success');
            } catch (error) {
                hideTyping();
                addMessage('Error: ' + error.message, 'assistant', '❌', 'Error');
            }
            isLoading = false;
        }

        function addMessage(content, role, icon = '👤', agentName = 'You') {
            const container = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            const parsedContent = role === 'assistant' ? marked.parse(content) : content;
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            messageDiv.innerHTML = `
                <div class="message-avatar">${role === 'user' ? '👤' : icon || '🤖'}</div>
                <div class="message-content">
                    ${parsedContent}
                    <div class="message-meta">${agentName} • ${time}</div>
                </div>
            `;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
            messageDiv.querySelectorAll('pre code').forEach(block => hljs.highlightBlock(block));
        }

        function showTyping() {
            const container = document.getElementById('chatMessages');
            const typingDiv = document.createElement('div');
            typingDiv.id = 'typing';
            typingDiv.className = 'message assistant';
            typingDiv.innerHTML = `<div class="message-avatar">💭</div><div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
            container.appendChild(typingDiv);
            container.scrollTop = container.scrollHeight;
        }

        function hideTyping() {
            const typing = document.getElementById('typing');
            if (typing) typing.remove();
        }

        function sendQuickQuery(query) {
            document.getElementById('chatInput').value = query;
            sendMessage();
        }

        function selectAgent(agent) {
            document.querySelectorAll('.agent-item').forEach(el => el.classList.remove('active'));
            event.currentTarget.classList.add('active');
            const queries = {
                'kubernetes': 'Help me with Kubernetes best practices',
                'docker': 'Create a Docker container setup',
                'prometheus': 'Write a PromQL query',
                'aws': 'Explain AWS architecture',
                'terraform': 'Create Terraform infrastructure',
                'jenkins': 'Setup Jenkins pipeline',
                'grafana': 'Configure Grafana dashboard',
                'vmware': 'VMware vSphere administration'
            };
            sendQuickQuery(queries[agent] || `Help me with ${agent}`);
        }

        function askAgent(agent) {
            selectAgent(agent);
        }

        function addActivity(title, type) {
            const container = document.getElementById('recentActivity');
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const activityDiv = document.createElement('div');
            activityDiv.className = 'activity-item';
            activityDiv.innerHTML = `
                <div class="activity-icon ${type}"><i class="fas fa-${type === 'success' ? 'check' : 'comment'}"></i></div>
                <div class="activity-content">
                    <div class="activity-title">${title}</div>
                    <div class="activity-time">${time}</div>
                </div>
            `;
            container.insertBefore(activityDiv, container.firstChild);
            if (container.children.length > 5) {
                container.removeChild(container.lastChild);
            }
        }

        async function clearChat() {
            try {
                await fetch(`/api/conversation/${sessionId}`, { method: 'DELETE' });
                sessionId = 'session_' + Date.now();
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message assistant">
                        <div class="message-avatar">🤖</div>
                        <div class="message-content">
                            Chat cleared. How can I help you today?
                            <div class="message-meta">Just now</div>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to clear chat:', error);
            }
        }

        // Auto-resize textarea
        document.getElementById('chatInput').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
    </script>
</body>
</html>'''
