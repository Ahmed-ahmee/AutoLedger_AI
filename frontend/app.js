/**
 * AutoLedger AI – Frontend Application Logic
 * Vanilla JS for API interaction and DOM manipulation
 */

const API_BASE = 'http://localhost:8000/api';
let currentBatchId = null;

// ══════════════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ══════════════════════════════════════════════════════════════════════

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(t => t.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.remove('hidden');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Load data for the tab
    const loaders = {
        dashboard: loadDashboardStats,
        results: loadPredictions,
        review: loadReviewQueue,
        audit: loadAuditLogs,
        coa: loadCOA,
    };
    if (loaders[tabName]) loaders[tabName]();
}

// ══════════════════════════════════════════════════════════════════════
// TOAST NOTIFICATIONS
// ══════════════════════════════════════════════════════════════════════

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const colors = {
        success: 'bg-emerald-500/90 text-white',
        error: 'bg-red-500/90 text-white',
        info: 'bg-brand-500/90 text-white',
        warning: 'bg-amber-500/90 text-white',
    };

    const toast = document.createElement('div');
    toast.className = `toast ${colors[type] || colors.info} px-5 py-3 rounded-xl text-sm font-medium shadow-2xl backdrop-blur-xl max-w-sm`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ══════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ══════════════════════════════════════════════════════════════════════

// Detection logic for Render deployment vs Localhost
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000/api'
    : 'https://autoledger-backend.onrender.com/api'; // This should match your backend service name on Render

// ══════════════════════════════════════════════════════════════════════
// API HELPERS
// ══════════════════════════════════════════════════════════════════════

async function apiFetch(endpoint, options = {}) {
    try {
        const res = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (error) {
        if (error.message.includes('Failed to fetch')) {
            showToast('Cannot connect to backend. Is the server running?', 'error');
        } else {
            showToast(error.message, 'error');
        }
        throw error;
    }
}

// ══════════════════════════════════════════════════════════════════════
// DASHBOARD
// ══════════════════════════════════════════════════════════════════════

async function loadDashboardStats() {
    try {
        const stats = await apiFetch('/dashboard/stats');

        document.getElementById('kpi-total-txn').textContent = stats.total_transactions.toLocaleString();
        document.getElementById('kpi-auto-posted').textContent = stats.auto_posted_count.toLocaleString();
        document.getElementById('kpi-pending').textContent = stats.pending_review_count.toLocaleString();
        document.getElementById('kpi-manual').textContent = stats.manual_required_count.toLocaleString();
        document.getElementById('kpi-avg-conf').textContent = stats.avg_confidence > 0 ? `${stats.avg_confidence}%` : '–';
        document.getElementById('kpi-erp').textContent = stats.total_erp_postings.toLocaleString();
        document.getElementById('kpi-corrections').textContent = (stats.rejected_count || 0).toLocaleString();
        document.getElementById('kpi-corr-rate').textContent = `${stats.correction_rate}%`;

        // Update review badge
        const badge = document.getElementById('reviewBadge');
        const reviewCount = stats.pending_review_count + stats.manual_required_count;
        if (reviewCount > 0) {
            badge.textContent = reviewCount;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }

        // Classification breakdown
        const breakdown = document.getElementById('classificationBreakdown');
        if (stats.total_predictions > 0) {
            const total = stats.total_predictions;
            const items = [
                { label: 'Auto-Posted', count: stats.auto_posted_count, color: 'bg-emerald-400', pct: (stats.auto_posted_count / total * 100).toFixed(1) },
                { label: 'Pending Review', count: stats.pending_review_count, color: 'bg-amber-400', pct: (stats.pending_review_count / total * 100).toFixed(1) },
                { label: 'Manual Required', count: stats.manual_required_count, color: 'bg-red-400', pct: (stats.manual_required_count / total * 100).toFixed(1) },
                { label: 'Approved', count: stats.approved_count, color: 'bg-blue-400', pct: (stats.approved_count / total * 100).toFixed(1) },
                { label: 'Rejected', count: stats.rejected_count, color: 'bg-purple-400', pct: (stats.rejected_count / total * 100).toFixed(1) },
            ];
            breakdown.innerHTML = items.map(i => `
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-gray-400">${i.label}</span>
                        <span class="font-medium text-gray-300">${i.count} (${i.pct}%)</span>
                    </div>
                    <div class="conf-bar"><div class="conf-bar-fill ${i.color}" style="width:${i.pct}%"></div></div>
                </div>
            `).join('');
        }

        // ML status
        try {
            const ml = await apiFetch('/ml/status');
            document.getElementById('kpi-vectors').textContent = ml.total_vectors.toLocaleString();
            document.getElementById('mlStatus').textContent = `Vectors: ${ml.total_vectors}`;
        } catch (_) { }

    } catch (_) { }
}

// ══════════════════════════════════════════════════════════════════════
// FILE UPLOAD
// ══════════════════════════════════════════════════════════════════════

function handleDrop(e) {
    e.preventDefault();
    e.target.closest('#dropZone').classList.remove('border-brand-500/60', 'bg-brand-500/5');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) uploadFile(file);
}

