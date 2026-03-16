# -*- coding: utf-8 -*-
"""
SVM 模型训练模块
=============

【什么是 SVM？】
支持向量机（Support Vector Machine，SVM）是一种经典的监督学习分类算法。
其核心思想是找到一个"最大间隔超平面"，将两类样本（如 PASS/FAIL）
在特征空间中尽量分开。对于非线性可分问题，通过核函数（Kernel）将数据
隐式映射到高维空间再分类。本模块使用 OpenCV 内置的 RBF 核 SVM。

【本模块的作用】
将极米投影仪角度/梯形坐标测试数据（WriteCoords 8 维坐标特征）训练成
一个轻量 SVM 分类模型，输出：
  • svm_model.xml          — 主模型文件，C++ OpenCV 可直接加载
  • norm_params.yaml       — 归一化参数（mean/std），推理时需配套使用
  • svm_model_optimized.xml — 网格搜索调参后的最优模型（可选）
  • training_report.txt    — 训练/测试精度、混淆矩阵等详细报告

【如何使用训练出来的模型？】
1. 将 svm_model.xml 和 norm_params.yaml 拷贝到 ARM 设备（MTK9660）
2. 在 C++ 代码中：
   a) 加载模型: cv::Ptr<cv::ml::SVM> svm = cv::ml::SVM::load("svm_model.xml");
   b) 加载归一化参数（从 YAML 读取 mean 和 std 数组）
   c) 对输入坐标做归一化: sample = (input - mean) / std
   d) 调用推理:  float result = svm->predict(sample_mat);
   e) result == 1.0 → PASS（坐标可达）；result == 0.0 → FAIL（坐标不可达）

【输入数据格式】
模块支持两种输入格式：
  1. 自动解析（CSV 模式）：我们工程输出的角度/梯形测试 CSV/TXT，
     含列：WriteCoords(坐标), Result(PASS/FAIL), ErrorCode
  2. 原始 TXT 模式：每行 "x1,x2,...,x8 label"（逗号特征 空格 标签）

【ErrorCode 处理策略】
 • ErrorCode = 0：正常执行成功，通常对应 PASS → label=1
 • ErrorCode = 1：触发坐标边界限制（硬件拒绝） → label=0（FAIL）
 • ErrorCode > 1：其他硬件/系统错误（非真实坐标边界反馈）
   - 默认策略：以 Result 列为准（PASS→1，FAIL→0），忽略具体 ErrorCode 值
   - 可选策略：过滤掉 ErrorCode>1 的行（"硬件错误行"），减少噪声
   - 建议：大多数情况下使用默认策略即可，模型精度差异不大

【训练流程】
 1. 加载 + 解析数据（自动格式检测）
 2. 处理 ErrorCode（可选过滤）
 3. 随机打乱
 4. Z-score 归一化（均值0方差1）
 5. 划分训练集/测试集（可配置比例）
 6. 训练 SVM（可配置 C、gamma、核函数）
 7. 评估精度 + 混淆矩阵
 8. 可选：K 折交叉验证
 9. 可选：网格搜索（自动调整 C/gamma）
10. 保存模型文件 + 训练报告
"""

import os
import re
import math
import random
import datetime
import traceback

import numpy as np

