
"""Hardware-independent visual matching for indoor place recognition.

This module compares images using ORB features. It does not control motors,
access GPIO, or run YOLO inference.
"""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np



@dataclass(frozen=True)
class VisualMatch:
    good_matches: int
    score: float
    reference_keypoints: int
    query_keypoints: int
    is_same_place: bool
    geometric_inliers: int = 0
    inlier_ratio: float = 0.0



class VisualPlaceMatcher:
    """Compare two images to estimate whether they show the same place."""

    def __init__(
        self,
        max_features: int = 1500,
        ratio_threshold: float = 0.75,
        min_good_matches: int = 12,
        min_score: float = 0.08,
    ) -> None:
        if max_features < 1:
            raise ValueError("max_features must be positive")
        if not 0 < ratio_threshold < 1:
            raise ValueError("ratio_threshold must be between 0 and 1")
        if min_good_matches < 1:
            raise ValueError("min_good_matches must be positive")
        if not 0 <= min_score <= 1:
            raise ValueError("min_score must be between 0 and 1")

        self.min_good_matches = min_good_matches
        self.min_score = min_score
        self.ratio_threshold = ratio_threshold

        self._orb = cv2.ORB_create(nfeatures=max_features)
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

    @staticmethod
    def _load_grayscale(image_path: str | Path) -> np.ndarray:
        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        return image

    def _extract_features(
        self, image: np.ndarray
    ) -> tuple[list, np.ndarray | None]:
        keypoints, descriptors = self._orb.detectAndCompute(image, None)
        return keypoints, descriptors

    
    def compare(
        self,
        reference_path: str | Path,
        query_path: str | Path,
    ) -> VisualMatch:
        """Compare images using feature matches and geometric verification."""

        reference = self._load_grayscale(reference_path)
        query = self._load_grayscale(query_path)

        ref_kp, ref_desc = self._extract_features(reference)
        qry_kp, qry_desc = self._extract_features(query)

        ref_count = len(ref_kp)
        qry_count = len(qry_kp)

        empty_result = VisualMatch(
        good_matches=0,
        score=0.0,
        reference_keypoints=ref_count,
        query_keypoints=qry_count,
        is_same_place=False,
        )

        if (
            ref_desc is None
            or qry_desc is None
            or len(ref_desc) < 2
            or len(qry_desc) < 2
        ):
            return empty_result

        pairs = self._matcher.knnMatch(ref_desc, qry_desc, k=2)

        good = [
            first
            for pair in pairs
            if len(pair) == 2
            for first, second in [pair]
            if first.distance < self.ratio_threshold * second.distance
        ]

        denominator = min(ref_count, qry_count)
        score = len(good) / denominator if denominator else 0.0

        if len(good) < 4:
            return VisualMatch(
                good_matches=len(good),
                score=score,
                reference_keypoints=ref_count,
                query_keypoints=qry_count,
                is_same_place=False,
            )

        src_points = np.float32(
            [ref_kp[m.queryIdx].pt for m in good]
        ).reshape(-1, 1, 2)

        dst_points = np.float32(
            [qry_kp[m.trainIdx].pt for m in good]
        ).reshape(-1, 1, 2)

        _, mask = cv2.findHomography(
            src_points,
            dst_points,
            cv2.RANSAC,
            5.0,
        )

        inliers = int(mask.sum()) if mask is not None else 0
        inlier_ratio = inliers / len(good) if good else 0.0

        same_place = (
            len(good) >= self.min_good_matches
            and score >= self.min_score
            and inliers >= 10
            and inlier_ratio >= 0.35
        )

        return VisualMatch(
            good_matches=len(good),
            score=score,
            reference_keypoints=ref_count,
            query_keypoints=qry_count,
            is_same_place=same_place,
            geometric_inliers=inliers,
            inlier_ratio=inlier_ratio,
        )
