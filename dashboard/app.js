// ── State ────────────────────────────────────────────────────────────────────
let jobs = [];
let currentJob = null;
let selectedJobs = new Set();
let colSort = { new: 'score-desc', shortlisted: 'score-desc', applied: 'date-desc', closed: 'date-desc' };

// ── DOM refs ─────────────────────────────────────────────────────────────────
const views = {
  'board-view': document.getElementById('board-view'),
  'skills-view': document.getElementById('skills-view'),
  'graveyard-view': document.getElementById('graveyard-view')
};
const tabs = document.querySelectorAll('.tab');
const cols = {
  new: document.getElementById('col-new')?.querySelector('.col-body'),
  shortlisted: document.getElementById('col-shortlisted')?.querySelector('.col-body'),
  applied: document.getElementById('col-applied')?.querySelector('.col-body'),
  closed: document.getElementById('col-closed')?.querySelector('.col-body'),
  graveyard: document.getElementById('col-graveyard')?.querySelector('.col-body')
};
const counters = {
  new: document.getElementById('col-new')?.querySelector('.count'),
  shortlisted: document.getElementById('col-shortlisted')?.querySelector('.count'),
  applied: document.getElementById('col-applied')?.querySelector('.count'),
  closed: document.getElementById('col-closed')?.querySelector('.count'),
  graveyard: document.getElementById('col-graveyard')?.querySelector('.count')
};
const modal = document.getElementById('job-modal');

// ── Helpers ──────────────────────────────────────────────────────────────────
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = (new Date() - new Date(dateStr)) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return `${Math.floor(diff / 604800)}w ago`;
}

