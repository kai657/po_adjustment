// 全局状态
let appState = {
    scheduleFile: null,
    poFile: null,
    currentStep: 1,
    optimizationResult: null
};

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initFileUpload();
    initParams();
});

// 文件上传初始化
function initFileUpload() {
    const scheduleInput = document.getElementById('schedule-file');
    const poInput = document.getElementById('po-file');
    const uploadBtn = document.getElementById('btn-upload');
    const scheduleBox = document.getElementById('schedule-upload-box');
    const poBox = document.getElementById('po-upload-box');

    scheduleInput.addEventListener('change', function(e) {
        handleFileSelect(e, 'schedule');
    });

    poInput.addEventListener('change', function(e) {
        handleFileSelect(e, 'po');
    });

    uploadBtn.addEventListener('click', function() {
        uploadFiles();
    });

    // 拖拽上传功能
    setupDragAndDrop(scheduleBox, scheduleInput, 'schedule');
    setupDragAndDrop(poBox, poInput, 'po');
}

// 设置拖拽上传
function setupDragAndDrop(box, input, type) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        box.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        box.addEventListener(eventName, function() {
            box.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        box.addEventListener(eventName, function() {
            box.classList.remove('drag-over');
        }, false);
    });

    box.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            const file = files[0];
            // 检查文件类型
            if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                input.files = files;
                handleFileSelect({target: {files: [file]}}, type);
                showToast(`已选择文件: ${file.name}`, 'success');
            } else {
                showToast('请上传 Excel 文件 (.xlsx 或 .xls)', 'error');
            }
        }
    }, false);

    // 点击整个区域触发文件选择
    box.addEventListener('click', function(e) {
        if (e.target === box || e.target.classList.contains('upload-icon') ||
            e.target.classList.contains('file-desc')) {
            input.click();
        }
    });
}

// 处理文件选择
function handleFileSelect(event, type) {
    const file = event.target.files[0];
    if (!file) return;

    if (type === 'schedule') {
        appState.scheduleFile = file;
        showFileInfo('schedule', file);
        document.getElementById('schedule-upload-box').classList.add('has-file');
    } else if (type === 'po') {
        appState.poFile = file;
        showFileInfo('po', file);
        document.getElementById('po-upload-box').classList.add('has-file');
    }

    // 检查是否两个文件都已选择
    if (appState.scheduleFile && appState.poFile) {
        const uploadBtn = document.getElementById('btn-upload');
        uploadBtn.disabled = false;
        uploadBtn.classList.add('pulse');
    }
}

