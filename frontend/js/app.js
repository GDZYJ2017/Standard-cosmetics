// === 应用主逻辑 ===
const APP = {
    currentPage: 'standards',
    selectedStandardId: null,
    selectedStandardName: null,
    currentTaskId: null,
    pollTimer: null,

    init() {
        this.renderNav();
        this.navigate(this.getHashPage() || 'standards');
        window.addEventListener('hashchange', () => {
            this.navigate(this.getHashPage());
        });
    },

    getHashPage() {
        return location.hash.replace('#', '') || 'standards';
    },

    navigate(page) {
        this.currentPage = page;
        this.renderNav();
        const main = document.getElementById('main-content');
        switch (page) {
            case 'standards':   renderStandardsPage(main); break;
            case 'new-review':  renderNewReviewPage(main); break;
            case 'history':     renderKanbanPage(main); break;
            case 'batch-review': renderBatchReviewPage(main); break;
            default:            renderStandardsPage(main);
        }
    },

    renderNav() {
        document.querySelectorAll('.nav-links a').forEach(a => {
            a.classList.toggle('active', a.dataset.page === this.currentPage);
        });
    },

    goTo(page) {
        location.hash = page;
    }
};

// ================================================
// 页面一：参考标准管理
// ================================================
async function renderStandardsPage(container) {
    container.innerHTML = `
        <div class="container">
            <!-- 快速开始（居中、大字体、更舒展） -->
            <div style="margin:32px auto 0;padding:36px 40px;background:linear-gradient(135deg,rgba(26,86,219,0.04) 0%,rgba(59,130,246,0.06) 100%);border-radius:var(--radius);border:1px dashed rgba(26,86,219,0.18);text-align:center;max-width:900px">
                <h3 style="font-size:18px;font-weight:600;margin-bottom:24px;color:var(--primary)">🚀 审查流程</h3>
                <div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px">
                    ${['① 上传参考标准', '② 创建审查任务', '③ 等待 AI 分析', '④ 查看审查报告'].map((s, i) => `
                        <div style="display:flex;align-items:center;gap:10px">
                            <div style="padding:10px 18px;background:white;border-radius:10px;font-size:15px;font-weight:500;box-shadow:var(--shadow-sm);border:1px solid var(--border);white-space:nowrap">${s}</div>
                            ${i < 3 ? '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>' : ''}
                        </div>
                    `).join('')}
                </div>
                <div style="margin-top:26px">
                    <button class="btn btn-primary" style="font-size:15px;padding:10px 22px" onclick="APP.goTo('new-review')">
                        开始审查初稿 →
                    </button>
                </div>
            </div>

            <!-- 上传区域 -->
            <div style="margin-top:24px" class="card">
                <div class="card-header">
                    <h3>📄 上传参考标准</h3>
                </div>
                <div class="card-body">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px">
                        <div class="form-group" style="margin:0">
                            <label>标准名称</label>
                            <input type="text" id="std-name" class="form-input" placeholder="如：化妆品中二甘醇的检验方法">
                        </div>
                        <div class="form-group" style="margin:0">
                            <label>标准号</label>
                            <input type="text" id="std-number" class="form-input" placeholder="如：化妆品安全技术规范（可选）">
                        </div>
                    </div>
                    <div class="upload-zone" id="std-upload-zone">
                        <input type="file" id="std-file-input" accept=".pdf,.docx,.doc" />
                        <div class="upload-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="17 8 12 3 7 8"/>
                                <line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                        </div>
                        <h4>拖拽或点击上传标准文件</h4>
                        <p>支持 PDF、Word (.docx) 格式，检验方法或国家标准均可，最大 50MB</p>
                    </div>
                    <div id="std-selected-file" style="display:none;margin-top:12px;padding:12px;background:#F0F9FF;border-radius:8px;font-size:14px;color:#0369A1;display:flex;align-items:center;gap:8px"></div>
                    <div style="margin-top:16px;display:flex;justify-content:flex-end">
                        <button class="btn btn-primary" id="std-upload-btn" onclick="uploadStandard()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="17 8 12 3 7 8"/>
                                <line x1="12" y1="3" x2="12" y2="15"/>
                            </svg>
                            上传标准
                        </button>
                    </div>
                </div>
            </div>

            <!-- 标准列表 -->
            <div class="card" style="margin-top:24px">
                <div class="card-header">
                    <h3>📚 已上传标准</h3>
                    <span id="std-count" style="font-size:13px;color:var(--text-muted)"></span>
                </div>
                <div class="card-body" id="standards-list" style="padding:0 22px">
                    <div class="empty-state"><div class="spinner"></div><p style="margin-top:12px">加载中...</p></div>
                </div>
            </div>
        </div>
    `;

    // 文件选择显示
    const fileInput = document.getElementById('std-file-input');
    const selectedDiv = document.getElementById('std-selected-file');
    fileInput.addEventListener('change', () => {
        if (fileInput.files[0]) {
            selectedDiv.style.display = 'flex';
            selectedDiv.innerHTML = `
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span>${fileInput.files[0].name} (${formatSize(fileInput.files[0].size)})</span>
            `;
        }
    });

    // 拖拽
    const zone = document.getElementById('std-upload-zone');
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files[0]) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });

    // 加载标准列表
    await loadStandardsList();
}

