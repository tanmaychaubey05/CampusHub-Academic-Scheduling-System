// CampusHub Web Dashboard Controller
const API_BASE = '/api';

// State
let usersList = [];
let groupsList = [];

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupModals();
  loadInitialData();
  setupEventListeners();
});

// Setup Tab Navigation
function setupTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetId = `tab-${tab.getAttribute('data-tab')}`;
      document.getElementById(targetId)?.classList.add('active');

      if (tab.getAttribute('data-tab') === 'groups') loadGroups();
      if (tab.getAttribute('data-tab') === 'sessions') loadSessions();
      if (tab.getAttribute('data-tab') === 'resources') loadResources();
      if (tab.getAttribute('data-tab') === 'analytics') loadAnalytics();
    });
  });
}

// Setup Modals
function setupModals() {
  const openButtons = [
    { btn: 'btn-open-create-group', modal: 'modal-group' },
    { btn: 'btn-open-schedule-session', modal: 'modal-session' },
    { btn: 'btn-open-upload-resource', modal: 'modal-resource' }
  ];

  openButtons.forEach(({ btn, modal }) => {
    document.getElementById(btn)?.addEventListener('click', () => {
      populateUserDropdowns();
      populateGroupDropdowns();
      document.getElementById(modal)?.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.close-modal').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
    });
  });
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  toast.innerText = message;
  toast.style.background = isError ? '#ef4444' : '#10b981';
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
}

// Initial Data Load
async function loadInitialData() {
  try {
    const resUsers = await fetch(`${API_BASE}/users`);
    usersList = await resUsers.json();
    await loadGroups();
    await loadSessions();
    await loadResources();
  } catch (err) {
    console.error('Failed to load initial data:', err);
  }
}

function populateUserDropdowns() {
  const userSelects = ['group-creator-id', 'session-host-id', 'res-uploader-id'];
  userSelects.forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = usersList.map(u => `<option value="${u.id}">${u.full_name} (${u.role})</option>`).join('');
  });
}

function populateGroupDropdowns() {
  const groupSelects = ['session-group-id', 'res-group-id', 'analytics-group-select'];
  groupSelects.forEach(id => {
    const sel = document.getElementById(id);
    if (!sel) return;
    sel.innerHTML = groupsList.map(g => `<option value="${g.id}">${g.course_code} - ${g.name}</option>`).join('');
  });
}

// 1. Groups Logic
async function loadGroups() {
  const grid = document.getElementById('groups-grid');
  try {
    const search = document.getElementById('group-search')?.value || '';
    const course = document.getElementById('group-course-filter')?.value || '';
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (course) params.append('course', course);

    const res = await fetch(`${API_BASE}/groups?${params.toString()}`);
    groupsList = await res.json();
    populateGroupDropdowns();

    if (groupsList.length === 0) {
      grid.innerHTML = '<div class="loading-state">No study groups found. Click "Load Demo Data" or "+ Create New Group".</div>';
      return;
    }

    grid.innerHTML = groupsList.map(g => `
      <div class="card">
        <span class="card-tag">${g.course_code}</span>
        <h3 class="card-title">${g.name}</h3>
        <p class="card-desc">${g.description || 'No description provided.'}</p>
        <div class="card-meta">
          <span>Leader: <strong>${g.creator_name || 'N/A'}</strong></span>
          <span>👥 ${g.member_count}/${g.max_members}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = '<div class="loading-state">Error loading groups.</div>';
  }
}

// 2. Sessions Logic
async function loadSessions() {
  const list = document.getElementById('sessions-list');
  try {
    const res = await fetch(`${API_BASE}/sessions`);
    const sessions = await res.json();

    if (sessions.length === 0) {
      list.innerHTML = '<div class="loading-state">No scheduled sessions found.</div>';
      return;
    }

    list.innerHTML = sessions.map(s => `
      <div class="session-item">
        <div class="session-info">
          <span class="card-tag">${s.group_name || 'Group ' + s.group_id}</span>
          <h3>${s.title}</h3>
          <div class="session-time">⏰ ${s.start_time} to ${s.end_time}</div>
          <p class="card-desc">📍 ${s.location_or_link} | Host: ${s.host_name || 'N/A'}</p>
        </div>
        <div class="session-actions">
          <span class="badge" style="margin-right: 12px;">RSVPs: ${s.attendee_count}</span>
          <button class="btn btn-secondary" onclick="rsvpSession(${s.id})">RSVP Spot</button>
        </div>
      </div>
    `).join('');
  } catch (err) {
    list.innerHTML = '<div class="loading-state">Error loading sessions.</div>';
  }
}

async function rsvpSession(sessionId) {
  if (usersList.length === 0) return;
  const userId = usersList[0].id;
  try {
    const res = await fetch(`${API_BASE}/sessions/rsvp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, user_id: userId })
    });
    const data = await res.json();
    if (res.ok) {
      showToast('RSVP Confirmed!');
      loadSessions();
    } else {
      showToast(data.error || 'Failed to RSVP', true);
    }
  } catch (err) {
    showToast('Network error during RSVP', true);
  }
}