// 显示文件信息
function showFileInfo(type, file) {
    const infoId = type === 'schedule' ? 'schedule-info' : 'po-info';
    const infoDiv = document.getElementById(infoId);

    const sizeKB = (file.size / 1024).toFixed(2);
    const sizeMB = (file.size / 1024 / 1024).toFixed(2);
    const sizeText = sizeKB < 1024 ? `${sizeKB} KB` : `${sizeMB} MB`;

    infoDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.5em;">✅</span>
            <div style="flex: 1; text-align: left;">
                <strong>${file.name}</strong><br>
                <small style="color: #666;">大小: ${sizeText} | 类型: ${file.type || 'Excel'}</small>
            </div>
        </div>
    `;
    infoDiv.classList.add('show');
}

// 上传文件
function uploadFiles() {
    if (!appState.scheduleFile || !appState.poFile) {
        showToast('请选择两个文件', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('schedule_aim', appState.scheduleFile);
    formData.append('po_lists', appState.poFile);

    const uploadBtn = document.getElementById('btn-upload');
    uploadBtn.disabled = true;
    uploadBtn.classList.add('loading');
    uploadBtn.textContent = '上传中...';

    showToast('正在上传文件...', 'info');

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        uploadBtn.classList.remove('loading');
        uploadBtn.textContent = '上传并预览';

        if (data.success) {
            showToast('✅ 文件上传成功！', 'success');
            displayFilePreview(data.data);
            setTimeout(() => goToStep(2), 1000);
        } else {
            showToast(data.error || '上传失败', 'error');
            uploadBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        uploadBtn.classList.remove('loading');
        uploadBtn.textContent = '上传并预览';
        uploadBtn.disabled = false;
        showToast('❌ 上传失败: ' + error.message, 'error');
    });
}

// 显示文件预览
function displayFilePreview(data) {
    // 排程目标预览
    if (data.schedule_aim) {
        const preview = document.getElementById('schedule-preview');
        preview.innerHTML = `
            <div class="slide-in-up" style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 10px; text-align: left;">
                <div style="font-weight: bold; color: #0369a1; margin-bottom: 8px;">📊 数据概览</div>
                <div style="font-size: 0.9em; color: #666;">
                    <span class="badge badge-info">行数: ${data.schedule_aim.rows}</span>
                    <span class="badge badge-info">SKU数: ${data.schedule_aim.skus.length}</span>
                </div>
                <div style="font-size: 0.85em; color: #888; margin-top: 8px;">
                    列: ${data.schedule_aim.columns.join(', ')}
                </div>
            </div>
        `;
    }

    // PO清单预览
    if (data.po_lists) {
        const preview = document.getElementById('po-preview');
        preview.innerHTML = `
            <div class="slide-in-up" style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 10px; text-align: left;">
                <div style="font-weight: bold; color: #0369a1; margin-bottom: 8px;">📦 数据概览</div>
                <div style="font-size: 0.9em; color: #666;">
                    <span class="badge badge-info">行数: ${data.po_lists.rows}</span>
                    <span class="badge badge-info">SKU数: ${data.po_lists.skus.length}</span>
                </div>
                <div style="font-size: 0.85em; color: #888; margin-top: 8px;">
                    列: ${data.po_lists.columns.join(', ')}
                </div>
            </div>
        `;
    }
}

// 参数初始化
function initParams() {
    const inputs = ['priority-weeks', 'priority-weight', 'date-weight', 'max-workers'];
    inputs.forEach(id => {
        const input = document.getElementById(id);
        input.addEventListener('change', updateParamSummary);
    });
}

// 更新参数摘要
function updateParamSummary() {
    document.getElementById('summary-weeks').textContent =
        document.getElementById('priority-weeks').value;
    document.getElementById('summary-weight').textContent =
        document.getElementById('priority-weight').value;
    document.getElementById('summary-date-weight').textContent =
        document.getElementById('date-weight').value;
    document.getElementById('summary-workers').textContent =
        document.getElementById('max-workers').value;
}

// 步骤导航
function goToStep(step) {
    // 隐藏所有步骤内容
    document.querySelectorAll('.step-content').forEach(el => {
        el.classList.remove('active');
    });

    // 显示当前步骤
    const stepElements = {
        1: 'step-upload',
        2: 'step-params',
        3: 'step-optimize',
        4: 'step-results'
    };

    document.getElementById(stepElements[step]).classList.add('active');

    // 更新步骤指示器
    document.querySelectorAll('.step').forEach((el, index) => {
        if (index + 1 < step) {
            el.classList.add('completed');
            el.classList.remove('active');
        } else if (index + 1 === step) {
            el.classList.add('active');
            el.classList.remove('completed');
        } else {
            el.classList.remove('active', 'completed');
        }
    });

    // 更新参数摘要
    if (step === 3) {
        updateParamSummary();
    }

    appState.currentStep = step;
}

// 开始优化
function startOptimization() {
    const params = {
        priority_weeks: parseInt(document.getElementById('priority-weeks').value),
        priority_weight: parseFloat(document.getElementById('priority-weight').value),
        date_weight: parseFloat(document.getElementById('date-weight').value),
        max_workers: parseInt(document.getElementById('max-workers').value)
    };

    // 显示进度条
    const progressPanel = document.getElementById('progress-panel');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const optimizeBtn = document.getElementById('btn-optimize');

    progressPanel.style.display = 'block';
    optimizeBtn.disabled = true;
    optimizeBtn.classList.add('loading');

    const statusMessages = [
        '🔄 正在初始化优化引擎...',
        '📊 正在加载数据文件...',
        '🔍 正在分析SKU数据...',
        '⚡ 正在执行优化算法...',
        '📈 正在计算最优方案...',
        '🎨 正在生成可视化图表...'
    ];
    let messageIndex = 0;

    progressText.textContent = statusMessages[0];

    // 模拟进度更新
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 10 + 5;
        if (progress > 90) progress = 90;
        progressFill.style.width = progress + '%';
        progressFill.textContent = Math.floor(progress) + '%';

        // 更新状态消息
        if (progress > messageIndex * 15 && messageIndex < statusMessages.length - 1) {
            messageIndex++;
            progressText.textContent = statusMessages[messageIndex];
        }
    }, 500);

    // 发送优化请求
    fetch('/api/optimize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        progressFill.textContent = '100%';
        progressText.textContent = '✅ 优化完成！';
        optimizeBtn.classList.remove('loading');

        if (data.success) {
            showToast('🎉 优化成功完成！', 'success');
            appState.optimizationResult = data.data;
            setTimeout(() => {
                displayResults(data.data);
                goToStep(4);
            }, 1500);
        } else {
            showToast('❌ ' + (data.error || '优化失败'), 'error');
            optimizeBtn.disabled = false;
            progressPanel.style.display = 'none';
        }
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error('Optimization error:', error);
        showToast('❌ 优化失败: ' + error.message, 'error');
        optimizeBtn.disabled = false;
        optimizeBtn.classList.remove('loading');
        progressPanel.style.display = 'none';
    });
}

// 显示结果
function displayResults(data) {
    // 显示汇总统计
    const summaryDiv = document.getElementById('summary-stats');
    let summaryHTML = '<h3>📈 优化效果汇总</h3><div class="stat-grid">';

    if (data.summary && data.summary.length > 0) {
        // 计算总体统计
        let totalOriginalDeviation = 0;
        let totalOptimizedDeviation = 0;
        let skuCount = data.summary.length;

        data.summary.forEach(sku => {
            totalOriginalDeviation += sku['原始总偏差'] || 0;
            totalOptimizedDeviation += sku['优化后总偏差'] || 0;
        });

        const totalImprovement = totalOriginalDeviation - totalOptimizedDeviation;
        const improvementRate = totalOriginalDeviation > 0
            ? (totalImprovement / totalOriginalDeviation * 100).toFixed(2)
            : 0;

        // 判断改善程度的emoji
        let improvementIcon = '📊';
        if (improvementRate > 50) improvementIcon = '🎉';
        else if (improvementRate > 30) improvementIcon = '✅';
        else if (improvementRate > 10) improvementIcon = '📈';

        summaryHTML += `
            <div class="stat-card slide-in-up" style="animation-delay: 0.1s;">
                <h4>处理SKU数</h4>
                <div class="value" style="color: #667eea;">🎯 ${skuCount}</div>
            </div>
            <div class="stat-card slide-in-up" style="animation-delay: 0.2s;">
                <h4>原始总偏差</h4>
                <div class="value" style="color: #ef4444;">📉 ${totalOriginalDeviation.toLocaleString()}</div>
            </div>
            <div class="stat-card slide-in-up" style="animation-delay: 0.3s;">
                <h4>优化后总偏差</h4>
                <div class="value" style="color: #10b981;">📈 ${totalOptimizedDeviation.toLocaleString()}</div>
            </div>
            <div class="stat-card slide-in-up" style="animation-delay: 0.4s; border: 2px solid #10b981;">
                <h4>改善率</h4>
                <div class="value" style="color: #10b981; font-size: 2.5em;">${improvementIcon} ${improvementRate}%</div>
            </div>
        `;
    }

    summaryHTML += '</div>';
    summaryDiv.innerHTML = summaryHTML;

    // 显示图表
    const comparisonChart = document.getElementById('comparison-chart');
    const deviationChart = document.getElementById('deviation-chart');

    comparisonChart.src = `/api/preview/${data.files.comparison_chart}`;
    deviationChart.src = `/api/preview/${data.files.deviation_chart}`;

    // 显示下载按钮
    const downloadDiv = document.getElementById('download-buttons');
    downloadDiv.innerHTML = `
        <a href="/api/download/${data.files.optimized_po}" class="btn btn-download slide-in-up" style="animation-delay: 0.1s;" download>
            📄 优化后PO清单
        </a>
        <a href="/api/download/${data.files.report}" class="btn btn-download slide-in-up" style="animation-delay: 0.2s;" download>
            📊 详细对比报告
        </a>
        <a href="/api/download/${data.files.comparison_chart}" class="btn btn-download slide-in-up" style="animation-delay: 0.3s;" download>
            📈 数量对比图
        </a>
        <a href="/api/download/${data.files.deviation_chart}" class="btn btn-download slide-in-up" style="animation-delay: 0.4s;" download>
            📉 偏差对比图
        </a>
    `;
}

// 添加数字动画效果
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Toast 消息
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast show ' + type;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}