function daysSince(dateStr) {
  if (!dateStr) return 0;
  return (new Date() - new Date(dateStr)) / (1000 * 60 * 60 * 24);
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  loadSkills();
  loadDiscoveryStatus();

  // Tabs
  tabs.forEach(t => t.addEventListener('click', (e) => {
    tabs.forEach(btn => btn.classList.remove('active'));
    Object.values(views).forEach(v => { if (v) v.classList.remove('active'); });
    e.target.classList.add('active');
    const targetView = views[e.target.dataset.target];
    if (targetView) targetView.classList.add('active');
  }));

  // Discover button
  const btnDiscover = document.getElementById('btn-discover');
  if (btnDiscover) {
    btnDiscover.addEventListener('click', async (e) => {
      const btn = e.target;
      btn.disabled = true;
      btn.innerHTML = '⏳ Discovering & Scoring (takes a minute)...';
      try {
        const res = await fetch('/api/discover', { method: 'POST' });
        const data = await res.json();
        alert(`Done! Found ${data.discovery.added_new} new jobs. Scored ${data.scoring.scored}. Archived ${data.scoring.archived}.`);
        loadJobs();
        loadSkills();
        loadDiscoveryStatus();
      } catch (err) {
        alert('Error running discovery.');
      }
      btn.disabled = false;
      btn.innerHTML = '<span class="icon">🔍</span> Discover New Jobs';
    });
  }

  // Modal close
  document.querySelector('.close-btn').onclick = () => { modal.classList.remove('active'); };
  document.getElementById('btn-close-docs').onclick = () => { document.getElementById('docs-modal').classList.remove('active'); };
  document.getElementById('diff-close-btn').onclick = () => { document.getElementById('diff-modal').classList.remove('active'); };

  window.onclick = (e) => {
    if (e.target === modal) modal.classList.remove('active');
    if (e.target === document.getElementById('docs-modal')) document.getElementById('docs-modal').classList.remove('active');
    if (e.target === document.getElementById('diff-modal')) document.getElementById('diff-modal').classList.remove('active');
  };

  document.getElementById('btn-open-link').onclick = () => {
    if (currentJob) window.open(currentJob.url, '_blank');
  };

  // Archive filters
  document.getElementById('archive-filter-domain').addEventListener('change', renderBoard);
  document.getElementById('archive-filter-date').addEventListener('change', renderBoard);

  // Score filter slider
  const slider = document.getElementById('score-filter-slider');
  const sliderVal = document.getElementById('score-filter-value');
  slider.addEventListener('input', () => {
    sliderVal.textContent = slider.value;
    renderBoard();
  });

  // Column search
  document.getElementById('col-new-search').addEventListener('input', renderBoard);

  // Column sort selects
  document.querySelectorAll('.col-sort').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const col = e.target.dataset.col;
      colSort[col] = e.target.value;
      renderBoard();
    });
  });

  // Save Notes
  const btnSaveNotes = document.getElementById('btn-save-notes');
  if (btnSaveNotes) {
    btnSaveNotes.onclick = async (e) => {
      if (!currentJob) return;
      const btn = e.target;
      const newNotes = document.getElementById('modal-job-notes').value;
      btn.disabled = true;
      btn.innerText = 'Saving...';
      try {
        const res = await fetch(`/api/jobs/${currentJob.id}/notes`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ notes: newNotes })
        });
        const data = await res.json();
        if (data.success) {
          btn.innerText = 'Saved! ✓';
          setTimeout(() => { btn.innerText = '💾 Save Notes'; }, 2000);
          const idx = jobs.findIndex(j => j.id === currentJob.id);
          if (idx !== -1) jobs[idx].notes = newNotes;
          currentJob.notes = newNotes;
          renderBoard();
        } else {
          alert('Failed to save notes.');
          btn.innerText = '💾 Save Notes';
        }
      } catch (err) {
        alert('API error saving notes.');
        btn.innerText = '💾 Save Notes';
      }
      btn.disabled = false;
    };
  }

  // Save Description
  const btnSaveDesc = document.getElementById('btn-save-desc');
  if (btnSaveDesc) {
    btnSaveDesc.onclick = async (e) => {
      if (!currentJob) return;
      const btn = e.target;
      const newDesc = document.getElementById('modal-job-desc').value;
      btn.disabled = true;
      btn.innerText = 'Saving...';
      try {
        const res = await fetch(`/api/jobs/${currentJob.id}/description`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description: newDesc })
        });
        const data = await res.json();
        if (data.success) {
          alert('Description saved successfully.');
          const idx = jobs.findIndex(j => j.id === currentJob.id);
          if (idx !== -1) jobs[idx].description = newDesc;
          currentJob.description = newDesc;
        } else {
          alert('Failed to save description.');
        }
      } catch (err) {
        alert('API error saving description.');
      }
      btn.disabled = false;
      btn.innerText = '💾 Save Description';
    };
  }

  // Shortlist
  const btnShortlist = document.getElementById('btn-shortlist');
  if (btnShortlist) {
    btnShortlist.onclick = async (e) => {
      if (!currentJob) return;
      const btn = e.target;
      btn.disabled = true;
      try {
        await fetch(`/api/jobs/${currentJob.id}/status`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: 'shortlisted' })
        });
        currentJob.status = 'shortlisted';
        const idx = jobs.findIndex(j => j.id === currentJob.id);
        if (idx !== -1) jobs[idx].status = 'shortlisted';
        loadJobs();
        modal.classList.remove('active');
      } catch (err) { alert('API error shortlisting.'); }
      btn.disabled = false;
    };
  }

  // Tailor Resume
  const btnTailor = document.getElementById('btn-tailor');
  if (btnTailor) {
    btnTailor.onclick = async (e) => {
      if (!currentJob) return;
      const btn = e.target;
      btn.disabled = true;
      btn.innerText = 'Tailoring...';
      if (currentJob.status !== 'shortlisted') {
        try {
          await fetch(`/api/jobs/${currentJob.id}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'shortlisted' })
          });
          currentJob.status = 'shortlisted';
        } catch (e) { }
      }
      try {
        const res = await fetch(`/api/tailor/${currentJob.id}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          alert(`Resume tailored! Saved to: ${data.path}`);
          currentJob.resume_path = data.path;
          const btnDocs = document.getElementById('btn-open-docs');
          btnDocs.disabled = false;
          btnDocs.style.opacity = '1';
          btnDocs.style.cursor = 'pointer';
          loadJobs();
        } else {
          alert('Tailoring failed.');
        }
      } catch (err) {
        alert('API error tailoring resume.');
      }
      btn.disabled = false;
      btn.innerText = 'Tailor Resume (AI)';
    };
  }

  // Open Docs
  const btnOpenDocs = document.getElementById('btn-open-docs');
  if (btnOpenDocs) {
    btnOpenDocs.addEventListener('click', (e) => {
      e.preventDefault();
      if (!currentJob) return;
      document.getElementById('job-modal').classList.remove('active');
      openDocsEditor(currentJob);
    });
  }

  // Delete Job
  const btnDeleteJob = document.getElementById('btn-delete-job');
  if (btnDeleteJob) {
    btnDeleteJob.onclick = async (e) => {
      if (!currentJob) return;
      if (!confirm(`Are you sure you want to PERMANENTLY delete "${currentJob.title}" at ${currentJob.company || 'this company'}?`)) return;
      const btn = e.target;
      btn.disabled = true;
      btn.innerText = 'Deleting...';
      try {
        const res = await fetch(`/api/jobs/${currentJob.id}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
          jobs = jobs.filter(j => j.id !== currentJob.id);
          renderBoard();
          modal.classList.remove('active');
        } else {
          alert('Failed to delete job.');
        }
      } catch (err) {
        alert('API error deleting job.');
      }
      btn.disabled = false;
      btn.innerText = '🗑️ Delete';
    };
  }
});

// ── Loaders ──────────────────────────────────────────────────────────────────
async function loadJobs() {
  const res = await fetch('/api/jobs');
  jobs = await res.json();
  renderBoard();
}

async function loadSkills() {
  try {
    const res = await fetch('/api/skills');
    const data = await res.json();
    const lists = {
      tools: document.getElementById('list-tools'),
      skills: document.getElementById('list-skills'),
      signals: document.getElementById('list-signals')
    };
    ['tools', 'skills', 'signals'].forEach(cat => {
      lists[cat].innerHTML = '';
      (data[cat] || []).slice(0, 15).forEach(item => {
        lists[cat].innerHTML += `
          <li>
            <span>${item.keyword}</span>
            <span class="skill-freq">${item.frequency}</span>
          </li>`;
      });
    });
  } catch (e) { console.error('No skills data yet'); }
}

async function loadDiscoveryStatus() {
  const el = document.getElementById('last-discovery-status');
  if (!el) return;
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (!data.last_discovery) {
      el.textContent = 'No discovery run yet';
      return;
    }
    el.textContent = `Last run: ${timeAgo(data.last_discovery)} · ${data.added} new · ${data.scored} scored · ${data.archived} archived`;
  } catch (e) {
    el.textContent = 'Status unavailable';
  }
}

// ── Kanban Render ─────────────────────────────────────────────────────────────
function sortFn(sort) {
  return (a, b) => {
    switch (sort) {
      case 'date-desc': return new Date(b.discovered_at) - new Date(a.discovered_at);
      case 'date-asc':  return new Date(a.discovered_at) - new Date(b.discovered_at);
      case 'score-asc': return a.score - b.score;
      case 'salary-desc': return (b.salary_monthly || 0) - (a.salary_monthly || 0);
      default: return b.score - a.score; // score-desc
    }
  };
}

function renderBoard() {
  Object.values(cols).forEach(c => { if (c) c.innerHTML = ''; });
  const counts = { new: 0, shortlisted: 0, applied: 0, closed: 0, graveyard: 0 };

  const filterDomain = document.getElementById('archive-filter-domain').value;
  const filterDate   = document.getElementById('archive-filter-date').value;
  const searchText   = (document.getElementById('col-new-search')?.value || '').toLowerCase().trim();
  const scoreMin     = parseInt(document.getElementById('score-filter-slider')?.value || '0');

  // Categorize
  const grouped = { new: [], shortlisted: [], applied: [], closed: [], graveyard: [] };

  jobs.forEach(job => {
    let status = job.status || 'new';
    const days = daysSince(job.discovered_at);

    if (status === 'archived' || status === 'closed') {
      status = days > 3 ? 'graveyard' : 'closed';
    } else if (status === 'applied') {
      if (days > 15) status = 'graveyard';
    } else if (status === 'new') {
      if (days > 7) status = 'graveyard'; // stale new jobs
    }

    if (grouped[status]) grouped[status].push(job);
  });

  // Filter new column
  const newJobs = grouped.new.filter(job => {
    if (scoreMin > 0 && job.score < scoreMin) return false;
    if (searchText && !`${job.title || ''} ${job.company || ''}`.toLowerCase().includes(searchText)) return false;
    return true;
  });

  // Filter closed column
  const closedJobs = grouped.closed.filter(job => {
    if (filterDomain === 'health') {
      try {
        const bd = JSON.parse(job.score_breakdown || '{}');
        if (!bd.healthcare || bd.healthcare <= 0) return false;
      } catch (e) { return false; }
    }
    if (filterDate === 'new' && job.discovered_at) {
      const twoDaysAgo = new Date();
      twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
      if (new Date(job.discovered_at) < twoDaysAgo) return false;
    }
    return true;
  });

  // Render each column
  const renderCol = (status, jobList) => {
    const sorted = [...jobList].sort(sortFn(colSort[status] || 'score-desc'));
    sorted.forEach(job => {
      counts[status]++;
      cols[status].appendChild(createCard(job, status));
    });
  };

  renderCol('new', newJobs);
  renderCol('shortlisted', grouped.shortlisted);
  renderCol('applied', grouped.applied);
  renderCol('closed', closedJobs);
  renderCol('graveyard', grouped.graveyard);

  Object.keys(counts).forEach(k => {
    if (counters[k]) counters[k].innerText = counts[k];
  });

  updateBatchBar();
}

function createCard(job, status) {
  const card = document.createElement('div');
  card.className = 'job-card';
  card.draggable = true;
  card.dataset.id = job.id;

  const days = daysSince(job.discovered_at);
  if (status === 'new' && days > 3) card.classList.add('stale');
  if (selectedJobs.has(job.id)) card.classList.add('selected');

  const scoreColor = job.score >= 80 ? 'score-high' : 'score-med';
  const ts = job.discovered_at ? timeAgo(job.discovered_at) : '';
  const salHTML = job.salary_monthly
    ? `<div class="job-sal">~$${Math.round(job.salary_monthly).toLocaleString()}/mo</div>`
    : '';
  const notesHTML = job.notes
    ? `<div class="job-notes-preview">📝 ${job.notes.slice(0, 60)}${job.notes.length > 60 ? '…' : ''}</div>`
    : '';
  const overdue = status === 'applied' && job.follow_up_date && new Date(job.follow_up_date) < new Date();
  const overdueHTML = overdue ? '<span class="overdue-badge">Follow up!</span>' : '';
  const quickShortlistBtn = status === 'new'
    ? `<button class="quick-shortlist" title="Quick Shortlist" onclick="event.stopPropagation(); quickShortlist(${job.id})">⭐</button>`
    : '';

  card.innerHTML = `
    <div class="card-top-row">
      <div class="job-score ${scoreColor}">${job.score}/100</div>
      <div class="card-actions">
        ${quickShortlistBtn}
        <input type="checkbox" class="batch-check" title="Select for batch action"
          onclick="event.stopPropagation(); toggleBatchSelect(${job.id})"
          ${selectedJobs.has(job.id) ? 'checked' : ''}>
      </div>
    </div>
    <div class="job-title">${job.title}${overdueHTML}</div>
    <div class="job-company">${job.company || job.board}</div>
    ${salHTML}
    <div class="card-footer">
      <span class="job-timestamp">${ts}</span>
      ${notesHTML}
    </div>
  `;

  card.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('text/plain', job.id);
    setTimeout(() => card.classList.add('dragging'), 0);
  });
  card.addEventListener('dragend', () => card.classList.remove('dragging'));
  card.addEventListener('click', () => openModal(job));

  return card;
}

// ── Drag / Drop ───────────────────────────────────────────────────────────────
function allowDrop(ev) { ev.preventDefault(); }
async function drop(ev, newStatus) {
  ev.preventDefault();
  const id = parseInt(ev.dataTransfer.getData('text/plain'));
  const job = jobs.find(j => j.id === id);
  if (job && job.status !== newStatus) {
    job.status = newStatus;
    renderBoard();
    await fetch(`/api/jobs/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
  }
}

// ── Quick Shortlist ───────────────────────────────────────────────────────────
async function quickShortlist(id) {
  const job = jobs.find(j => j.id === id);
  if (!job) return;
  job.status = 'shortlisted';
  renderBoard();
  await fetch(`/api/jobs/${id}/status`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'shortlisted' })
  });
}

