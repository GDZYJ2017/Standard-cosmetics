// === API 调用封装 ===
// API 基础地址：优先使用环境变量，其次使用相对路径
const API_BASE = window.API_BASE || '/api';

// 检测当前是否通过 HTTP 服务访问
function isServerMode() {
    return location.protocol === 'http:' || location.protocol === 'https:';
}

async function request(url, options = {}) {
    try {
        const resp = await fetch(API_BASE + url, options);
        const data = await resp.json();
        if (!data.success && resp.status >= 400) {
            throw new Error(data.message || '请求失败');
        }
        return data;
    } catch (err) {
        // file:/// 模式下友好提示
        if (!isServerMode()) {
            throw new Error('需要启动后端服务。请运行 start.bat 或在后端目录执行: python -m uvicorn main:app --port 8000，然后通过 http://localhost:8000 访问');
        }
        console.error(`API Error [${url}]:`, err);
        throw err;
    }
}

// 参考标准 API
const standardsAPI = {
    async upload(file, name = '', number = '', description = '') {
        const form = new FormData();
        form.append('file', file);
        form.append('name', name);
        form.append('number', number);
        form.append('description', description);
        return request('/standards/upload', { method: 'POST', body: form });
    },
    async list() {
        return request('/standards');
    },
    async delete(id) {
        return request(`/standards/${id}`, { method: 'DELETE' });
    }
};

// 审查任务 API
const reviewsAPI = {
    async create(name, standardIds, file) {
        const form = new FormData();
        form.append('name', name);
        if (Array.isArray(standardIds)) {
            form.append('standard_ids', standardIds.join(','));
        } else {
            form.append('standard_ids', standardIds);
        }
        form.append('file', file);
        return request('/reviews/create', { method: 'POST', body: form });
    },
    async batchCreate(batchName, standardIds, files) {
        // 批量创建：一次上传多份初稿
        const form = new FormData();
        form.append('batch_name', batchName);
        if (Array.isArray(standardIds)) {
            form.append('standard_ids', standardIds.join(','));
        } else {
            form.append('standard_ids', standardIds);
        }
        for (const file of files) {
            form.append('files', file);
        }
        return request('/reviews/batch-create', { method: 'POST', body: form });
    },
    async list() {
        return request('/reviews');
    },
    async getStatus(taskId) {
        return request(`/reviews/${taskId}/status`);
    },
    async getReport(taskId) {
        return request(`/reviews/${taskId}/report`);
    },
    async getReportHtml(taskId) {
        return request(`/reviews/${taskId}/report/html`);
    },
    async delete(taskId) {
        return request(`/reviews/${taskId}`, { method: 'DELETE' });
    }
};

// Toast 通知
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function createToastContainer() {
    const div = document.createElement('div');
    div.id = 'toast-container';
    div.className = 'toast-container';
    document.body.appendChild(div);
    return div;
}

// 格式化文件大小
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
        + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}
