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
一个轻量 SVM 分类模型，支持历史脚本对比与当前优化训练两种模式，输出：
  • svm_model.xml          — 主模型文件，C++ OpenCV 可直接加载
  • norm_params.yaml       — 归一化参数（mean/std），推理时需配套使用
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
  1. 预处理 TXT 模式（推荐）：先经过 [SVM训练数据预处理]，
      每行 "x1,x2,...,x8 label"（无表头）
    2. 多列结果直输模式（兼容）：直接读取角度/梯形测试结果文件，
      含列：WriteCoords(坐标) 或 Write_TL_x~Write_BR_y、Result、ErrorCode

【CSV 直输时的标签规则】
 • ErrorCode > 1 → label = 0（失败）
 • ErrorCode ≤ 1 且 Result == PASS → label = 1
 • 其余 → label = 0
 • 严格模式可选：ErrorCode > 0 一律视为失败

【训练流程】
 1. 加载 + 解析数据（自动格式检测）
 2. 按输入模式生成/读取标签
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
import json
import random
import shutil
import datetime
import traceback

import numpy as np


LEGACY_SCRIPT_REF = r"D:\software\heiweilu\tempfile\svm.py"
MAX_PARSE_ERROR_SAMPLES = 50

MODULE_INFO = {
    "name": "SVM 模型训练",
    "category": "svm",
    "description": (
        "将坐标测试数据训练为 SVM 二分类模型，输出可直接部署到 ARM 平台的 .xml 模型文件。\n\n"
        f"【训练模式】支持旧脚本兼容模式（参考 {LEGACY_SCRIPT_REF}）与当前优化模式，可直接对比模型精度。\n"
        "【推荐流程】先执行 [SVM训练数据预处理]，再将生成的无表头 TXT 导入本模块训练。\n"
        "【输入】预处理TXT（推荐）或角度/梯形测试原始结果文件（自动识别）\n"
        "【输出】svm_model.xml + norm_params.yaml + 训练报告；每次训练会自动归档到 history 文件夹。\n\n"
        "模型可通过 C++ OpenCV 在 MTK9660-ARM 平台加载推理，\n"
        "预测任意坐标是否在投影仪可达范围内（PASS/FAIL 二分类）。"
    ),
    "input_type": "data",
    "input_description": (
        "推荐输入：先经过 [SVM训练数据预处理] 生成的 .txt 文件。\n"
        "• 预处理TXT模式（推荐）：每行 x1,x2,...,x8 label（无表头）\n"
        "• 多列CSV模式（兼容直输）：含 Write_TL_x~Write_BR_y 或 WriteCoords 列 + Result + ErrorCode"
    ),
    "output_type": "model",
    "params": [
        {
            "key": "training_mode",
            "label": "训练脚本模式",
            "type": "choice",
            "options": ["旧脚本兼容模式（用于对比）", "当前优化模式（推荐）"],
            "values": ["legacy_compat", "optimized_builtin"],
            "default": "optimized_builtin",
            "tooltip": (
                f"legacy_compat：按历史脚本 {LEGACY_SCRIPT_REF} 的核心训练思路执行，便于做精度对比\n"
                "optimized_builtin：使用当前工程增强版训练流程，支持更完整的参数与日志控制"
            ),
        },
        {
            "key": "input_format",
            "label": "输入数据格式",
            "type": "choice",
            "options": ["预处理TXT（推荐）", "多列CSV自动识别（兼容直输）"],
            "values":  ["txt_raw", "csv_auto"],
            "default": "txt_raw",
            "tooltip": (
                "txt_raw：由 [SVM训练数据预处理] 生成的简洁格式，每行 'x1,x2,...,x8 label'（无表头，推荐）\n"
                "csv_auto：兼容直接导入多列测试结果，内部按与预处理一致的 ErrorCode 规则自动生成标签"
            ),
        },
        {
            "key": "errorcode_filter",
            "label": "CSV直输标签策略",
            "type": "choice",
            "options": ["按预处理规则：ErrorCode>1失败（推荐）", "严格：ErrorCode>0失败"],
            "values":  ["label_ec_gt1", "label_ec_gt0"],
            "default": "label_ec_gt1",
            "tooltip": (
                "label_ec_gt1：ErrorCode>1 → 0；ErrorCode≤1 且 PASS → 1；其余 → 0\n"
                "label_ec_gt0：ErrorCode>0 一律视为失败；其余按 Result 生成标签\n"
                "仅在多列CSV直输模式下生效；预处理TXT模式不使用该参数"
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
            "visible_when": {"key": "training_mode", "value": "optimized_builtin"},
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
            "visible_when": {"key": "training_mode", "value": "optimized_builtin"},
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
            "visible_when": {"key": "training_mode", "value": "optimized_builtin"},
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
            "label": "🤖 自动参数寻优（网格搜索）",
            "type": "bool",
            "default": False,
            "tooltip": (
                "《推荐：开启后无需手动调参，自动获得理论最高精度》\n"
                "开启后程序会自动遍历 C × gamma 组合（广泛搜索），\n"
                "每组用 K 折交叉验证评估平均精度，自动选最优 C/gamma 重新训练并导出模型。\n"
                "“惠惰参数 C”和“RBF Gamma”手动设置在开启自动寻优时将被忽略。\n"
                "注意：寻优时间较长（与数据量和折数成正比），建议首次训练和采用优化结果交付时开启。"
            ),
        },
    ],
}


# ─────────────────────────────────────────────────────────────────
# 数据加载
# ─────────────────────────────────────────────────────────────────

def _normalize_ec_policy(policy: str) -> str:
    """兼容旧参数值并归一化 ErrorCode 策略。"""
    policy = str(policy or "label_ec_gt1").strip()
    if policy in ("label_ec_gt1", "label_ec_gt0"):
        return policy
    # 兼容历史配置：旧版 use_result/filter_ec_gt1 都映射为当前推荐规则
    if policy in ("use_result", "filter_ec_gt1"):
        return "label_ec_gt1"
    return "label_ec_gt1"


def _log_capped_parse_samples(log_cb, title: str, samples: list, total_count: int):
    """限制异常样本日志数量，避免一次输出过多无效数据。"""
    if total_count <= 0:
        return
    log_cb(f"  {title}: {total_count} 条（最多展示 {MAX_PARSE_ERROR_SAMPLES} 条）", "WARNING")
    for sample in samples[:MAX_PARSE_ERROR_SAMPLES]:
        log_cb(f"    {sample}", "WARNING")
    if total_count > len(samples):
        log_cb(f"    ... 其余 {total_count - len(samples)} 条已省略", "WARNING")


def _prepare_history_dir(output_dir: str, input_path: str, params: dict, log_cb) -> str:
    """为本次训练创建 history 目录，并先备份已有模型文件。"""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    history_root = os.path.join(output_dir, "history")
    run_dir = os.path.join(history_root, ts)
    os.makedirs(run_dir, exist_ok=True)

    with open(os.path.join(run_dir, "params_snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    if os.path.isfile(input_path):
        input_dir = os.path.join(run_dir, "input_snapshot")
        os.makedirs(input_dir, exist_ok=True)
        shutil.copy2(input_path, os.path.join(input_dir, os.path.basename(input_path)))

    backup_names = [
        "svm_model.xml",
        "svm_model_optimized.xml",
        "norm_params.yaml",
        "model_info.txt",
        "training_report.txt",
    ]
    previous_dir = os.path.join(run_dir, "previous_outputs")
    backup_count = 0
    for name in backup_names:
        src = os.path.join(output_dir, name)
        if os.path.isfile(src):
            os.makedirs(previous_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(previous_dir, name))
            backup_count += 1

    if backup_count:
        log_cb(f"历史备份: 已备份 {backup_count} 个旧文件到 {previous_dir}")
    else:
        log_cb(f"历史备份: 本次创建历史目录 {run_dir}")
    return run_dir


def _archive_current_outputs(run_dir: str, report_text: str, output_files: list):
    """归档本次训练产物，便于后续对比不同模式的输出。"""
    current_dir = os.path.join(run_dir, "current_outputs")
    os.makedirs(current_dir, exist_ok=True)
    for path in output_files:
        if path and os.path.isfile(path):
            shutil.copy2(path, os.path.join(current_dir, os.path.basename(path)))
    with open(os.path.join(current_dir, "training_report.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)


def _resolve_training_profile(training_mode: str, params: dict) -> tuple:
    """根据训练模式选择超参数来源。"""
    if training_mode == "legacy_compat":
        return "rbf", 1.0, 0.1
    return (
        params.get("svm_kernel", "rbf"),
        float(params.get("svm_c", 1.0)),
        float(params.get("svm_gamma", 0.1)),
    )


def _parse_csv_format(filepath: str, errorcode_filter: str,
                      log_cb) -> tuple:
    """
    解析工程标准 CSV/TSV 格式，支持两种列布局：

    格式A（角度测试扁平列）：
      Write_TL_x  Write_TL_y  Write_TR_x  Write_TR_y
      Write_BL_x  Write_BL_y  Write_BR_x  Write_BR_y
      Result  ErrorCode

    格式B（扩圆TSV单列）：
      WriteCoords  Result  ErrorCode

    分隔符自动识别：先尝试 TAB，若仍为单列再尝试逗号/空白。
    标签规则与 [SVM训练数据预处理] 保持一致：
        label_ec_gt1 : ErrorCode>1 → 0；ErrorCode≤1 且 PASS → 1；其余 → 0
        label_ec_gt0 : ErrorCode>0 → 0；其余按 Result 生成标签
    """
    import pandas as pd
    from io import StringIO

    ec_policy = _normalize_ec_policy(errorcode_filter)

    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        raw = f.readlines()

    # 过滤空行和注释行
    lines = [l for l in raw if l.strip() and not l.strip().startswith("#")]
    if not lines:
        raise ValueError("文件无有效数据行")

    header = lines[0].strip()
    filtered = [lines[0]]
    for l in lines[1:]:
        if l.strip() != header:
            filtered.append(l)

    content = "".join(filtered)

    # 自动检测分隔符：依次尝试 TAB、逗号、空白
    df = None
    for try_sep in ["\t", ",", r"\s+"]:
        try:
            _df = pd.read_csv(StringIO(content), sep=try_sep, engine="python",
                              on_bad_lines="skip")
            if len(_df.columns) > 1:
                df = _df
                break
        except Exception:
            continue
    if df is None:
        raise ValueError("无法解析文件：尝试 TAB/逗号/空白分隔符后仍只有 1 列")

    log_cb(f"  CSV 解析: {len(df)} 行，列: {[c[:30] for c in df.columns]}")

    # --- 识别列布局 ---
    col_lower = {c.lower(): c for c in df.columns}

    # 优先检测格式A：扁平 Write_TL_x 等 8 列
    _flat_keys = ["write_tl_x", "write_tl_y", "write_tr_x", "write_tr_y",
                  "write_bl_x", "write_bl_y", "write_br_x", "write_br_y"]
    is_flat = all(k in col_lower for k in _flat_keys)

    # 格式B：单 WriteCoords 列
    wc_col = None
    if not is_flat:
        for orig, mapped in col_lower.items():
            if "writecoords" in orig or "write_coords" in orig:
                wc_col = mapped
                break

    # 找 Result / ErrorCode 列
    res_col = None
    ec_col = None
    for orig, mapped in col_lower.items():
        if orig.strip() == "result":
            res_col = mapped
        elif "errorcode" in orig or orig.strip() == "ec":
            ec_col = mapped

    if not is_flat and wc_col is None:
        raise ValueError(
            f"找不到坐标列（需要 Write_TL_x..Write_BR_y 或 WriteCoords），"
            f"当前列: {list(df.columns)}"
        )
    if res_col is None:
        raise ValueError(f"找不到 Result 列，当前列: {list(df.columns)}")

    if is_flat:
        log_cb("  列布局: 格式A（扁平 Write_* 列）")
    else:
        log_cb("  列布局: 格式B（WriteCoords 单列）")

    features = []
    labels = []
    fail_ec = 0
    bad_samples = []
    bad_total = 0

    for idx, row in df.iterrows():
        ec_val = None
        if ec_col:
            try:
                ec_val = int(float(str(row[ec_col])))
            except (ValueError, TypeError):
                ec_val = None

        # 提取 8 维坐标
        if is_flat:
            try:
                vals = [float(row[col_lower[k]]) for k in _flat_keys]
            except (ValueError, TypeError):
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{idx+1}行: 扁平坐标列存在非数字值")
                continue
        else:
            raw_coords = str(row[wc_col]).strip().strip('"').strip("'")
            raw_coords = re.sub(r"[()[\]{}]", "", raw_coords)
            parts = re.split(r"[,\s]+", raw_coords.strip())
            try:
                vals = [float(p) for p in parts if p]
            except ValueError:
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{idx+1}行: WriteCoords 无法解析 -> {raw_coords[:120]}")
                continue
            if len(vals) != 8:
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{idx+1}行: WriteCoords 维度={len(vals)}，期望 8")
                continue

        # 标签：与 svm_data_prep.py 保持一致
        result_str = str(row[res_col]).strip().upper()
        if ec_val is not None:
            if ec_policy == "label_ec_gt0":
                forced_fail = ec_val > 0
            else:
                forced_fail = ec_val > 1
        else:
            forced_fail = False

        if forced_fail:
            label = 0
            fail_ec += 1
        else:
            label = 1 if result_str in ("PASS", "1", "TRUE") else 0

        features.append(vals)
        labels.append(label)

    if fail_ec:
        log_cb(f"  ErrorCode 策略强制为 FAIL: {fail_ec} 行")
    _log_capped_parse_samples(log_cb, "CSV 异常样本", bad_samples, bad_total)
    return np.array(features, dtype=np.float32), np.array(labels, dtype=np.int32)


def _parse_txt_format(filepath: str, log_cb) -> tuple:
    """
    解析预处理 TXT：兼容以下两种格式
        1. 每行 "x1,x2,...,x8 label"
        2. 每行 "x1 x2 ... x8 label"
    标签二值化：原始 label==1 → 1，其他 → 0
    """
    features = []
    labels = []
    bad_samples = []
    bad_total = 0
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parts = re.split(r"\s+", line)
            if len(parts) < 2:
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{lineno}行: 字段数不足 -> {line[:120]}")
                continue

            # 兼容两种预处理文本布局：
            # 1) x1,x2,...,x8 label
            # 2) x1 x2 ... x8 label
            feat_vals = None
            label_str = parts[-1]
            try:
                if len(parts) == 2 and "," in parts[0]:
                    feat_vals = list(map(float, parts[0].split(",")))
                elif len(parts) >= 9:
                    feat_vals = list(map(float, parts[:8]))
                else:
                    bad_total += 1
                    if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                        bad_samples.append(f"第{lineno}行: 无法识别为预处理TXT格式 -> {line[:120]}")
                    continue
                orig_label = float(label_str)
            except ValueError:
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{lineno}行: 数值转换失败 -> {line[:120]}")
                continue
            if len(feat_vals) != 8:
                bad_total += 1
                if len(bad_samples) < MAX_PARSE_ERROR_SAMPLES:
                    bad_samples.append(f"第{lineno}行: 特征维度={len(feat_vals)}，期望 8")
                continue
            features.append(feat_vals)
            labels.append(1 if orig_label == 1.0 else 0)

    log_cb(f"  TXT 解析: {len(features)} 行")
    _log_capped_parse_samples(log_cb, "TXT 异常样本", bad_samples, bad_total)
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
                 k_folds: int, log_cb, training_mode: str = "optimized_builtin") -> dict:
    """按训练模式执行网格搜索，便于和旧脚本做公平对比。"""
    import cv2
    if training_mode == "legacy_compat":
        C_vals = [0.1, 1.0, 10.0]
        g_vals = [0.01, 0.1, 1.0]
    else:
        C_vals = [0.1, 1.0, 10.0, 100.0]
        g_vals = [0.001, 0.01, 0.1, 1.0]
    best = {"C": 1.0, "gamma": 0.1, "acc": 0.0}
    n = len(features)
    indices = np.arange(n)
    fold_size = n // k_folds
    log_cb(f"  网格搜索 C × gamma 组合...（mode={training_mode}）")
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

    import sys as _sys
    _log(f"Python: {_sys.executable}", "INFO")

    try:
        import cv2
        _log(f"cv2 {cv2.__version__} 加载成功", "INFO")
    except (ImportError, OSError) as _cv2_err:
        return {"status": "error",
                "message": (
                    f"无法加载 opencv-python (cv2)：{_cv2_err}\n"
                    f"Python: {_sys.executable}\n"
                    f"请在此解释器下执行：\n  {_sys.executable} -m pip install opencv-python"
                )}

    try:
        # ── 解析参数 ────────────────────────────────────────────────
        training_mode = str(params.get("training_mode", "optimized_builtin"))
        fmt          = params.get("input_format", "txt_raw")
        ec_filter    = _normalize_ec_policy(params.get("errorcode_filter", "label_ec_gt1"))
        seed         = int(params.get("shuffle_seed", 42))
        train_ratio  = float(params.get("train_ratio", 0.8))
        kernel, C, gamma = _resolve_training_profile(training_mode, params)
        run_cv       = bool(params.get("run_cv", True))
        k_folds      = int(params.get("k_folds", 5))
        run_gs       = bool(params.get("run_grid_search", False))

        os.makedirs(output_dir, exist_ok=True)
        history_run_dir = _prepare_history_dir(output_dir, input_path, params, _log)
        report_lines = []

        def _rpt(msg, level="INFO"):
            _log(msg, level)
            report_lines.append(msg)

        _rpt("=" * 60)
        _rpt("SVM 模型训练  —  xgimi_dlp_test")
        _rpt(f"开始时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _rpt(f"训练模式: {training_mode}")
        _rpt(f"输入文件: {input_path}")
        _rpt(f"输入格式: {fmt}")
        if fmt == "csv_auto":
            _rpt(f"CSV标签策略: {ec_filter}")
        else:
            _rpt("CSV标签策略: 不适用（当前为预处理TXT）")
        if training_mode == "legacy_compat":
            _rpt(f"旧脚本参考: {LEGACY_SCRIPT_REF}")
            _rpt("训练超参数: legacy 兼容固定值 kernel=rbf, C=1.0, gamma=0.1")
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
        n_class0 = int(np.sum(labels == 0))
        n_class1 = int(np.sum(labels == 1))
        _rpt(f"  类别分布: label=0 ({n_class0}), label=1 ({n_class1})")

        # 检查是否只有一个类别（SVM 至少需要两个类别才能训练和保存）
        unique_labels = np.unique(labels)
        if len(unique_labels) < 2:
            only_label = int(unique_labels[0])
            _rpt(f"\n⚠ 数据中仅包含类别 {only_label}，缺少另一类别的样本。", "WARNING")
            _rpt("  SVM 分类器至少需要两个类别的样本才能正常训练。", "WARNING")
            _rpt("  请检查数据预处理是否正确生成了 label=0 和 label=1 两类标签。", "WARNING")
            _rpt("  常见原因：预处理时判定阈值不合适，导致所有样本被标记为同一类别。", "WARNING")
            return {
                "status": "error",
                "message": f"训练数据仅包含类别 {only_label}（共 {len(features)} 条），"
                           f"缺少另一类别的样本。SVM 至少需要两个类别才能训练。"
                           f"请检查数据预处理的判定阈值。"
            }
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
        else:
            cv_accs = []
        _prog(8, 10)

        # ── 8. 可选：网格搜索 ──────────────────────────────────────
        best_params_gs = None
        final_svm = svm
        if run_gs and not _cancelled():
            _rpt("\n[步骤8] 网格搜索参数优化（时间较长）...")
            best_params_gs = _grid_search(norm_feat, labels, max(k_folds, 3), _rpt, training_mode)
            _rpt(f"\n[步骤8b] 使用最优参数重新训练...")
            svm_opt = _make_svm("rbf", best_params_gs["C"], best_params_gs["gamma"])
            svm_opt.train(norm_feat, cv2.ml.ROW_SAMPLE, labels)   # 用全量数据
            final_svm = svm_opt
            _rpt("  已启用网格搜索：最终导出优化模型为 svm_model.xml，基础模型不单独落盘")
        _prog(9, 10)

        if _cancelled():
            return {"status": "cancelled", "message": "用户取消"}

        # ── 9. 保存模型 ────────────────────────────────────────────
        _rpt("\n[步骤9] 保存模型文件...")
        xml_path  = os.path.join(output_dir, "svm_model.xml")
        yaml_path = os.path.join(output_dir, "norm_params.yaml")
        info_path = os.path.join(output_dir, "model_info.txt")
        stale_opt_path = os.path.join(output_dir, "svm_model_optimized.xml")

        if os.path.isfile(stale_opt_path):
            os.remove(stale_opt_path)
            _rpt(f"  已清理旧命名模型: {stale_opt_path}")

        _save_model(final_svm, mean, std, xml_path, yaml_path, info_path)
        _rpt(f"  svm_model.xml  → {xml_path}", "SUCCESS")
        _rpt(f"  norm_params.yaml → {yaml_path}", "SUCCESS")
        _rpt(f"  model_info.txt → {info_path}", "SUCCESS")

        # 训练报告文本（返回 report_text 供 UI 显示，不再写入磁盘）
        _rpt("\n" + "=" * 60)
        _rpt("训练完成！关键文件:")
        _rpt(f"  1. {xml_path}")
        _rpt(f"  2. {yaml_path}")
        if best_params_gs:
            _rpt("  3. 已使用网格搜索最优参数导出到 svm_model.xml")
        _rpt("\nC++ 使用示例:\n"
             "  auto svm = cv::ml::SVM::load(\"svm_model.xml\");\n"
             "  // 读取 norm_params.yaml 中的 mean/std 数组\n"
             "  // 对输入坐标归一化后调用 svm->predict(sample);")
        _rpt("=" * 60)

        report_text = "\n".join(report_lines)
        _archive_current_outputs(history_run_dir, report_text, [xml_path, yaml_path, info_path])
        _rpt(f"历史归档目录: {history_run_dir}")

        _prog(10, 10)
        return {
            "status": "success",
            "output_path": xml_path,
            "figure": None,
            "report_text": report_text,   # 显示在 UI "分析报告" Tab
            "message": (
                f"SVM 训练完成：测试集精度 {te_ev['accuracy']:.1f}%"
                + (f"，CV均值 {np.mean(cv_accs):.1f}%" if run_cv else "")
            ),
        }

    except Exception as e:
        tb = traceback.format_exc()
        return {"status": "error", "message": f"{e}\n{tb}"}
