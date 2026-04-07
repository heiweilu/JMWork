# -*- coding: utf-8 -*-
"""
SVM 模型验证模块
===============

使用已训练好的 svm_model.xml + norm_params.yaml，
在指定数据集上运行推理，输出：
  • 整体准确率
  • 各类别准确率（class 0 / class 1）
  • 混淆矩阵
  • 误分类样本列表（TXT）

典型用途：模型训练完成后，用训练集或独立测试集验证模型效果。
"""

import os
import datetime

MODULE_INFO = {
    "name": "SVM 模型验证",
    "category": "svm_validate",
    "description": (
        "加载已训练好的 SVM 模型，对数据集进行预测并输出准确率报告。\n\n"
        "【如何使用】\n"
        "  1. 在「模型文件」中选择训练输出的 svm_model.xml\n"
        "  2. 在「验证数据文件」中选择要跑的数据（支持预处理TXT格式）\n"
        "     - 格式：每行 x1,x2,...,x8 label（与训练输入格式相同）\n"
        "  3. norm_params.yaml 默认与模型同目录，可留空自动查找\n\n"
        "【输出】\n"
        "  • 准确率、各类别准确率、混淆矩阵（显示在分析报告）\n"
        "  • 误分类样本列表（TXT 文件）"
    ),
    "input_type": "txt",
    "input_description": "验证数据文件（预处理TXT格式，每行 x1,x2,...,x8 label）",
    "input_file_formats": "数据文件 (*.txt *.csv);;All (*)",
    "output_type": "txt",
    "params": [
        {
            "key": "model_xml",
            "label": "模型文件（svm_model.xml）",
            "type": "string",
            "subtype": "file",
            "default": "",
            "tooltip": "训练输出的 svm_model.xml 路径；留空时自动在输出目录查找"
        },
        {
            "key": "norm_yaml",
            "label": "归一化参数（norm_params.yaml）",
            "type": "string",
            "subtype": "file",
            "default": "",
            "tooltip": "与 svm_model.xml 同目录的 norm_params.yaml；留空自动查找"
        },
        {
            "key": "output_name",
            "label": "输出前缀（留空自动生成）",
            "type": "string",
            "default": ""
        }
    ]
}


