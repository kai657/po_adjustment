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
            // 显示转换信息
            if (data.data.conversion) {
                if (data.data.conversion.converted) {
                    showToast('✅ 文件上传成功！已自动转换交叉表格式', 'success');
                } else {
                    showToast('✅ 文件上传成功！', 'success');
                }
            } else {
                showToast('✅ 文件上传成功！', 'success');
            }

            displayFilePreview(data.data);
            setTimeout(() => goToStep(2), 1500);
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
        let conversionBadge = '';

        // 显示转换状态
        if (data.conversion) {
            if (data.conversion.converted) {
                conversionBadge = `
                    <div style="margin-top: 10px; padding: 8px; background: #dcfce7; border-left: 3px solid #10b981; border-radius: 4px;">
                        <span style="color: #059669; font-size: 0.85em;">
                            🔄 ${data.conversion.message}
                        </span>
                    </div>
                `;
            }
        }

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
                ${conversionBadge}
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

// 全局变量保存gap分析文件名
let currentGapAnalysisFile = '';

// 显示结果
function displayResults(data) {
    // 1. 首先显示差异分析表
    if (data.gap_analysis) {
        displayGapAnalysis(data.gap_analysis);
        currentGapAnalysisFile = data.files.gap_analysis;
    }

    // 2. 显示汇总统计
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
    comparisonChart.src = `/api/preview/${data.files.comparison_chart}`;

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

// 显示差异分析表
function displayGapAnalysis(gapData) {
    // 显示统计信息
    const statsDiv = document.getElementById('gap-stats');
    const stats = gapData.stats;

    statsDiv.innerHTML = `
        <div class="gap-stat-card">
            <div class="label">SKU总数</div>
            <div class="value">${stats.sku_count}</div>
        </div>
        <div class="gap-stat-card">
            <div class="label">日期数</div>
            <div class="value">${stats.date_count}</div>
        </div>
        <div class="gap-stat-card">
            <div class="label">总差异</div>
            <div class="value" style="color: ${stats.total_gap >= 0 ? '#2f9e44' : '#c92a2a'}">
                ${stats.total_gap.toLocaleString()}
            </div>
        </div>
        <div class="gap-stat-card">
            <div class="label">绝对差异</div>
            <div class="value">${stats.abs_total_gap.toLocaleString()}</div>
        </div>
        <div class="gap-stat-card">
            <div class="label">最大差异</div>
            <div class="value" style="color: #c92a2a;">${stats.max_gap.toLocaleString()}</div>
        </div>
        <div class="gap-stat-card">
            <div class="label">最小差异</div>
            <div class="value" style="color: #2f9e44;">${stats.min_gap.toLocaleString()}</div>
        </div>
    `;

    // 生成差异表格
    const tableDiv = document.getElementById('gap-table');
    const skus = gapData.skus;
    const dates = gapData.dates;
    const gapValues = gapData.gap_values;
    const scheduleValues = gapData.schedule_values;
    const poValues = gapData.po_values;

    // 计算top30%阈值
    const allGaps = gapValues.flat().map(Math.abs).filter(v => v > 0);
    const threshold = calculatePercentile(allGaps, 70);

    // 构建表格HTML
    let tableHTML = '<thead>';

    // 第一行：分类标题
    tableHTML += '<tr>';
    tableHTML += '<th rowspan="2" class="sku-header">SKU</th>';
    tableHTML += `<th colspan="${dates.length}" class="section-header">GAP差异</th>`;
    tableHTML += `<th colspan="${dates.length}" class="section-header">排程目标</th>`;
    tableHTML += `<th colspan="${dates.length}" class="section-header">PO汇总结果</th>`;
    tableHTML += '</tr>';

    // 第二行：日期
    tableHTML += '<tr>';
    for (let i = 0; i < 3; i++) {
        for (const date of dates) {
            tableHTML += `<th>${date}</th>`;
        }
    }
    tableHTML += '</tr>';
    tableHTML += '</thead>';

    // 数据行
    tableHTML += '<tbody>';
    for (let i = 0; i < skus.length; i++) {
        tableHTML += '<tr>';

        // SKU列
        tableHTML += `<td class="sku-cell">${skus[i]}</td>`;

        // GAP差异列
        for (let j = 0; j < dates.length; j++) {
            const value = gapValues[i][j];
            let className = value > 0 ? 'positive' : (value < 0 ? 'negative' : 'zero');

            // 高亮top30%
            if (Math.abs(value) >= threshold && Math.abs(value) > 0) {
                className += ' highlight';
            }

            tableHTML += `<td class="${className}">${value.toLocaleString()}</td>`;
        }

        // 排程目标列
        for (let j = 0; j < dates.length; j++) {
            const value = scheduleValues[i][j];
            tableHTML += `<td>${value.toLocaleString()}</td>`;
        }

        // PO汇总结果列
        for (let j = 0; j < dates.length; j++) {
            const value = poValues[i][j];
            tableHTML += `<td>${value.toLocaleString()}</td>`;
        }

        tableHTML += '</tr>';
    }
    tableHTML += '</tbody>';

    tableDiv.innerHTML = tableHTML;
}

// 计算百分位数
function calculatePercentile(arr, percentile) {
    if (arr.length === 0) return 0;

    const sorted = arr.slice().sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;

    return sorted[index] || 0;
}

// 下载差异分析表
function downloadGapAnalysis() {
    if (!currentGapAnalysisFile) {
        showToast('差异分析文件不存在', 'error');
        return;
    }

    window.location.href = `/api/download/${currentGapAnalysisFile}`;
    showToast('开始下载差异分析表...', 'success');
}

// 折叠/展开图表
function toggleChart(contentId) {
    const content = document.getElementById(contentId);
    const icon = document.getElementById(contentId.replace('-content', '-icon'));

    if (content.classList.contains('collapsed')) {
        // 展开
        content.classList.remove('collapsed');
        icon.classList.add('expanded');
        icon.textContent = '▼';
    } else {
        // 折叠
        content.classList.add('collapsed');
        icon.classList.remove('expanded');
        icon.textContent = '▶';
    }
}