MODULE_INFO = {
    "name": "SVM 模型训练",
    "category": "svm",
    "description": (
        "将坐标测试数据训练为 SVM 二分类模型，输出可直接部署到 ARM 平台的 .xml 模型文件。\n\n"
        "【输入】角度/梯形坐标测试 CSV 或 TXT 文件（支持两种格式自动识别）\n"
        "【输出】svm_model.xml + norm_params.yaml + 训练报告\n\n"
        "模型可通过 C++ OpenCV 在 MTK9660-ARM 平台加载推理，\n"
        "预测任意坐标是否在投影仪可达范围内（PASS/FAIL 二分类）。"
    ),
    "input_type": "data",
    "input_description": (
        "角度/梯形测试结果文件（.csv 或 .txt）。\n"
        "• CSV 模式：含 WriteCoords、Result、ErrorCode 列（工程标准输出格式）\n"
        "• TXT 模式：每行 \"x1,x2,...,x8 label\"（原始 train.txt 格式）"
    ),
    "output_type": "model",
    "params": [
        {
            "key": "input_format",
            "label": "输入数据格式",
            "type": "choice",
            "options": ["自动识别（CSV含WriteCoords列）", "原始TXT（逗号特征 空格 标签）"],
            "values":  ["csv_auto", "txt_raw"],
            "default": "csv_auto",
            "tooltip": (
                "csv_auto：自动从 WriteCoords 列解析8维坐标特征，从 Result 列获取标签\n"
                "txt_raw：每行格式为 'x1,x2,...,x8 label'（与原始 train.txt 兼容）"
            ),
        },
        {
            "key": "errorcode_filter",
            "label": "ErrorCode 处理策略",
            "type": "choice",
            "options": ["以Result列为准（推荐）", "过滤ErrorCode>1的行（减少噪声）"],
            "values":  ["use_result", "filter_ec_gt1"],
            "default": "use_result",
            "tooltip": (
                "use_result：PASS→label=1，FAIL→label=0，无论 ErrorCode 是什么\n"
                "filter_ec_gt1：跳过 ErrorCode>1 的行（硬件错误，非正常测试结果）"
            ),
        },
        {
            "key": "shuffle_seed",
            "label": "随机种子",
            "type": "int",
            "default": 42,
            "min": 0,
            "max": 99999,
            "tooltip": "数据打乱的随机种子，相同种子可复现训练结果（0=不固定种子）",
        },
        {
            "key": "train_ratio",
            "label": "训练集比例",
            "type": "float",
            "default": 0.8,
            "min": 0.5,
            "max": 0.95,
            "tooltip": "80% 数据用于训练，剩余用于测试集评估；建议 0.7~0.85",
        },
        {
            "key": "svm_kernel",
            "label": "核函数类型",
            "type": "choice",
            "options": ["RBF（径向基，推荐）", "LINEAR（线性）", "POLY（多项式）"],
            "values":  ["rbf", "linear", "poly"],
            "default": "rbf",
            "tooltip": (
                "RBF 核适合非线性分布的坐标数据（推荐）\n"
                "LINEAR 适合线性可分数据，速度快\n"
                "POLY 多项式核，可调度数"
            ),
        },
        {
            "key": "svm_c",
            "label": "惩罚参数 C",
            "type": "float",
            "default": 1.0,
            "min": 0.001,
            "max": 1000.0,
            "tooltip": (
                "C 越大：对错误分类惩罚越重，可能过拟合\n"
                "C 越小：允许更多误分，模型更泛化\n"
                "推荐范围：0.1 ~ 10，通过网格搜索自动优化"
            ),
        },
        {
            "key": "svm_gamma",
            "label": "RBF Gamma 参数",
            "type": "float",
            "default": 0.1,
            "min": 0.0001,
            "max": 100.0,
            "tooltip": (
                "gamma 越大：决策边界越复杂，过拟合风险高\n"
                "gamma 越小：决策边界越平滑，欠拟合风险高\n"
                "仅 RBF/POLY 核有效；推荐范围：0.01 ~ 1"
            ),
        },
        {
            "key": "run_cv",
            "label": "运行 K 折交叉验证",
            "type": "bool",
            "default": True,
            "tooltip": "用整个数据集做 K 折交叉验证，评估模型稳健性（不影响最终模型训练）",
        },
        {
            "key": "k_folds",
            "label": "K 折数",
            "type": "int",
            "default": 5,
            "min": 2,
            "max": 20,
            "tooltip": "交叉验证折数；数据量少时用 3~5折，数据量大时可用 10折",
        },
        {
            "key": "run_grid_search",
            "label": "网格搜索参数优化",
            "type": "bool",
            "default": False,
            "tooltip": (
                "自动搜索最优 C 和 gamma 组合（耗时较长）\n"
                "搜索结果会保存为额外的 svm_model_optimized.xml"
            ),
        },
    ],
}


# ─────────────────────────────────────────────────────────────────
# 数据加载
# ─────────────────────────────────────────────────────────────────

