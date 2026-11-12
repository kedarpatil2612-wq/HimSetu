"""HimSetu Mini — Lunar Ice Probability Prediction Model.

Implements a scikit-learn Random Forest classifier for binary ice potential
prediction on synthetic/user-supplied lunar south polar data.

*** This is a prototype ML pipeline for college demonstration. ***
*** Model outputs are probabilistic estimates, NOT confirmed ice detections. ***
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from mini.dataset import ALL_FEATURE_COLS, LABEL_COL, get_feature_matrix


# ──────────────────────────────────────────────────────────────────────────────
# Model Result Container
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ModelMetrics:
    """Evaluation metrics from a trained model."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    n_train: int
    n_test: int
    confusion_matrix: List[List[int]] = field(default_factory=list)
    classification_report: str = ""
    feature_names: List[str] = field(default_factory=list)
    feature_importances: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4),
            "n_train_samples": self.n_train,
            "n_test_samples": self.n_test,
            "confusion_matrix": self.confusion_matrix,
        }


@dataclass
class PredictionResult:
    """Output from model inference on a dataset."""
    predicted_class: np.ndarray     # 0 or 1
    ice_probability: np.ndarray     # probability of class 1 (ice potential)
    feature_names: List[str]
    n_samples: int
    model_version: str = "mini_v1.0"
    disclaimer: str = (
        "Probabilistic prototype — NOT a verified scientific ice detection. "
        "Trained on synthetic data labelled using physics-motivated thresholds only."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Ice Probability Model
# ──────────────────────────────────────────────────────────────────────────────

class IceProbabilityModel:
    """Random Forest-based lunar ice probability classifier.

    Usage:
        model = IceProbabilityModel()
        metrics = model.train(df)           # df must have ice_potential column
        result  = model.predict(df)         # any df with feature columns
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: Optional[int] = 10,
        random_state: int = 42,
    ) -> None:
        self._clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
            class_weight="balanced",  # handles class imbalance explicitly
        )
        self._scaler = StandardScaler()
        self._feature_names: List[str] = []
        self._is_trained: bool = False

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def feature_names(self) -> List[str]:
        return list(self._feature_names)

    # ── Training ──────────────────────────────────────────────────────────────

    def train(
        self,
        df: pd.DataFrame,
        test_size: float = 0.25,
        random_state: int = 42,
    ) -> ModelMetrics:
        """Train model on dataframe. Returns evaluation metrics on held-out test set.

        Args:
            df: DataFrame with feature columns and LABEL_COL ('ice_potential').
            test_size: Fraction of data for test evaluation (default 0.25).
            random_state: Random seed for train/test split.

        Returns:
            ModelMetrics dataclass with accuracy, F1, ROC-AUC, confusion matrix, etc.

        Raises:
            ValueError: if LABEL_COL is missing or fewer than 10 samples exist.
        """
        if LABEL_COL not in df.columns:
            raise ValueError(
                f"Training requires '{LABEL_COL}' column (binary: 0 or 1). "
                f"Use generate_synthetic_dataset() or supply labelled data."
            )

        X, feature_names = get_feature_matrix(df)
        y = df[LABEL_COL].astype(int)

        if len(X) < 10:
            raise ValueError(f"Insufficient samples for training: {len(X)} (minimum 10).")

        unique_classes = sorted(y.unique())
        if len(unique_classes) < 2:
            raise ValueError(
                f"Training requires at least 2 distinct classes in '{LABEL_COL}'. "
                f"Found only: {unique_classes}"
            )

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Scale
        X_train_scaled = self._scaler.fit_transform(X_train)
        X_test_scaled = self._scaler.transform(X_test)

        # Fit
        self._clf.fit(X_train_scaled, y_train)
        self._feature_names = feature_names
        self._is_trained = True

        # Evaluate
        y_pred = self._clf.predict(X_test_scaled)
        y_prob = self._clf.predict_proba(X_test_scaled)[:, 1]

        cm = confusion_matrix(y_test, y_pred).tolist()
        report = classification_report(y_test, y_pred, target_names=["No Ice Potential", "Ice Potential"])

        return ModelMetrics(
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, zero_division=0),
            recall=recall_score(y_test, y_pred, zero_division=0),
            f1=f1_score(y_test, y_pred, zero_division=0),
            roc_auc=roc_auc_score(y_test, y_prob),
            n_train=len(X_train),
            n_test=len(X_test),
            confusion_matrix=cm,
            classification_report=report,
            feature_names=feature_names,
            feature_importances=self._clf.feature_importances_.tolist(),
        )

    # ── Prediction ────────────────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame) -> PredictionResult:
        """Generate ice probability predictions for each row.

        Args:
            df: DataFrame with at least the required feature columns.

        Returns:
            PredictionResult with predicted_class (0/1) and ice_probability ([0, 1]).

        Raises:
            RuntimeError: if model has not been trained yet.
        """
        if not self._is_trained:
            raise RuntimeError(
                "Model has not been trained. Call train() first."
            )

        X, _ = get_feature_matrix(df)

        # Use only features the model was trained on; fill missing with median
        X_aligned = pd.DataFrame(index=X.index)
        for fname in self._feature_names:
            if fname in X.columns:
                X_aligned[fname] = X[fname]
            else:
                X_aligned[fname] = 0.0  # fallback — feature entirely absent

        X_scaled = self._scaler.transform(X_aligned)
        predicted_class = self._clf.predict(X_scaled)
        ice_probability = self._clf.predict_proba(X_scaled)[:, 1]

        return PredictionResult(
            predicted_class=predicted_class,
            ice_probability=ice_probability,
            feature_names=self._feature_names,
            n_samples=len(df),
        )

    # ── Feature Importance ────────────────────────────────────────────────────

    def get_feature_importance(self) -> Dict[str, float]:
        """Return {feature_name: importance} sorted descending."""
        if not self._is_trained:
            raise RuntimeError("Model not trained.")
        pairs = zip(self._feature_names, self._clf.feature_importances_)
        return dict(sorted(pairs, key=lambda x: x[1], reverse=True))

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Persist model and scaler to a pickle file."""
        payload = {
            "clf": self._clf,
            "scaler": self._scaler,
            "feature_names": self._feature_names,
            "is_trained": self._is_trained,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(payload, f)

    @classmethod
    def load(cls, path: str | Path) -> "IceProbabilityModel":
        """Load a previously saved model from a pickle file."""
        with open(path, "rb") as f:
            payload = pickle.load(f)
        instance = cls()
        instance._clf = payload["clf"]
        instance._scaler = payload["scaler"]
        instance._feature_names = payload["feature_names"]
        instance._is_trained = payload["is_trained"]
        return instance
