// ================================================
// 批量审查页面
// ================================================
async function renderBatchReviewPage(container) {
    window._batchFiles = [];  // 当前选择的文件列表

    container.innerHTML = `
        <div class="container">
            <div class="page-header">
                <h2>📦 批量审查</h2>
                <p>一次上传多份初稿，同时创建多个审查任务，适合大量送审文件</p>
            </div>

            <!-- 步骤引导 -->
            <div class="steps" style="margin-bottom:32px">
                <div class="step active" id="batch-step-1">
                    <div class="step-num">1</div>
                    <div class="step-label">选择参考标准</div>
                </div>
                <div class="step-line"></div>
                <div class="step" id="batch-step-2">
                    <div class="step-num">2</div>
                    <div class="step-label">批量上传初稿</div>
                </div>
                <div class="step-line"></div>
                <div class="step" id="batch-step-3">
                    <div class="step-num">3</div>
                    <div class="step-label">确认并提交</div>
                </div>
            </div>

            <div id="batch-content"></div>
        </div>`;

    await renderBatchStep1();
}

async function renderBatchStep1() {
    updateBatchStep(1);
    const res = await standardsAPI.list();
    const standards = res.data || [];
    const selectedIds = [];

    const content = document.getElementById('batch-content');
    if (standards.length === 0) {
        content.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="empty-state">
                        <div class="empty-icon">📂</div>
                        <p>还没有上传任何参考标准</p>
                        <button class="btn btn-primary" onclick="APP.goTo('standards')">去上传标准</button>
                    </div>
                </div>
            </div>`;
        return;
    }

    content.innerHTML = `
        <div class="card">
            <div class="card-header"><h3>选择参考标准</h3></div>
            <div class="card-body">
                <p style="font-size:14px;color:var(--text-muted);margin-bottom:16px">请选择本次批量审查所使用的参考标准，所有初稿将共用此标准</p>
                ${standards.map((s, i) => `
                    <div class="standard-select-item" id="batch-std-${s.id}" onclick="toggleBatchStandard('${s.id}', ${i})">
                        <input type="checkbox" id="batch-cb-${s.id}" style="width:18px;height:18px;cursor:pointer;margin-right:12px;accent-color:var(--primary)">
                        <div class="standard-icon ${s.file_type}" style="flex-shrink:0">${s.file_type.toUpperCase()}</div>
                        <div style="flex:1">
                            <div style="font-size:15px;font-weight:500">${s.name}</div>
                            <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${s.number || ''} · ${formatDate(s.upload_time)}</div>
                        </div>
                        <div id="batch-std-check-${s.id}" style="flex-shrink:0;color:var(--text-muted);font-size:13px">点击选择</div>
                    </div>
                `).join('')}
                <div style="margin-top:20px;display:flex;justify-content:space-between;align-items:center">
                    <div style="font-size:13px;color:var(--text-muted)">已选择 <strong id="batch-selected-count">0</strong> 项</div>
                    <button class="btn btn-primary" id="batch-step1-next" onclick="renderBatchStep2()" disabled>下一步 →</button>
                </div>
            </div>
        </div>`;

    window._batchSelectedStdIds = [];

    window.toggleBatchStandard = function(id, idx) {
        const cb = document.getElementById('batch-cb-' + id);
        const check = document.getElementById('batch-std-check-' + id);
        const item = document.getElementById('batch-std-' + id);
        cb.checked = !cb.checked;
        if (cb.checked) {
            window._batchSelectedStdIds.push(id);
            check.innerHTML = '<span style="color:var(--primary);font-weight:600">✓ 已选择</span>';
            item.classList.add('selected');
        } else {
            window._batchSelectedStdIds = window._batchSelectedStdIds.filter(sid => sid !== id);
            check.innerHTML = '点击选择';
            item.classList.remove('selected');
        }
        document.getElementById('batch-selected-count').textContent = window._batchSelectedStdIds.length;
        document.getElementById('batch-step1-next').disabled = window._batchSelectedStdIds.length === 0;
    };
}

async function renderBatchStep2() {
    if (window._batchSelectedStdIds.length === 0) {
        showToast('请先选择参考标准', 'error'); return;
    }
    updateBatchStep(2);
    const content = document.getElementById('batch-content');
    content.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h3>批量上传初稿</h3>
            </div>
            <div class="card-body">
                <div class="form-group">
                    <label>批次名称（可选）</label>
                    <input type="text" id="batch-name" class="form-input" placeholder="如：2024年第一批送审稿（留空自动生成）">
                </div>
                <div class="upload-zone" id="batch-upload-zone" style="margin-top:16px;border:2px dashed var(--primary);background:rgba(26,86,219,0.03)">
                    <input type="file" id="batch-file-input" multiple accept=".pdf,.docx,.doc" />
                    <div class="upload-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:32px;height:32px;color:var(--primary)">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="17 8 12 3 7 8"/>
                            <line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                    </div>
                    <h4 style="color:var(--primary)">拖拽文件到此处</h4>
                    <p>支持多选，一次最多20份 · 支持 PDF、Word (.docx)</p>
                </div>
                <div id="batch-file-list" style="margin-top:16px;display:flex;flex-direction:column;gap:8px"></div>
                <div style="margin-top:20px;display:flex;justify-content:space-between">
                    <button class="btn btn-secondary" onclick="renderBatchStep1()">← 上一步</button>
                    <button class="btn btn-primary" id="batch-step2-next" onclick="renderBatchStep3()" disabled>下一步 →</button>
                </div>
            </div>
        </div>`;

    const fileInput = document.getElementById('batch-file-input');
    const fileList = document.getElementById('batch-file-list');
    window._batchFiles = [];

    fileInput.addEventListener('change', () => {
        addBatchFiles(Array.from(fileInput.files));
    });

    const zone = document.getElementById('batch-upload-zone');
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        addBatchFiles(Array.from(e.dataTransfer.files));
    });

    function addBatchFiles(files) {
        const valid = files.filter(f => f.name.match(/\.(pdf|docx|doc)$/i));
        if (!valid.length) { showToast('请上传 PDF 或 Word 文件', 'error'); return; }
        if (window._batchFiles.length + valid.length > 20) {
            showToast('单次批量任务不超过20份', 'error'); return;
        }
        window._batchFiles.push(...valid);
        renderFileList();
    }

    function renderFileList() {
        if (window._batchFiles.length === 0) {
            fileList.innerHTML = '';
            document.getElementById('batch-step2-next').disabled = true;
            return;
        }
        fileList.innerHTML = window._batchFiles.map((f, i) => `
            <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:var(--bg-secondary);border-radius:8px;border:1px solid var(--border)">
                <span style="font-size:18px">📄</span>
                <div style="flex:1;min-width:0">
                    <div style="font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${f.name}</div>
                    <div style="font-size:11px;color:var(--text-muted)">${formatSize(f.size)}</div>
                </div>
                <button onclick="removeBatchFile(${i})" style="background:none;border:none;cursor:pointer;font-size:16px;color:var(--text-muted)">✕</button>
            </div>`).join('');
        document.getElementById('batch-step2-next').disabled = false;
    }

    window.removeBatchFile = function(idx) {
        window._batchFiles.splice(idx, 1);
        renderFileList();
    };
}

