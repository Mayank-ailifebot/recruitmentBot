/* ===== RecruitAI — Frontend Logic ===== */

// ──────────────────────────────────────
// NAVIGATION
// ──────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const sectionId = item.dataset.section;
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById('section-' + sectionId).classList.add('active');
    });
});

// ──────────────────────────────────────
// HELPER: API call wrapper
// ──────────────────────────────────────
async function apiCall(endpoint, body) {
    const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Server error' }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

function setLoading(btn, loading) {
    const text = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (text) text.style.display = loading ? 'none' : '';
    if (loader) loader.style.display = loading ? 'inline-block' : 'none';
    btn.disabled = loading;
}

// ──────────────────────────────────────
// SECTION 1: JD GENERATOR
// ──────────────────────────────────────
async function generateJD() {
    const btn = document.getElementById('btn-generate-jd');
    const output = document.getElementById('jd-output');
    setLoading(btn, true);
    output.innerHTML = '<div class="placeholder-text">Generating your inclusive job description...</div>';

    try {
        const data = await apiCall('/api/generate-jd', {
            role_title: document.getElementById('jd-role').value,
            department: document.getElementById('jd-dept').value,
            location: document.getElementById('jd-location').value,
            key_requirements: document.getElementById('jd-requirements').value
        });
        // Simple markdown-to-HTML (handles headers, bold, bullets)
        output.innerHTML = renderMarkdown(data.jd);
        document.getElementById('posting-channels').style.display = 'block';
    } catch (e) {
        output.innerHTML = `<div class="placeholder-text" style="color:var(--accent-coral)">Error: ${e.message}</div>`;
    } finally {
        setLoading(btn, false);
    }
}

function renderMarkdown(md) {
    return md
        .replace(/^### (.+)$/gm, '<h4>$1</h4>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        .replace(/^# (.+)$/gm, '<h2>$1</h2>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/^\- (.+)$/gm, '• $1<br>')
        .replace(/\n/g, '<br>');
}

function simulatePosting() {
    const channels = ['naukri', 'linkedin', 'indeed'];
    channels.forEach((ch, i) => {
        setTimeout(() => {
            const status = document.getElementById('status-' + ch);
            const card = document.getElementById('ch-' + ch);
            status.textContent = '✓ Posted';
            status.classList.add('done');
            card.classList.add('posted');
        }, (i + 1) * 800);
    });
}

// ──────────────────────────────────────
// SECTION 2: SOURCING AGENT
// ──────────────────────────────────────
const MOCK_CANDIDATES = [
    { name: "Priya Sharma", initials: "PS", role: "Regional Sales Head, PharmaCorp India", match: 94, tags: ["Pharma Sales 6yr", "MBA-IIM Indore", "Team of 12", "IRDA Cert"], signal: "🔔 3yr Work Anniversary — likely open to new roles" },
    { name: "Rahul Mehta", initials: "RM", role: "Sr. Relationship Manager, HDFC Life", match: 89, tags: ["Insurance 5yr", "BBA", "₹14L Premium/yr", "Client Retention 88%"], signal: "🔔 Manager recently promoted — may feel stagnated" },
    { name: "Ananya Krishnan", initials: "AK", role: "Guest Relations Director, Taj Hotels", match: 86, tags: ["Hospitality 7yr", "MBA-Symbiosis", "Upselling Expert", "Client-Facing"], signal: "🔔 Skill adjacency match: Hospitality → Insurance" },
    { name: "Vikram Patel", initials: "VP", role: "Business Development Lead, Bajaj Allianz", match: 82, tags: ["Insurance 4yr", "BSc", "Agency Builder", "Hindi+Gujarati"], signal: "🔔 Company restructuring announced last month" },
    { name: "Neha Gupta", initials: "NG", role: "Branch Manager, Kotak Mahindra Bank", match: 78, tags: ["Retail Banking 6yr", "MBA", "Team of 8", "Cross-sell Expert"], signal: "🔔 Skill adjacency match: Banking → Insurance" },
];

function renderCandidates() {
    const grid = document.getElementById('candidates-grid');
    grid.innerHTML = MOCK_CANDIDATES.map((c, i) => `
        <div class="candidate-card glass-card" style="animation-delay:${i * 0.1}s">
            <div class="match-bar" style="width:${c.match}%"></div>
            <div class="cand-header">
                <div class="cand-avatar">${c.initials}</div>
                <div>
                    <div class="cand-name">${c.name}</div>
                    <div class="cand-role">${c.role}</div>
                </div>
                <div class="cand-match">${c.match}%</div>
            </div>
            <div class="cand-details">
                ${c.tags.map(t => `<span class="cand-tag">${t}</span>`).join('')}
            </div>
            <div class="cand-signals">${c.signal}</div>
            <button class="btn-outreach" onclick="openOutreach(${i})">✉️ Generate Outreach</button>
        </div>
    `).join('');
}

async function openOutreach(idx) {
    const c = MOCK_CANDIDATES[idx];
    const modal = document.getElementById('outreach-modal');
    const body = document.getElementById('outreach-body');
    modal.style.display = 'flex';
    body.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    try {
        const data = await apiCall('/api/sourcing/outreach', {
            candidate_name: c.name,
            candidate_background: c.role + '. ' + c.tags.join(', '),
            target_role: 'Senior Life Insurance Sales Agent at AILifeBot'
        });
        body.innerHTML = `
            <p><strong>To:</strong> ${c.name}</p>
            <p><strong>Subject:</strong> A quick note about an exciting opportunity</p>
            <div class="outreach-text">${data.outreach}</div>
            <p style="margin-top:1rem;font-size:.75rem;color:var(--text-secondary)">Interest Score: Pending first interaction</p>
        `;
    } catch (e) {
        body.innerHTML = `<p style="color:var(--accent-coral)">Error: ${e.message}</p>`;
    }
}

function closeOutreachModal() {
    document.getElementById('outreach-modal').style.display = 'none';
}

// ──────────────────────────────────────
// SECTION 3: SCREENING
// ──────────────────────────────────────
const SAMPLE_RESUME = `ANKIT VERMA
Mumbai, Maharashtra | ankit.verma@email.com | +91-98765-43210

PROFESSIONAL SUMMARY
Results-driven sales professional with 5+ years in financial services. Proven track record of exceeding targets by 120% consistently. Skilled in consultative selling, relationship management, and team leadership.

EXPERIENCE
Senior Sales Executive — Max Life Insurance (2022 – Present)
• Managed a portfolio of 200+ HNI clients with 94% retention rate
• Led a team of 6 junior agents, achieving ₹12Cr annual premium collection
• Recognized as "Top Performer Q3 2025" for highest policy conversion rate

Sales Associate — HDFC Bank (2019 – 2022)
• Cross-sold insurance and investment products achieving 130% of quarterly targets
• Built client relationships through needs-based financial planning

Sales Intern — Cipla Pharmaceuticals (2018 – 2019)
• Promoted OTC products across 50+ retail pharmacy outlets in Western Maharashtra

EDUCATION
MBA (Marketing) — Symbiosis International University, Pune (2019)
B.Com — Mumbai University (2017)

CERTIFICATIONS
• IRDA Life Insurance License (Active)
• NISM Mutual Fund Distributor Certification

SKILLS
Consultative Selling, Financial Planning, CRM (Salesforce), Team Leadership, Hindi, English, Marathi`;

function loadSampleResume() {
    document.getElementById('resume-text').value = SAMPLE_RESUME;
}

async function screenResume() {
    const btn = document.querySelector('#section-screening .btn-primary');
    const resultsCard = document.getElementById('screening-results');
    const content = document.getElementById('screening-content');
    const resumeText = document.getElementById('resume-text').value.trim();

    if (!resumeText) { alert('Please paste a resume or load a sample.'); return; }

    setLoading(btn, true);
    resultsCard.style.display = 'block';
    content.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    try {
        const data = await apiCall('/api/screen-resume', { resume_text: resumeText });
        const blind = document.getElementById('dei-toggle').checked;
        const name = blind ? '██████████' : (data.candidate_name || 'Unknown');

        content.innerHTML = `
            <div class="overall-score">
                <div class="overall-value">${data.fit_score?.overall || '—'}</div>
                <div class="overall-label">Overall Fit Score</div>
            </div>
            <div class="score-gauges">
                <div class="gauge">
                    <div class="gauge-circle" style="background:conic-gradient(var(--accent-1) ${(data.fit_score?.hard_skills || 0) * 3.6}deg, rgba(255,255,255,0.05) 0)">
                        <span class="gauge-value">${data.fit_score?.hard_skills || 0}</span>
                    </div>
                    <div class="gauge-label">Hard Skills (30%)</div>
                </div>
                <div class="gauge">
                    <div class="gauge-circle" style="background:conic-gradient(var(--accent-2) ${(data.fit_score?.experience_quality || 0) * 3.6}deg, rgba(255,255,255,0.05) 0)">
                        <span class="gauge-value">${data.fit_score?.experience_quality || 0}</span>
                    </div>
                    <div class="gauge-label">Experience Quality (40%)</div>
                </div>
                <div class="gauge">
                    <div class="gauge-circle" style="background:conic-gradient(var(--accent-cyan) ${(data.fit_score?.behavioral_intent || 0) * 3.6}deg, rgba(255,255,255,0.05) 0)">
                        <span class="gauge-value">${data.fit_score?.behavioral_intent || 0}</span>
                    </div>
                    <div class="gauge-label">Behavioral Intent (30%)</div>
                </div>
            </div>
            <div class="profile-field"><div class="profile-field-label">Name</div><div class="profile-field-value">${name}</div></div>
            <div class="profile-field"><div class="profile-field-label">Current Role</div><div class="profile-field-value">${data.current_role || '—'}</div></div>
            <div class="profile-field"><div class="profile-field-label">Experience</div><div class="profile-field-value">${data.experience_years || '—'} years</div></div>
            <div class="profile-field"><div class="profile-field-label">Education</div><div class="profile-field-value">${data.education || '—'}</div></div>
            <div class="profile-field"><div class="profile-field-label">Career Narrative</div><div class="profile-field-value">${data.career_narrative || '—'}</div></div>
            <div class="profile-field"><div class="profile-field-label">Skills</div><div class="profile-field-value">${(data.skills || []).map(s => `<span class="cand-tag">${s}</span>`).join(' ')}</div></div>
            ${(data.anomalies && data.anomalies.length) ? `<div class="profile-field"><div class="profile-field-label">⚠️ Anomalies</div><div class="profile-field-value" style="color:var(--accent-coral)">${data.anomalies.join('; ')}</div></div>` : ''}
            <div class="profile-field"><div class="profile-field-label">Top Strengths</div>
                <ul class="strengths-list">${(data.top_strengths || []).map(s => `<li>${s}</li>`).join('')}</ul>
            </div>
            <div class="profile-field"><div class="profile-field-label">Concerns</div>
                <ul class="concerns-list">${(data.concerns || []).map(s => `<li>${s}</li>`).join('')}</ul>
            </div>
        `;
    } catch (e) {
        content.innerHTML = `<p style="color:var(--accent-coral)">Error: ${e.message}</p>`;
    } finally {
        setLoading(btn, false);
    }
}

function toggleDEI() {
    const badge = document.getElementById('dei-badge');
    badge.style.display = document.getElementById('dei-toggle').checked ? 'inline' : 'none';
    // Re-render if results already visible
    const nameField = document.querySelector('#screening-content .profile-field-value');
    if (nameField && document.getElementById('dei-toggle').checked) {
        nameField.textContent = '██████████';
    }
}

// ──────────────────────────────────────
// SECTION 4: AI INTERVIEW
// ──────────────────────────────────────
let interviewHistory = [];
let interviewTurnCount = 0;

async function startInterview() {
    const msgArea = document.getElementById('chat-messages');
    const startBtn = document.getElementById('btn-start-interview');
    const endBtn = document.getElementById('btn-end-interview');
    interviewHistory = [];
    interviewTurnCount = 0;
    msgArea.innerHTML = '';
    startBtn.style.display = 'none';
    endBtn.style.display = 'inline-block';

    addMessage(msgArea, 'bot', null, true); // typing indicator
    try {
        const data = await apiCall('/api/interview/chat', { message: '', history: [] });
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', data.response);
        interviewHistory.push({ role: 'assistant', content: data.response });
    } catch (e) {
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', 'Error starting interview: ' + e.message);
    }
}

async function sendInterviewMessage() {
    const input = document.getElementById('chat-input');
    const msgArea = document.getElementById('chat-messages');
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msgArea, 'user', msg);
    input.value = '';
    interviewHistory.push({ role: 'user', content: msg });
    interviewTurnCount++;

    addMessage(msgArea, 'bot', null, true);
    try {
        const data = await apiCall('/api/interview/chat', { message: msg, history: interviewHistory });
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', data.response);
        interviewHistory.push({ role: 'assistant', content: data.response });

        if (interviewTurnCount >= 6) {
            addMessage(msgArea, 'bot', '📋 You can now click "End & Generate Snapshot" to see your Candidate Snapshot.');
        }
    } catch (e) {
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', 'Error: ' + e.message);
    }
}

async function endInterview() {
    const snapCard = document.getElementById('snapshot-card');
    const snapContent = document.getElementById('snapshot-content');
    snapCard.style.display = 'block';
    snapContent.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

    try {
        const data = await apiCall('/api/interview/snapshot', { message: '', history: interviewHistory });
        const impClass = (data.overall_impression || '').toLowerCase();
        snapContent.innerHTML = `
            <div class="snap-impression ${impClass}">${data.overall_impression || 'N/A'}</div>
            <div class="snap-section">
                <h4>🎭 Vibe Check</h4>
                <p>${data.vibe_check || '—'}</p>
            </div>
            <div class="snap-section">
                <h4>🚩 Red Flags</h4>
                <ul>${(data.red_flags || []).map(f => `<li>⚠️ ${f}</li>`).join('') || '<li>None detected</li>'}</ul>
            </div>
            <div class="snap-section">
                <h4>✅ Top 3 Reasons to Hire</h4>
                <ul>${(data.top_3_reasons_to_hire || []).map((r, i) => `<li>${i + 1}. ${r}</li>`).join('')}</ul>
            </div>
            <div class="snap-section">
                <h4>➡️ Recommended Next Step</h4>
                <p>${data.recommended_next_step || '—'}</p>
            </div>
        `;
    } catch (e) {
        snapContent.innerHTML = `<p style="color:var(--accent-coral)">Error: ${e.message}</p>`;
    }
}

// ──────────────────────────────────────
// SECTION 5: PREBOARDING
// ──────────────────────────────────────
let preboardHistory = [];

function sendPreboardQuick(msg) {
    document.getElementById('preboard-input').value = msg;
    sendPreboardMessage();
}

async function sendPreboardMessage() {
    const input = document.getElementById('preboard-input');
    const msgArea = document.getElementById('preboard-messages');
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msgArea, 'user', msg);
    input.value = '';
    preboardHistory.push({ role: 'user', content: msg });

    addMessage(msgArea, 'bot', null, true);
    try {
        const data = await apiCall('/api/preboarding/chat', { message: msg, history: preboardHistory });
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', data.response);
        preboardHistory.push({ role: 'assistant', content: data.response });
    } catch (e) {
        removeTyping(msgArea);
        addMessage(msgArea, 'bot', 'Error: ' + e.message);
    }
}

// ──────────────────────────────────────
// CHAT HELPERS
// ──────────────────────────────────────
function addMessage(container, role, text, isTyping = false) {
    const div = document.createElement('div');
    div.className = `message ${role === 'bot' ? 'bot-message' : 'user-message'}`;
    if (isTyping) {
        div.classList.add('typing-msg');
        div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    } else {
        div.innerHTML = `<div class="message-content">${text}</div>`;
    }
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function removeTyping(container) {
    const t = container.querySelector('.typing-msg');
    if (t) t.remove();
}

// ──────────────────────────────────────
// INIT
// ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    renderCandidates();
});