async function uploadFile(file) {
    const progressDiv = document.getElementById('uploadProgress');
    const resultDiv = document.getElementById('uploadResult');
    const classifyDiv = document.getElementById('classifyResult');
    const bar = document.getElementById('uploadBar');
    const statusText = document.getElementById('uploadStatusText');

    progressDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    classifyDiv.classList.add('hidden');
    bar.style.width = '30%';
    statusText.textContent = `Uploading ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        bar.style.width = '60%';
        const data = await apiFetch('/transactions/upload', {
            method: 'POST',
            body: formData,
        });

        bar.style.width = '100%';
        statusText.textContent = 'Upload complete!';
        currentBatchId = data.batch_id;

        setTimeout(() => {
            progressDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
            document.getElementById('uploadResultText').textContent = data.message;
            document.getElementById('uploadBatchId').textContent = `Batch ID: ${data.batch_id}`;
        }, 500);

        showToast(`${data.total_transactions} transactions uploaded`, 'success');
    } catch (error) {
        bar.style.width = '0%';
        statusText.textContent = 'Upload failed';
        showToast('Upload failed: ' + error.message, 'error');
    }
}

// ══════════════════════════════════════════════════════════════════════
// CLASSIFY ALL
// ══════════════════════════════════════════════════════════════════════

async function classifyAll() {
    showToast('Classifying transactions...', 'info');

    try {
        const body = currentBatchId ? { batch_id: currentBatchId } : {};
        const data = await apiFetch('/predictions/classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        const classifyDiv = document.getElementById('classifyResult');
        classifyDiv.classList.remove('hidden');
        document.getElementById('classifyDetails').innerHTML = `
            <div class="flex justify-between"><span class="text-gray-400">Total Classified</span><span class="font-semibold text-white">${data.total_classified}</span></div>
            <div class="flex justify-between"><span class="text-emerald-400">✓ Auto-Posted</span><span class="font-semibold text-emerald-300">${data.auto_posted}</span></div>
            <div class="flex justify-between"><span class="text-amber-400">⏳ Pending Review</span><span class="font-semibold text-amber-300">${data.pending_review}</span></div>
            <div class="flex justify-between"><span class="text-red-400">✋ Manual Required</span><span class="font-semibold text-red-300">${data.manual_required}</span></div>
        `;

        showToast(`Classified ${data.total_classified} transactions`, 'success');
        loadDashboardStats();
    } catch (error) {
        showToast('Classification failed', 'error');
    }
}

// ══════════════════════════════════════════════════════════════════════
// QUICK ENTRY (MANUAL TRANSACTION)
// ══════════════════════════════════════════════════════════════════════

async function handleQuickEntry(e) {
    e.preventDefault();
    const descInput = document.getElementById('quickDesc');
    let desc = descInput.value.trim();
    if (!desc) return;

    descInput.disabled = true;
    showToast('Classifying...', 'info');

    // Attempt to extract an amount from the description (e.g., "$50 office supplies", "lunch 15.50")
    let amount = 0.0;
    const amountMatch = desc.match(/\$?\b(\d+(?:\.\d{1,2})?)\b/);
    if (amountMatch) {
        amount = parseFloat(amountMatch[1]);
        // Optional: remove the amount from the description to clean it up for the ML model
        // desc = desc.replace(amountMatch[0], '').trim(); 
    }

    try {
        // 1. Create transaction
        const txn = await apiFetch('/transactions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc, amount: amount }),
        });

        // 2. Classify it
        await apiFetch('/predictions/classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_ids: [txn.id] }),
        });

        showToast('Classification complete!', 'success');
        descInput.value = '';

        // Refresh dashboard and results
        loadDashboardStats();
        switchTab('results');

    } catch (error) {
        showToast('Failed to classify: ' + error.message, 'error');
    } finally {
        descInput.disabled = false;
        descInput.focus();
    }
}

// ══════════════════════════════════════════════════════════════════════
// PREDICTIONS TABLE
// ══════════════════════════════════════════════════════════════════════

async function loadPredictions() {
    try {
        const status = document.getElementById('statusFilter').value;
        const params = status ? `?status=${status}&limit=100` : '?limit=100';
        const predictions = await apiFetch(`/predictions${params}`);

        const body = document.getElementById('predictionsBody');
        const empty = document.getElementById('predictionsEmpty');

        if (predictions.length === 0) {
            body.innerHTML = '';
            empty.classList.remove('hidden');
            return;
        }

        empty.classList.add('hidden');
        body.innerHTML = predictions.map(p => `
            <tr>
                <td class="px-4 py-3 text-gray-500 font-mono text-xs">#${p.transaction_id}</td>
                <td class="px-4 py-3 text-gray-300 max-w-xs truncate">${p.transaction?.description || '–'}</td>
                <td class="px-4 py-3 text-gray-300 font-mono">$${(p.transaction?.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td class="px-4 py-3">
                    <span class="font-mono text-brand-400 font-semibold">${p.predicted_gl_code}</span>
                    <span class="text-gray-500 text-xs ml-1">${p.predicted_gl_name || ''}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                        <span class="font-semibold ${getConfidenceColor(p.confidence_score)}">${p.confidence_score}%</span>
                        <div class="conf-bar w-16"><div class="conf-bar-fill ${getConfidenceBarColor(p.confidence_score)}" style="width:${Math.min(p.confidence_score, 100)}%"></div></div>
                    </div>
                </td>
                <td class="px-4 py-3"><span class="badge ${getStatusBadge(p.status)}">${formatStatus(p.status)}</span></td>
            </tr>
        `).join('');
    } catch (_) { }
}

function getConfidenceColor(score) {
    if (score >= 80) return 'text-emerald-400';
    if (score >= 50) return 'text-amber-400';
    return 'text-red-400';
}

function getConfidenceBarColor(score) {
    if (score >= 80) return 'bg-emerald-400';
    if (score >= 50) return 'bg-amber-400';
    return 'bg-red-400';
}

function getStatusBadge(status) {
    const map = {
        auto_posted: 'badge-auto',
        pending_review: 'badge-review',
        manual_required: 'badge-manual',
        approved: 'badge-approved',
        rejected: 'badge-rejected',
    };
    return map[status] || '';
}

function formatStatus(status) {
    return (status || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// ══════════════════════════════════════════════════════════════════════
// REVIEW QUEUE
// ══════════════════════════════════════════════════════════════════════

async function loadReviewQueue() {
    try {
        const items = await apiFetch('/reviews/queue?limit=50');
        const container = document.getElementById('reviewQueue');
        const empty = document.getElementById('reviewEmpty');

        if (items.length === 0) {
            container.innerHTML = '';
            empty.classList.remove('hidden');
            return;
        }

        empty.classList.add('hidden');
        container.innerHTML = items.map(p => `
            <div class="review-card" id="review-${p.id}">
                <div class="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-2">
                            <span class="badge ${getStatusBadge(p.status)}">${formatStatus(p.status)}</span>
                            <span class="text-xs text-gray-500">TXN #${p.transaction_id}</span>
                        </div>
                        <p class="text-gray-200 font-medium mb-1">${p.transaction?.description || '–'}</p>
                        <div class="flex flex-wrap gap-4 text-sm text-gray-500">
                            <span>Amount: <span class="text-gray-300 font-mono">$${(p.transaction?.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span></span>
                            <span>Vendor: <span class="text-gray-300">${p.transaction?.vendor || '–'}</span></span>
                            <span>Dept: <span class="text-gray-300">${p.transaction?.department || '–'}</span></span>
                        </div>
                        <div class="mt-3 flex items-center gap-3">
                            <span class="text-sm text-gray-400">Predicted:</span>
                            <span class="font-mono font-semibold text-brand-400">${p.predicted_gl_code}</span>
                            <span class="text-gray-500 text-sm">${p.predicted_gl_name || ''}</span>
                            <span class="font-semibold ${getConfidenceColor(p.confidence_score)}">${p.confidence_score}%</span>
                        </div>
                        ${p.top_candidates && p.top_candidates.length > 0 ? `
                        <div class="mt-2">
                            <p class="text-xs text-gray-500 mb-1">Top candidates:</p>
                            <div class="flex flex-wrap gap-2">
                                ${p.top_candidates.map(c => `
                                    <span class="text-xs px-2 py-1 rounded-lg bg-white/5 text-gray-400">
                                        <span class="font-mono text-gray-300">${c.gl_code}</span> ${c.gl_name} (${c.score}%)
                                    </span>
                                `).join('')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="flex flex-col gap-2 lg:w-64 shrink-0">
                        <button onclick="approveReview(${p.id})" class="w-full py-2.5 rounded-xl bg-emerald-500/15 text-emerald-400 font-semibold text-sm hover:bg-emerald-500/25 transition-colors border border-emerald-500/20">
                            ✓ Approve
                        </button>
                        <div class="relative">
                            <input type="text" id="corrGL-${p.id}" placeholder="Corrected GL Code" class="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-brand-500">
                        </div>
                        <input type="text" id="corrReason-${p.id}" placeholder="Reason (optional)" class="w-full px-3 py-2 rounded-xl bg-surface-800 border border-white/10 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-brand-500">
                        <button onclick="rejectReview(${p.id})" class="w-full py-2.5 rounded-xl bg-red-500/15 text-red-400 font-semibold text-sm hover:bg-red-500/25 transition-colors border border-red-500/20">
                            ✗ Reject & Correct
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (_) { }
}

async function approveReview(predictionId) {
    try {
        await apiFetch(`/reviews/${predictionId}/approve`, { method: 'POST' });
        showToast('Prediction approved & posted to ERP', 'success');
        document.getElementById(`review-${predictionId}`).remove();
        loadDashboardStats();
    } catch (error) {
        showToast('Approval failed: ' + error.message, 'error');
    }
}

async function rejectReview(predictionId) {
    const glCode = document.getElementById(`corrGL-${predictionId}`).value.trim();
    const reason = document.getElementById(`corrReason-${predictionId}`).value.trim();

    if (!glCode) {
        showToast('Please enter the corrected GL code', 'warning');
        return;
    }

    try {
        await apiFetch(`/reviews/${predictionId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                corrected_gl_code: glCode,
                reason: reason || null,
                corrected_by: 'analyst',
            }),
        });
        showToast('Correction saved & posted to ERP', 'success');
        document.getElementById(`review-${predictionId}`).remove();
        loadDashboardStats();
    } catch (error) {
        showToast('Rejection failed: ' + error.message, 'error');
    }
}

// ══════════════════════════════════════════════════════════════════════
// AUDIT LOGS
// ══════════════════════════════════════════════════════════════════════

async function loadAuditLogs() {
    try {
        const action = document.getElementById('auditFilter').value;
        const params = action ? `?action=${action}&limit=100` : '?limit=100';
        const logs = await apiFetch(`/audit/logs${params}`);

        const body = document.getElementById('auditBody');
        const empty = document.getElementById('auditEmpty');

        if (logs.length === 0) {
            body.innerHTML = '';
            empty.classList.remove('hidden');
            return;
        }

        empty.classList.add('hidden');
        body.innerHTML = logs.map(l => `
            <tr>
                <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">${new Date(l.timestamp).toLocaleString()}</td>
                <td class="px-4 py-3"><span class="badge ${getActionBadge(l.action)}">${formatStatus(l.action)}</span></td>
                <td class="px-4 py-3 text-gray-400 text-sm">${l.actor}</td>
                <td class="px-4 py-3 text-gray-500 font-mono text-xs">${l.transaction_id ? '#' + l.transaction_id : '–'}</td>
                <td class="px-4 py-3 text-gray-400 text-sm max-w-md truncate">${l.details || '–'}</td>
            </tr>
        `).join('');
    } catch (_) { }
}

function getActionBadge(action) {
    const map = {
        uploaded: 'badge-approved',
        predicted: 'badge-review',
        auto_posted: 'badge-auto',
        sent_for_review: 'badge-review',
        approved: 'badge-approved',
        rejected: 'badge-rejected',
        corrected: 'badge-rejected',
        retrained: 'badge-auto',
    };
    return map[action] || '';
}

// ══════════════════════════════════════════════════════════════════════
// CHART OF ACCOUNTS
// ══════════════════════════════════════════════════════════════════════

async function loadCOA() {
    try {
        const accounts = await apiFetch('/transactions/coa');
        const body = document.getElementById('coaBody');

        body.innerHTML = accounts.map(a => `
            <tr>
                <td class="px-4 py-3 font-mono font-semibold text-brand-400">${a.gl_code}</td>
                <td class="px-4 py-3 text-gray-300">${a.gl_name}</td>
                <td class="px-4 py-3"><span class="badge ${getCategoryBadge(a.category)}">${a.category}</span></td>
                <td class="px-4 py-3 text-gray-500">${a.sub_category || '–'}</td>
            </tr>
        `).join('');
    } catch (_) { }
}

function getCategoryBadge(cat) {
    const map = {
        Assets: 'badge-approved',
        Liabilities: 'badge-review',
        Equity: 'badge-rejected',
        Revenue: 'badge-auto',
        Expenses: 'badge-manual',
    };
    return map[cat] || '';
}

// ══════════════════════════════════════════════════════════════════════
// RETRAIN
// ══════════════════════════════════════════════════════════════════════

async function triggerRetrain() {
    showToast('Starting retraining...', 'info');
    try {
        const data = await apiFetch('/ml/retrain', { method: 'POST' });
        showToast(data.message, 'success');
        loadDashboardStats();
    } catch (error) {
        showToast('Retraining failed', 'error');
    }
}

// ══════════════════════════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
});