async function renderBatchStep3() {
    if (!window._batchFiles || window._batchFiles.length === 0) {
        showToast('请先上传初稿文件', 'error'); return;
    }
    updateBatchStep(3);
    const content = document.getElementById('batch-content');
    const batchName = document.getElementById('batch-name')?.value?.trim() || '';

    // 获取已选标准名称
    const stdNames = window._batchSelectedStdIds.map(sid => {
        const el = document.getElementById('batch-std-' + sid);
        return el ? el.querySelector('div[style*="font-size:15px"]')?.textContent || sid : sid;
    }).join('、');

    content.innerHTML = `
        <div class="card">
            <div class="card-header"><h3>确认并提交</h3></div>
            <div class="card-body">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
                    <div class="form-group">
                        <label>批次名称</label>
                        <div style="padding:10px 12px;background:var(--bg-secondary);border-radius:var(--radius-sm);font-size:14px;border:1px solid var(--border)">${batchName || '(自动生成)'}</div>
                    </div>
                    <div class="form-group">
                        <label>文件数量</label>
                        <div style="padding:10px 12px;background:var(--bg-secondary);border-radius:var(--radius-sm);font-size:14px;border:1px solid var(--border)">${window._batchFiles.length} 份初稿</div>
                    </div>
                </div>
                <div class="form-group" style="margin-bottom:20px">
                    <label>参考标准</label>
                    <div style="padding:10px 12px;background:var(--bg-secondary);border-radius:var(--radius-sm);font-size:13px;border:1px solid var(--border);color:var(--text-muted);line-height:1.8">${stdNames}</div>
                </div>
                <div style="display:flex;justify-content:space-between">
                    <button class="btn btn-secondary" onclick="renderBatchStep2()">← 上一步</button>
                    <button class="btn btn-primary" id="batch-submit-btn" onclick="submitBatchReview()">
                        📦 确认创建 ${window._batchFiles.length} 个审查任务
                    </button>
                </div>
            </div>
        </div>`;
}

async function submitBatchReview() {
    const btn = document.getElementById('batch-submit-btn');
    const batchName = document.getElementById('batch-name')?.value?.trim() || '';
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px"></span> 提交中...';
    try {
        const res = await reviewsAPI.batchCreate(
            batchName,
            window._batchSelectedStdIds.join(','),
            window._batchFiles
        );
        if (res.success) {
            showToast(`批量任务已创建：${res.data.total_count} 份`, 'success');
            APP.goTo('history');
        } else {
            showToast(res.message || '创建失败', 'error');
            btn.disabled = false;
            btn.textContent = '提交失败，请重试';
        }
    } catch(e) {
        showToast('提交失败：' + e.message, 'error');
        btn.disabled = false;
        btn.textContent = '提交失败，请重试';
    }
}

function updateBatchStep(step) {
    for (let i = 1; i <= 3; i++) {
        const el = document.getElementById('batch-step-' + i);
        if (!el) continue;
        el.classList.remove('active', 'completed');
        if (i < step) el.classList.add('completed');
        else if (i === step) el.classList.add('active');
    }
}