// 3. Resources Logic
async function loadResources() {
  const grid = document.getElementById('resources-grid');
  try {
    const search = document.getElementById('resource-search')?.value || '';
    const tag = document.getElementById('resource-tag-filter')?.value || '';
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (tag) params.append('tag', tag);

    const res = await fetch(`${API_BASE}/resources?${params.toString()}`);
    const resources = await res.json();

    if (resources.length === 0) {
      grid.innerHTML = '<div class="loading-state">No academic materials shared yet.</div>';
      return;
    }

    grid.innerHTML = resources.map(r => `
      <div class="card">
        <span class="card-tag">${r.resource_type}</span>
        <h3 class="card-title">${r.title}</h3>
        <p class="card-desc">${r.description || ''}</p>
        <p class="card-desc" style="font-size: 0.75rem; color: #6366f1;">🏷️ ${r.tags || 'General'}</p>
        <div class="card-meta">
          <span>By: <strong>${r.uploader_name}</strong></span>
          <a href="${r.file_or_url}" target="_blank" class="btn btn-secondary" style="font-size: 0.75rem; padding: 4px 8px;">Access</a>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = '<div class="loading-state">Error loading resources.</div>';
  }
}

// 4. Analytics Logic
async function loadAnalytics() {
  const sel = document.getElementById('analytics-group-select');
  if (!sel || !sel.value) return;

  try {
    const res = await fetch(`${API_BASE}/analytics?group_id=${sel.value}`);
    const data = await res.json();

    document.getElementById('stat-sessions').innerText = data.total_sessions || 0;
    document.getElementById('stat-members').innerText = data.total_members || 0;
    document.getElementById('stat-attendance').innerText = `${data.attendance_rate_percent || 0}%`;
    document.getElementById('stat-rating').innerText = `${data.average_satisfaction_rating || 0} / 5.0`;

    document.getElementById('analytics-report-text').innerText = `
============================================================
       CAMPUSHUB ACADEMIC STUDY GROUP ANALYTICS REPORT
============================================================
Group Name       : ${data.group_name}
Course Code      : ${data.course_code}
Active Members   : ${data.total_members}
------------------------------------------------------------
SESSION PERFORMANCE METRICS:
  * Total Sessions Created : ${data.total_sessions}
  * Completed Sessions     : ${data.completed_sessions}
  * Currently Scheduled    : ${data.scheduled_sessions}
  * Cancelled Sessions     : ${data.cancelled_sessions}
------------------------------------------------------------
ATTENDANCE & ENGAGEMENT:
  * Total RSVPs Recorded   : ${data.total_rsvps}
  * Verified Attendances   : ${data.total_attended}
  * Attendance Rate        : ${data.attendance_rate_percent}%
------------------------------------------------------------
RESOURCE SHARING:
  * Study Files Uploaded   : ${data.total_resources}
  * Material Access Count  : ${data.total_resource_downloads}
------------------------------------------------------------
PEER FEEDBACK:
  * Average Satisfaction   : ${data.average_satisfaction_rating} / 5.0
  * Reviews Evaluated      : ${data.total_reviews}
============================================================`;
  } catch (err) {
    console.error('Analytics load error:', err);
  }
}

// Event Listeners for Forms & Filters
function setupEventListeners() {
  document.getElementById('btn-seed')?.addEventListener('click', async () => {
    try {
      const res = await fetch(`${API_BASE}/seed`, { method: 'POST' });
      const data = await res.json();
      showToast(data.message || 'Sample data seeded!');
      await loadInitialData();
    } catch (err) {
      showToast('Failed to seed demo data', true);
    }
  });

  document.getElementById('btn-filter-groups')?.addEventListener('click', loadGroups);
  document.getElementById('btn-filter-resources')?.addEventListener('click', loadResources);
  document.getElementById('analytics-group-select')?.addEventListener('change', loadAnalytics);

  // Form: Create Group
  document.getElementById('form-create-group')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      creator_id: document.getElementById('group-creator-id').value,
      name: document.getElementById('group-name').value,
      course_code: document.getElementById('group-course').value,
      description: document.getElementById('group-desc').value,
      max_members: 20
    };
    try {
      const res = await fetch(`${API_BASE}/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Study Group created successfully!');
        document.getElementById('modal-group').classList.add('hidden');
        loadGroups();
      } else {
        showToast(data.error || 'Failed to create group', true);
      }
    } catch (err) {
      showToast('Network error', true);
    }
  });

  // Form: Schedule Session
  document.getElementById('form-create-session')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      group_id: document.getElementById('session-group-id').value,
      host_id: document.getElementById('session-host-id').value,
      title: document.getElementById('session-title').value,
      location_or_link: document.getElementById('session-loc').value,
      start_time: document.getElementById('session-start').value,
      end_time: document.getElementById('session-end').value,
      description: document.getElementById('session-desc').value
    };
    try {
      const res = await fetch(`${API_BASE}/sessions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Session scheduled without conflicts!');
        document.getElementById('modal-session').classList.add('hidden');
        loadSessions();
      } else {
        showToast(`Conflict or Validation Error: ${data.error}`, true);
      }
    } catch (err) {
      showToast('Network error', true);
    }
  });

  // Form: Upload Resource
  document.getElementById('form-upload-resource')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      group_id: document.getElementById('res-group-id').value,
      uploader_id: document.getElementById('res-uploader-id').value,
      title: document.getElementById('res-title').value,
      resource_type: document.getElementById('res-type').value,
      file_or_url: document.getElementById('res-url').value,
      tags: document.getElementById('res-tags').value
    };
    try {
      const res = await fetch(`${API_BASE}/resources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        showToast('Study resource indexed successfully!');
        document.getElementById('modal-resource').classList.add('hidden');
        loadResources();
      } else {
        showToast(data.error || 'Failed to index resource', true);
      }
    } catch (err) {
      showToast('Network error', true);
    }
  });

  // AI Code Detection Trigger
  document.getElementById('btn-detect-ai')?.addEventListener('click', async () => {
    const codeText = document.getElementById('ai-code-input')?.value || '';
    if (!codeText.trim()) {
      showToast('Please paste some code to analyze', true);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/integrity/ai-detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code_text: codeText })
      });
      const data = await res.json();
      if (res.ok) {
        document.getElementById('ai-detect-results').style.display = 'block';
        document.getElementById('ai-verdict').innerText = data.verdict;
        document.getElementById('ai-prob').innerText = `${data.ai_probability_percent}%`;
        const m = data.metrics;
        document.getElementById('ai-metrics-detail').innerText =
          `Tokens: ${m.token_count} | Entropy: ${m.shannon_entropy} bits | TTR: ${m.type_token_ratio} | Line Variance: ${m.line_length_std_dev} | AI Cliche Hits: ${m.ai_cliche_hits}`;
        showToast('AI Code analysis complete!');
      } else {
        showToast(data.error || 'AI detection failed', true);
      }
    } catch (err) {
      showToast('Network error during AI detection', true);
    }
  });

  // Plagiarism Comparison Trigger
  document.getElementById('btn-check-plagiarism')?.addEventListener('click', async () => {
    const srcText = document.getElementById('plag-source-input')?.value || '';
    const tgtText = document.getElementById('plag-target-input')?.value || '';
    if (!srcText.trim() || !tgtText.trim()) {
      showToast('Please provide both source and comparison code', true);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/integrity/plagiarism`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_text: srcText, target_text: tgtText })
      });
      const data = await res.json();
      if (res.ok) {
        document.getElementById('plag-results').style.display = 'block';
        document.getElementById('plag-verdict').innerText = data.verdict;
        document.getElementById('plag-sim').innerText = `${data.similarity_percentage}%`;
        document.getElementById('plag-contain').innerText = `${data.containment_percentage}%`;
        document.getElementById('plag-hashes-detail').innerText =
          `Matched Hashes: ${data.matching_fingerprints} (Source: ${data.source_fingerprints}, Target: ${data.target_fingerprints})`;
        showToast('Plagiarism check complete!');
      } else {
        showToast(data.error || 'Plagiarism check failed', true);
      }
    } catch (err) {
      showToast('Network error during plagiarism check', true);
    }
  });
}