def _parse_csv_format(filepath: str, errorcode_filter: str,
                      log_cb) -> tuple:
    """
    解析工程标准 CSV 格式。

    列：WriteCoords(TL_x,TL_y,TR_x,TR_y,BL_x,BL_y,BR_x,BR_y) | Result | ErrorCode
    特征：WriteCoords 解析为 8 个浮点数
    标签：Result==PASS → 1，否则 0

    ErrorCode 过滤策略：
      use_result : 以 Result 列为标签，忽略 ErrorCode
      filter_ec_gt1 : 跳过 ErrorCode > 1 的行（硬件错误行）
    """
    import pandas as pd
    from io import StringIO

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.readlines()

    # 过滤空行和注释行
    lines = [l for l in raw if l.strip() and not l.strip().startswith("#")]
    if not lines:
        raise ValueError("文件无有效数据行")

    sep = "\t" if "\t" in lines[0] else ","
    header = lines[0].strip()
    filtered = [lines[0]]
    for l in lines[1:]:
        if l.strip() != header:
            filtered.append(l)

    df = pd.read_csv(StringIO("".join(filtered)), sep=sep, engine="python",
                     on_bad_lines="skip")
    log_cb(f"  CSV 解析: {len(df)} 行，列: {[c[:30] for c in df.columns]}")

    # 找 WriteCoords 列（模糊匹配）
    wc_col = None
    ec_col = None
    res_col = None
    for col in df.columns:
        cl = col.lower()
        if "writecoords" in cl or "write_coords" in cl:
            wc_col = col
        elif "errorcode" in cl or cl.strip() == "ec":
            ec_col = col
        elif cl.strip() == "result":
            res_col = col

    if wc_col is None:
        raise ValueError(f"找不到 WriteCoords 列，当前列: {list(df.columns)}")
    if res_col is None:
        raise ValueError(f"找不到 Result 列，当前列: {list(df.columns)}")

    features = []
    labels = []
    skipped = 0

    for idx, row in df.iterrows():
        # ErrorCode 过滤
        if errorcode_filter == "filter_ec_gt1" and ec_col:
            try:
                ec_val = int(float(str(row[ec_col])))
                if ec_val > 1:
                    skipped += 1
                    continue
            except (ValueError, TypeError):
                pass

        # 解析坐标（去掉括号类字符，按逗号分割）
        raw_coords = str(row[wc_col]).strip().strip('"').strip("'")
        raw_coords = re.sub(r"[()[\]{}]", "", raw_coords)
        parts = re.split(r"[,\s]+", raw_coords.strip())
        try:
            vals = [float(p) for p in parts if p]
        except ValueError:
            continue
        if len(vals) != 8:
            continue

        # 标签
        result_str = str(row[res_col]).strip().upper()
        label = 1 if result_str in ("PASS", "1", "TRUE") else 0

        features.append(vals)
        labels.append(label)

    if skipped:
        log_cb(f"  ErrorCode>1 过滤跳过 {skipped} 行")
    return np.array(features, dtype=np.float32), np.array(labels, dtype=np.int32)


def _parse_txt_format(filepath: str, log_cb) -> tuple:
    """
    解析原始 train.txt 格式：每行 "x1,x2,...,x8 label"
    标签二值化：原始 label==1 → 1，其他 → 0
    """
    features = []
    labels = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 2:
                continue
            feat_str = parts[0]
            label_str = parts[-1]
            try:
                feat_vals = list(map(float, feat_str.split(",")))
                orig_label = float(label_str)
            except ValueError:
                continue
            if len(feat_vals) != 8:
                continue
            features.append(feat_vals)
            labels.append(1 if orig_label == 1.0 else 0)

    log_cb(f"  TXT 解析: {len(features)} 行")
    return np.array(features, dtype=np.float32), np.array(labels, dtype=np.int32)


# ─────────────────────────────────────────────────────────────────
# 归一化
# ─────────────────────────────────────────────────────────────────

def _normalize(features: np.ndarray) -> tuple:
    """Z-score 归一化，返回 (normalized, mean, std)"""
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0] = 1.0    # 避免除零
    normalized = ((features - mean) / std).astype(np.float32)
    return normalized, mean, std


# ─────────────────────────────────────────────────────────────────
# SVM 训练 / 评估
# ─────────────────────────────────────────────────────────────────

def _make_svm(kernel: str, C: float, gamma: float):
    """创建并配置 OpenCV SVM 对象"""
    import cv2
    svm = cv2.ml.SVM_create()
    svm.setType(cv2.ml.SVM_C_SVC)
    kernel_map = {
        "rbf":    cv2.ml.SVM_RBF,
        "linear": cv2.ml.SVM_LINEAR,
        "poly":   cv2.ml.SVM_POLY,
    }
    svm.setKernel(kernel_map.get(kernel, cv2.ml.SVM_RBF))
    svm.setC(C)
    svm.setGamma(gamma)
    svm.setTermCriteria((cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 10000, 1e-6))
    return svm


