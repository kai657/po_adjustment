#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PO优化Web应用 - Flask后端
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import sys
import pandas as pd
import json
from datetime import datetime
import traceback

# 添加项目根目录到路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from src.core.po_adjustment import POOptimizer
from src.core.visualization import POVisualizer
from src.core.data_transformer import ScheduleTransformer
from src.core.gap_analysis import GapAnalyzer

# 使用根目录的templates和static
app = Flask(__name__,
            template_folder=os.path.join(PROJECT_ROOT, 'templates'),
            static_folder=os.path.join(PROJECT_ROOT, 'static'))

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(PROJECT_ROOT, 'data/uploads')
app.config['RESULT_FOLDER'] = os.path.join(PROJECT_ROOT, 'data/output')

# 确保文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """处理文件上传"""
    try:
        # 检查文件是否存在
        if 'schedule_aim' not in request.files or 'po_lists' not in request.files:
            return jsonify({'success': False, 'error': '请同时上传排程目标和PO清单文件'}), 400

        schedule_file = request.files['schedule_aim']
        po_file = request.files['po_lists']

        # 检查文件名
        if schedule_file.filename == '' or po_file.filename == '':
            return jsonify({'success': False, 'error': '文件名不能为空'}), 400

        # 检查文件类型
        if not (allowed_file(schedule_file.filename) and allowed_file(po_file.filename)):
            return jsonify({'success': False, 'error': '只支持.xlsx和.xls文件'}), 400

        # 保存文件
        schedule_filename = secure_filename(schedule_file.filename)
        po_filename = secure_filename(po_file.filename)

        schedule_path = os.path.join(app.config['UPLOAD_FOLDER'], 'schedule_aim.xlsx')
        po_path = os.path.join(app.config['UPLOAD_FOLDER'], 'po_lists.xlsx')

        schedule_file.save(schedule_path)
        po_file.save(po_path)

        # 读取排程文件
        schedule_df_raw = pd.read_excel(schedule_path)

        # 检测排程文件格式并自动转换
        transformer = ScheduleTransformer()
        format_type = transformer.detect_format(schedule_df_raw)

        conversion_info = {'format': format_type, 'converted': False}

        if format_type == 'cross_table':
            # 需要转换：二维交叉表 -> 长表
            print(f"检测到交叉表格式，执行自动转换...")
            schedule_df = transformer.transform_cross_table_to_long(schedule_df_raw)
            schedule_df = transformer.add_week_number(schedule_df)

            # 保存转换后的文件
            schedule_df.to_excel(schedule_path, index=False)

            conversion_info['converted'] = True
            conversion_info['message'] = '已自动转换交叉表格式为长表格式'
            print(f"转换完成：{schedule_df_raw.shape} -> {schedule_df.shape}")

        elif format_type == 'long_format':
            # 已是长表格式，无需转换
            schedule_df = schedule_df_raw.copy()

            # 标准化列名
            columns_map = {}
            for col in schedule_df.columns:
                col_lower = str(col).lower()
                if '日期' in col_lower or 'date' in col_lower:
                    columns_map[col] = '日期'
                elif 'sku' in col_lower:
                    columns_map[col] = 'SKU'
                elif '计划' in col_lower or '产量' in col_lower or 'quantity' in col_lower:
                    columns_map[col] = '计划产量'

            schedule_df = schedule_df.rename(columns=columns_map)

            # 添加week_num（如果没有）
            if 'week_num' not in schedule_df.columns and '日期' in schedule_df.columns:
                schedule_df = transformer.add_week_number(schedule_df)
                schedule_df.to_excel(schedule_path, index=False)

            conversion_info['message'] = '文件已是长表格式'
            print("文件已是长表格式，无需转换")

        else:
            return jsonify({
                'success': False,
                'error': '无法识别排程文件格式。请确保文件为交叉表或长表格式。'
            }), 400

        # 读取PO文件
        po_df = pd.read_excel(po_path)

        # 获取SKU列表
        schedule_skus = schedule_df['SKU'].unique().tolist() if 'SKU' in schedule_df.columns else []
        po_skus = po_df['SKU'].unique().tolist() if 'SKU' in po_df.columns else []

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'schedule_aim': {
                    'filename': schedule_filename,
                    'rows': len(schedule_df),
                    'columns': schedule_df.columns.tolist(),
                    'skus': schedule_skus,
                    'preview': schedule_df.head(5).to_dict('records')
                },
                'po_lists': {
                    'filename': po_filename,
                    'rows': len(po_df),
                    'columns': po_df.columns.tolist(),
                    'skus': po_skus,
                    'preview': po_df.head(5).to_dict('records')
                },
                'conversion': conversion_info
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500