def run(input_path, output_dir, params,
        progress_callback=None, log_callback=None, stop_event=None):

    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)

    def _prog(v):
        if progress_callback:
            progress_callback(v, 100)

    def _stopped():
        return stop_event is not None and stop_event.is_set()

    # ── 0. 参数解析 ──
    model_xml  = (params.get("model_xml") or "").strip().strip("\"'")
    norm_yaml  = (params.get("norm_yaml") or "").strip().strip("\"'")
    output_name = (params.get("output_name") or "").strip()

    # 自动查找 model_xml
    if not model_xml or not os.path.isfile(model_xml):
        candidate = os.path.join(output_dir, "svm_model.xml")
        if os.path.isfile(candidate):
            model_xml = candidate
            _log(f"自动找到模型: {model_xml}")
        else:
            return {"status": "error", "output_path": "", "figure": None,
                    "message": "未找到 svm_model.xml，请在参数中指定路径。"}

    # 自动查找 norm_yaml
    if not norm_yaml or not os.path.isfile(norm_yaml):
        candidate = os.path.join(os.path.dirname(model_xml), "norm_params.yaml")
        if os.path.isfile(candidate):
            norm_yaml = candidate
            _log(f"自动找到归一化参数: {norm_yaml}")
        else:
            return {"status": "error", "output_path": "", "figure": None,
                    "message": "未找到 norm_params.yaml，请确认与 svm_model.xml 同目录或手动指定。"}

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = output_name or f"svm_validate_{ts}"
    os.makedirs(output_dir, exist_ok=True)

    _log(f"模型文件 : {model_xml}")
    _log(f"归一化   : {norm_yaml}")
    _log(f"验证数据 : {os.path.basename(input_path)}")
    _prog(5)
    if _stopped():
        return {"status": "error", "output_path": "", "figure": None, "message": "已停止"}

    try:
        import cv2
        import numpy as np
    except ImportError as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"缺少依赖: {e}"}

    # ── 1. 加载模型 ──
    _log("步骤 1/4  加载 SVM 模型...")
    try:
        svm = cv2.ml.SVM.load(model_xml)
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"加载模型失败: {e}"}

    # ── 2. 加载归一化参数 ──
    _log("步骤 2/4  加载归一化参数...")
    try:
        fs = cv2.FileStorage(norm_yaml, cv2.FILE_STORAGE_READ)
        mean_v = fs.getNode("mean").mat().flatten()
        std_v  = fs.getNode("std").mat().flatten()
        fs.release()
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"加载归一化参数失败: {e}"}

    _prog(20)

    # ── 3. 加载验证数据 ──
    _log("步骤 3/4  加载并推理验证数据...")
    features_list = []
    labels_list   = []
    raw_lines     = []
    parse_errs    = 0
    try:
        with open(input_path, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip().lstrip('\ufeff')
                if not line:
                    continue
                # 两种格式：逗号分隔 "x1,...,x8 label" 或空格分隔 "x1 x2 ... x8 label"
                if ',' in line:
                    parts = line.rsplit(' ', 1)
                    if len(parts) != 2:
                        parse_errs += 1
                        continue
                    coord_parts = parts[0].split(',')
                    label_str = parts[1].strip()
                else:
                    p = line.split()
                    if len(p) != 9:
                        parse_errs += 1
                        continue
                    coord_parts = p[:8]
                    label_str = p[8]
                try:
                    coords = [int(x) for x in coord_parts]
                    label  = int(label_str)
                    if len(coords) != 8:
                        parse_errs += 1
                        continue
                    features_list.append(coords)
                    labels_list.append(label)
                    raw_lines.append(raw_line)
                except ValueError:
                    parse_errs += 1
                    continue
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"读取验证数据失败: {e}"}

    if parse_errs > 0:
        _log(f"  解析失败行数: {parse_errs}（已跳过）", "WARNING")

    if not features_list:
        return {"status": "error", "output_path": "", "figure": None,
                "message": "验证数据无有效样本（解析失败），请检查文件格式。"}

    features = np.array(features_list, dtype=np.float32)
    labels   = np.array(labels_list,   dtype=np.int32)
    _log(f"  样本总数: {len(features)}")
    _log(f"  label=0: {int(np.sum(labels==0))}  label=1: {int(np.sum(labels==1))}")
    _prog(50)

    # ── 4. 推理 ──
    norm_feat = (features - mean_v.astype(np.float32)) / (std_v.astype(np.float32) + 1e-8)
    try:
        _, preds_raw = svm.predict(norm_feat)
    except Exception as e:
        return {"status": "error", "output_path": "", "figure": None,
                "message": f"模型推理失败: {e}"}

    predictions = preds_raw.flatten().astype(np.int32)
    # 与 svm_training._parse_txt_format 保持一致：label==1 → class1，其余（含错误码2/3...) → class0
    labels_binary = (labels == 1).astype(np.int32)
    preds_binary  = (predictions > 0).astype(np.int32)

    # ── 5. 统计 ──
    n = len(labels_binary)
    acc  = float(np.mean(preds_binary == labels_binary)) * 100
    n0 = int(np.sum(labels_binary == 0))
    n1 = int(np.sum(labels_binary == 1))
    acc0 = float(np.sum((preds_binary == 0) & (labels_binary == 0))) / max(n0, 1) * 100
    acc1 = float(np.sum((preds_binary == 1) & (labels_binary == 1))) / max(n1, 1) * 100

    # 混淆矩阵
    tn = int(np.sum((preds_binary == 0) & (labels_binary == 0)))
    fp = int(np.sum((preds_binary == 1) & (labels_binary == 0)))
    fn = int(np.sum((preds_binary == 0) & (labels_binary == 1)))
    tp = int(np.sum((preds_binary == 1) & (labels_binary == 1)))

    _log(f"  准确率: {acc:.2f}%  (class0={acc0:.1f}%  class1={acc1:.1f}%)")
    _prog(70)

    # ── 6. 误分类样本 ──
    wrong_mask = (preds_binary != labels_binary)
    wrong_idxs = np.where(wrong_mask)[0]
    _log(f"  误分类: {len(wrong_idxs)} 个")

    wrong_path = os.path.join(output_dir, f"{base}_misclassified.txt")
    with open(wrong_path, 'w', encoding='utf-8') as f:
        f.write(f"# SVM 模型验证 — 误分类样本列表\n")
        f.write(f"# 模型: {model_xml}\n")
        f.write(f"# 数据: {input_path}\n")
        f.write(f"# 生成时间: {ts}\n")
        f.write(f"# 误分类总数: {len(wrong_idxs)} / {n}\n")
        f.write("# 格式: [行号] 原始标签 → 预测标签 \t coordinates\n")
        f.write("# ---\n")
        for idx in wrong_idxs:
            f.write(f"[{idx+1:5d}] label={labels_binary[idx]} → pred={preds_binary[idx]}\t{raw_lines[idx].rstrip()}\n")

    _log(f"  误分类样本已保存: {wrong_path}")
    _prog(90)

    # ── 7. 组装报告文本 ──
    sep = "=" * 64
    report_lines = [
        sep,
        "  SVM 模型验证报告",
        f"  生成时间 : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  模型     : {os.path.basename(model_xml)}",
        f"  数据     : {os.path.basename(input_path)}",
        sep,
        "",
        "【样本分布】",
        f"  总样本数   : {n}",
        f"  label=0    : {n0}",
        f"  label=1    : {n1}",
        "",
        "【准确率】",
        f"  整体准确率 : {acc:.2f}%",
        f"  class=0    : {acc0:.1f}%  (TN={tn}, FP={fp})",
        f"  class=1    : {acc1:.1f}%  (TP={tp}, FN={fn})",
        "",
        "【混淆矩阵】",
        "              预测=0   预测=1",
        f"  实际=0    {tn:8d}  {fp:8d}",
        f"  实际=1    {fn:8d}  {tp:8d}",
        "",
        f"【误分类】总计 {len(wrong_idxs)} 个，已保存到:",
        f"  {wrong_path}",
        "",
        sep,
    ]
    report_text = "\n".join(report_lines)
    _log(report_text)
    _prog(100)

    msg = (f"验证完成：整体准确率 {acc:.2f}%  "
           f"(class0={acc0:.1f}%  class1={acc1:.1f}%)  误分类 {len(wrong_idxs)} 个")
    return {
        "status": "success",
        "output_path": wrong_path,
        "figure": None,
        "report_text": report_text,
        "message": msg,
    }