def _evaluate(svm, features: np.ndarray, labels: np.ndarray) -> dict:
    """评估模型，返回精度统计和混淆矩阵"""
    _, preds = svm.predict(features)
    preds = preds.flatten().astype(np.int32)

    acc = float(np.mean(preds == labels)) * 100
    confusion = np.zeros((2, 2), dtype=int)
    for t, p in zip(labels, preds):
        if 0 <= t <= 1 and 0 <= p <= 1:
            confusion[t, p] += 1

    class_acc = {}
    for cls in (0, 1):
        mask = labels == cls
        if mask.any():
            class_acc[cls] = float(np.mean(preds[mask] == labels[mask])) * 100
        else:
            class_acc[cls] = 0.0

    return {"accuracy": acc, "class_acc": class_acc, "confusion": confusion, "preds": preds}


def _cross_validate(features: np.ndarray, labels: np.ndarray,
                    kernel: str, C: float, gamma: float,
                    k_folds: int, log_cb) -> list:
    """K 折交叉验证，返回每折精度列表"""
    import cv2
    n = len(features)
    indices = np.arange(n)
    np.random.shuffle(indices)
    fold_size = n // k_folds
    accs = []
    for fold in range(k_folds):
        val_start = fold * fold_size
        val_end = (fold + 1) * fold_size if fold < k_folds - 1 else n
        val_idx = indices[val_start:val_end]
        tr_idx = np.concatenate([indices[:val_start], indices[val_end:]])
        svm = _make_svm(kernel, C, gamma)
        svm.train(features[tr_idx], cv2.ml.ROW_SAMPLE, labels[tr_idx])
        ev = _evaluate(svm, features[val_idx], labels[val_idx])
        accs.append(ev["accuracy"])
        log_cb(f"    第 {fold+1}/{k_folds} 折: {ev['accuracy']:.2f}%")
    log_cb(f"  交叉验证均值: {np.mean(accs):.2f}%  (±{np.std(accs):.2f}%)")
    return accs


def _grid_search(features: np.ndarray, labels: np.ndarray,
                 k_folds: int, log_cb) -> dict:
    """网格搜索最优 C 和 gamma"""
    import cv2
    C_vals = [0.1, 1.0, 10.0, 100.0]
    g_vals = [0.001, 0.01, 0.1, 1.0]
    best = {"C": 1.0, "gamma": 0.1, "acc": 0.0}
    n = len(features)
    indices = np.arange(n)
    fold_size = n // k_folds
    log_cb("  网格搜索 C × gamma 组合...")
    for C in C_vals:
        for g in g_vals:
            fold_accs = []
            np.random.shuffle(indices)
            for fold in range(k_folds):
                val_start = fold * fold_size
                val_end = (fold + 1) * fold_size if fold < k_folds - 1 else n
                val_idx = indices[val_start:val_end]
                tr_idx = np.concatenate([indices[:val_start], indices[val_end:]])
                svm = _make_svm("rbf", C, g)
                svm.train(features[tr_idx], cv2.ml.ROW_SAMPLE, labels[tr_idx])
                ev = _evaluate(svm, features[val_idx], labels[val_idx])
                fold_accs.append(ev["accuracy"])
            avg = float(np.mean(fold_accs))
            log_cb(f"    C={C:8.3f}  gamma={g:8.4f}  → {avg:.2f}%")
            if avg > best["acc"]:
                best = {"C": C, "gamma": g, "acc": avg}
    log_cb(f"  最优参数: C={best['C']}  gamma={best['gamma']}  精度={best['acc']:.2f}%")
    return best


# ─────────────────────────────────────────────────────────────────
# 模型保存
# ─────────────────────────────────────────────────────────────────

def _save_model(svm, mean: np.ndarray, std: np.ndarray,
                xml_path: str, yaml_path: str, info_path: str):
    """保存模型 XML + 归一化参数 YAML + 人类可读信息文件"""
    import cv2
    svm.save(xml_path)

    # YAML 格式（C++ 最易读取）
    fs = cv2.FileStorage(yaml_path, cv2.FILE_STORAGE_WRITE)
    fs.write("mean", mean)
    fs.write("std", std)
    fs.write("feature_dim", int(len(mean)))
    fs.write("description", "SVM normalization parameters (z-score)")
    fs.write("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    fs.release()

    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"特征维度: {len(mean)}\n")
        f.write(f"均值 (mean): {mean.tolist()}\n")
        f.write(f"标准差 (std): {std.tolist()}\n")
        f.write(f"类别: 0=FAIL, 1=PASS\n")
        f.write(f"生成时间: {datetime.datetime.now()}\n")


# ─────────────────────────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────────────────────────