// ── Batch Actions ─────────────────────────────────────────────────────────────
function toggleBatchSelect(id) {
  if (selectedJobs.has(id)) selectedJobs.delete(id);
  else selectedJobs.add(id);
  renderBoard();
}

function clearSelection() {
  selectedJobs.clear();
  renderBoard();
}

function updateBatchBar() {
  const bar = document.getElementById('batch-bar');
  if (!bar) return;
  bar.style.display = selectedJobs.size > 0 ? 'flex' : 'none';
  const el = document.getElementById('batch-count');
  if (el) el.textContent = `${selectedJobs.size} selected`;
}

async function batchArchive() {
  if (!selectedJobs.size) return;
  if (!confirm(`Archive ${selectedJobs.size} job(s)?`)) return;
  for (const id of selectedJobs) {
    await fetch(`/api/jobs/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'archived' })
    });
    const job = jobs.find(j => j.id === id);
    if (job) job.status = 'archived';
  }
  selectedJobs.clear();
  renderBoard();
}

async function batchDelete() {
  if (!selectedJobs.size) return;
  if (!confirm(`PERMANENTLY delete ${selectedJobs.size} job(s)? This cannot be undone.`)) return;
  for (const id of selectedJobs) {
    await fetch(`/api/jobs/${id}`, { method: 'DELETE' });
    jobs = jobs.filter(j => j.id !== id);
  }
  selectedJobs.clear();
  renderBoard();
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function openModal(job) {
  currentJob = job;
  const body = document.getElementById('modal-body');

  let bdHTML = '';
  try {
    const bd = JSON.parse(job.score_breakdown || '{}');
    bdHTML = Object.entries(bd).map(([k, v]) =>
      `<span style="display:inline-block; padding:2px 6px; background:#334155; border-radius:4px; margin:2px 4px 2px 0; font-size:0.8rem">${k}: ${v}</span>`
    ).join('');
  } catch (e) { }

  const days = daysSince(job.discovered_at);
  const followUpValue = job.follow_up_date ? job.follow_up_date.split('T')[0] : '';
  const followUpOverdue = followUpValue && new Date(followUpValue) < new Date();
  const overdueLabel = followUpOverdue
    ? '<span class="follow-up-overdue-label">⚠ Overdue!</span>'
    : '';

  body.innerHTML = `
    <h2 style="margin-bottom:0.5rem">${job.title}</h2>
    <h4 style="color:var(--text-muted); margin-bottom:0.5rem">${job.company || ''} · ${job.board}</h4>
    <div style="font-size:0.8rem; color:var(--text-muted); margin-bottom:1rem">
      Discovered ${timeAgo(job.discovered_at)} &nbsp;·&nbsp; ${Math.floor(days)} day(s) ago
    </div>

    <div style="display:flex; gap:1rem; margin-bottom:1rem">
      <div class="job-score ${job.score >= 80 ? 'score-high' : 'score-med'}" style="font-size:1.2rem; padding:4px 12px">Score: ${job.score}/100</div>
    </div>

    <div style="margin-bottom:1rem">${bdHTML}</div>

    <div class="follow-up-row">
      <label for="modal-follow-up">Follow-up date:</label>
      <input type="date" id="modal-follow-up" value="${followUpValue}">
      <button class="btn secondary" id="btn-save-follow-up" style="font-size:0.8rem; padding:0.3rem 0.8rem">Save</button>
      ${overdueLabel}
    </div>

    <h4 style="margin-bottom:0.4rem">Notes</h4>
    <textarea id="modal-job-notes" style="width:100%; min-height:70px; resize:vertical; background:var(--bg-col); border:1px solid var(--border); color:var(--text-main); padding:0.6rem; border-radius:6px; font-family:inherit; font-size:0.9rem; margin-bottom:0.5rem">${job.notes || ''}</textarea>
    <button id="btn-save-notes" class="btn secondary" style="font-size:0.8rem; padding:0.3rem 0.8rem; margin-bottom:1rem">💾 Save Notes</button>

    <h4 style="margin-bottom:0.5rem">Job Description</h4>
    <textarea id="modal-job-desc" class="jd-block" style="width:100%; min-height:300px; resize:vertical; background:var(--bg-col); border:1px solid var(--border); color:var(--text-main); padding:1rem; border-radius:6px;">${job.description || 'Description not fetched.'}</textarea>
  `;

  // Wire up dynamically created buttons
  document.getElementById('btn-save-follow-up').onclick = saveFollowUp;
  document.getElementById('btn-save-notes').onclick = saveNotes;

  // Review Docs button
  const btnDocs = document.getElementById('btn-open-docs');
  btnDocs.style.display = 'inline-block';
  if (job.resume_path && job.resume_path.trim() !== '') {
    btnDocs.disabled = false;
    btnDocs.style.opacity = '1';
    btnDocs.style.cursor = 'pointer';
    btnDocs.title = 'Review tailored documents';
  } else {
    btnDocs.disabled = true;
    btnDocs.style.opacity = '0.5';
    btnDocs.style.cursor = 'not-allowed';
    btnDocs.title = 'Tailor a resume first to review docs';
  }

  modal.classList.add('active');
}

async function saveFollowUp() {
  if (!currentJob) return;
  const btn = document.getElementById('btn-save-follow-up');
  const dateVal = document.getElementById('modal-follow-up').value;
  btn.disabled = true;
  btn.innerText = 'Saving...';
  try {
    await fetch(`/api/jobs/${currentJob.id}/follow-up`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ follow_up_date: dateVal })
    });
    const idx = jobs.findIndex(j => j.id === currentJob.id);
    if (idx !== -1) jobs[idx].follow_up_date = dateVal;
    currentJob.follow_up_date = dateVal;
    btn.innerText = 'Saved! ✓';
    setTimeout(() => { btn.innerText = 'Save'; btn.disabled = false; }, 2000);
    renderBoard();
  } catch (err) {
    alert('API error saving follow-up date.');
    btn.innerText = 'Save';
    btn.disabled = false;
  }
}

async function saveNotes() {
  if (!currentJob) return;
  const btn = document.getElementById('btn-save-notes');
  const newNotes = document.getElementById('modal-job-notes').value;
  btn.disabled = true;
  btn.innerText = 'Saving...';
  try {
    const res = await fetch(`/api/jobs/${currentJob.id}/notes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: newNotes })
    });
    const data = await res.json();
    if (data.success) {
      btn.innerText = 'Saved! ✓';
      setTimeout(() => { btn.innerText = '💾 Save Notes'; btn.disabled = false; }, 2000);
      const idx = jobs.findIndex(j => j.id === currentJob.id);
      if (idx !== -1) jobs[idx].notes = newNotes;
      currentJob.notes = newNotes;
      renderBoard();
    } else {
      alert('Failed to save notes.');
      btn.innerText = '💾 Save Notes';
      btn.disabled = false;
    }
  } catch (err) {
    alert('API error saving notes.');
    btn.innerText = '💾 Save Notes';
    btn.disabled = false;
  }
}

