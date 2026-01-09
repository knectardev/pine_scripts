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
        sortScripts();  // Sort by default (Last Modified descending)
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
                <td>${escapeHtml(script.currentVersion || script.version)}</td>
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
                        <button class="btn btn-code" onclick="viewCode('${script.id}')">View Code</button>
                        <button class="btn btn-edit" onclick="openEditModal('${script.id}')">Edit</button>
                        <button class="btn btn-delete" onclick="deleteScript('${script.id}')">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Update statistics in dropdown options
function updateStats() {
    // Count all types from allScripts (not filtered)
    const allStrategies = allScripts.filter(s => s.type === 'strategy').length;
    const allIndicators = allScripts.filter(s => s.type === 'indicator').length;
    const allStudies = allScripts.filter(s => s.type === 'study').length;
    
    // Count all statuses from allScripts (not filtered)
    const allActive = allScripts.filter(s => s.status === 'active').length;
    const allTesting = allScripts.filter(s => s.status === 'testing').length;
    const allDeprecated = allScripts.filter(s => s.status === 'deprecated').length;
    const allArchived = allScripts.filter(s => s.status === 'archived').length;
    
    // Update Type filter options
    const typeFilter = document.getElementById('typeFilter');
    typeFilter.options[0].text = `All Types (${allScripts.length})`;
    typeFilter.options[1].text = `Strategies (${allStrategies})`;
    typeFilter.options[2].text = `Indicators (${allIndicators})`;
    typeFilter.options[3].text = `Studies (${allStudies})`;
    
    // Update Status filter options
    const statusFilter = document.getElementById('statusFilter');
    statusFilter.options[0].text = `All Status (${allScripts.length})`;
    statusFilter.options[1].text = `Active (${allActive})`;
    statusFilter.options[2].text = `Testing (${allTesting})`;
    statusFilter.options[3].text = `Deprecated (${allDeprecated})`;
    statusFilter.options[4].text = `Archived (${allArchived})`;
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
async function viewScript(scriptId) {
    const script = allScripts.find(s => s.id === scriptId);
    if (!script) return;
    
    const backtest = script.backtest || {};
    const hasBacktest = Object.keys(backtest).length > 0;
    
    // Fetch version history
    let versions = [];
    try {
        const versionsResponse = await fetch(`${API_BASE}/scripts/${scriptId}/versions`);
        if (versionsResponse.ok) {
            const versionsData = await versionsResponse.json();
            versions = versionsData.versions || [];
        }
    } catch (error) {
        console.error('Error fetching versions:', error);
    }
    
    const currentVersion = script.currentVersion || script.version || '1.0.0';
    
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="modal-header">
            <div>
                <h2>${escapeHtml(script.name)}</h2>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <span class="badge badge-${script.type}">${capitalize(script.type)}</span>
                    <span class="badge badge-${script.status}">${capitalize(script.status)}</span>
                    <span class="badge" style="background: var(--dark-bg);">v${escapeHtml(currentVersion)}</span>
                    ${versions.length > 1 ? `<span class="badge" style="background: var(--secondary-color);">${versions.length} versions</span>` : ''}
                </div>
            </div>
            <button class="btn btn-code" onclick="viewCode('${script.id}')" style="margin-top: 10px;">📄 View Code</button>
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
        
        ${versions.length > 0 ? `
        <div class="modal-section">
            <h3>📜 Version History</h3>
            <div style="max-height: 300px; overflow-y: auto;">
                ${versions.map(v => `
                    <div class="version-item ${v.isActive ? 'version-active' : ''}" style="padding: 12px; margin-bottom: 10px; background: var(--dark-bg); border-radius: 6px; border-left: 3px solid ${v.isActive ? 'var(--primary-color)' : 'var(--border-color)'};">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div>
                                <strong style="color: var(--primary-color);">v${escapeHtml(v.version)}</strong>
                                ${v.isActive ? '<span class="badge" style="background: var(--success-color); margin-left: 8px; font-size: 0.75rem;">ACTIVE</span>' : ''}
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn btn-secondary" onclick="viewCode('${script.id}', '${v.version}')" style="padding: 4px 10px; font-size: 0.85rem;">View Code</button>
                                ${!v.isActive ? `<button class="btn btn-secondary" onclick="restoreVersion('${script.id}', '${v.version}', 'activate')" style="padding: 4px 10px; font-size: 0.85rem;">Restore</button>` : ''}
                            </div>
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 4px;">
                            ${formatDate(v.dateCreated)} • ${escapeHtml(v.author || 'unknown')}
                        </div>
                        ${v.changelog ? `<div style="font-size: 0.9rem; color: var(--text-secondary); font-style: italic;">${escapeHtml(v.changelog)}</div>` : ''}
                        ${v.codeReviewScore ? `<div style="margin-top: 6px;"><span class="badge" style="background: ${v.codeReviewScore >= 90 ? 'var(--success-color)' : v.codeReviewScore >= 70 ? 'var(--warning-color)' : 'var(--danger-color)'};">Score: ${v.codeReviewScore}/100</span></div>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
    `;
    
    const modal = document.getElementById('scriptModal');
    modal.style.display = 'block';
}

// Fetch script code
async function fetchScriptCode(scriptId, version = null) {
    try {
        const url = version 
            ? `${API_BASE}/scripts/${scriptId}/code?version=${encodeURIComponent(version)}`
            : `${API_BASE}/scripts/${scriptId}/code`;
        
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch script code');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching script code:', error);
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// Update version dropdown in code modal
function updateCodeVersionDropdown() {
    const versionSelectContainer = document.getElementById('codeVersionSelect');
    if (!versionSelectContainer) return;
    
    if (currentVersions.length <= 1) {
        versionSelectContainer.style.display = 'none';
        return;
    }
    
    versionSelectContainer.style.display = 'flex';
    versionSelectContainer.style.alignItems = 'center';
    versionSelectContainer.style.gap = '10px';
    
    let html = `
        <label style="color: var(--text-secondary); font-size: 0.9rem;">Version:</label>
        <select id="versionDropdown" onchange="changeCodeVersion(this.value)" style="padding: 6px 12px; background: var(--dark-bg); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 4px;">
    `;
    
    currentVersions.forEach(v => {
        const isActive = v.version === currentSelectedVersion;
        const activeLabel = v.isActive ? ' (current)' : '';
        html += `<option value="${v.version}" ${isActive ? 'selected' : ''}>${v.version}${activeLabel}</option>`;
    });
    
    html += `</select>`;
    
    // Add restore button for non-active versions
    const selectedVersion = currentVersions.find(v => v.version === currentSelectedVersion);
    if (selectedVersion && !selectedVersion.isActive) {
        html += `<button class="btn btn-secondary" onclick="showRestoreOptions()" style="padding: 6px 12px; font-size: 0.9rem;">🔄 Restore</button>`;
    }
    
    versionSelectContainer.innerHTML = html;
}

// Change code version
async function changeCodeVersion(version) {
    currentSelectedVersion = version;
    await viewCode(currentScriptId, version);
}

// Show restore version options
function showRestoreOptions() {
    const message = `Choose how to restore version ${currentSelectedVersion}:\n\n` +
                    `• Activate: Make this version the active version\n` +
                    `• Create New: Create a new version based on this one\n\n` +
                    `Click OK to Activate, or Cancel to Create New.`;
    
    const activate = confirm(message);
    const mode = activate ? 'activate' : 'new';
    
    restoreVersion(currentScriptId, currentSelectedVersion, mode);
}

// Restore a version
async function restoreVersion(scriptId, version, mode) {
    try {
        showNotification(`Restoring version ${version}...`, 'info');
        
        const response = await fetch(`${API_BASE}/scripts/${scriptId}/versions/${version}/restore`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mode: mode })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to restore version');
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (mode === 'activate') {
                showNotification(`✅ Version ${version} is now active!`, 'success');
            } else {
                showNotification(`✅ Created new version ${result.newVersion} based on ${version}!`, 'success');
            }
            
            // Reload scripts and refresh view
            await loadScripts();
            await viewCode(scriptId);  // Refresh to show new current
        }
        
    } catch (error) {
        console.error('Error restoring version:', error);
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// Open code viewer modal
let currentScriptId = null;
let currentVersions = [];
let currentSelectedVersion = null;
let isEditMode = false;
let originalCode = '';

async function viewCode(scriptId, version = null) {
    try {
        currentScriptId = scriptId;  // Store for code review
        
        // Fetch version history first
        const versionsResponse = await fetch(`${API_BASE}/scripts/${scriptId}/versions`);
        if (versionsResponse.ok) {
            const versionsData = await versionsResponse.json();
            currentVersions = versionsData.versions || [];
            currentSelectedVersion = version || versionsData.currentVersion;
        }
        
        // Fetch code for specific version or current
        const codeData = await fetchScriptCode(scriptId, version);
        
        // Update modal content
        document.getElementById('codeModalTitle').textContent = codeData.name || 'Pine Script Code';
        document.getElementById('codeFilePath').textContent = `File: ${codeData.filePath} | Version: ${codeData.version || 'current'}`;
        
        // Update version dropdown if exists
        updateCodeVersionDropdown();
        
        const codeElement = document.getElementById('codeContent');
        codeElement.textContent = codeData.code;
        codeElement.className = 'language-pinescript';
        
        // Apply syntax highlighting
        if (typeof hljs !== 'undefined') {
            // Remove any previous highlighting
            codeElement.removeAttribute('data-highlighted');
            hljs.highlightElement(codeElement);
            console.log('Syntax highlighting applied');
        } else {
            console.error('Highlight.js not available');
        }
        
        // Show modal
        const modal = document.getElementById('codeModal');
        modal.style.display = 'block';
    } catch (error) {
        // Error already handled in fetchScriptCode
    }
}

// Close code viewer modal
function closeCodeModal() {
    const modal = document.getElementById('codeModal');
    modal.style.display = 'none';
    
    // Reset edit mode if active
    if (isEditMode) {
        cancelEditMode();
    }
}

// Copy code to clipboard
function copyCode() {
    const codeContent = isEditMode 
        ? document.getElementById('codeEditor').value 
        : document.getElementById('codeContent').textContent;
    const copyButton = document.getElementById('copyButtonText');
    
    navigator.clipboard.writeText(codeContent).then(() => {
        // Update button text temporarily
        const originalText = copyButton.textContent;
        copyButton.textContent = '✅ Copied!';
        showNotification('Code copied to clipboard!', 'success');
        
        // Reset button text after 2 seconds
        setTimeout(() => {
            copyButton.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy code:', err);
        showNotification('Failed to copy code', 'error');
    });
}

// Toggle edit mode
function toggleEditMode() {
    if (isEditMode) {
        cancelEditMode();
    } else {
        enterEditMode();
    }
}

// Enter edit mode
function enterEditMode() {
    isEditMode = true;
    
    // Get current code
    const codeContent = document.getElementById('codeContent');
    originalCode = codeContent.textContent;
    
    // Hide display elements
    document.getElementById('codeDisplay').style.display = 'none';
    
    // Show and populate editor
    const codeEditor = document.getElementById('codeEditor');
    codeEditor.value = originalCode;
    codeEditor.style.display = 'block';
    
    // Update buttons
    document.getElementById('editCodeButton').style.display = 'none';
    document.getElementById('saveCodeButton').style.display = 'inline-block';
    document.getElementById('cancelEditButton').style.display = 'inline-block';
    document.getElementById('copyCodeButton').style.display = 'inline-block';
    document.getElementById('reviewButtonText').parentElement.style.display = 'none';
    
    // Disable version selector if present
    const versionSelect = document.getElementById('versionDropdown');
    if (versionSelect) {
        versionSelect.disabled = true;
    }
    
    showNotification('Edit mode enabled. Make your changes and click Save to create a new version.', 'info');
}

// Cancel edit mode
function cancelEditMode() {
    if (isEditMode && document.getElementById('codeEditor').value !== originalCode) {
        if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
            return;
        }
    }
    
    isEditMode = false;
    
    // Show display elements
    document.getElementById('codeDisplay').style.display = 'block';
    
    // Hide editor
    document.getElementById('codeEditor').style.display = 'none';
    
    // Update buttons
    document.getElementById('editCodeButton').style.display = 'inline-block';
    document.getElementById('saveCodeButton').style.display = 'none';
    document.getElementById('cancelEditButton').style.display = 'none';
    document.getElementById('copyCodeButton').style.display = 'inline-block';
    document.getElementById('reviewButtonText').parentElement.style.display = 'inline-block';
    
    // Re-enable version selector if present
    const versionSelect = document.getElementById('versionDropdown');
    if (versionSelect) {
        versionSelect.disabled = false;
    }
}

// Save edited code
async function saveEditedCode() {
    if (!currentScriptId) {
        showNotification('No script loaded', 'error');
        return;
    }
    
    const editedCode = document.getElementById('codeEditor').value;
    
    if (editedCode === originalCode) {
        showNotification('No changes to save', 'info');
        return;
    }
    
    // Check if this is the initial template code being replaced
    const isInitialTemplate = originalCode.includes('This Pine Script was created via Pine Script Library');
    
    let changelog = 'Initial version';
    let isInitialSave = false;
    
    // Only prompt for changelog if this is NOT the initial template
    if (!isInitialTemplate) {
        const userChangelog = prompt('Enter a brief description of your changes:', 'Manual edit via web interface');
        
        if (userChangelog === null) {
            return; // User cancelled
        }
        changelog = userChangelog || 'Manual edit';
    } else {
        // This is the initial save - don't prompt for changelog
        isInitialSave = true;
        changelog = 'Initial version';
    }
    
    try {
        // Update button state
        const saveButton = document.getElementById('saveButtonText');
        const originalText = saveButton.textContent;
        saveButton.textContent = '⏳ Saving...';
        
        // Call API to save edited code
        const response = await fetch(`${API_BASE}/scripts/${currentScriptId}/save-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: editedCode,
                changelog: changelog,
                author: 'user',
                isInitialSave: isInitialSave
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save code');
        }
        
        const result = await response.json();
        
        // Reset button
        saveButton.textContent = originalText;
        
        // Show appropriate success message
        if (result.isInitialVersion) {
            showNotification(`✅ Initial script saved! Version: ${result.newVersion}`, 'success');
        } else {
            showNotification(`✅ Code saved! New version: ${result.newVersion}`, 'success');
        }
        
        // Exit edit mode without prompting (we just saved)
        isEditMode = false;
        document.getElementById('codeDisplay').style.display = 'block';
        document.getElementById('codeEditor').style.display = 'none';
        document.getElementById('editCodeButton').style.display = 'inline-block';
        document.getElementById('saveCodeButton').style.display = 'none';
        document.getElementById('cancelEditButton').style.display = 'none';
        document.getElementById('copyCodeButton').style.display = 'inline-block';
        document.getElementById('reviewButtonText').parentElement.style.display = 'inline-block';
        
        // Reload scripts list
        await loadScripts();
        
        // Refresh code view to show version
        await viewCode(currentScriptId, result.newVersion);
        
    } catch (error) {
        console.error('Error saving code:', error);
        showNotification(`Error: ${error.message}`, 'error');
        
        // Reset button
        const saveButton = document.getElementById('saveButtonText');
        saveButton.textContent = '💾 Save';
    }
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
    const filePathField = document.getElementById('edit_filePath');
    
    if (scriptId) {
        // Edit mode
        const script = allScripts.find(s => s.id === scriptId);
        if (!script) return;
        
        title.textContent = 'Edit Script';
        
        // Populate form
        document.getElementById('edit_name').value = script.name || '';
        document.getElementById('edit_type').value = script.type || 'indicator';
        document.getElementById('edit_version').value = script.currentVersion || script.version || '1.0.0';
        document.getElementById('edit_status').value = script.status || 'active';
        filePathField.value = script.filePath || '';
        document.getElementById('edit_description').value = script.description || '';
        document.getElementById('edit_author').value = script.author || '';
        document.getElementById('edit_tags').value = (script.tags || []).join(', ');
        document.getElementById('edit_timeframes').value = (script.timeframes || []).join(', ');
        document.getElementById('edit_notes').value = script.notes || '';
        
        // Make file path read-only in edit mode (can't change existing file location)
        filePathField.readOnly = true;
        filePathField.style.backgroundColor = 'var(--dark-bg)';
        filePathField.style.cursor = 'not-allowed';
        
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
        
        // Enable file path field in create mode
        filePathField.readOnly = false;
        filePathField.style.backgroundColor = '';
        filePathField.style.cursor = '';
        
        // Trigger initial path generation if name already has a value
        generateFilePath();
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
        description: document.getElementById('edit_description').value,
        author: document.getElementById('edit_author').value,
        pineVersion: 5
    };
    
    // Only include filePath when creating (not editing - backend preserves existing path)
    if (!editingScriptId) {
        formData.filePath = document.getElementById('edit_filePath').value;
    }
    
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
            // Updating existing script
            await updateScript(editingScriptId, formData);
            closeEditModal();
        } else {
            // Creating new script - open code editor automatically after save
            const newScript = await createScript(formData);
            closeEditModal();
            
            // Automatically open the code editor in edit mode for the newly created script
            if (newScript && newScript.id) {
                // Small delay to ensure modal transitions smoothly
                setTimeout(async () => {
                    await viewCode(newScript.id);
                    // Enter edit mode automatically so user can paste/write code
                    setTimeout(() => {
                        enterEditMode();
                    }, 100);
                }, 300);
            }
        }
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

// Auto-generate file path based on name and type
function generateFilePath() {
    const name = document.getElementById('edit_name').value.trim();
    const type = document.getElementById('edit_type').value;
    
    if (!name) {
        document.getElementById('edit_filePath').value = '';
        return;
    }
    
    // Convert name to filename format (lowercase, spaces to dashes)
    const filename = name
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '') // Remove special characters except spaces and dashes
        .replace(/\s+/g, '-')          // Replace spaces with dashes
        .replace(/-+/g, '-')           // Replace multiple dashes with single dash
        .trim();
    
    // Determine directory based on type
    let directory = '';
    switch(type) {
        case 'indicator':
            directory = 'scripts/indicators';
            break;
        case 'strategy':
            directory = 'scripts/strategies';
            break;
        case 'study':
            directory = 'scripts/studies';
            break;
        default:
            directory = 'scripts';
    }
    
    // Generate full path
    const filePath = `${directory}/${filename}.pine`;
    document.getElementById('edit_filePath').value = filePath;
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
    
    // Add listeners for auto-generating file path
    const editNameField = document.getElementById('edit_name');
    const editTypeField = document.getElementById('edit_type');
    
    if (editNameField) {
        editNameField.addEventListener('input', generateFilePath);
    }
    
    if (editTypeField) {
        editTypeField.addEventListener('change', generateFilePath);
    }
    
    // Modal close handlers
    const modal = document.getElementById('scriptModal');
    const codeModal = document.getElementById('codeModal');
    const editModal = document.getElementById('editModal');
    const reviewModal = document.getElementById('reviewModal');
    
    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
        if (event.target === codeModal) {
            closeCodeModal();
        }
        if (event.target === editModal) {
            closeEditModal();
        }
        if (event.target === reviewModal) {
            closeReviewModal();
        }
    };
});

// Code Review Functions
let currentReviewData = null;

async function reviewCode() {
    if (!currentScriptId) {
        showNotification('No script loaded for review', 'error');
        return;
    }
    
    try {
        // Update button state
        const reviewButton = document.getElementById('reviewButtonText');
        const originalText = reviewButton.textContent;
        reviewButton.textContent = '⏳ Reviewing...';
        
        // Build URL with version parameter if specific version is selected
        let url = `${API_BASE}/scripts/${currentScriptId}/review`;
        if (currentSelectedVersion) {
            url += `?version=${encodeURIComponent(currentSelectedVersion)}`;
        }
        
        // Fetch review
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to review code');
        }
        
        const reviewData = await response.json();
        currentReviewData = reviewData;  // Store for PDF export
        
        // Reset button
        reviewButton.textContent = originalText;
        
        // Display review results (with version info)
        displayReviewResults(reviewData);
        
    } catch (error) {
        console.error('Error reviewing code:', error);
        showNotification(`Error: ${error.message}`, 'error');
        
        // Reset button
        const reviewButton = document.getElementById('reviewButtonText');
        reviewButton.textContent = '🔍 Code Review';
    }
}

function displayReviewResults(reviewData) {
    const modalBody = document.getElementById('reviewModalBody');
    
    // Count issues by severity
    const criticalCount = reviewData.issues.filter(i => i.severity === 'CRITICAL').length;
    const highCount = reviewData.issues.filter(i => i.severity === 'HIGH').length;
    const warningCount = reviewData.issues.filter(i => i.severity === 'WARNING').length;
    const passCount = reviewData.issues.filter(i => i.severity === 'PASS').length;
    
    // Build summary with version info
    const reviewedVersion = reviewData.reviewedVersion || 'current';
    
    let summaryHTML = `
        <div style="margin-bottom: 15px; padding: 10px; background: var(--dark-bg); border-radius: 6px; border-left: 3px solid var(--primary-color);">
            <strong>Reviewing:</strong> ${escapeHtml(reviewData.scriptName)} 
            <span style="color: var(--text-secondary);">(Version: ${escapeHtml(reviewedVersion)})</span>
        </div>
        
        <div id="reviewStatusMessage" style="margin-bottom: 15px; padding: 10px; background: var(--dark-bg); border-radius: 6px; border-left: 3px solid var(--secondary-color); display: none; min-height: 40px; align-items: center;">
            <span id="reviewStatusText" style="color: var(--text-secondary); font-style: italic;"></span>
        </div>
        
        <div class="review-summary">
            <div class="review-summary-item critical">
                <h3>${criticalCount}</h3>
                <p>Critical Issues</p>
            </div>
            <div class="review-summary-item high">
                <h3>${highCount}</h3>
                <p>High Priority</p>
            </div>
            <div class="review-summary-item warning">
                <h3>${warningCount}</h3>
                <p>Warnings</p>
            </div>
            <div class="review-summary-item pass">
                <h3>${passCount}</h3>
                <p>Passed Checks</p>
            </div>
        </div>
    `;
    
    // Overall assessment
    let overallStatus = 'pass';
    let overallMessage = '✅ All checks passed! Code follows Pine Script v5 standards.';
    
    if (criticalCount > 0) {
        overallStatus = 'critical';
        overallMessage = '🔴 Critical issues found! These must be fixed before deployment.';
    } else if (highCount > 0) {
        overallStatus = 'high';
        overallMessage = '⚠️ High priority issues found. Review and fix recommended.';
    } else if (warningCount > 0) {
        overallStatus = 'warning';
        overallMessage = '⚡ Minor warnings detected. Code is functional but could be improved.';
    }
    
    summaryHTML += `
        <div class="review-item severity-${overallStatus}" style="margin-bottom: 25px;">
            <div class="review-item-header">
                <span class="review-item-title">${overallMessage}</span>
            </div>
        </div>
    `;
    
    // Group issues by category
    const categories = {
        'Script Structure': [],
        'Naming Conventions': [],
        'Formatting': [],
        'Performance': [],
        'Logical Sanity': [],
        'Other': []
    };
    
    reviewData.issues.forEach(issue => {
        const category = issue.category || 'Other';
        if (!categories[category]) {
            categories[category] = [];
        }
        categories[category].push(issue);
    });
    
    // Build issues HTML
    let issuesHTML = '';
    for (const [category, issues] of Object.entries(categories)) {
        if (issues.length === 0) continue;
        
        issuesHTML += `
            <div class="review-section">
                <h3>${category}</h3>
        `;
        
        issues.forEach(issue => {
            const severityClass = issue.severity.toLowerCase();
            issuesHTML += `
                <div class="review-item severity-${severityClass}">
                    <div class="review-item-header">
                        <span class="review-item-title">${escapeHtml(issue.check)}</span>
                        <span class="review-item-badge ${severityClass}">${issue.severity}</span>
                    </div>
                    <div class="review-item-message">${escapeHtml(issue.message)}</div>
                    ${issue.line ? `<div style="color: var(--text-secondary); font-size: 0.85rem;">Line ${issue.line}</div>` : ''}
                    ${issue.code ? `<div class="review-item-code">${escapeHtml(issue.code)}</div>` : ''}
                </div>
            `;
        });
        
        issuesHTML += '</div>';
    }
    
    // Recommendations
    let recommendationsHTML = '';
    if (reviewData.recommendations && reviewData.recommendations.length > 0) {
        recommendationsHTML = `
            <div class="review-recommendations">
                <h3>📚 Recommendations</h3>
                <ul>
                    ${reviewData.recommendations.map(rec => `<li>${escapeHtml(rec)}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Combine all HTML
    modalBody.innerHTML = summaryHTML + issuesHTML + recommendationsHTML;
    
    // Show export and copy buttons
    const exportBtn = document.getElementById('exportPdfBtn');
    if (exportBtn) {
        exportBtn.style.display = 'block';
    }
    const copyReviewBtn = document.getElementById('copyReviewBtn');
    if (copyReviewBtn) {
        copyReviewBtn.style.display = 'block';
    }
    
    // Show auto-fix button if there are fixable issues
    const autoFixBtn = document.getElementById('autoFixBtn');
    const smartAutoFixBtn = document.getElementById('smartAutoFixBtn');
    const autoFixAllBtn = document.getElementById('autoFixAllBtn');
    const hasFixableIssues = criticalCount > 0 || highCount > 0 || warningCount > 0;
    const hasCriticalOrHighIssues = criticalCount > 0 || highCount > 0;
    
    if (autoFixBtn && hasFixableIssues) {
        autoFixBtn.style.display = 'block';
    }
    
    // Show smart auto-fix button only if there are CRITICAL or HIGH issues
    if (smartAutoFixBtn && hasCriticalOrHighIssues) {
        smartAutoFixBtn.style.display = 'block';
    }
    
    // Show Auto-Fix All button if there are any fixable issues (best value for users!)
    if (autoFixAllBtn && hasFixableIssues) {
        autoFixAllBtn.style.display = 'block';
    }
    
    // Show modal
    const modal = document.getElementById('reviewModal');
    modal.style.display = 'block';
}

function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    modal.style.display = 'none';
    // Hide export and copy buttons
    const exportBtn = document.getElementById('exportPdfBtn');
    if (exportBtn) {
        exportBtn.style.display = 'none';
    }
    const copyReviewBtn = document.getElementById('copyReviewBtn');
    if (copyReviewBtn) {
        copyReviewBtn.style.display = 'none';
    }
    // Hide auto-fix buttons
    const autoFixBtn = document.getElementById('autoFixBtn');
    const smartAutoFixBtn = document.getElementById('smartAutoFixBtn');
    const autoFixAllBtn = document.getElementById('autoFixAllBtn');
    if (autoFixBtn) {
        autoFixBtn.style.display = 'none';
    }
    if (smartAutoFixBtn) {
        smartAutoFixBtn.style.display = 'none';
    }
    if (autoFixAllBtn) {
        autoFixAllBtn.style.display = 'none';
    }
}

// Export review to PDF
// Copy review report to clipboard (formatted for LLM prompts)
function copyReviewToClipboard() {
    if (!currentReviewData) {
        showNotification('No review data available', 'error');
        return;
    }
    
    const reviewData = currentReviewData;
    const reviewedVersion = reviewData.reviewedVersion || 'current';
    
    // Count issues by severity
    const criticalIssues = reviewData.issues.filter(i => i.severity === 'CRITICAL');
    const highIssues = reviewData.issues.filter(i => i.severity === 'HIGH');
    const warningIssues = reviewData.issues.filter(i => i.severity === 'WARNING');
    const passedChecks = reviewData.issues.filter(i => i.severity === 'PASS');
    
    // Build formatted text report
    let report = `CODE REVIEW REPORT
${'='.repeat(70)}

Script: ${reviewData.scriptName}
Version: ${reviewedVersion}

SUMMARY
${'-'.repeat(70)}
Critical Issues: ${criticalIssues.length}
High Priority: ${highIssues.length}
Warnings: ${warningIssues.length}
Passed Checks: ${passedChecks.length}

`;
    
    // Add critical issues
    if (criticalIssues.length > 0) {
        report += `\nCRITICAL ISSUES (${criticalIssues.length})\n${'-'.repeat(70)}\n`;
        criticalIssues.forEach((issue, idx) => {
            report += `\n${idx + 1}. [${issue.category}] ${issue.check}\n`;
            if (issue.line) report += `   Line ${issue.line}\n`;
            report += `   ${issue.message}\n`;
            if (issue.code) report += `   Code: ${issue.code}\n`;
        });
    }
    
    // Add high priority issues
    if (highIssues.length > 0) {
        report += `\nHIGH PRIORITY ISSUES (${highIssues.length})\n${'-'.repeat(70)}\n`;
        highIssues.forEach((issue, idx) => {
            report += `\n${idx + 1}. [${issue.category}] ${issue.check}\n`;
            if (issue.line) report += `   Line ${issue.line}\n`;
            report += `   ${issue.message}\n`;
            if (issue.code) report += `   Code: ${issue.code}\n`;
        });
    }
    
    // Add warnings
    if (warningIssues.length > 0) {
        report += `\nWARNINGS (${warningIssues.length})\n${'-'.repeat(70)}\n`;
        warningIssues.forEach((issue, idx) => {
            report += `\n${idx + 1}. [${issue.category}] ${issue.check}\n`;
            if (issue.line) report += `   Line ${issue.line}\n`;
            report += `   ${issue.message}\n`;
            if (issue.code) report += `   Code: ${issue.code}\n`;
        });
    }
    
    // Add recommendations if any
    if (reviewData.recommendations && reviewData.recommendations.length > 0) {
        report += `\nRECOMMENDATIONS\n${'-'.repeat(70)}\n`;
        reviewData.recommendations.forEach((rec, idx) => {
            report += `${idx + 1}. ${rec}\n`;
        });
    }
    
    report += `\n${'='.repeat(70)}\n`;
    report += `End of Report\n`;
    
    // Copy to clipboard
    navigator.clipboard.writeText(report).then(() => {
        const copyBtn = document.getElementById('copyReviewButtonText');
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✅ Copied!';
        showNotification('Code review copied to clipboard!', 'success');
        
        // Reset button text after 2 seconds
        setTimeout(() => {
            copyBtn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy review:', err);
        showNotification('Failed to copy review', 'error');
    });
}

async function exportReviewToPDF() {
    if (!currentReviewData) {
        showNotification('No review data available', 'error');
        return;
    }
    
    try {
        // Update button state
        const exportButton = document.getElementById('exportButtonText');
        const originalText = exportButton.textContent;
        exportButton.textContent = '⏳ Generating PDF...';
        
        // Get the review content
        const element = document.getElementById('reviewModalBody');
        
        // Clone the element to avoid modifying the original
        const clonedElement = element.cloneNode(true);
        
        // Create a wrapper for better PDF formatting
        const wrapper = document.createElement('div');
        wrapper.style.padding = '20px';
        wrapper.style.backgroundColor = '#ffffff';
        wrapper.style.color = '#000000';
        wrapper.style.fontFamily = 'Arial, sans-serif';
        
        // Add header
        const header = document.createElement('div');
        header.style.marginBottom = '20px';
        header.style.borderBottom = '2px solid #333';
        header.style.paddingBottom = '10px';
        header.innerHTML = `
            <h1 style="margin: 0; color: #2962ff;">Pine Script Code Review Report</h1>
            <p style="margin: 5px 0; color: #666;">Script: ${escapeHtml(currentReviewData.scriptName)}</p>
            <p style="margin: 5px 0; color: #666;">Generated: ${new Date().toLocaleString()}</p>
        `;
        wrapper.appendChild(header);
        
        // Style the cloned content for PDF
        styleForPDF(clonedElement);
        wrapper.appendChild(clonedElement);
        
        // Configure PDF options
        const opt = {
            margin: [10, 10, 10, 10],
            filename: `code-review-${currentReviewData.scriptName.replace(/[^a-z0-9]/gi, '-').toLowerCase()}-${Date.now()}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { 
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff'
            },
            jsPDF: { 
                unit: 'mm', 
                format: 'a4', 
                orientation: 'portrait'
            },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };
        
        // Generate PDF
        await html2pdf().set(opt).from(wrapper).save();
        
        // Reset button
        exportButton.textContent = originalText;
        showNotification('PDF exported successfully!', 'success');
        
    } catch (error) {
        console.error('Error exporting PDF:', error);
        showNotification(`Error exporting PDF: ${error.message}`, 'error');
        
        // Reset button
        const exportButton = document.getElementById('exportButtonText');
        exportButton.textContent = '📄 Export PDF';
    }
}

// Style content for PDF export
function styleForPDF(element) {
    // Convert dark theme colors to print-friendly colors
    const styleMap = {
        'review-summary': 'border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; background: #f9f9f9;',
        'review-summary-item': 'text-align: center; padding: 10px; border: 1px solid #ddd; background: #fff;',
        'review-section': 'margin-bottom: 20px; page-break-inside: avoid;',
        'review-item': 'border-left: 4px solid #ddd; padding: 12px; margin-bottom: 10px; background: #fff; page-break-inside: avoid;',
        'review-item.severity-critical': 'border-left-color: #f44336; background: #ffebee;',
        'review-item.severity-high': 'border-left-color: #ff9800; background: #fff3e0;',
        'review-item.severity-warning': 'border-left-color: #ffc107; background: #fffde7;',
        'review-item.severity-pass': 'border-left-color: #4caf50; background: #e8f5e9;',
        'review-item-badge': 'padding: 4px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; color: #fff;',
        'review-item-badge.critical': 'background: #f44336;',
        'review-item-badge.high': 'background: #ff9800;',
        'review-item-badge.warning': 'background: #ffc107; color: #000;',
        'review-item-badge.pass': 'background: #4caf50;',
        'review-item-code': 'background: #f5f5f5; padding: 8px; border-radius: 3px; font-family: monospace; font-size: 10px; color: #333; word-wrap: break-word;',
        'review-recommendations': 'background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px;'
    };
    
    // Apply styles recursively
    function applyStyles(el) {
        const classList = Array.from(el.classList || []);
        
        // Check for direct class matches
        for (const className of classList) {
            if (styleMap[className]) {
                el.style.cssText = styleMap[className];
            }
            
            // Check for compound classes
            for (const [selector, style] of Object.entries(styleMap)) {
                if (selector.includes('.') && classList.some(c => selector.includes(c))) {
                    const classes = selector.split('.');
                    if (classes.every(c => !c || classList.includes(c))) {
                        el.style.cssText = (el.style.cssText || '') + style;
                    }
                }
            }
        }
        
        // Apply general text color for readability
        if (el.style.color === '' || window.getComputedStyle(el).color.includes('240')) {
            el.style.color = '#333';
        }
        
        // Process children
        Array.from(el.children).forEach(child => applyStyles(child));
    }
    
    applyStyles(element);
    
    // Apply h3 styling
    element.querySelectorAll('h3').forEach(h3 => {
        h3.style.color = '#2962ff';
        h3.style.fontSize = '16px';
        h3.style.marginBottom = '10px';
        h3.style.borderBottom = '2px solid #ddd';
        h3.style.paddingBottom = '5px';
    });
    
    // Apply severity colors to summary items
    element.querySelectorAll('.review-summary-item.critical h3').forEach(el => el.style.color = '#f44336');
    element.querySelectorAll('.review-summary-item.high h3').forEach(el => el.style.color = '#ff9800');
    element.querySelectorAll('.review-summary-item.warning h3').forEach(el => el.style.color = '#ffc107');
    element.querySelectorAll('.review-summary-item.pass h3').forEach(el => el.style.color = '#4caf50');
}

// Auto-fix code issues
async function autoFixCode() {
    if (!currentScriptId || !currentReviewData) {
        showNotification('No review data available', 'error');
        return;
    }
    
    // Confirm before proceeding
    const issuesCount = currentReviewData.summary.critical + currentReviewData.summary.high + currentReviewData.summary.warning;
    const confirmMessage = `Auto-fix will attempt to automatically correct ${issuesCount} issue(s) and increment the version number.\n\nA backup will be created before making changes.\n\nProceed?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        // Show status message
        const statusMessage = document.getElementById('reviewStatusMessage');
        const statusText = document.getElementById('reviewStatusText');
        if (statusMessage && statusText) {
            statusMessage.style.display = 'flex';
            statusText.textContent = '⏳ Applying Quick Fix...';
        }
        
        // Call auto-fix API
        const response = await fetch(`${API_BASE}/scripts/${currentScriptId}/autofix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                issues: currentReviewData.issues
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to auto-fix code');
        }
        
        const result = await response.json();
        
        // Hide status message
        if (statusMessage) {
            statusMessage.style.display = 'none';
        }
        
        // Show success message with details
        const fixedCount = result.fixedIssues || 0;
        const newVersion = result.newVersion || 'unknown';
        showNotification(`✅ Fixed ${fixedCount} issue(s)! New version: ${newVersion}`, 'success');
        
        // Close review modal
        closeReviewModal();
        
        // Reload scripts to show updated version
        await loadScripts();
        
        // Optionally, re-open the code viewer to show fixed code
        if (confirm('Would you like to view the fixed code?')) {
            await viewCode(currentScriptId);
        }
        
    } catch (error) {
        console.error('Error auto-fixing code:', error);
        showNotification(`Error: ${error.message}`, 'error');
        
        // Hide status message
        const statusMessage = document.getElementById('reviewStatusMessage');
        if (statusMessage) {
            statusMessage.style.display = 'none';
        }
    }
}

// ============================================================================
// SMART AUTO-FIX (LLM-POWERED)
// ============================================================================

async function smartAutoFixCode() {
    if (!currentScriptId) return;
    
    try {
        // Show status message with progress animation
        const statusMessage = document.getElementById('reviewStatusMessage');
        const statusText = document.getElementById('reviewStatusText');
        
        if (!statusMessage || !statusText) {
            showNotification('Status display not available', 'error');
            return;
        }
        
        statusMessage.style.display = 'flex';
        
        // Create progress animation
        let progressStep = 0;
        const progressSteps = [
            '🔍 Analyzing code structure...',
            '📋 Identifying issues...',
            '🤖 Sending to AI...',
            '✨ AI is thinking...',
            '🔧 Generating fixes...',
            '📝 Applying changes...'
        ];
        
        const progressInterval = setInterval(() => {
            statusText.textContent = progressSteps[progressStep % progressSteps.length];
            progressStep++;
        }, 2000);
        
        // Clear any old cached API key from localStorage (force use of server key)
        localStorage.removeItem('llmApiKey');
        
        // Get API key and settings
        const useServerKey = localStorage.getItem('useServerKey') === 'true';
        const apiKey = localStorage.getItem('llmApiKey');
        const provider = localStorage.getItem('llmProvider') || 'openai';
        
        console.log('DEBUG: useServerKey:', useServerKey);
        console.log('DEBUG: apiKey:', apiKey ? `...${apiKey.slice(-10)}` : 'None');
        
        // Build request body - try server key first if no client key
        const requestBody = {
            provider: provider
        };
        
        // Only send client-side API key if explicitly provided
        if (!useServerKey && apiKey) {
            requestBody.apiKey = apiKey;
        }
        
        console.log('DEBUG: requestBody has apiKey:', !!requestBody.apiKey);
        
        // If no client key and not explicitly using server key, try server key anyway
        // (Server will return error if it doesn't have a key configured)
        
        // Add version if reviewing a specific version
        if (currentSelectedVersion) {
            requestBody.version = currentSelectedVersion;
        }
        
        const response = await fetch(`${API_BASE}/scripts/${currentScriptId}/smart-autofix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            clearInterval(progressInterval);
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to apply smart fixes');
        }
        
        const result = await response.json();
        
        // Clear progress animation and hide status message
        clearInterval(progressInterval);
        statusMessage.style.display = 'none';
        
        if (result.skipped) {
            showNotification('✅ No critical/high issues found to fix', 'success');
            return;
        }
        
        // Show success message with details
        const issuesFixed = result.issuesAddressed || 0;
        const newVersion = result.newVersion || 'unknown';
        showNotification(
            `✨ Smart Fix Complete!\n` +
            `Fixed ${issuesFixed} critical/high issues\n` +
            `New version: ${newVersion}`,
            'success'
        );
        
        // Show explanation if available
        if (result.explanation) {
            const showExplanation = confirm(
                `Smart fixes applied successfully!\n\n` +
                `Would you like to see what was changed?`
            );
            if (showExplanation) {
                alert(`Changes made:\n\n${result.explanation}`);
            }
        }
        
        // Close review modal
        closeReviewModal();
        
        // Reload scripts
        await loadScripts();
        
        // Offer to view fixed code
        if (confirm('Would you like to view the fixed code?')) {
            await viewCode(currentScriptId);
        }
        
    } catch (error) {
        console.error('Error applying smart fixes:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
        
        // Clear progress animation if still running
        if (typeof progressInterval !== 'undefined') {
            clearInterval(progressInterval);
        }
        
        // Hide status message
        const statusMessage = document.getElementById('reviewStatusMessage');
        if (statusMessage) {
            statusMessage.style.display = 'none';
        }
    }
}

// ============================================================================
// AUTO-FIX ALL (HYBRID: QUICK FIX + SMART FIX)
// ============================================================================

async function autoFixAll() {
    if (!currentScriptId) return;
    
    try {
        // Show status message with progress animation
        const statusMessage = document.getElementById('reviewStatusMessage');
        const statusText = document.getElementById('reviewStatusText');
        
        if (!statusMessage || !statusText) {
            showNotification('Status display not available', 'error');
            return;
        }
        
        statusMessage.style.display = 'flex';
        
        // Create enhanced progress animation
        let progressStep = 0;
        const progressSteps = [
            '⚡ Running Quick Fix...',
            '🔍 Re-analyzing code...',
            '🤖 Sending to AI...',
            '✨ AI is thinking...',
            '🔧 Applying smart fixes...',
            '📝 Finalizing changes...'
        ];
        
        const progressInterval = setInterval(() => {
            statusText.textContent = progressSteps[progressStep % progressSteps.length];
            progressStep++;
        }, 2500);
        
        // Clear any old cached API key
        localStorage.removeItem('llmApiKey');
        
        // Get settings
        const useServerKey = localStorage.getItem('useServerKey') === 'true';
        const apiKey = localStorage.getItem('llmApiKey');
        const provider = localStorage.getItem('llmProvider') || 'openai';
        
        const requestBody = {
            provider: provider
        };
        
        // Only send client-side API key if explicitly provided
        if (!useServerKey && apiKey) {
            requestBody.apiKey = apiKey;
        }
        
        // Add version if reviewing a specific version
        if (currentSelectedVersion) {
            requestBody.version = currentSelectedVersion;
        }
        
        const response = await fetch(`${API_BASE}/scripts/${currentScriptId}/auto-fix-all`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            clearInterval(progressInterval);
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to apply auto-fix all');
        }
        
        const result = await response.json();
        
        // Clear progress animation and hide status message
        clearInterval(progressInterval);
        statusMessage.style.display = 'none';
        
        // Build detailed success message
        const quickFixes = result.quickFixesApplied || 0;
        const smartFixes = result.criticalHighIssuesAddressed || 0;
        const newVersion = result.newVersion || 'unknown';
        
        let message = `⚡ Auto-Fix All Complete!\n\n`;
        message += `✅ Quick Fix: ${quickFixes} formatting issue(s)\n`;
        
        if (result.smartFixApplied) {
            message += `✅ Smart Fix: ${smartFixes} critical/high issue(s)\n`;
        } else {
            message += `✅ Smart Fix: Not needed (no critical issues remaining)\n`;
        }
        
        message += `\n🎉 New version: ${newVersion}`;
        
        showNotification(message, 'success');
        
        // Show detailed explanation if available
        if (result.smartFixApplied && result.smartExplanation) {
            const showDetails = confirm(
                `Auto-Fix All completed successfully!\n\n` +
                `Quick fixes: ${quickFixes} issues\n` +
                `Smart fixes: ${smartFixes} issues\n\n` +
                `Would you like to see what the AI changed?`
            );
            if (showDetails) {
                alert(`AI Changes:\n\n${result.smartExplanation}`);
            }
        }
        
        // Close review modal
        closeReviewModal();
        
        // Reload scripts
        await loadScripts();
        
        // Offer to view fixed code
        if (confirm('Would you like to view the fixed code?')) {
            await viewCode(currentScriptId);
        }
        
    } catch (error) {
        console.error('Error applying auto-fix all:', error);
        showNotification(`❌ Error: ${error.message}`, 'error');
        
        // Clear progress animation if still running
        if (typeof progressInterval !== 'undefined') {
            clearInterval(progressInterval);
        }
        
        // Hide status message
        const statusMessage = document.getElementById('reviewStatusMessage');
        if (statusMessage) {
            statusMessage.style.display = 'none';
        }
    }
}

// ============================================================================
// SETTINGS MODAL
// ============================================================================

function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    
    // Load saved settings
    const apiKey = localStorage.getItem('llmApiKey') || '';
    const provider = localStorage.getItem('llmProvider') || 'openai';
    const useServerKey = localStorage.getItem('useServerKey') === 'true';
    
    document.getElementById('apiKeyInput').value = apiKey;
    document.getElementById('llmProvider').value = provider;
    document.getElementById('useServerKey').checked = useServerKey;
    
    // Update UI based on checkbox
    toggleApiKeyInput();
    
    modal.style.display = 'flex';
}

function closeSettingsModal() {
    const modal = document.getElementById('settingsModal');
    modal.style.display = 'none';
}

function toggleApiKeyInput() {
    const useServerKey = document.getElementById('useServerKey').checked;
    const apiKeyInput = document.getElementById('apiKeyInput');
    
    if (useServerKey) {
        apiKeyInput.disabled = true;
        apiKeyInput.style.opacity = '0.5';
    } else {
        apiKeyInput.disabled = false;
        apiKeyInput.style.opacity = '1';
    }
}

function updateApiKeyPlaceholder() {
    const provider = document.getElementById('llmProvider').value;
    const apiKeyInput = document.getElementById('apiKeyInput');
    
    if (provider === 'openai') {
        apiKeyInput.placeholder = 'sk-...';
    } else if (provider === 'claude') {
        apiKeyInput.placeholder = 'sk-ant-...';
    }
}

function saveSettings() {
    const apiKey = document.getElementById('apiKeyInput').value;
    const provider = document.getElementById('llmProvider').value;
    const useServerKey = document.getElementById('useServerKey').checked;
    
    // Validate API key if not using server key
    if (!useServerKey && apiKey && !apiKey.startsWith('sk-')) {
        alert('⚠️ Warning: API key should start with "sk-"');
        return;
    }
    
    // Save to localStorage
    if (apiKey) {
        localStorage.setItem('llmApiKey', apiKey);
    }
    localStorage.setItem('llmProvider', provider);
    localStorage.setItem('useServerKey', useServerKey.toString());
    
    showNotification('✅ Settings saved successfully!', 'success');
    closeSettingsModal();
}

function clearApiKey() {
    if (confirm('Are you sure you want to clear your stored API key?')) {
        localStorage.removeItem('llmApiKey');
        document.getElementById('apiKeyInput').value = '';
        showNotification('✅ API key cleared', 'success');
    }
}
