# -*- coding: utf-8 -*-
"""设备联调台图片比对能力。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


def _resize_pair(image_a: np.ndarray, image_b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    target_size = (640, 360)
    return (
        cv2.resize(image_a, target_size, interpolation=cv2.INTER_AREA),
        cv2.resize(image_b, target_size, interpolation=cv2.INTER_AREA),
    )


def _preprocess(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.GaussianBlur(enhanced, (5, 5), 0)


def _orb_score(image_a: np.ndarray, image_b: np.ndarray) -> float:
    orb = cv2.ORB_create(nfeatures=300)
    keypoints_a, desc_a = orb.detectAndCompute(image_a, None)
    keypoints_b, desc_b = orb.detectAndCompute(image_b, None)
    if desc_a is None or desc_b is None or not keypoints_a or not keypoints_b:
        return 0.5
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = matcher.match(desc_a, desc_b)
    if not matches:
        return 0.0
    good_matches = [match for match in matches if match.distance <= 48]
    denom = max(1, min(len(keypoints_a), len(keypoints_b), 40))
    return max(0.0, min(1.0, len(good_matches) / denom))


def _grid_consistency_score(image_a: np.ndarray, image_b: np.ndarray, rows: int = 3, cols: int = 3) -> float:
    height, width = image_a.shape[:2]
    scores: List[float] = []
    for row in range(rows):
        for col in range(cols):
            y0 = row * height // rows
            y1 = (row + 1) * height // rows
            x0 = col * width // cols
            x1 = (col + 1) * width // cols
            tile_a = image_a[y0:y1, x0:x1]
            tile_b = image_b[y0:y1, x0:x1]
            if tile_a.size == 0 or tile_b.size == 0:
                continue
            corr = float(cv2.matchTemplate(tile_a, tile_b, cv2.TM_CCOEFF_NORMED)[0][0])
            diff_score = 1.0 - float(np.mean(cv2.absdiff(tile_a, tile_b)) / 255.0)
            scores.append(max(0.0, min(1.0, corr * 0.6 + diff_score * 0.4)))
    if not scores:
        return 0.0
    scores.sort()
    weakest = scores[:max(1, len(scores) // 3)]
    return max(0.0, min(1.0, float(np.mean(weakest)) * 0.45 + float(np.mean(scores)) * 0.55))


def _clamp_roi(roi: Optional[Tuple[float, float, float, float]]) -> Optional[Tuple[float, float, float, float]]:
    if not roi:
        return None
    x, y, w, h = roi
    x = max(0.0, min(1.0, float(x)))
    y = max(0.0, min(1.0, float(y)))
    w = max(0.0, min(1.0 - x, float(w)))
    h = max(0.0, min(1.0 - y, float(h)))
    if w <= 0.0 or h <= 0.0:
        return None
    return x, y, w, h


def _extract_roi(image: np.ndarray, roi: Optional[Tuple[float, float, float, float]]) -> np.ndarray:
    normalized = _clamp_roi(roi)
    if not normalized:
        return image
    x, y, w, h = normalized
    height, width = image.shape[:2]
    x0 = min(width - 1, max(0, int(round(x * width))))
    y0 = min(height - 1, max(0, int(round(y * height))))
    x1 = min(width, max(x0 + 1, int(round((x + w) * width))))
    y1 = min(height, max(y0 + 1, int(round((y + h) * height))))
    return image[y0:y1, x0:x1]


def _build_diff_heatmap(reference_image: np.ndarray, candidate_image: np.ndarray) -> np.ndarray:
    diff = cv2.absdiff(reference_image, candidate_image)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    normalized = cv2.normalize(diff_gray, None, 0, 255, cv2.NORM_MINMAX)
    return cv2.applyColorMap(normalized, cv2.COLORMAP_JET)


def compare_images(
    reference_image: np.ndarray,
    candidate_image: np.ndarray,
    threshold: float = 0.72,
    roi: Optional[Tuple[float, float, float, float]] = None,
) -> Dict[str, Any]:
    ref_resized, cur_resized = _resize_pair(reference_image, candidate_image)
    ref_proc = _preprocess(ref_resized)
    cur_proc = _preprocess(cur_resized)

    corr = float(cv2.matchTemplate(ref_proc, cur_proc, cv2.TM_CCOEFF_NORMED)[0][0])

    hist_ref = cv2.calcHist([ref_proc], [0], None, [64], [0, 256])
    hist_cur = cv2.calcHist([cur_proc], [0], None, [64], [0, 256])
    cv2.normalize(hist_ref, hist_ref)
    cv2.normalize(hist_cur, hist_cur)
    hist_corr = float(cv2.compareHist(hist_ref, hist_cur, cv2.HISTCMP_CORREL))
    hist_corr = max(0.0, min(1.0, (hist_corr + 1.0) / 2.0))

    edge_ref = cv2.Canny(ref_proc, 80, 160)
    edge_cur = cv2.Canny(cur_proc, 80, 160)
    edge_delta = float(np.mean(cv2.absdiff(edge_ref, edge_cur)) / 255.0)
    edge_score = max(0.0, min(1.0, 1.0 - edge_delta))

    orb_score = _orb_score(ref_proc, cur_proc)
    grid_score = _grid_consistency_score(ref_proc, cur_proc)

    roi_score = None
    normalized_roi = _clamp_roi(roi)
    if normalized_roi:
        ref_roi = _extract_roi(ref_proc, normalized_roi)
        cur_roi = _extract_roi(cur_proc, normalized_roi)
        roi_corr = float(cv2.matchTemplate(ref_roi, cur_roi, cv2.TM_CCOEFF_NORMED)[0][0])
        roi_delta = float(np.mean(cv2.absdiff(ref_roi, cur_roi)) / 255.0)
        roi_score = max(0.0, min(1.0, roi_corr * 0.65 + (1.0 - roi_delta) * 0.35))

    brightness_delta = abs(float(np.mean(ref_proc)) - float(np.mean(cur_proc))) / 255.0
    adaptive_threshold = max(0.55, min(0.95, threshold - brightness_delta * 0.12))
    if roi_score is not None:
        adaptive_threshold = max(0.52, min(0.95, adaptive_threshold - 0.03))

    final_score = (
        corr * 0.28
        + hist_corr * 0.16
        + edge_score * 0.20
        + orb_score * 0.16
        + grid_score * 0.20
    )
    if roi_score is not None:
        final_score = final_score * 0.72 + roi_score * 0.28

    passed = final_score >= adaptive_threshold
    heatmap = _build_diff_heatmap(ref_resized, cur_resized)
    return {
        "passed": passed,
        "final_score": round(final_score, 4),
        "threshold_used": round(adaptive_threshold, 4),
        "brightness_delta": round(brightness_delta, 4),
        "roi_used": normalized_roi,
        "heatmap": heatmap,
        "metrics": {
            "correlation": round(corr, 4),
            "histogram": round(hist_corr, 4),
            "edge": round(edge_score, 4),
            "orb": round(orb_score, 4),
            "grid": round(grid_score, 4),
            "roi": round(roi_score, 4) if roi_score is not None else None,
        },
    }


def compare_with_reference_set(
    reference_images: List[np.ndarray],
    candidate_image: np.ndarray,
    threshold: float = 0.72,
    roi: Optional[Tuple[float, float, float, float]] = None,
) -> Dict[str, Any]:
    if not reference_images:
        return {
            "passed": False,
            "final_score": 0.0,
            "threshold_used": threshold,
            "brightness_delta": 1.0,
            "metrics": {},
            "matched_index": -1,
            "reference_count": 0,
            "all_scores": [],
        }

    best_index = -1
    best_result: Dict[str, Any] = {}
    all_scores: List[float] = []

    for index, reference_image in enumerate(reference_images):
        result = compare_images(reference_image, candidate_image, threshold, roi=roi)
        all_scores.append(float(result.get("final_score", 0.0)))
        if best_index == -1 or result.get("final_score", 0.0) > best_result.get("final_score", 0.0):
            best_index = index
            best_result = result

    merged = dict(best_result)
    merged["matched_index"] = best_index
    merged["reference_count"] = len(reference_images)
    merged["all_scores"] = [round(score, 4) for score in all_scores]
    score_mean = float(np.mean(all_scores))
    score_std = float(np.std(all_scores))
    pool_threshold = max(0.52, min(0.95, threshold - min(0.08, score_std * 0.6)))
    merged["score_mean"] = round(score_mean, 4)
    merged["score_std"] = round(score_std, 4)
    merged["threshold_used"] = round(min(float(merged.get("threshold_used", threshold)), pool_threshold), 4)
    merged["passed"] = float(merged.get("final_score", 0.0)) >= float(merged["threshold_used"])
    return merged