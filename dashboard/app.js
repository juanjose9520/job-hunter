// State
let jobs = [];
let currentJob = null;

// DOM
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

// Init
document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  loadSkills();

  // Tabs
  tabs.forEach(t => t.addEventListener('click', (e) => {
    tabs.forEach(btn => btn.classList.remove('active'));
    Object.values(views).forEach(v => {
      if (v) v.classList.remove('active');
    });
    e.target.classList.add('active');
    const targetView = views[e.target.dataset.target];
    if (targetView) targetView.classList.add('active');
  }));

  // Discover Button
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
      } catch (err) {
        alert('Error running discovery.');
      }
      btn.disabled = false;
      btn.innerHTML = '<span class="icon">🔍</span> Discover New Jobs';
    });
  }

  // Modal actions
  document.querySelector('.close-btn').onclick = () => { modal.classList.remove('active'); };
  document.getElementById('btn-close-docs').onclick = () => { document.getElementById('docs-modal').classList.remove('active'); };

  window.onclick = (e) => {
    if (e.target == modal) modal.classList.remove('active');
    if (e.target == document.getElementById('docs-modal')) document.getElementById('docs-modal').classList.remove('active');
  };

  document.getElementById('btn-open-link').onclick = () => {
    if (currentJob) window.open(currentJob.url, '_blank');
  };

  // Archive filters
  document.getElementById('archive-filter-domain').addEventListener('change', renderBoard);
  document.getElementById('archive-filter-date').addEventListener('change', renderBoard);

  // Save Notes Button
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

  // Save Description Button
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
          // Update local state so it doesn't revert if modal is closed and reopened
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
        loadJobs();
        modal.classList.remove('active');
      } catch (err) { alert('API error shortlisting.'); }
      btn.disabled = false;
    };
  }

  const btnTailor = document.getElementById('btn-tailor');
  if (btnTailor) {
    btnTailor.onclick = async (e) => {
      if (!currentJob) return;
      const btn = e.target;
      btn.disabled = true;
      btn.innerText = 'Tailoring...';

      // Auto-shortlist
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
          currentJob.resume_path = data.path; // Update local state so button shows
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

  const btnOpenDocs = document.getElementById('btn-open-docs');
  if (btnOpenDocs) {
    btnOpenDocs.addEventListener('click', (e) => {
      e.preventDefault();
      if (!currentJob) return;
      
      // Explicitly hide the job modal
      document.getElementById('job-modal').classList.remove('active');
      
      // Open the docs editor modal
      openDocsEditor(currentJob);
    });
  }

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
          // Remove from local state
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

// Loaders
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

// Kanban Render
function renderBoard() {
  // Clear columns
  Object.values(cols).forEach(c => { if (c) c.innerHTML = ''; });
  const counts = { new: 0, shortlisted: 0, applied: 0, closed: 0, graveyard: 0 };

  const filterDomain = document.getElementById('archive-filter-domain').value;
  const filterDate = document.getElementById('archive-filter-date').value;

  jobs.forEach(job => {
    let status = job.status || 'new';

    // Auto-graveyard logic based on time
    if (status === 'archived' || status === 'closed') {
      if (job.discovered_at) {
        const jobDate = new Date(job.discovered_at);
        const diffDays = (new Date() - jobDate) / (1000 * 60 * 60 * 24);
        if (diffDays > 3) status = 'graveyard';
        else status = 'closed';
      } else {
        status = 'closed';
      }
    } else if (status === 'applied') {
      if (job.discovered_at) {
        const jobDate = new Date(job.discovered_at);
        const diffDays = (new Date() - jobDate) / (1000 * 60 * 60 * 24);
        if (diffDays > 15) status = 'graveyard';
      }
    }

    if (!cols[status]) return; // ignore if column doesn't exist

    // Apply filters to closed column ONLY
    if (status === 'closed') {
      // Health Domain Filter
      if (filterDomain === 'health') {
        try {
          const bd = JSON.parse(job.score_breakdown || '{}');
          if (!bd.healthcare || bd.healthcare <= 0) return; // Skip if no health score
        } catch (e) { return; } // Skip if no breakdown available
      }

      // Date Filter (Last 2 days)
      if (filterDate === 'new' && job.discovered_at) {
        const jobDate = new Date(job.discovered_at);
        const twoDaysAgo = new Date();
        twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
        if (jobDate < twoDaysAgo) return; // Skip if older than 2 days
      }
    }

    counts[status]++;
    const scoreColor = job.score >= 80 ? 'score-high' : 'score-med';
    let salHTML = '';
    if (job.salary_monthly) {
      salHTML = `<div class="job-sal">~$${Math.round(job.salary_monthly).toLocaleString()}/mo</div>`;
    }

    const card = document.createElement('div');
    card.className = 'job-card';
    card.draggable = true;
    card.dataset.id = job.id;
    card.innerHTML = `
      <div class="job-score ${scoreColor}">${job.score}/100</div>
      <div class="job-title">${job.title}</div>
      <div class="job-company">${job.company || job.board}</div>
      ${salHTML}
    `;

    // Drag handlers
    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', job.id);
      setTimeout(() => card.classList.add('dragging'), 0);
    });
    card.addEventListener('dragend', () => card.classList.remove('dragging'));

    // Click handler
    card.addEventListener('click', () => openModal(job));

    cols[status].appendChild(card);
  });

  // Update counters
  Object.keys(counts).forEach(k => {
    counters[k].innerText = counts[k];
  });
}

