// Requests page — kanban-style list grouped by status. Single source of
// truth is the backend (/api/requests); we re-fetch after every mutation
// rather than maintain a parallel client-side cache.

const API = 'http://100.69.184.113:8091';
const STATUSES = ['Backlog', 'Requested', 'In Progress', 'Done'];
const STATUS_CLASS = { 'Backlog': 'status-Backlog', 'Requested': 'status-Requested',
                       'In Progress': 'status-InProgress', 'Done': 'status-Done' };

const $ = (sel) => document.querySelector(sel);
const esc = (s) => (s == null ? '' : String(s)).replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtDate = (ms) => {
    if (!ms) return '';
    const d = new Date(ms);
    const today = new Date();
    const sameDay = d.toDateString() === today.toDateString();
    return sameDay
        ? d.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})
        : d.toLocaleDateString([], {month: 'short', day: 'numeric'});
};

let _items = [];
let _editingId = null;   // null = creating new, string = editing existing

async function loadAll() {
    try {
        const res = await fetch(`${API}/api/requests`, {cache: 'no-store'});
        const data = await res.json();
        _items = data.items || [];
    } catch (e) {
        console.error('Failed to load requests:', e);
        _items = [];
    }
    render();
}

function render() {
    const container = $('#container');
    if (_items.length === 0) {
        container.innerHTML = '<div class="empty">No requests yet. Tap + to add one.</div>';
        return;
    }
    const groups = {};
    STATUSES.forEach(s => groups[s] = []);
    _items.forEach(it => {
        const s = STATUSES.includes(it.status) ? it.status : 'Backlog';
        groups[s].push(it);
    });
    const html = STATUSES.map(status => {
        const items = groups[status];
        if (items.length === 0) return '';
        const cards = items.map(it => `
            <div class="req-card ${STATUS_CLASS[status]}" data-id="${esc(it.id)}">
                <div class="req-title">${esc(it.title)}</div>
                <div class="req-meta">
                    <span>${esc(fmtDate(it.updated))}</span>
                    ${it.comments && it.comments.length ? `<span>💬 ${it.comments.length}</span>` : ''}
                </div>
            </div>`).join('');
        return `<div class="group-header">${esc(status)} <span class="count">${items.length}</span></div>${cards}`;
    }).join('');
    container.innerHTML = html;
    container.querySelectorAll('.req-card').forEach(el => {
        el.addEventListener('click', () => openDetail(el.dataset.id));
    });
}

function openDetail(id) {
    _editingId = id;
    const item = id ? _items.find(it => it.id === id) : null;
    const isNew = !item;
    $('#detail-title').textContent = isNew ? 'New Request' : 'Edit Request';
    $('#detail-delete').style.display = isNew ? 'none' : '';
    const cur = item || {title: '', body: '', status: 'Backlog', comments: []};
    const statusOpts = STATUSES.map(s =>
        `<option value="${s}"${s === cur.status ? ' selected' : ''}>${s}</option>`).join('');
    const commentsHtml = (cur.comments || []).map(c => `
        <div class="comment">
            <div class="c-meta"><span>${esc(c.author || 'user')}</span><span>${esc(fmtDate(c.ts))}</span></div>
            <div class="c-text">${esc(c.text)}</div>
        </div>`).join('');
    $('#detail-body').innerHTML = `
        <div class="field-label">Title</div>
        <input class="field-input" id="f-title" type="text" value="${esc(cur.title)}" placeholder="Short summary">
        <div class="field-label">Status</div>
        <select class="field-select" id="f-status">${statusOpts}</select>
        <div class="field-label">Description</div>
        <textarea class="field-textarea" id="f-body" placeholder="More detail (optional)">${esc(cur.body)}</textarea>
        <div class="row-buttons">
            <button class="btn btn-primary" id="f-save">${isNew ? 'Create' : 'Save'}</button>
        </div>
        ${isNew ? '' : `
            <div class="field-label">Comments (${(cur.comments || []).length})</div>
            <div id="comments-list">${commentsHtml || '<div class="empty" style="padding:16px 0;">No comments yet.</div>'}</div>
            <div class="field-label">Add comment</div>
            <div class="comment-composer">
                <textarea class="field-textarea" id="f-comment" placeholder="Reply / iterate…"></textarea>
                <button class="btn btn-primary" id="f-comment-send">Post</button>
            </div>
        `}
    `;
    $('#f-save').addEventListener('click', saveDetail);
    if (!isNew) {
        $('#f-comment-send').addEventListener('click', postComment);
    }
    $('#detail-overlay').classList.add('open');
}

function closeDetail() {
    $('#detail-overlay').classList.remove('open');
    _editingId = null;
}

async function saveDetail() {
    const title = $('#f-title').value.trim();
    if (!title) { alert('Title is required.'); return; }
    const body = $('#f-body').value;
    const status = $('#f-status').value;
    try {
        if (_editingId) {
            await fetch(`${API}/api/requests/${_editingId}`, {
                method: 'PUT', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, body, status})
            });
        } else {
            await fetch(`${API}/api/requests`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, body, status})
            });
        }
    } catch (e) { alert('Save failed: ' + e); return; }
    closeDetail();
    loadAll();
}

async function postComment() {
    const text = $('#f-comment').value.trim();
    if (!text || !_editingId) return;
    try {
        const res = await fetch(`${API}/api/requests/${_editingId}/comments`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text})
        });
        const updated = await res.json();
        // Refresh in-memory item and re-render detail to show new comment.
        const i = _items.findIndex(it => it.id === _editingId);
        if (i >= 0) _items[i] = updated;
        openDetail(_editingId);
    } catch (e) { alert('Failed to post: ' + e); }
}

async function deleteDetail() {
    if (!_editingId) { closeDetail(); return; }
    if (!confirm('Delete this request? This cannot be undone.')) return;
    try {
        await fetch(`${API}/api/requests/${_editingId}`, {method: 'DELETE'});
    } catch (e) { alert('Delete failed: ' + e); return; }
    closeDetail();
    loadAll();
}

$('#back-btn').addEventListener('click', () => { window.location.href = '/'; });
$('#new-btn').addEventListener('click', () => openDetail(null));
$('#detail-back').addEventListener('click', closeDetail);
$('#detail-delete').addEventListener('click', deleteDetail);

loadAll();