// ── Docs Editor ───────────────────────────────────────────────────────────────
let currentDocs = { resume: '', cover: '', artifacts: '' };
let activeDocTab = 'resume';

async function openDocsEditor(job) {
  const docsModal = document.getElementById('docs-modal');
  docsModal.classList.add('active');
  document.getElementById('doc-editor').value = 'Loading documents...';

  try {
    const res = await fetch(`/api/jobs/${job.id}/files`);
    const data = await res.json();
    if (data.success) {
      currentDocs.resume    = data.resume || '';
      currentDocs.cover     = data.cover_seed || '';
      currentDocs.artifacts = data.artifacts || '';
      document.getElementById('doc-editor').value = currentDocs[activeDocTab];
    } else {
      document.getElementById('doc-editor').value = 'Error loading files.';
    }
  } catch (e) {
    document.getElementById('doc-editor').value = 'API error loading files.';
  }
}

// Docs tabs
document.getElementById('tab-resume').onclick = () => switchDocTab('resume');
document.getElementById('tab-cover').onclick   = () => switchDocTab('cover');
document.getElementById('tab-artifacts').onclick = () => switchDocTab('artifacts');

function switchDocTab(tab) {
  activeDocTab = tab;
  ['resume', 'cover', 'artifacts'].forEach(t => {
    document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
  });
  document.getElementById('doc-editor').value = currentDocs[tab];
}