// Drag/Drop logic
function allowDrop(ev) { ev.preventDefault(); }
async function drop(ev, newStatus) {
  ev.preventDefault();
  const id = parseInt(ev.dataTransfer.getData('text/plain'));
  const job = jobs.find(j => j.id === id);
  if (job && job.status !== newStatus) {
    job.status = newStatus;
    renderBoard(); // optimistic UI
    await fetch(`/api/jobs/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
  }
}

// Modal
function openModal(job) {
  currentJob = job;
  const body = document.getElementById('modal-body');
  let bdHTML = '';
  try {
    const bd = JSON.parse(job.score_breakdown || '{}');
    bdHTML = Object.entries(bd).map(([k, v]) => `<span style="display:inline-block; padding:2px 6px; background:#334155; border-radius:4px; margin:2px 4px 2px 0; font-size:0.8rem">${k}: ${v}</span>`).join('');
  } catch (e) { }

  body.innerHTML = `
    <h2 style="margin-bottom:0.5rem">${job.title}</h2>
    <h4 style="color:var(--text-muted); margin-bottom:1rem">${job.company || ''} · ${job.board}</h4>
    
    <div style="display:flex; gap:1rem; margin-bottom:1rem">
      <div class="job-score ${job.score >= 80 ? 'score-high' : 'score-med'}" style="font-size:1.2rem; padding:4px 12px">Score: ${job.score}/100</div>
    </div>
    
    <div style="margin-bottom:1rem">
      ${bdHTML}
    </div>
    
    <p style="color:var(--text-main); font-size:0.95rem; border-left:3px solid var(--accent); padding-left:1rem; margin-bottom:1rem">
      <em>${job.notes || 'No notes yet.'}</em>
    </p>

    <h4 style="margin-bottom:0.5rem">Job Description</h4>
    <textarea id="modal-job-desc" class="jd-block" style="width:100%; min-height:300px; resize:vertical; background:var(--bg-col); border:1px solid var(--border); color:var(--text-main); padding:1rem; border-radius:6px;">${job.description || 'Description not fetched.'}</textarea>
  `;

  // Show "Review Docs" button always, but grey it out if no docs
  const btnDocs = document.getElementById('btn-open-docs');
  btnDocs.style.display = 'inline-block'; // always visible now

  if (job.resume_path && job.resume_path.trim() !== '') {
    btnDocs.disabled = false;
    btnDocs.style.opacity = '1';
    btnDocs.style.cursor = 'pointer';
    btnDocs.title = "Review tailored documents";
  } else {
    btnDocs.disabled = true;
    btnDocs.style.opacity = '0.5';
    btnDocs.style.cursor = 'not-allowed';
    btnDocs.title = "Tailor a resume first to review docs";
  }

  modal.classList.add('active');
}

// Docs Editor State
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
      currentDocs.resume = data.resume || '';
      currentDocs.cover = data.cover_seed || '';
      currentDocs.artifacts = data.artifacts || '';
      document.getElementById('doc-editor').value = currentDocs[activeDocTab];
    } else {
      document.getElementById('doc-editor').value = 'Error loading files.';
    }
  } catch (e) {
    document.getElementById('doc-editor').value = 'API error loading files.';
  }
}

// Docs Tabs logic
document.getElementById('tab-resume').onclick = (e) => {
  activeDocTab = 'resume';
  document.getElementById('tab-resume').classList.add('active');
  document.getElementById('tab-cover').classList.remove('active');
  document.getElementById('tab-artifacts').classList.remove('active');
  document.getElementById('doc-editor').value = currentDocs.resume;
};

document.getElementById('tab-cover').onclick = (e) => {
  activeDocTab = 'cover';
  document.getElementById('tab-cover').classList.add('active');
  document.getElementById('tab-resume').classList.remove('active');
  document.getElementById('tab-artifacts').classList.remove('active');
  document.getElementById('doc-editor').value = currentDocs.cover;
};

document.getElementById('tab-artifacts').onclick = (e) => {
  activeDocTab = 'artifacts';
  document.getElementById('tab-artifacts').classList.add('active');
  document.getElementById('tab-resume').classList.remove('active');
  document.getElementById('tab-cover').classList.remove('active');
  document.getElementById('doc-editor').value = currentDocs.artifacts;
};

// Update active doc state as user types
document.getElementById('doc-editor').addEventListener('input', (e) => {
  currentDocs[activeDocTab] = e.target.value;
});

// Image Attachment Logic
const imageInput = document.getElementById('chat-image');
const imageInfo = document.getElementById('attached-image-info');
imageInput.addEventListener('change', () => {
  if (imageInput.files.length > 0) {
    imageInfo.style.display = 'block';
    imageInfo.innerText = `📎 Attached: ${imageInput.files[0].name}`;
  } else {
    imageInfo.style.display = 'none';
  }
});

// Chat Logic
document.getElementById('btn-send-chat').onclick = async () => {
  const inputEl = document.getElementById('chat-input');
  const msg = inputEl.value.trim();
  if (!msg || !currentJob) return;

  const historyEl = document.getElementById('chat-history');

  // Append user message
  historyEl.innerHTML += `<div style="background:rgba(59,130,246,0.1); border-left:2px solid var(--accent); padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>You:</strong> ${msg}</div>`;
  inputEl.value = '';
  historyEl.scrollTop = historyEl.scrollHeight;

  // Append thinking
  const thEl = document.createElement('div');
  thEl.style.cssText = "padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem; font-style:italic; color:var(--text-muted);";
  thEl.innerText = "Gemini is rewriting...";
  historyEl.appendChild(thEl);
  historyEl.scrollTop = historyEl.scrollHeight;

  let base64Image = null;
  let mimeType = null;
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
    
    // Clear image
    imageInput.value = '';
    imageInfo.style.display = 'none';

    if (data.success) {
      currentDocs[activeDocTab] = data.document;
      document.getElementById('doc-editor').value = data.document;
      historyEl.innerHTML += `<div style="background:rgba(16,185,129,0.1); border-left:2px solid #10b981; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>AI:</strong> Updated the document! You can review the changes on the left.</div>`;
    } else {
      historyEl.innerHTML += `<div style="color:#ef4444; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>Error:</strong> Failed to edit document.</div>`;
    }
  } catch (err) {
    historyEl.removeChild(thEl);
    historyEl.innerHTML += `<div style="color:#ef4444; padding:0.5rem; margin-bottom:0.5rem; font-size:0.9rem;"><strong>Error:</strong> API Request failed.</div>`;
  }
  historyEl.scrollTop = historyEl.scrollHeight;
};

// Allow Enter key in chat input
document.getElementById('chat-input').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') document.getElementById('btn-send-chat').click();
});

// Save Document to Disk Logic
document.getElementById('btn-save-doc').onclick = async (e) => {
  if (!currentJob) return;
  const btn = e.target;
  btn.disabled = true;
  btn.innerText = 'Saving...';

  try {
    const res = await fetch(`/api/jobs/${currentJob.id}/save-file`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        doc_type: activeDocTab,
        content: currentDocs[activeDocTab]
      })
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

// Export PDF Logic
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
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${activeDocTab}_${currentJob.company.replace(/\\s+/g, '_')}.pdf`;
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
