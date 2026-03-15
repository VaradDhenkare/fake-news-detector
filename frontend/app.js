/**
 * app.js — TruthLens v2  (Text + URL + Live Feed)
 * ─────────────────────────────────────────────────────────────
 * API_BASE → Spring Boot :8080
 *
 * Features:
 *   1. Register / Login (JWT)
 *   2. Analyze text    POST /api/news/predict
 *   3. Analyze URL     POST /api/news/analyze-url
 *   4. Live Feed       GET  /api/news/live-feed
 *   5. History         GET  /api/news/history  (paginated)
 *   6. Delete          DELETE /api/news/history/{id}
 */

const API_BASE = 'http://localhost:8080';

// ── Storage ───────────────────────────────────────────────────────────────────
const store = {
  get token() { return localStorage.getItem('fn_token'); },
  set token(v) { localStorage.setItem('fn_token', v); },
  get username() { return localStorage.getItem('fn_username'); },
  set username(v) { localStorage.setItem('fn_username', v); },
  clear() { localStorage.removeItem('fn_token'); localStorage.removeItem('fn_username'); }
};

// ── HTTP client ───────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (store.token) headers['Authorization'] = `Bearer ${store.token}`;
  const res = await fetch(API_BASE + path, { ...opts, headers });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { message: text }; }
  if (!res.ok) {
    const msg = data.message || data.error || `HTTP ${res.status}`;
    throw Object.assign(new Error(msg), { status: res.status, data });
  }
  return data;
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let _toastTimer;
function showToast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type} show`;
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => { el.className = 'toast'; }, 3400);
}

// ── Button spinner ────────────────────────────────────────────────────────────
function setLoading(btn, on) {
  const txt = btn.querySelector('.btn-text');
  const sp = btn.querySelector('.btn-spinner');
  btn.disabled = on;
  if (txt) txt.hidden = on;
  if (sp) sp.hidden = !on;
}

// ── DOM helpers ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const show = (id, d = 'block') => { const el = $(id); if (el) el.style.display = d; };
const hide = id => { const el = $(id); if (el) el.style.display = 'none'; };
const showEl = el => { if (el) el.hidden = false; };
const hideEl = el => { if (el) el.hidden = true; };

// ═════════════════════════════════════════════════════════════════════════════
// APP
// ═════════════════════════════════════════════════════════════════════════════
const App = {

  _historyPage: 0,
  _historyTotalPages: 1,
  _inputMode: 'text', // 'text' | 'url'

  // ── Init ────────────────────────────────────────────────────────────────────
  init() {
    if (store.token) this._enterApp();

    const ta = $('news-input');
    if (ta) ta.addEventListener('input', () => { $('char-count').textContent = ta.value.length; });
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // AUTH
  // ═══════════════════════════════════════════════════════════════════════════
  switchAuthTab(tab) {
    $('tab-login').classList.toggle('active', tab === 'login');
    $('tab-register').classList.toggle('active', tab === 'register');
    $('login-form').style.display = tab === 'login' ? 'flex' : 'none';
    $('register-form').style.display = tab === 'register' ? 'flex' : 'none';
  },

  async handleLogin(e) {
    e.preventDefault();
    const btn = $('login-btn');
    const errEl = $('login-error');
    hideEl(errEl); setLoading(btn, true);
    try {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: $('login-username').value.trim(),
          password: $('login-password').value,
        })
      });
      store.token = data.token;
      store.username = data.username;
      this._enterApp();
      showToast(`Welcome back, ${data.username}! 👋`, 'success');
    } catch (err) {
      errEl.textContent = err.message;
      showEl(errEl);
    } finally { setLoading(btn, false); }
  },

  async handleRegister(e) {
    e.preventDefault();
    const btn = $('register-btn');
    const errEl = $('register-error');
    const succEl = $('register-success');
    hideEl(errEl); hideEl(succEl); setLoading(btn, true);
    try {
      await api('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          username: $('reg-username').value.trim(),
          email: $('reg-email').value.trim(),
          password: $('reg-password').value,
        })
      });
      succEl.textContent = '✅ Account created! Please sign in.';
      showEl(succEl);
      setTimeout(() => this.switchAuthTab('login'), 1400);
    } catch (err) {
      errEl.textContent = err.message;
      showEl(errEl);
    } finally { setLoading(btn, false); }
  },

  logout() {
    store.clear();
    hide('app-screen');
    show('auth-screen', 'flex');
    $('login-username').value = '';
    $('login-password').value = '';
    showToast('Signed out.', 'info');
  },

  _enterApp() {
    hide('auth-screen');
    show('app-screen');
    $('nav-username').textContent = store.username || 'User';
    this.switchTab('analyze');
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // TAB SWITCHING
  // ═══════════════════════════════════════════════════════════════════════════
  switchTab(tab) {
    ['analyze', 'livefeed', 'history'].forEach(t => {
      $(`nav-${t}`)?.classList.toggle('active', t === tab);
      const el = $(`tab-${t}`);
      if (el) el.style.display = t === tab ? 'block' : 'none';
    });
    if (tab === 'history') { this._historyPage = 0; this.loadHistory(); }
    if (tab === 'livefeed') { /* user clicks Refresh manually */ }
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // INPUT MODE TOGGLE  (Text / URL)
  // ═══════════════════════════════════════════════════════════════════════════
  switchInputMode(mode) {
    this._inputMode = mode;
    $('mode-text').classList.toggle('active', mode === 'text');
    $('mode-url').classList.toggle('active', mode === 'url');
    $('analyze-form').style.display = mode === 'text' ? 'flex' : 'none';
    $('url-form').style.display = mode === 'url' ? 'flex' : 'none';
    $('result-area').innerHTML = '';
  },

  clearAnalyze() {
    $('news-input').value = '';
    $('char-count').textContent = '0';
    $('url-input') && ($('url-input').value = '');
    $('result-area').innerHTML = '';
    hideEl($('analyze-error'));
    hideEl($('url-error'));
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // PREDICT — text
  // ═══════════════════════════════════════════════════════════════════════════
  async handlePredict(e) {
    e.preventDefault();
    const btn = $('analyze-btn');
    const errEl = $('analyze-error');
    const newsText = $('news-input').value.trim();
    hideEl(errEl);

    this._renderResult({ state: 'checking', newsText, prediction: 'Checking…', confidence: null });
    setLoading(btn, true);

    try {
      const data = await api('/api/news/predict', {
        method: 'POST', body: JSON.stringify({ newsText })
      });
      this._renderResult({
        state: data.prediction.toLowerCase(),
        newsText,
        prediction: data.prediction,
        confidence: data.confidence,
      });
      this._showVerifyToast(data.prediction);
    } catch (err) {
      $('result-area').innerHTML = '';
      errEl.textContent = this._apiErrMsg(err);
      showEl(errEl);
      if (err.status === 401) setTimeout(() => this.logout(), 2000);
    } finally { setLoading(btn, false); }
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // PREDICT — URL
  // ═══════════════════════════════════════════════════════════════════════════
  async handleUrlAnalyze(e) {
    e.preventDefault();
    const btn = $('url-btn');
    const errEl = $('url-error');
    const url = $('url-input').value.trim();
    hideEl(errEl);

    this._renderResult({ state: 'checking', newsText: url, prediction: 'Analyzing URL…', confidence: null, isUrl: true });
    setLoading(btn, true);

    try {
      const data = await api('/api/news/analyze-url', {
        method: 'POST', body: JSON.stringify({ url })
      });
      this._renderResult({
        state: data.prediction.toLowerCase(),
        newsText: data.newsText,
        prediction: data.prediction,
        confidence: data.confidence,
        articleTitle: data.articleTitle,
        sourceName: data.sourceName,
        sourceUrl: data.sourceUrl,
        isUrl: true,
      });
      this._showVerifyToast(data.prediction);
    } catch (err) {
      $('result-area').innerHTML = '';
      errEl.textContent = this._apiErrMsg(err, true);
      showEl(errEl);
      if (err.status === 401) setTimeout(() => this.logout(), 2000);
    } finally { setLoading(btn, false); }
  },

  // ── Render analysis result card ───────────────────────────────────────────
  _renderResult({ state, newsText, prediction, confidence, articleTitle, sourceName, sourceUrl, isUrl }) {
    const icons = { real: '✅', fake: '⚠️', checking: '🔄' };
    const labels = { real: 'Verdict', fake: 'Verdict', checking: 'Analyzing' };
    const pct = confidence != null ? Math.round(confidence * 100) : 0;
    const snippet = (newsText || '').length > 160 ? newsText.slice(0, 160) + '…' : (newsText || '');

    const confHtml = state !== 'checking' ? `
      <div class="confidence-row">
        <div class="confidence-label">
          <span>Confidence</span><span>${pct}%</span>
        </div>
        <div class="confidence-bar-bg">
          <div class="confidence-bar-fill" id="conf-fill" style="width:0%"></div>
        </div>
      </div>` : `
      <div class="confidence-row">
        <div class="confidence-label"><span>Please wait…</span></div>
        <div class="confidence-bar-bg">
          <div class="confidence-bar-fill skeleton" style="width:55%"></div>
        </div>
      </div>`;

    const sourceRow = sourceName ? `
      <div class="result-source-row">
        <span class="source-chip">📰 ${sourceName}</span>
      </div>` : '';
    const titleRow = articleTitle ? `<div class="result-title">${articleTitle}</div>` : '';
    const linkRow = sourceUrl && state !== 'checking' ? `<a class="result-link" href="${sourceUrl}" target="_blank" rel="noopener">🔗 View original article</a>` : '';

    $('result-area').innerHTML = `
      <div class="result-card ${state}">
        <div class="result-header">
          <div class="result-icon">${icons[state]}</div>
          <div class="result-meta">
            <div class="result-label">${labels[state]}</div>
            <div class="result-verdict">${prediction}</div>
          </div>
          ${state !== 'checking'
        ? `<span class="badge badge-${state}">${prediction}</span>`
        : `<span class="badge badge-check">⏳ Checking</span>`}
        </div>
        ${sourceRow}
        ${titleRow}
        ${confHtml}
        <div class="result-snippet">"${snippet}"</div>
        ${linkRow}
      </div>`;

    if (state !== 'checking') {
      requestAnimationFrame(() => requestAnimationFrame(() => {
        const fill = $('conf-fill');
        if (fill) fill.style.width = pct + '%';
      }));
    }
  },

  _showVerifyToast(prediction) {
    showToast(
      prediction === 'REAL' ? '✅ Likely Credible' : '⚠️ Likely Fake — Verify with another source',
      prediction === 'REAL' ? 'success' : 'error'
    );
  },

  _apiErrMsg(err, isUrl = false) {
    if (err.status === 401) return '🔒 Session expired. Logging you out…';
    if (err.status === 502) return '⚡ ML service is offline. Start ml_service/app.py first.';
    if (isUrl && err.message?.includes('timeout')) return '⏱ The article page took too long to respond. Try a different URL.';
    if (isUrl && err.message?.includes('Not enough')) return '⚠ Couldn\'t extract enough text from that URL. Try pasting text directly.';
    return '⚠ ' + (err.message || 'Unexpected error. Please try again.');
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // LIVE FEED
  // ═══════════════════════════════════════════════════════════════════════════
  async loadLiveFeed() {
    const btn = $('refresh-feed-btn');
    const loadEl = $('live-feed-loading');
    const errEl = $('live-feed-error');
    const statsEl = $('live-feed-stats');
    const listEl = $('live-feed-list');

    setLoading(btn, true);
    listEl.innerHTML = '';
    showEl(loadEl); hideEl(errEl); hideEl(statsEl);

    try {
      const data = await api('/api/news/live-feed?maxPerSource=5');
      hideEl(loadEl);

      const articles = data.articles || [];
      if (articles.length === 0) {
        listEl.innerHTML = `<div class="empty-state"><p class="empty-icon">📭</p><p>No articles found. Check your internet connection.</p></div>`;
        return;
      }

      // Stats bar
      const realCount = articles.filter(a => a.prediction === 'REAL').length;
      const fakeCount = articles.filter(a => a.prediction === 'FAKE').length;
      statsEl.innerHTML = `
        <div class="feed-stat">
          <span class="feed-stat-value">${articles.length}</span>
          <span class="feed-stat-label">Articles Fetched</span>
        </div>
        <div class="feed-stat">
          <span class="feed-stat-value real-val">${realCount}</span>
          <span class="feed-stat-label">Likely Real</span>
        </div>
        <div class="feed-stat">
          <span class="feed-stat-value fake-val">${fakeCount}</span>
          <span class="feed-stat-label">Likely Fake</span>
        </div>
        <div class="feed-stat">
          <span class="feed-stat-value">✅</span>
          <span class="feed-stat-label">Saved to History</span>
        </div>`;
      showEl(statsEl);

      listEl.innerHTML = articles.map(a => this._feedCardHtml(a)).join('');
      showToast(`📡 ${articles.length} articles analyzed & saved!`, 'success');

    } catch (err) {
      hideEl(loadEl);
      errEl.textContent = '⚠ ' + (err.message || 'Failed to load live feed.');
      showEl(errEl);
      if (err.status === 401) setTimeout(() => this.logout(), 2000);
    } finally { setLoading(btn, false); }
  },

  _feedCardHtml(article) {
    const state = (article.prediction || 'FAKE').toLowerCase();
    const pct = Math.round((article.confidence || 0) * 100);
    const icon = article.sourceIcon || '📰';
    const title = article.articleTitle || '(no title)';
    const summary = article.summary || '';
    const url = article.sourceUrl || '#';
    const badge = `<span class="badge badge-${state}">${article.prediction}</span>`;
    return `
      <div class="feed-card ${state}">
        <div class="feed-card-top"></div>
        <div class="feed-card-body">
          <div class="feed-card-header">
            <span class="feed-source-chip">${icon} ${article.sourceName || 'News'}</span>
            ${badge}
          </div>
          <div class="feed-card-title">${title}</div>
          ${summary ? `<div class="feed-card-summary">${summary}</div>` : ''}
          <div class="feed-card-footer">
            <span class="feed-conf">Confidence: ${pct}%</span>
            ${url !== '#' ? `<a class="feed-link" href="${url}" target="_blank" rel="noopener">Read →</a>` : ''}
          </div>
        </div>
      </div>`;
  },

  // ═══════════════════════════════════════════════════════════════════════════
  // HISTORY
  // ═══════════════════════════════════════════════════════════════════════════
  async loadHistory() {
    const listEl = $('history-list');
    const emptyEl = $('history-empty');
    const loadEl = $('history-loading');
    const pagEl = $('pagination');
    listEl.innerHTML = '';
    hideEl(emptyEl); hideEl(pagEl); showEl(loadEl);

    try {
      const data = await api(`/api/news/history?page=${this._historyPage}&size=8`);
      hideEl(loadEl);
      const items = data.content || [];
      this._historyTotalPages = data.totalPages || 1;

      if (items.length === 0) { showEl(emptyEl); return; }

      listEl.innerHTML = items.map(item => this._historyCardHtml(item)).join('');

      $('page-indicator').textContent = `Page ${this._historyPage + 1} of ${this._historyTotalPages}`;
      $('prev-page').disabled = this._historyPage === 0;
      $('next-page').disabled = this._historyPage >= this._historyTotalPages - 1;
      showEl(pagEl);

    } catch (err) {
      hideEl(loadEl);
      listEl.innerHTML = `<p style="color:var(--fake-color);padding:20px">Failed: ${err.message}</p>`;
      if (err.status === 401) setTimeout(() => this.logout(), 2000);
    }
  },

  _historyCardHtml(item) {
    const state = (item.prediction || '').toLowerCase();
    const pct = Math.round((item.confidence || 0) * 100);
    const date = item.createdAt
      ? new Date(item.createdAt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
      : '—';
    const snippet = (item.articleTitle || item.newsText || '').slice(0, 120);
    // Source type chip
    const sourceChip = item.sourceUrl
      ? `<span class="source-type-chip">🔗 ${item.sourceName || 'URL'}</span>`
      : '';

    return `
      <div class="history-card" id="hcard-${item.id}">
        <div class="history-card-accent ${state}"></div>
        <div class="history-body">
          <div class="history-snippet">${snippet}${(item.articleTitle || item.newsText || '').length > 120 ? '…' : ''}</div>
          <div class="history-meta">
            <span class="badge badge-${state}">${item.prediction}</span>
            ${sourceChip}
            <span class="history-conf">Confidence: ${pct}%</span>
            <span class="history-time">🕐 ${date}</span>
          </div>
        </div>
        <button class="btn btn-danger btn-sm" onclick="App.deleteHistory(${item.id})" title="Delete">🗑</button>
      </div>`;
  },

  changePage(delta) {
    this._historyPage = Math.max(0, Math.min(this._historyTotalPages - 1, this._historyPage + delta));
    this.loadHistory();
  },

  async deleteHistory(id) {
    if (!confirm('Delete this entry from your history?')) return;
    try {
      await api(`/api/news/history/${id}`, { method: 'DELETE' });
      const card = $(`hcard-${id}`);
      if (card) { card.style.opacity = '0'; card.style.transition = '.2s'; }
      setTimeout(() => this.loadHistory(), 220);
      showToast('Entry deleted.', 'info');
    } catch (err) {
      showToast('Could not delete: ' + err.message, 'error');
    }
  },
};

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());