document.getElementById('doc-editor').addEventListener('input', (e) => {
  currentDocs[activeDocTab] = e.target.value;
});

// ── Diff View ─────────────────────────────────────────────────────────────────
document.getElementById('btn-diff').onclick = async () => {
  try {
    const res = await fetch('/api/base-resume');
    const data = await res.json();
    if (!data.success || !data.content) {
      alert('Base resume not found. Make sure data/base_resume.md exists.');
      return;
    }
    openDiffView(data.content, currentDocs[activeDocTab]);
  } catch (e) {
    alert('Error loading base resume for comparison.');
  }
};

function openDiffView(baseText, currentText) {
  const diffModal = document.getElementById('diff-modal');
  const baseEl    = document.getElementById('diff-base');
  const curEl     = document.getElementById('diff-current');

  const baseLines = baseText.split('\n');
  const curLines  = currentText.split('\n');
  const diff      = computeLineDiff(baseLines, curLines);

  baseEl.innerHTML  = '';
  curEl.innerHTML   = '';

  diff.forEach(({ type, base, current }) => {
    if (type === 'same') {
      appendDiffLine(baseEl, base, 'same');
      appendDiffLine(curEl, current, 'same');
    } else if (type === 'removed') {
      appendDiffLine(baseEl, base, 'removed');
    } else if (type === 'added') {
      appendDiffLine(curEl, current, 'added');
    }
  });

  diffModal.classList.add('active');
}

