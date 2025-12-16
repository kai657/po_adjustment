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

    scheduleInput.addEventListener('change', function(e) {
        handleFileSelect(e, 'schedule');
    });

    poInput.addEventListener('change', function(e) {
        handleFileSelect(e, 'po');
    });

    uploadBtn.addEventListener('click', function() {
        uploadFiles();
    });
}

// 处理文件选择
function handleFileSelect(event, type) {
    const file = event.target.files[0];
    if (!file) return;

    if (type === 'schedule') {
        appState.scheduleFile = file;
        showFileInfo('schedule', file);
    } else if (type === 'po') {
        appState.poFile = file;
        showFileInfo('po', file);
    }

    // 检查是否两个文件都已选择
    if (appState.scheduleFile && appState.poFile) {
        document.getElementById('btn-upload').disabled = false;
    }
}

// 显示文件信息
function showFileInfo(type, file) {
    const infoId = type === 'schedule' ? 'schedule-info' : 'po-info';
    const infoDiv = document.getElementById(infoId);

    const sizeKB = (file.size / 1024).toFixed(2);
    infoDiv.innerHTML = `
        <strong>✓ ${file.name}</strong><br>
        大小: ${sizeKB} KB
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

    showToast('正在上传文件...', 'info');

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('文件上传成功！', 'success');
            displayFilePreview(data.data);
            setTimeout(() => goToStep(2), 1000);
        } else {
            showToast(data.error || '上传失败', 'error');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showToast('上传失败: ' + error.message, 'error');
    });
}

// 显示文件预览
function displayFilePreview(data) {
    // 排程目标预览
    if (data.schedule_aim) {
        const preview = document.getElementById('schedule-preview');
        preview.innerHTML = `
            <strong>数据概览:</strong><br>
            行数: ${data.schedule_aim.rows} |
            SKU数: ${data.schedule_aim.skus.length}<br>
            列: ${data.schedule_aim.columns.join(', ')}
        `;
    }

    // PO清单预览
    if (data.po_lists) {
        const preview = document.getElementById('po-preview');
        preview.innerHTML = `
            <strong>数据概览:</strong><br>
            行数: ${data.po_lists.rows} |
            SKU数: ${data.po_lists.skus.length}<br>
            列: ${data.po_lists.columns.join(', ')}
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
    progressText.textContent = '正在初始化优化引擎...';

    // 模拟进度更新
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        progressFill.style.width = progress + '%';
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
        progressText.textContent = '优化完成！';

        if (data.success) {
            showToast('优化成功完成！', 'success');
            appState.optimizationResult = data.data;
            setTimeout(() => {
                displayResults(data.data);
                goToStep(4);
            }, 1000);
        } else {
            showToast(data.error || '优化失败', 'error');
            optimizeBtn.disabled = false;
            progressPanel.style.display = 'none';
        }
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error('Optimization error:', error);
        showToast('优化失败: ' + error.message, 'error');
        optimizeBtn.disabled = false;
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

        summaryHTML += `
            <div class="stat-card">
                <h4>处理SKU数</h4>
                <div class="value">${skuCount}</div>
            </div>
            <div class="stat-card">
                <h4>原始总偏差</h4>
                <div class="value">${totalOriginalDeviation.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <h4>优化后总偏差</h4>
                <div class="value">${totalOptimizedDeviation.toLocaleString()}</div>
            </div>
            <div class="stat-card">
                <h4>改善率</h4>
                <div class="value">${improvementRate}%</div>
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
        <a href="/api/download/${data.files.optimized_po}" class="btn btn-download" download>
            📄 优化后PO清单
        </a>
        <a href="/api/download/${data.files.report}" class="btn btn-download" download>
            📊 详细对比报告
        </a>
        <a href="/api/download/${data.files.comparison_chart}" class="btn btn-download" download>
            📈 数量对比图
        </a>
        <a href="/api/download/${data.files.deviation_chart}" class="btn btn-download" download>
            📉 偏差对比图
        </a>
    `;
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