async function uploadStandard() {
    const file = document.getElementById('std-file-input').files[0];
    if (!file) { showToast('请先选择标准文件', 'error'); return; }
    const name = document.getElementById('std-name').value.trim();
    const number = document.getElementById('std-number').value.trim();
    const btn = document.getElementById('std-upload-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px"></span> 上传中...';
    try {
        const res = await standardsAPI.upload(file, name || file.name, number);
        if (res.success) {
            showToast('标准上传成功！', 'success');
            document.getElementById('std-file-input').value = '';
            document.getElementById('std-selected-file').style.display = 'none';
            document.getElementById('std-name').value = '';
            document.getElementById('std-number').value = '';
            await loadStandardsList();
        } else {
            showToast(res.message || '上传失败', 'error');
        }
    } catch(e) {
        showToast('上传失败：' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> 上传标准';
    }
}

async function loadStandardsList() {
    const listEl = document.getElementById('standards-list');
    if (!listEl) return;
    try {
        const res = await standardsAPI.list();
        const standards = res.data || [];
        document.getElementById('std-count').textContent = `共 ${standards.length} 个标准`;
        if (standards.length === 0) {
            listEl.innerHTML = `<div class="empty-state"><div class="empty-icon">📂</div><p>还没有上传任何参考标准</p></div>`;
            return;
        }
        listEl.innerHTML = standards.map(s => `
            <div class="standard-item">
                <div class="standard-info">
                    <div class="standard-icon ${s.file_type}">${s.file_type.toUpperCase()}</div>
                    <div class="standard-meta">
                        <div class="std-name">${s.name}</div>
                        <div class="std-number">${s.number || '未填写标准号'} · ${formatSize(s.file_size)} · ${formatDate(s.upload_time)}</div>
                    </div>
                </div>
                <div class="standard-actions">
                    <button class="btn btn-sm btn-danger" onclick="deleteStandard('${s.id}')">删除</button>
                </div>
            </div>
        `).join('');
    } catch(e) {
        listEl.innerHTML = `<div class="empty-state"><p style="color:var(--danger)">加载失败：${e.message}</p></div>`;
    }
}

async function deleteStandard(id) {
    if (!confirm('确认删除该参考标准？删除后无法恢复。')) return;
    try {
        const res = await standardsAPI.delete(id);
        if (res.success) {
            showToast('删除成功', 'success');
            await loadStandardsList();
        } else {
            showToast(res.message || '删除失败', 'error');
        }
    } catch(e) {
        showToast('删除失败：' + e.message, 'error');
    }
}

async function deleteReview(id) {
    if (!confirm('确认删除该审查记录？删除后无法恢复。')) return;
    try {
        const res = await reviewsAPI.delete(id);
        if (res.success) {
            showToast('删除成功', 'success');
            await renderKanbanPage(document.getElementById('main-content'));
        } else {
            showToast(res.message || '删除失败', 'error');
        }
    } catch(e) {
        showToast('删除失败：' + e.message, 'error');
    }
}


// ================================================
// 页面二：新建审查任务（三步骤）
// ================================================
let newReviewState = {
    step: 1,
    selectedStandard: null,
    draftFile: null
};

async function renderNewReviewPage(container) {
    newReviewState = { step: 1, selectedStandards: [], draftFile: null };
    window._currentStandards = [];  // 当前步骤1可选择的标准列表（完整对象）
    container.innerHTML = `
        <div class="container">
            <div class="page-header">
                <h2>新建审查任务</h2>
                <p>选择参考标准并上传待审初稿，开始智能审查</p>
            </div>
            <div id="new-review-content"></div>
        </div>
    `;
    await renderNewReviewStep(1);
}

async function renderNewReviewStep(step) {
    newReviewState.step = step;
    const content = document.getElementById('new-review-content');
    if (!content) return;

    const stepsHtml = `
        <div class="steps" style="margin-bottom:32px">
            ${['选择参考标准', '上传待审初稿', '确认并开始'].map((label, i) => {
                const num = i + 1;
                const cls = num < step ? 'completed' : num === step ? 'active' : '';
                const lineClass = num < step ? 'completed' : '';
                return `
                    <div class="step ${cls}">
                        <div class="step-num">${num < step ? '✓' : num}</div>
                        <div class="step-label">${label}</div>
                    </div>
                    ${i < 2 ? `<div class="step-line ${lineClass}"></div>` : ''}
                `;
            }).join('')}
        </div>
    `;

    let bodyHtml = '';

    if (step === 1) {
        const res = await standardsAPI.list();
        const standards = res.data || [];
        window._currentStandards = standards;  // 保存完整对象列表供 toggleStandard 使用
        if (standards.length === 0) {
            bodyHtml = `
                <div class="card">
                    <div class="card-body">
                        <div class="empty-state">
                            <div class="empty-icon">📂</div>
                            <p>还没有上传任何参考标准</p>
                            <button class="btn btn-primary" onclick="APP.goTo('standards')">去上传标准</button>
                        </div>
                    </div>
                </div>`;
        } else {
            const selectedIds = newReviewState.selectedStandards.map(s => s.id);
            bodyHtml = `
                <div class="card">
                    <div class="card-header"><h3>选择参考标准</h3></div>
                    <div class="card-body">
                        <p style="font-size:14px;color:var(--text-muted);margin-bottom:16px">可选择多个参考标准，审查将综合多个标准进行对比分析（至少选择一项）</p>
                        ${standards.map(s => `
                            <div class="standard-select-item ${selectedIds.includes(s.id) ? 'selected' : ''}"
                                 onclick="toggleStandard('${s.id}')">
                                <input type="checkbox" id="std-${s.id}" style="width:18px;height:18px;cursor:pointer;margin-right:12px;accent-color:var(--primary)" ${selectedIds.includes(s.id) ? 'checked' : ''} onclick="event.stopPropagation();toggleStandard('${s.id}')">
                                <div class="standard-icon ${s.file_type}" style="flex-shrink:0">${s.file_type.toUpperCase()}</div>
                                <div style="flex:1">
                                    <div style="font-size:15px;font-weight:500">${s.name}</div>
                                    <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${s.number || ''} · ${formatDate(s.upload_time)}</div>
                                </div>
                                <div style="flex-shrink:0">
                                    ${selectedIds.includes(s.id)
                                        ? '<span style="color:var(--primary);font-weight:600;font-size:14px">✓ 已选择</span>'
                                        : '<span style="color:var(--text-muted);font-size:13px">点击选择</span>'}
                                </div>
                            </div>
                        `).join('')}
                        <div style="margin-top:20px;display:flex;justify-content:space-between;align-items:center">
                            <div style="font-size:13px;color:var(--text-muted)">已选择 <strong id="selected-count">${newReviewState.selectedStandards.length}</strong> 项</div>
                            <button class="btn btn-primary" id="step1-next-btn" onclick="goToStep2()" ${newReviewState.selectedStandards.length === 0 ? 'disabled' : ''}>
                                下一步 →
                            </button>
                        </div>
                    </div>
                </div>`;
        }
    } else if (step === 2) {
        const stdNames = newReviewState.selectedStandards.map(s => s.name).join('、');
        bodyHtml = `
            <div class="card">
                <div class="card-header">
                    <h3>上传待审初稿</h3>
                    <span style="font-size:13px;color:var(--text-muted)">参考标准：${stdNames}</span>
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>任务名称（可选）</label>
                        <input type="text" id="review-name" class="form-input" placeholder="留空将自动生成">
                    </div>
                    <div class="upload-zone" id="draft-upload-zone">
                        <input type="file" id="draft-file-input" accept=".pdf,.docx,.doc" />
                        <div class="upload-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:28px;height:28px">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                <polyline points="14 2 14 8 20 8"/>
                                <line x1="12" y1="7" x2="12" y2="17"/>
                                <line x1="9" y1="10" x2="15" y2="10"/>
                            </svg>
                        </div>
                        <h4>拖拽或点击选择初稿文件</h4>
                        <p>支持 PDF、Word (.docx)，最大 50MB</p>
                    </div>
                    <div id="draft-selected-file" style="display:none;margin-top:12px;padding:12px;background:#F0F9FF;border-radius:8px;font-size:14px;color:#0369A1;display:flex;align-items:center;gap:8px"></div>
                    <div style="margin-top:20px;display:flex;justify-content:space-between">
                        <button class="btn btn-secondary" onclick="renderNewReviewStep(1)">← 上一步</button>
                        <button class="btn btn-primary" onclick="goToStep3()">下一步 →</button>
                    </div>
                </div>
            </div>`;
    } else if (step === 3) {
        const stdNames = newReviewState.selectedStandards.map(s => s.name).join('、');
        const stdNumbers = newReviewState.selectedStandards.map(s => s.number || '—').join('、');
        bodyHtml = `
            <div class="card">
                <div class="card-header"><h3>确认审查信息</h3></div>
                <div class="card-body">
                    <div style="background:#F9FAFB;border-radius:10px;padding:20px;margin-bottom:20px">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                            <div>
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">参考标准（共${newReviewState.selectedStandards.length}项）</div>
                                <div style="font-size:15px;font-weight:500">${stdNames}</div>
                                <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${stdNumbers}</div>
                            </div>
                            <div>
                                <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">待审初稿</div>
                                <div style="font-size:15px;font-weight:500">${newReviewState.draftFile?.name}</div>
                                <div style="font-size:12px;color:var(--text-muted);margin-top:2px">${formatSize(newReviewState.draftFile?.size || 0)}</div>
                            </div>
                        </div>
                    </div>
                    <div style="background:rgba(26,86,219,0.04);border:1px solid rgba(26,86,219,0.12);border-radius:10px;padding:16px;margin-bottom:20px">
                        <div style="font-size:14px;font-weight:500;color:var(--primary);margin-bottom:10px">将执行以下审查项目：</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">
                            ${['📋 检验方法结构检查', '📌 试剂仪器规范检查', '📝 术语与格式合规性', '🤖 AI 语义深度对比', '📊 数据参数完整性', '🔍 附录标准品表检查'].map(item => 
                                `<div style="font-size:13px;color:var(--text-secondary)">${item}</div>`
                            ).join('')}
                        </div>
                        <div style="margin-top:10px;font-size:12px;color:var(--text-muted)">
                            💡 系统专为化妆品检验方法、补充检验方法等标准初稿审查设计
                        </div>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <button class="btn btn-secondary" onclick="renderNewReviewStep(2)">← 上一步</button>
                        <button class="btn btn-primary" id="start-review-btn" onclick="startReview()" style="min-width:140px">
                            🚀 开始审查
                        </button>
                    </div>
                </div>
            </div>`;
    }

    content.innerHTML = stepsHtml + bodyHtml;

    // 绑定文件上传事件
    if (step === 2) {
        const draftInput = document.getElementById('draft-file-input');
        const draftZone = document.getElementById('draft-upload-zone');
        const selectedDiv = document.getElementById('draft-selected-file');
        
        draftInput.addEventListener('change', () => {
            if (draftInput.files[0]) {
                newReviewState.draftFile = draftInput.files[0];
                selectedDiv.style.display = 'flex';
                selectedDiv.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <span>${draftInput.files[0].name} (${formatSize(draftInput.files[0].size)})</span>
                `;
            }
        });

        draftZone.addEventListener('dragover', e => { e.preventDefault(); draftZone.classList.add('drag-over'); });
        draftZone.addEventListener('dragleave', () => draftZone.classList.remove('drag-over'));
        draftZone.addEventListener('drop', e => {
            e.preventDefault();
            draftZone.classList.remove('drag-over');
            if (e.dataTransfer.files[0]) {
                draftInput.files = e.dataTransfer.files;
                draftInput.dispatchEvent(new Event('change'));
            }
        });
    }
}

function toggleStandard(stdId) {
    const allStandards = window._currentStandards || [];
    const fullStd = allStandards.find(s => s.id === stdId);
    if (!fullStd) return;
    const idx = newReviewState.selectedStandards.findIndex(s => s.id === stdId);
    if (idx >= 0) {
        newReviewState.selectedStandards.splice(idx, 1);
    } else {
        newReviewState.selectedStandards.push(fullStd);
    }
    renderNewReviewStep(1);
}

function goToStep2() {
    if (newReviewState.selectedStandards.length === 0) { showToast('请至少选择一项参考标准', 'error'); return; }
    renderNewReviewStep(2);
}

function goToStep3() {
    if (!newReviewState.draftFile) { showToast('请先选择初稿文件', 'error'); return; }
    renderNewReviewStep(3);
}

async function startReview() {
    const btn = document.getElementById('start-review-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px"></span> 提交中...';
    const name = document.getElementById('review-name')?.value || '';
    const standardIds = newReviewState.selectedStandards.map(s => s.id).join(',');
    try {
        const res = await reviewsAPI.create(name, standardIds, newReviewState.draftFile);
        if (res.success) {
            showToast('审查任务已创建，正在分析...', 'success');
            APP.currentTaskId = res.data.task_id;
            renderProgressPage(document.getElementById('main-content'), res.data.task_id);
        } else {
            showToast(res.message || '创建失败', 'error');
            btn.disabled = false;
            btn.innerHTML = '🚀 开始审查';
        }
    } catch(e) {
        showToast('提交失败：' + e.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '🚀 开始审查';
    }
}


// ================================================
// 页面三：审查进度
// ================================================
function renderProgressPage(container, taskId) {
    container.innerHTML = `
        <div class="container">
            <div class="page-header">
                <h2>审查进行中</h2>
                <p>正在对初稿进行多维度智能审查，请稍候...</p>
            </div>
            <div class="card" style="max-width:600px;margin:0 auto">
                <div class="card-body" style="padding:40px;text-align:center">
                    <div style="width:72px;height:72px;background:linear-gradient(135deg,rgba(26,86,219,0.08) 0%,rgba(59,130,246,0.12) 100%);border-radius:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;font-size:32px">🔍</div>
                    <h3 id="progress-task-name" style="font-size:18px;font-weight:600;margin-bottom:8px">加载中...</h3>
                    <p id="progress-step" style="font-size:14px;color:var(--text-muted);margin-bottom:24px">正在初始化...</p>
                    <div class="progress-bar" style="margin-bottom:8px">
                        <div class="progress-bar-fill" id="progress-fill" style="width:0%"></div>
                    </div>
                    <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-muted);margin-bottom:4px">
                        <span>进度</span>
                        <span id="progress-pct">0%</span>
                    </div>
                    <div id="progress-elapsed" style="text-align:right;font-size:11px;color:var(--text-muted);margin-bottom:32px">-</div>
                    <div id="progress-steps-list" style="text-align:left">
                        ${['解析文档', '检验方法结构检查', '术语与格式检查', 'AI 语义对比分析', '生成审查报告'].map((s, i) => `
                            <div class="progress-step-item" id="pstep-${i}" style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);font-size:14px;color:var(--text-muted)">
                                <div style="width:20px;height:20px;border-radius:50%;background:#E5E7EB;display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0" id="pstep-icon-${i}">○</div>
                                <span>${s}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div id="progress-done" style="display:none;margin-top:24px">
                        <button class="btn btn-primary" onclick="showReport('${taskId}')" style="width:100%">
                            📊 查看审查报告
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    startPolling(taskId);
}

let pollingTimer = null;
let _lastProgress = 0;
let _animFrame = null;
let _taskCreatedAt = null;   // 任务创建时间戳
let _elapsedTimer = null;     // 计时器 interval ID
let _taskDoneAt = null;       // 任务完成时间戳

function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '-';
    if (seconds < 60) return Math.round(seconds) + '秒';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return m + '分' + (s > 0 ? s + '秒' : '');
}

function startElapsedTimer() {
    if (_elapsedTimer) clearInterval(_elapsedTimer);
    _elapsedTimer = setInterval(() => {
        const el = document.getElementById('progress-elapsed');
        if (!el || !_taskCreatedAt) return;
        const secs = (Date.now() - _taskCreatedAt) / 1000;
        el.textContent = '已进行 ' + formatDuration(secs);
    }, 1000);
}

function animateProgress(from, to, fillEl, pctEl) {
    // 平滑动画过渡进度条
    if (_animFrame) cancelAnimationFrame(_animFrame);
    const start = performance.now();
    const duration = 400;
    function step(now) {
        const t = Math.min((now - start) / duration, 1);
        const eased = t < 0.5 ? 2*t*t : -1+(4-2*t)*t;
        const cur = from + (to - from) * eased;
        if (fillEl) fillEl.style.width = `${cur}%`;
        if (pctEl) pctEl.textContent = `${Math.round(cur)}%`;
        if (t < 1) _animFrame = requestAnimationFrame(step);
    }
    _animFrame = requestAnimationFrame(step);
}

function startPolling(taskId) {
    if (pollingTimer) clearInterval(pollingTimer);
    _lastProgress = 0;
    _taskCreatedAt = null;
    _taskDoneAt = null;
    if (_elapsedTimer) clearInterval(_elapsedTimer);
    pollingTimer = setInterval(async () => {
        try {
            const res = await reviewsAPI.getStatus(taskId);
            if (!res.success) return;
            const { status, progress, current_step, name, created_at, completed_at } = res.data;

            // 首次拿到 created_at 时启动计时器
            if (created_at && !_taskCreatedAt) {
                _taskCreatedAt = new Date(created_at).getTime();
                _taskDoneAt = completed_at ? new Date(completed_at).getTime() : null;
                startElapsedTimer();
            }

            const nameEl = document.getElementById('progress-task-name');
            const stepEl = document.getElementById('progress-step');
            const fillEl = document.getElementById('progress-fill');
            const pctEl = document.getElementById('progress-pct');
            if (!nameEl) { clearInterval(pollingTimer); return; }

            if (nameEl) nameEl.textContent = name || '审查任务';
            if (stepEl) {
                stepEl.textContent = current_step || '处理中...';
                if (status === 'running') {
                    stepEl.style.animation = 'none';
                    void stepEl.offsetWidth;
                    stepEl.style.animation = '';
                }
            }

            if (progress !== _lastProgress) {
                animateProgress(_lastProgress, progress, fillEl, pctEl);
                _lastProgress = progress;
            }

            const stepThresholds = [15, 35, 50, 65, 85, 100];
            stepThresholds.forEach((threshold, i) => {
                const icon = document.getElementById(`pstep-icon-${i}`);
                const item = document.getElementById(`pstep-${i}`);
                if (!icon || !item) return;
                if (progress >= threshold) {
                    icon.innerHTML = '✓';
                    icon.style.background = 'var(--success)';
                    icon.style.color = 'white';
                    icon.style.animation = '';
                    item.style.color = 'var(--text-primary)';
                    item.style.fontWeight = '';
                } else if (progress >= (stepThresholds[i-1] || 0)) {
                    icon.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite">⟳</span>';
                    icon.style.background = 'var(--primary)';
                    icon.style.color = 'white';
                    item.style.color = 'var(--primary)';
                    item.style.fontWeight = '500';
                }
            });

            if (status === 'done') {
                clearInterval(pollingTimer);
                clearInterval(_elapsedTimer);
                // 计算总耗时
                if (_taskCreatedAt) {
                    const doneTs = _taskDoneAt || Date.now();
                    const totalSecs = (doneTs - _taskCreatedAt) / 1000;
                    const elEl = document.getElementById('progress-elapsed');
                    if (elEl) elEl.textContent = '共计 ' + formatDuration(totalSecs);
                }
                animateProgress(_lastProgress, 100, fillEl, pctEl);
                document.getElementById('progress-done').style.display = 'block';
                showToast('✅ 审查完成！', 'success');
            } else if (status === 'failed') {
                clearInterval(pollingTimer);
                clearInterval(_elapsedTimer);
                if (stepEl) stepEl.textContent = '❌ 审查失败：' + (current_step || '未知错误');
                if (fillEl) fillEl.style.background = 'var(--danger)';
                showToast('审查任务失败', 'error');
            }
        } catch(e) {
            console.error('轮询失败', e);
        }
    }, 800);
}

async function showReport(taskId) {
    const main = document.getElementById('main-content');
    renderReportPage(main, taskId);
}


// ================================================
// 页面四：审查报告 (Linear Dark Theme)
// ================================================
async function renderReportPage(container, taskId) {
    // Apply Linear dark theme root
    document.documentElement.classList.add('linear-report');

    container.innerHTML = `
        <div class="report-page linear-report">
            <div class="r-navbar">
                <a href="#" class="r-logo" onclick="APP.goTo('history'); return false;">
                    <div class="r-logo-icon">
                        <svg viewBox="0 0 16 16" fill="none">
                            <path d="M2 8L8 2L14 8L8 14L2 8Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span>标准审查助手</span>
                </a>
                <a href="#" class="r-nav-btn" onclick="APP.goTo('history'); return false;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="15 18 9 12 15 6"/>
                    </svg>
                    返回列表
                </a>
            </div>
            <div style="text-align:center;padding:80px 24px">
                <div style="width:32px;height:32px;border:2px solid rgba(255,255,255,0.1);border-top-color:#5e6ad2;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 16px"></div>
                <p style="color:#8a8f98;font-size:14px">加载审查报告中...</p>
            </div>
        </div>`;

    try {
        const res = await reviewsAPI.getReport(taskId);
        if (!res.success || !res.data) {
            container.innerHTML = `<div class="report-page linear-report"><div class="r-navbar"><a href="#" class="r-logo" onclick="APP.goTo('history');return false"><div class="r-logo-icon"><svg viewBox="0 0 16 16" fill="none"><path d="M2 8L8 2L14 8L8 14L2 8Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/></svg></div><span>标准审查助手</span></a></div><div class="r-empty"><div class="r-empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div><div class="r-empty-title">报告加载失败</div></div></div>`;
            return;
        }
        const report = res.data;
        const levelMap = { critical: '严重', major: '一般', minor: '轻微', suggestion: '建议' };
        const catMap = { format: '格式合规', completeness: '内容完整性', terminology: '术语一致性', semantic: '语义对比', inspection_method: '检验方法检查' };

        const issues = report.issues || [];
        const total = issues.length;

        container.innerHTML = `
        <div class="report-page linear-report">
            <!-- Navbar -->
            <div class="r-navbar">
                <a href="#" class="r-logo" onclick="APP.goTo('history'); return false;">
                    <div class="r-logo-icon">
                        <svg viewBox="0 0 16 16" fill="none">
                            <path d="M2 8L8 2L14 8L8 14L2 8Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/>
                        </svg>
                    </div>
                    <span>标准审查助手</span>
                </a>
                <div style="display:flex;align-items:center;gap:8px">
                    <a href="/api/reviews/${taskId}/report/download" class="r-btn-ghost">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                        下载报告
                    </a>
                    <a href="/api/reviews/${taskId}/report/docx" class="r-btn-brand">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                        Word
                    </a>
                    <a href="#" class="r-btn-ghost" onclick="APP.goTo('history'); return false;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="15 18 9 12 15 6"/>
                        </svg>
                        返回
                    </a>
                </div>
            </div>

            <!-- Report Header -->
            <div class="r-header">
                <div class="r-header-meta">
                    <div class="r-header-title">${report.task_name || '标准审查报告'}</div>
                    <div class="r-header-sub">
                        <span>初稿</span>${report.draft_title || '未知文件'}&nbsp;&nbsp;·&nbsp;&nbsp;<span>参考</span>${report.reference_title || '未知'}
                    </div>
                </div>
                <div class="r-score-wrap">
                    <div class="r-score-circle">
                        <div class="r-score-num">${Math.round(report.score)}</div>
                        <div class="r-score-den">/100</div>
                    </div>
                    <div class="r-score-label">综合评分</div>
                </div>
            </div>

            <!-- Stats Bento Grid -->
            <div class="r-stats-grid">
                <div class="r-stat-card score-card">
                    <div class="r-stat-label">综合评分</div>
                    <div class="r-stat-value">${Math.round(report.score)}</div>
                </div>
                <div class="r-stat-card critical-card">
                    <div class="r-stat-label">严重问题</div>
                    <div class="r-stat-value">${report.critical_issues}</div>
                </div>
                <div class="r-stat-card major-card">
                    <div class="r-stat-label">一般问题</div>
                    <div class="r-stat-value">${report.major_issues}</div>
                </div>
                <div class="r-stat-card minor-card">
                    <div class="r-stat-label">轻微问题</div>
                    <div class="r-stat-value">${report.minor_issues}</div>
                </div>
            </div>

            <!-- Filter Bar -->
            <div class="r-filter-bar">
                <button class="r-filter-pill active" data-filter="all" onclick="rFilterReport('all',this)">
                    全部 <span class="r-filter-count">${total}</span>
                </button>
                ${report.critical_issues ? `<button class="r-filter-pill" data-filter="critical" onclick="rFilterReport('critical',this)">严重 <span class="r-filter-count">${report.critical_issues}</span></button>` : ''}
                ${report.major_issues ? `<button class="r-filter-pill" data-filter="major" onclick="rFilterReport('major',this)">一般 <span class="r-filter-count">${report.major_issues}</span></button>` : ''}
                ${report.minor_issues ? `<button class="r-filter-pill" data-filter="minor" onclick="rFilterReport('minor',this)">轻微 <span class="r-filter-count">${report.minor_issues}</span></button>` : ''}
                ${issues.some(i => i.category === 'format') ? `<button class="r-filter-pill" data-filter="format" onclick="rFilterReport('format',this)">格式合规</button>` : ''}
                ${issues.some(i => i.category === 'completeness') ? `<button class="r-filter-pill" data-filter="completeness" onclick="rFilterReport('completeness',this)">内容完整性</button>` : ''}
                ${issues.some(i => i.category === 'terminology') ? `<button class="r-filter-pill" data-filter="terminology" onclick="rFilterReport('terminology',this)">术语一致性</button>` : ''}
                ${issues.some(i => i.category === 'inspection_method') ? `<button class="r-filter-pill" data-filter="inspection_method" onclick="rFilterReport('inspection_method',this)">检验方法</button>` : ''}
                ${issues.some(i => i.category === 'semantic') ? `<button class="r-filter-pill" data-filter="semantic" onclick="rFilterReport('semantic',this)">语义对比</button>` : ''}
            </div>

            <!-- Issues List -->
            <div class="r-issues-list" id="r-issues-list">
                ${total === 0
                    ? `<div class="r-empty">
                        <div class="r-empty-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                        </div>
                        <div class="r-empty-title">未发现问题</div>
                        <div class="r-empty-sub">文档质量良好，所有检查项均已通过</div>
                       </div>`
                    : issues.map(issue => `
                        <div class="r-issue-card" data-level="${issue.level}" data-category="${issue.category}">
                            <div class="r-issue-main">
                                <div class="r-issue-header">
                                    <span class="r-badge r-badge-${issue.level}">${levelMap[issue.level] || issue.level}</span>
                                    <span class="r-cat-pill">${catMap[issue.category] || issue.category}</span>
                                    ${issue.section && issue.section !== '-' ? `<span class="r-sec-tag">§${issue.section}</span>` : ''}
                                </div>
                                <div class="r-issue-title">${issue.title}</div>
                                <div class="r-issue-desc">${issue.description}</div>
                                ${issue.reference ? `<div class="r-issue-ref">${issue.reference}</div>` : ''}
                                ${issue.suggestion ? `<div class="r-issue-suggestion"><strong>改进建议：</strong>${issue.suggestion}</div>` : ''}
                            </div>
                            <div class="r-issue-severity">
                                <div class="r-severity-dot ${issue.level}"></div>
                            </div>
                        </div>
                    `).join('')
                }
            </div>
        </div>`;
    } catch(e) {
        container.innerHTML = `<div class="report-page linear-report"><div class="r-navbar"><a href="#" class="r-logo" onclick="APP.goTo('history');return false"><div class="r-logo-icon"><svg viewBox="0 0 16 16" fill="none"><path d="M2 8L8 2L14 8L8 14L2 8Z" stroke="white" stroke-width="1.5" stroke-linejoin="round"/></svg></div><span>标准审查助手</span></a></div><div class="r-empty"><div class="r-empty-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/></svg></div><div class="r-empty-title">加载失败：${e.message}</div></div></div>`;
    }
}

function rFilterReport(type, btn) {
    document.querySelectorAll('.r-filter-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    document.querySelectorAll('.r-issue-card').forEach(card => {
        if (type === 'all') { card.classList.remove('hidden'); return; }
        const level = card.dataset.level;
        const cat = card.dataset.category;
        if (level === type || cat === type) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
}


// ================================================
// 页面五：审查历史
// ================================================

// ================================================
// 看板视图：审查看板
// ================================================
async function renderKanbanPage(container) {
    container.innerHTML = `
        <div class="container">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
                <div>
                    <h2 style="font-size:20px;font-weight:600">📊 审查看板</h2>
                    <p style="color:var(--text-muted);font-size:13px;margin-top:4px">实时跟踪所有审查任务，支持批量上传</p>
                </div>
                <div style="display:flex;gap:8px">
                    <button class="btn btn-primary" onclick="APP.goTo('new-review')">+ 新建审查</button>
                    <button class="btn btn-secondary" onclick="APP.goTo('batch-review')">📦 批量审查</button>
                </div>
            </div>
            <div id="kanban-stats" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px"></div>
            <div class="kanban-grid">
                <div class="kanban-col">
                    <div class="kanban-col-header"><span>⏳ 待处理</span><span class="kanban-count" id="count-pending">0</span></div>
                    <div id="col-pending" class="kanban-cards"></div>
                </div>
                <div class="kanban-col">
                    <div class="kanban-col-header"><span>🔄 审查中</span><span class="kanban-count" id="count-running">0</span></div>
                    <div id="col-running" class="kanban-cards"></div>
                </div>
                <div class="kanban-col">
                    <div class="kanban-col-header"><span>✅ 已完成</span><span class="kanban-count" id="count-done">0</span></div>
                    <div id="col-done" class="kanban-cards"></div>
                </div>
                <div class="kanban-col">
                    <div class="kanban-col-header" style="border-color:rgba(239,68,68,0.25);background:rgba(239,68,68,0.04)"><span>⚠️ 有问题</span><span class="kanban-count" id="count-problem">0</span></div>
                    <div id="col-problem" class="kanban-cards"></div>
                </div>
            </div>
        </div>`;
    await loadKanban();
    if (window._kanbanTimer) clearInterval(window._kanbanTimer);
    window._kanbanTimer = setInterval(loadKanban, 15000);
    // 每秒更新 running 卡片的已耗时
    if (window._kanbanElapsedTimer) clearInterval(window._kanbanElapsedTimer);
    window._kanbanElapsedTimer = setInterval(() => {
        document.querySelectorAll('[id^="kelapsed-"]').forEach(el => {
            const id = el.id.replace('kelapsed-', '');
            const card = el.closest('.kanban-card');
            if (!card) return;
            // 找到 data-created-at（通过 DOM 方式不行，改用 window._kanbanTasks）
        });
        // 读取保存在 window._kanbanTasks 中的任务创建时间
        const tasks = window._kanbanTasks || [];
        tasks.forEach(t => {
            if (t.status !== 'pending' && t.status !== 'running') return;
            const el = document.getElementById('kelapsed-' + t.id);
            if (!el) return;
            const secs = (Date.now() - new Date(t.created_at).getTime()) / 1000;
            el.textContent = '⏱ ' + formatDuration(secs);
        });
    }, 1000);
}

async function loadKanban() {
    try {
        const res = await reviewsAPI.list();
        const tasks = res.data || [];
        window._kanbanTasks = tasks;  // 保存供计时器使用
        const cols = { pending: [], running: [], done: [], problem: [] };
        for (const t of tasks) {
            if (t.status === 'pending') cols.pending.push(t);
            else if (t.status === 'running') cols.running.push(t);
            else if (t.status === 'failed' || (t.status === 'done' && (t.critical_issues > 0 || (t.score != null && t.score < 60)))) cols.problem.push(t);
            else cols.done.push(t);
        }
        document.getElementById('kanban-stats').innerHTML =
            '<div class="stat-card" style="text-align:center;padding:14px"><div class="stat-number" style="font-size:26px">' + tasks.length + '</div><div class="stat-label">全部任务</div></div>' +
            '<div class="stat-card" style="text-align:center;padding:14px"><div class="stat-number" style="font-size:26px;color:var(--success)">' + cols.done.length + '</div><div class="stat-label">✅ 正常完成</div></div>' +
            '<div class="stat-card" style="text-align:center;padding:14px"><div class="stat-number" style="font-size:26px;color:var(--danger)">' + cols.problem.length + '</div><div class="stat-label">⚠️ 有问题</div></div>' +
            '<div class="stat-card" style="text-align:center;padding:14px"><div class="stat-number" style="font-size:26px;color:var(--warning)">' + (cols.running.length + cols.pending.length) + '</div><div class="stat-label">⏳ 进行中</div></div>';
        for (const [colId, items] of Object.entries(cols)) {
            document.getElementById('count-' + colId).textContent = items.length;
            const el = document.getElementById('col-' + colId);
            el.innerHTML = items.length === 0
                ? '<div class="kanban-empty">暂无任务</div>'
                : items.map(t => buildKanbanCard(t)).join('');
        }
    } catch(e) { console.error('看板加载失败', e); }
}

function buildKanbanCard(t) {
    const scoreColor = t.score == null ? '' : t.score >= 80 ? '#10b981' : t.score >= 60 ? '#e3b341' : '#f85149';
    const scoreHtml = t.score != null
        ? '<div style="margin-top:8px;display:flex;align-items:baseline;gap:4px"><span style="font-size:10px;color:#9ca3af;font-weight:600;text-transform:uppercase">评分</span><span style="font-size:18px;font-weight:700;color:' + scoreColor + '">' + Math.round(t.score) + '</span></div>'
        : '';
    const issueBadges = (t.critical_issues || t.major_issues || t.minor_issues)
        ? '<div style="display:flex;gap:4px;margin-top:6px;flex-wrap:wrap">'
            + (t.critical_issues ? '<span style="background:rgba(239,68,68,0.12);color:#f85149;font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600">' + t.critical_issues + ' 严重</span>' : '')
            + (t.major_issues ? '<span style="background:rgba(227,179,65,0.12);color:#e3b341;font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600">' + t.major_issues + ' 一般</span>' : '')
            + (t.minor_issues ? '<span style="background:rgba(88,166,255,0.12);color:#58a6ff;font-size:10px;padding:1px 5px;border-radius:3px;font-weight:600">' + t.minor_issues + ' 轻微</span>' : '')
            + '</div>' : '';
    const progressHtml = t.status === 'running'
        ? '<div style="margin-top:8px"><div class="progress-bar"><div class="progress-bar-fill" style="width:' + t.progress + '%"></div></div></div>'
        : '';
    // 耗时展示：pending/running 显示已耗时，done 显示总耗时
    let elapsedHtml = '';
    if (t.created_at) {
        const startMs = new Date(t.created_at).getTime();
        if (t.status === 'pending' || t.status === 'running') {
            const secs = (Date.now() - startMs) / 1000;
            elapsedHtml = '<div class="kanban-elapsed" id="kelapsed-' + t.id + '" style="font-size:10px;color:var(--text-muted);margin-top:4px">⏱ ' + formatDuration(secs) + '</div>';
        } else if (t.status === 'done' && t.completed_at) {
            const endMs = new Date(t.completed_at).getTime();
            const secs = (endMs - startMs) / 1000;
            elapsedHtml = '<div style="font-size:10px;color:var(--text-muted);margin-top:4px">⏱ 共 ' + formatDuration(secs) + '</div>';
        }
    }
    const statusMap = {pending:'等待中', running:'分析中', done:'已完成', failed:'失败'};
    const onClick = t.status === 'done'
        ? "onclick=\"showReport('" + t.id + "')\" style=\"cursor:pointer\""
        : (t.status === 'failed' ? '' : "onclick=\"startPolling('" + t.id + "');APP.goTo('progress')\" style=\"cursor:pointer\"");
    const label = t.current_step || statusMap[t.status] || '';
    return '<div class="kanban-card" ' + onClick + '>' +
        '<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px">' +
            '<div style="flex:1;min-width:0">' +
                '<div style="font-size:13px;font-weight:600;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="' + t.name + '">' + t.name + '</div>' +
                '<div style="font-size:11px;color:var(--text-muted);margin-top:2px">' + t.draft_file_name + '</div>' +
            '</div>' +
            (t.status !== 'running' ? '<button class="btn-icon" onclick="event.stopPropagation();deleteReview(\'' + t.id + '\')" title="删除">🗑</button>' : '') +
        '</div>' +
        scoreHtml + issueBadges + progressHtml + elapsedHtml +
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:8px;padding-top:8px;border-top:1px solid var(--border)">' +
            '<span style="font-size:11px;color:var(--text-muted)">' + formatDate(t.created_at) + '</span>' +
            '<span style="font-size:11px;color:var(--text-muted)">' + label + '</span>' +
        '</div>' +
    '</div>';
}