function appendDiffLine(container, text, type) {
  const span = document.createElement('span');
  span.className = `diff-line-${type}`;
  span.textContent = text;
  container.appendChild(span);
}

// Simple LCS-based line diff (O(n*m), capped at 200 lines each)
function computeLineDiff(oldLines, newLines) {
  const A = oldLines.slice(0, 200);
  const B = newLines.slice(0, 200);
  const m = A.length, n = B.length;

  // Build LCS table
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = A[i - 1] === B[j - 1]
        ? dp[i - 1][j - 1] + 1
        : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  // Backtrack
  const result = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && A[i - 1] === B[j - 1]) {
      result.push({ type: 'same', base: A[i - 1], current: B[j - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.push({ type: 'added', base: '', current: B[j - 1] });
      j--;
    } else {
      result.push({ type: 'removed', base: A[i - 1], current: '' });
      i--;
    }
  }
  return result.reverse();
}

// ── Image Attachment ──────────────────────────────────────────────────────────
const imageInput = document.getElementById('chat-image');
const imageInfo  = document.getElementById('attached-image-info');
imageInput.addEventListener('change', () => {
  if (imageInput.files.length > 0) {
    imageInfo.style.display = 'block';
    imageInfo.innerText = `📎 Attached: ${imageInput.files[0].name}`;
  } else {
    imageInfo.style.display = 'none';
  }
});

// ── Chat ──────────────────────────────────────────────────────────────────────
document.getElementById('btn-send-chat').onclick = async () => {
  const inputEl   = document.getElementById('chat-input');
  const msg       = inputEl.value.trim();
  if (!msg || !currentJob) return;

  const historyEl = document.getElementById('chat-history');
  historyEl.innerHTML += `<div style="background:rgba(59,130,246,0.1); border-left:2px solid var(--accent); padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>You:</strong> ${msg}</div>`;
  inputEl.value = '';
  historyEl.scrollTop = historyEl.scrollHeight;

  const thEl = document.createElement('div');
  thEl.style.cssText = 'padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem; font-style:italic; color:var(--text-muted);';
  thEl.innerText = 'Gemini is rewriting...';
  historyEl.appendChild(thEl);
  historyEl.scrollTop = historyEl.scrollHeight;

  let base64Image = null, mimeType = null;
  if (imageInput.files.length > 0) {
    const file = imageInput.files[0];
    mimeType = file.type;
    base64Image = await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.readAsDataURL(file);
    });
  }

  try {
    const res = await fetch(`/api/jobs/${currentJob.id}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instruction: msg,
        document: currentDocs[activeDocTab],
        doc_type: activeDocTab,
        image: base64Image,
        image_mime_type: mimeType
      })
    });
    const data = await res.json();
    historyEl.removeChild(thEl);
    imageInput.value = '';
    imageInfo.style.display = 'none';

    if (data.success) {
      currentDocs[activeDocTab] = data.document;
      document.getElementById('doc-editor').value = data.document;
      historyEl.innerHTML += `<div style="background:rgba(16,185,129,0.1); border-left:2px solid #10b981; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>AI:</strong> Updated the document! Review the changes on the left.</div>`;
    } else {
      historyEl.innerHTML += `<div style="color:#ef4444; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>Error:</strong> Failed to edit document.</div>`;
    }
  } catch (err) {
    historyEl.removeChild(thEl);
    historyEl.innerHTML += `<div style="color:#ef4444; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>Error:</strong> API Request failed.</div>`;
  }
  historyEl.scrollTop = historyEl.scrollHeight;
};