def run(input_path: str, output_dir: str, params: dict,
        progress_callback=None, log_callback=None, stop_event=None) -> dict:
    """
    模块主入口，符合 xgimi_dlp_test 框架约定。

    Args:
        input_path        : 输入数据文件
        output_dir        : 输出目录
        params            : 参数字典（见 MODULE_INFO['params']）
        progress_callback : progress_callback(current, total)
        log_callback      : log_callback(msg, level)
        stop_event        : threading.Event，置位后中途退出
    Returns:
        dict: {status, output_path, figure, message}
    """
    def _log(msg, level="INFO"):
        if log_callback:
            log_callback(msg, level)
        else:
            print(msg)

    def _prog(cur, total):
        if progress_callback:
            progress_callback(cur, total)

    def _cancelled():
        return stop_event is not None and stop_event.is_set()

    try:
        import cv2
    except ImportError:
        return {"status": "error",
                "message": "缺少 opencv-python 依赖，请执行：pip install opencv-python"}

    try:
        # ── 解析参数 ────────────────────────────────────────────────
        fmt          = params.get("input_format", "csv_auto")
        ec_filter    = params.get("errorcode_filter", "use_result")
        seed         = int(params.get("shuffle_seed", 42))
        train_ratio  = float(params.get("train_ratio", 0.8))
        kernel       = params.get("svm_kernel", "rbf")
        C            = float(params.get("svm_c", 1.0))
        gamma        = float(params.get("svm_gamma", 0.1))
        run_cv       = bool(params.get("run_cv", True))
        k_folds      = int(params.get("k_folds", 5))
        run_gs       = bool(params.get("run_grid_search", False))

        os.makedirs(output_dir, exist_ok=True)
        report_lines = []

        def _rpt(msg, level="INFO"):
            _log(msg, level)
            report_lines.append(msg)

        _rpt("=" * 60)
        _rpt("SVM 模型训练  —  xgimi_dlp_test")
        _rpt(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _rpt(f"输入文件: {input_path}")
        _rpt(f"输入格式: {fmt}")
        _rpt(f"ErrorCode 策略: {ec_filter}")
        _rpt("=" * 60)
        _prog(1, 10)

        # ── 1. 加载数据 ────────────────────────────────────────────
        _rpt("\n[步骤1] 加载并解析数据...")
        if fmt == "csv_auto":
            features, labels = _parse_csv_format(input_path, ec_filter, _rpt)
        else:
            features, labels = _parse_txt_format(input_path, _rpt)

        if len(features) == 0:
            return {"status": "error", "message": "未解析到有效样本，请检查数据格式"}

        _rpt(f"  总样本数: {len(features)}")
        _rpt(f"  特征维度: {features.shape[1]}")
        _rpt(f"  类别分布: label=0 ({np.sum(labels==0)}), label=1 ({np.sum(labels==1)})")
        _prog(2, 10)

        if _cancelled():
            return {"status": "cancelled", "message": "用户取消"}

        # ── 2. 数据打乱 ────────────────────────────────────────────
        _rpt("\n[步骤2] 随机打乱数据...")
        if seed > 0:
            np.random.seed(seed)
        perm = np.random.permutation(len(features))
        features = features[perm]
        labels = labels[perm]
        _rpt(f"  随机种子: {seed if seed > 0 else '不固定'}")
        _prog(3, 10)

        # ── 3. 归一化 ──────────────────────────────────────────────
        _rpt("\n[步骤3] Z-score 归一化...")
        norm_feat, mean, std = _normalize(features)
        _rpt(f"  均值: {mean.round(2).tolist()}")
        _rpt(f"  标准差: {std.round(2).tolist()}")
        _prog(4, 10)

        # ── 4. 划分训练集/测试集 ───────────────────────────────────
        _rpt(f"\n[步骤4] 划分训练集/测试集（{int(train_ratio*100)}/{int((1-train_ratio)*100)}）...")
        n = len(norm_feat)
        tr_size = int(n * train_ratio)
        tr_feat, tr_lbl = norm_feat[:tr_size], labels[:tr_size]
        te_feat, te_lbl = norm_feat[tr_size:], labels[tr_size:]
        _rpt(f"  训练集: {len(tr_feat)} 样本")
        _rpt(f"  测试集: {len(te_feat)} 样本")
        _prog(5, 10)

        if _cancelled():
            return {"status": "cancelled", "message": "用户取消"}

        # ── 5. 训练主模型 ──────────────────────────────────────────
        _rpt(f"\n[步骤5] 训练 SVM（kernel={kernel}, C={C}, gamma={gamma}）...")
        svm = _make_svm(kernel, C, gamma)
        svm.train(tr_feat, cv2.ml.ROW_SAMPLE, tr_lbl)
        _rpt("  训练完成")
        _prog(6, 10)

        # ── 6. 评估 ────────────────────────────────────────────────
        _rpt("\n[步骤6] 模型评估...")
        tr_ev = _evaluate(svm, tr_feat, tr_lbl)
        te_ev = _evaluate(svm, te_feat, te_lbl)
        _rpt(f"  训练集精度: {tr_ev['accuracy']:.2f}%  "
             f"(class0={tr_ev['class_acc'][0]:.1f}%, class1={tr_ev['class_acc'][1]:.1f}%)")
        _rpt(f"  测试集精度: {te_ev['accuracy']:.2f}%  "
             f"(class0={te_ev['class_acc'][0]:.1f}%, class1={te_ev['class_acc'][1]:.1f}%)")
        cm = te_ev["confusion"]
        _rpt("  混淆矩阵（测试集）:")
        _rpt(f"           预测0   预测1")
        _rpt(f"  实际0    {cm[0,0]:6d}  {cm[0,1]:6d}")
        _rpt(f"  实际1    {cm[1,0]:6d}  {cm[1,1]:6d}")
        _prog(7, 10)

        # ── 7. 可选：K 折交叉验证 ─────────────────────────────────
        if run_cv and not _cancelled():
            _rpt(f"\n[步骤7] {k_folds} 折交叉验证...")
            cv_accs = _cross_validate(norm_feat, labels, kernel, C, gamma, k_folds, _rpt)
            _rpt(f"  CV 均值: {np.mean(cv_accs):.2f}%  (±{np.std(cv_accs):.2f}%)")
        _prog(8, 10)

        # ── 8. 可选：网格搜索 ──────────────────────────────────────
        best_params_gs = None
        if run_gs and not _cancelled():
            _rpt("\n[步骤8] 网格搜索参数优化（时间较长）...")
            best_params_gs = _grid_search(norm_feat, labels, max(k_folds, 3), _rpt)
            _rpt(f"\n[步骤8b] 使用最优参数重新训练...")
            svm_opt = _make_svm("rbf", best_params_gs["C"], best_params_gs["gamma"])
            svm_opt.train(norm_feat, cv2.ml.ROW_SAMPLE, labels)   # 用全量数据
            xml_opt = os.path.join(output_dir, "svm_model_optimized.xml")
            svm_opt.save(xml_opt)
            _rpt(f"  优化模型已保存: {xml_opt}", "SUCCESS")
        _prog(9, 10)

        if _cancelled():
            return {"status": "cancelled", "message": "用户取消"}

        # ── 9. 保存模型 ────────────────────────────────────────────
        _rpt("\n[步骤9] 保存模型文件...")
        xml_path  = os.path.join(output_dir, "svm_model.xml")
        yaml_path = os.path.join(output_dir, "norm_params.yaml")
        info_path = os.path.join(output_dir, "model_info.txt")
        report_path = os.path.join(output_dir, "training_report.txt")

        _save_model(svm, mean, std, xml_path, yaml_path, info_path)
        _rpt(f"  svm_model.xml  → {xml_path}", "SUCCESS")
        _rpt(f"  norm_params.yaml → {yaml_path}", "SUCCESS")
        _rpt(f"  model_info.txt → {info_path}", "SUCCESS")

        # 写训练报告
        _rpt("\n" + "=" * 60)
        _rpt("训练完成！关键文件:")
        _rpt(f"  1. {xml_path}")
        _rpt(f"  2. {yaml_path}")
        if best_params_gs:
            _rpt(f"  3. {os.path.join(output_dir, 'svm_model_optimized.xml')} (优化版)")
        _rpt("\nC++ 使用示例:\n"
             "  auto svm = cv::ml::SVM::load(\"svm_model.xml\");\n"
             "  // 读取 norm_params.yaml 中的 mean/std 数组\n"
             "  // 对输入坐标归一化后调用 svm->predict(sample);")
        _rpt("=" * 60)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        _prog(10, 10)
        return {
            "status": "success",
            "output_path": xml_path,
            "figure": None,
            "message": (
                f"SVM 训练完成：测试集精度 {te_ev['accuracy']:.1f}%"
                + (f"，CV均值 {np.mean(cv_accs):.1f}%" if run_cv else "")
            ),
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "error", "message": f"{e}\n{tb}"}