@app.route('/api/optimize', methods=['POST'])
def optimize():
    """执行优化"""
    try:
        # 获取参数
        params = request.json
        priority_weeks = params.get('priority_weeks', 8)
        priority_weight = params.get('priority_weight', 10.0)
        date_weight = 0.0  # 不考虑日期接近度目标
        max_workers = params.get('max_workers', 4)

        # 检查上传的文件是否存在
        schedule_path = os.path.join(app.config['UPLOAD_FOLDER'], 'schedule_aim.xlsx')
        po_path = os.path.join(app.config['UPLOAD_FOLDER'], 'po_lists.xlsx')

        if not (os.path.exists(schedule_path) and os.path.exists(po_path)):
            return jsonify({'success': False, 'error': '请先上传文件'}), 400

        # 创建优化器（传递参数）
        optimizer = POOptimizer(schedule_path, po_path)

        # 临时修改优化参数（通过猴子补丁）
        original_calc = optimizer._calculate_weekly_deviation

        def patched_calc(po_assignments, target_weekly, priority_weeks_param=priority_weeks):
            return original_calc(po_assignments, target_weekly, priority_weeks_param)

        optimizer._calculate_weekly_deviation = patched_calc

        # 执行优化
        optimized_po = optimizer.optimize(max_workers=max_workers)

        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_path = os.path.join(app.config['RESULT_FOLDER'], f'po_optimized_{timestamp}.xlsx')
        optimized_po.to_excel(result_path, index=False)

        # 生成可视化和报告
        visualizer = POVisualizer(schedule_path, po_path, result_path)

        report_path = os.path.join(app.config['RESULT_FOLDER'], f'report_{timestamp}.xlsx')
        comparison_path = os.path.join(app.config['RESULT_FOLDER'], f'comparison_{timestamp}.png')

        comparison, summary = visualizer.generate_summary_report(report_path)
        visualizer.create_comparison_plots(comparison_path)

        # 生成差异分析表
        gap_analysis_path = os.path.join(app.config['RESULT_FOLDER'], f'gap_analysis_{timestamp}.xlsx')
        gap_analyzer = GapAnalyzer(schedule_path, po_path, result_path)
        gap_analyzer.export_to_excel(gap_analysis_path, highlight_top_percent=30)

        # 生成差异统计和表格数据
        gap_stats = gap_analyzer.generate_summary_stats()
        gap_data = gap_analyzer.create_gap_table()

        # 转换gap数据为JSON格式
        gap_json = {
            'skus': gap_data['gap'].index.tolist(),
            'dates': [d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)
                     for d in gap_data['dates']],
            'gap_values': gap_data['gap'].values.tolist(),
            'schedule_values': gap_data['schedule'].values.tolist(),
            'po_values': gap_data['po'].values.tolist(),
            'stats': gap_stats
        }

        # 准备返回数据
        summary_data = summary.to_dict('records')

        return jsonify({
            'success': True,
            'message': '优化完成',
            'data': {
                'timestamp': timestamp,
                'summary': summary_data,
                'gap_analysis': gap_json,
                'files': {
                    'optimized_po': f'po_optimized_{timestamp}.xlsx',
                    'report': f'report_{timestamp}.xlsx',
                    'comparison_chart': f'comparison_{timestamp}.png',
                    'gap_analysis': f'gap_analysis_{timestamp}.xlsx'
                }
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'优化失败: {str(e)}'}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """下载结果文件"""
    try:
        file_path = os.path.join(app.config['RESULT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'success': False, 'error': f'下载失败: {str(e)}'}), 500


@app.route('/api/preview/<filename>')
def preview_file(filename):
    """预览图片文件"""
    try:
        file_path = os.path.join(app.config['RESULT_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': '文件不存在'}), 404

        return send_file(file_path, mimetype='image/png')
    except Exception as e:
        return jsonify({'success': False, 'error': f'预览失败: {str(e)}'}), 500


@app.route('/api/status')
def status():
    """获取系统状态"""
    schedule_path = os.path.join(app.config['UPLOAD_FOLDER'], 'schedule_aim.xlsx')
    po_path = os.path.join(app.config['UPLOAD_FOLDER'], 'po_lists.xlsx')

    return jsonify({
        'success': True,
        'data': {
            'schedule_uploaded': os.path.exists(schedule_path),
            'po_uploaded': os.path.exists(po_path),
            'upload_folder': app.config['UPLOAD_FOLDER'],
            'result_folder': app.config['RESULT_FOLDER']
        }
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