document.getElementById('chat-input').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-send-chat').click();
});

// ── Save / Export ─────────────────────────────────────────────────────────────
document.getElementById('btn-save-doc').onclick = async (e) => {
  if (!currentJob) return;
  const btn = e.target;
  btn.disabled = true;
  btn.innerText = 'Saving...';
  try {
    const res = await fetch(`/api/jobs/${currentJob.id}/save-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_type: activeDocTab, content: currentDocs[activeDocTab] })
    });
    const data = await res.json();
    if (data.success) {
      btn.innerText = 'Saved! ✓';
      setTimeout(() => { btn.innerText = '💾 Save File'; }, 2000);
    } else {
      alert('Failed to save file.');
      btn.innerText = '💾 Save File';
    }
  } catch (err) {
    alert('API error saving file.');
    btn.innerText = '💾 Save File';
  }
  btn.disabled = false;
};

document.getElementById('btn-export-pdf').onclick = async (e) => {
  if (!currentJob) return;
  const btn = e.target;
  btn.disabled = true;
  btn.innerText = 'Generating PDF...';
  try {
    const res = await fetch(`/api/jobs/${currentJob.id}/export-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: currentDocs[activeDocTab] })
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = window.URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.style.display = 'none';
      a.href     = url;
      a.download = `${activeDocTab}_${(currentJob.company || 'resume').replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      alert('Failed to generate PDF.');
    }
  } catch (err) {
    alert('API error exporting PDF.');
  }
  btn.disabled = false;
  btn.innerText = '📥 Export PDF';
};
