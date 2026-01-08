// Pine Script Library Web Interface
let allScripts = [];
let filteredScripts = [];
let editingScriptId = null;

// API Configuration
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : '/api';

// Load scripts data
async function loadScripts() {
    try {
        const response = await fetch(`${API_BASE}/scripts`);
        const data = await response.json();
        allScripts = data.scripts || [];
        filteredScripts = [...allScripts];
        renderScripts();
        updateStats();
    } catch (error) {
        console.error('Error loading scripts:', error);
        document.getElementById('scriptsTableBody').innerHTML = 
            '<tr><td colspan="13" style="text-align: center; padding: 40px;">Error loading scripts data. Please make sure the Flask server is running.</td></tr>';
    }
}

// Create new script
async function createScript(scriptData) {
    try {
        const response = await fetch(`${API_BASE}/scripts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(scriptData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create script');
        }
        
        const newScript = await response.json();
        showNotification('Script created successfully!', 'success');
        await loadScripts();
        return newScript;
    } catch (error) {
        console.error('Error creating script:', error);
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// Update existing script
async function updateScript(scriptId, scriptData) {
    try {
        const response = await fetch(`${API_BASE}/scripts/${scriptId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(scriptData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update script');
        }
        
        const updatedScript = await response.json();
        showNotification('Script updated successfully!', 'success');
        await loadScripts();
        return updatedScript;
    } catch (error) {
        console.error('Error updating script:', error);
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// Delete script
async function deleteScript(scriptId) {
    if (!confirm('Are you sure you want to delete this script? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/scripts/${scriptId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete script');
        }
        
        showNotification('Script deleted successfully!', 'success');
        await loadScripts();
    } catch (error) {
        console.error('Error deleting script:', error);
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Render scripts table
function renderScripts() {
    const tbody = document.getElementById('scriptsTableBody');
    const noResults = document.getElementById('noResults');
    
    if (filteredScripts.length === 0) {
        tbody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    
    tbody.innerHTML = filteredScripts.map(script => {
        const backtest = script.backtest || {};
        const hasBacktest = Object.keys(backtest).length > 0;
        
        return `
            <tr>
                <td>
                    <strong>${escapeHtml(script.name)}</strong><br>
                    <small style="color: var(--text-secondary);">${escapeHtml(script.description || '')}</small>
                </td>
                <td>
                    <span class="badge badge-${script.type}">${capitalize(script.type)}</span>
                </td>
                <td>${escapeHtml(script.version)}</td>
                <td>
                    <span class="badge badge-${script.status}">${capitalize(script.status)}</span>
                </td>
                <td>
                    <div class="tags">
                        ${(script.tags || []).slice(0, 3).map(tag => 
                            `<span class="tag">${escapeHtml(tag)}</span>`
                        ).join('')}
                        ${script.tags && script.tags.length > 3 ? `<span class="tag">+${script.tags.length - 3}</span>` : ''}
                    </div>
                </td>
                <td class="metric-value ${getMetricClass(backtest.winRate, 50, 60, true)}">
                    ${hasBacktest && backtest.winRate != null ? `${backtest.winRate.toFixed(2)}%` : '-'}
                </td>
                <td class="metric-value ${getMetricClass(backtest.profitFactor, 1, 1.5, true)}">
                    ${hasBacktest && backtest.profitFactor != null ? backtest.profitFactor.toFixed(2) : '-'}
                </td>
                <td class="metric-value ${getMetricClass(backtest.netProfitPercent, 0, 20, true)}">
                    ${hasBacktest && backtest.netProfitPercent != null ? `${backtest.netProfitPercent.toFixed(2)}%` : '-'}
                </td>
                <td class="metric-value ${getMetricClass(backtest.maxDrawdown, -20, -10, false)}">
                    ${hasBacktest && backtest.maxDrawdown != null ? `${backtest.maxDrawdown.toFixed(2)}%` : '-'}
                </td>
                <td class="metric-value metric-neutral">
                    ${hasBacktest && backtest.totalTrades != null ? backtest.totalTrades : '-'}
                </td>
                <td>
                    <small>${formatDate(script.dateModified || script.dateCreated)}</small>
                </td>
                <td>
                    <div class="actions">
                        <button class="btn btn-primary" onclick="viewScript('${script.id}')">View</button>
                        <button class="btn btn-edit" onclick="openEditModal('${script.id}')">Edit</button>
                        <button class="btn btn-delete" onclick="deleteScript('${script.id}')">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Update statistics summary
function updateStats() {
    const totalScripts = filteredScripts.length;
    const strategies = filteredScripts.filter(s => s.type === 'strategy').length;
    const indicators = filteredScripts.filter(s => s.type === 'indicator').length;
    
    const strategiesWithBacktest = filteredScripts.filter(s => s.type === 'strategy' && s.backtest && s.backtest.winRate != null);
    const avgWinRate = strategiesWithBacktest.length > 0
        ? strategiesWithBacktest.reduce((sum, s) => sum + s.backtest.winRate, 0) / strategiesWithBacktest.length
        : 0;
    
    document.getElementById('totalScripts').textContent = totalScripts;
    document.getElementById('totalStrategies').textContent = strategies;
    document.getElementById('totalIndicators').textContent = indicators;
    document.getElementById('avgWinRate').textContent = avgWinRate.toFixed(1) + '%';
}

// Filter and search scripts
function filterScripts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const typeFilter = document.getElementById('typeFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    filteredScripts = allScripts.filter(script => {
        const matchesSearch = !searchTerm || 
            script.name.toLowerCase().includes(searchTerm) ||
            (script.description && script.description.toLowerCase().includes(searchTerm)) ||
            (script.tags && script.tags.some(tag => tag.toLowerCase().includes(searchTerm)));
        
        const matchesType = typeFilter === 'all' || script.type === typeFilter;
        const matchesStatus = statusFilter === 'all' || script.status === statusFilter;
        
        return matchesSearch && matchesType && matchesStatus;
    });
    
    sortScripts();
    renderScripts();
    updateStats();
}

// Sort scripts
function sortScripts() {
    const sortBy = document.getElementById('sortBy').value;
    
    filteredScripts.sort((a, b) => {
        switch (sortBy) {
            case 'name':
                return a.name.localeCompare(b.name);
            case 'dateModified':
                return new Date(b.dateModified || b.dateCreated) - new Date(a.dateModified || a.dateCreated);
            case 'winRate':
                return (b.backtest?.winRate || 0) - (a.backtest?.winRate || 0);
            case 'profitFactor':
                return (b.backtest?.profitFactor || 0) - (a.backtest?.profitFactor || 0);
            case 'netProfitPercent':
                return (b.backtest?.netProfitPercent || 0) - (a.backtest?.netProfitPercent || 0);
            default:
                return 0;
        }
    });
}

// View script details in modal
function viewScript(scriptId) {
    const script = allScripts.find(s => s.id === scriptId);
    if (!script) return;
    
    const backtest = script.backtest || {};
    const hasBacktest = Object.keys(backtest).length > 0;
    
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="modal-header">
            <h2>${escapeHtml(script.name)}</h2>
            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <span class="badge badge-${script.type}">${capitalize(script.type)}</span>
                <span class="badge badge-${script.status}">${capitalize(script.status)}</span>
                <span class="badge" style="background: var(--dark-bg);">v${escapeHtml(script.version)}</span>
            </div>
        </div>
        
        <div class="modal-section">
            <h3>Description</h3>
            <p>${escapeHtml(script.description || 'No description available.')}</p>
        </div>
        
        <div class="modal-section">
            <h3>Details</h3>
            <div class="param-list">
                <div class="param-item">
                    <span>File Path:</span>
                    <code>${escapeHtml(script.filePath)}</code>
                </div>
                <div class="param-item">
                    <span>Author:</span>
                    <span>${escapeHtml(script.author || 'N/A')}</span>
                </div>
                <div class="param-item">
                    <span>Pine Version:</span>
                    <span>${script.pineVersion || 5}</span>
                </div>
                <div class="param-item">
                    <span>Created:</span>
                    <span>${formatDate(script.dateCreated)}</span>
                </div>
                <div class="param-item">
                    <span>Modified:</span>
                    <span>${formatDate(script.dateModified || script.dateCreated)}</span>
                </div>
                ${script.timeframes ? `
                <div class="param-item">
                    <span>Timeframes:</span>
                    <span>${script.timeframes.join(', ')}</span>
                </div>
                ` : ''}
            </div>
        </div>
        
        ${script.parameters && script.parameters.length > 0 ? `
        <div class="modal-section">
            <h3>Parameters</h3>
            <div class="param-list">
                ${script.parameters.map(param => `
                    <div class="param-item">
                        <span><strong>${escapeHtml(param.name)}</strong> (${param.type})</span>
                        <span>Default: ${param.default}</span>
                    </div>
                    ${param.description ? `<div style="padding-left: 10px; color: var(--text-secondary); font-size: 0.9rem;">${escapeHtml(param.description)}</div>` : ''}
                `).join('')}
            </div>
        </div>
        ` : ''}
        
        ${hasBacktest ? `
        <div class="modal-section">
            <h3>Backtest Results</h3>
            <p style="margin-bottom: 10px;"><strong>Symbol:</strong> ${escapeHtml(backtest.symbol || 'N/A')} | <strong>Timeframe:</strong> ${escapeHtml(backtest.timeframe || 'N/A')}</p>
            <p style="margin-bottom: 10px; color: var(--text-secondary);">${escapeHtml(backtest.startDate || 'N/A')} to ${escapeHtml(backtest.endDate || 'N/A')}</p>
            <div class="backtest-metrics">
                <div class="metric-item">
                    <span>Net Profit:</span>
                    <span class="${getMetricClass(backtest.netProfitPercent, 0, 20, true)}">${backtest.netProfit != null ? '$' + backtest.netProfit.toFixed(2) : 'N/A'} (${backtest.netProfitPercent != null ? backtest.netProfitPercent.toFixed(2) + '%' : 'N/A'})</span>
                </div>
                <div class="metric-item">
                    <span>Total Trades:</span>
                    <span>${backtest.totalTrades || 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span>Winning / Losing:</span>
                    <span>${backtest.winningTrades || 0} / ${backtest.losingTrades || 0}</span>
                </div>
                <div class="metric-item">
                    <span>Win Rate:</span>
                    <span class="${getMetricClass(backtest.winRate, 50, 60, true)}">${backtest.winRate != null ? backtest.winRate.toFixed(2) + '%' : 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span>Profit Factor:</span>
                    <span class="${getMetricClass(backtest.profitFactor, 1, 1.5, true)}">${backtest.profitFactor != null ? backtest.profitFactor.toFixed(2) : 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span>Max Drawdown:</span>
                    <span class="${getMetricClass(backtest.maxDrawdown, -20, -10, false)}">${backtest.maxDrawdown != null ? backtest.maxDrawdown.toFixed(2) + '%' : 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span>Average Trade:</span>
                    <span>${backtest.avgTrade != null ? '$' + backtest.avgTrade.toFixed(2) : 'N/A'}</span>
                </div>
                <div class="metric-item">
                    <span>Sharpe Ratio:</span>
                    <span class="${getMetricClass(backtest.sharpeRatio, 0.5, 1, true)}">${backtest.sharpeRatio != null ? backtest.sharpeRatio.toFixed(2) : 'N/A'}</span>
                </div>
            </div>
            ${backtest.notes ? `<p style="margin-top: 15px; color: var(--text-secondary); font-style: italic;">${escapeHtml(backtest.notes)}</p>` : ''}
        </div>
        ` : '<div class="modal-section"><p style="color: var(--text-secondary);">No backtest data available.</p></div>'}
        
        ${script.tags && script.tags.length > 0 ? `
        <div class="modal-section">
            <h3>Tags</h3>
            <div class="tags">
                ${script.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
            </div>
        </div>
        ` : ''}
        
        ${script.notes ? `
        <div class="modal-section">
            <h3>Notes</h3>
            <p>${escapeHtml(script.notes)}</p>
        </div>
        ` : ''}
    `;
    
    const modal = document.getElementById('scriptModal');
    modal.style.display = 'block';
}

// Copy file path to clipboard
function copyFilePath(filePath) {
    navigator.clipboard.writeText(filePath).then(() => {
        showNotification('File path copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy file path', 'error');
    });
}

// Open create/edit modal
function openEditModal(scriptId = null) {
    editingScriptId = scriptId;
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    const title = document.getElementById('editModalTitle');
    
    if (scriptId) {
        // Edit mode
        const script = allScripts.find(s => s.id === scriptId);
        if (!script) return;
        
        title.textContent = 'Edit Script';
        
        // Populate form
        document.getElementById('edit_name').value = script.name || '';
        document.getElementById('edit_type').value = script.type || 'indicator';
        document.getElementById('edit_version').value = script.version || '1.0.0';
        document.getElementById('edit_status').value = script.status || 'active';
        document.getElementById('edit_filePath').value = script.filePath || '';
        document.getElementById('edit_description').value = script.description || '';
        document.getElementById('edit_author').value = script.author || '';
        document.getElementById('edit_tags').value = (script.tags || []).join(', ');
        document.getElementById('edit_timeframes').value = (script.timeframes || []).join(', ');
        document.getElementById('edit_notes').value = script.notes || '';
        
        // Backtest fields
        if (script.backtest) {
            document.getElementById('edit_bt_symbol').value = script.backtest.symbol || '';
            document.getElementById('edit_bt_timeframe').value = script.backtest.timeframe || '';
            document.getElementById('edit_bt_netProfitPercent').value = script.backtest.netProfitPercent || '';
            document.getElementById('edit_bt_totalTrades').value = script.backtest.totalTrades || '';
            document.getElementById('edit_bt_winRate').value = script.backtest.winRate || '';
            document.getElementById('edit_bt_profitFactor').value = script.backtest.profitFactor || '';
            document.getElementById('edit_bt_maxDrawdown').value = script.backtest.maxDrawdown || '';
        }
    } else {
        // Create mode
        title.textContent = 'Create New Script';
        form.reset();
    }
    
    modal.style.display = 'block';
}

// Close edit modal
function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.style.display = 'none';
    editingScriptId = null;
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = {
        name: document.getElementById('edit_name').value,
        type: document.getElementById('edit_type').value,
        version: document.getElementById('edit_version').value,
        status: document.getElementById('edit_status').value,
        filePath: document.getElementById('edit_filePath').value,
        description: document.getElementById('edit_description').value,
        author: document.getElementById('edit_author').value,
        pineVersion: 5
    };
    
    // Parse tags
    const tagsValue = document.getElementById('edit_tags').value.trim();
    if (tagsValue) {
        formData.tags = tagsValue.split(',').map(t => t.trim()).filter(t => t);
    }
    
    // Parse timeframes
    const timeframesValue = document.getElementById('edit_timeframes').value.trim();
    if (timeframesValue) {
        formData.timeframes = timeframesValue.split(',').map(t => t.trim()).filter(t => t);
    }
    
    // Notes
    const notesValue = document.getElementById('edit_notes').value.trim();
    if (notesValue) {
        formData.notes = notesValue;
    }
    
    // Backtest data
    const btSymbol = document.getElementById('edit_bt_symbol').value.trim();
    const btTimeframe = document.getElementById('edit_bt_timeframe').value.trim();
    const btNetProfit = parseFloat(document.getElementById('edit_bt_netProfitPercent').value);
    const btTotalTrades = parseInt(document.getElementById('edit_bt_totalTrades').value);
    const btWinRate = parseFloat(document.getElementById('edit_bt_winRate').value);
    const btProfitFactor = parseFloat(document.getElementById('edit_bt_profitFactor').value);
    const btMaxDrawdown = parseFloat(document.getElementById('edit_bt_maxDrawdown').value);
    
    if (btSymbol || btTimeframe || !isNaN(btNetProfit) || !isNaN(btTotalTrades)) {
        formData.backtest = {};
        if (btSymbol) formData.backtest.symbol = btSymbol;
        if (btTimeframe) formData.backtest.timeframe = btTimeframe;
        if (!isNaN(btNetProfit)) formData.backtest.netProfitPercent = btNetProfit;
        if (!isNaN(btTotalTrades)) formData.backtest.totalTrades = btTotalTrades;
        if (!isNaN(btWinRate)) formData.backtest.winRate = btWinRate;
        if (!isNaN(btProfitFactor)) formData.backtest.profitFactor = btProfitFactor;
        if (!isNaN(btMaxDrawdown)) formData.backtest.maxDrawdown = btMaxDrawdown;
    }
    
    try {
        if (editingScriptId) {
            await updateScript(editingScriptId, formData);
        } else {
            await createScript(formData);
        }
        closeEditModal();
    } catch (error) {
        // Error already handled in create/update functions
    }
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getMetricClass(value, thresholdNeutral, thresholdPositive, higherIsBetter) {
    if (value == null) return 'metric-neutral';
    
    if (higherIsBetter) {
        if (value >= thresholdPositive) return 'metric-positive';
        if (value >= thresholdNeutral) return 'metric-neutral';
        return 'metric-negative';
    } else {
        if (value <= thresholdPositive) return 'metric-positive';
        if (value <= thresholdNeutral) return 'metric-neutral';
        return 'metric-negative';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadScripts();
    
    document.getElementById('searchInput').addEventListener('input', filterScripts);
    document.getElementById('typeFilter').addEventListener('change', filterScripts);
    document.getElementById('statusFilter').addEventListener('change', filterScripts);
    document.getElementById('sortBy').addEventListener('change', () => {
        sortScripts();
        renderScripts();
    });
    
    // Modal close handlers
    const modal = document.getElementById('scriptModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
});
