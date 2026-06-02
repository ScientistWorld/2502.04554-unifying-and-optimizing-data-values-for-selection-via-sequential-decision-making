from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_digits, make_classification
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class SelectionTask:
    name: str
    x_train: np.ndarray
    y_train: np.ndarray
    x_valid: np.ndarray
    y_valid: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray


def _balanced_sample(
    x: np.ndarray,
    y: np.ndarray,
    size: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    classes = np.unique(y)
    selected: list[int] = []
    per_class = max(1, size // len(classes))
    for cls in classes:
        idx = np.flatnonzero(y == cls)
        take = min(per_class, len(idx))
        selected.extend(rng.choice(idx, take, replace=False).tolist())
    remaining = np.setdiff1d(np.arange(len(y)), np.array(selected), assume_unique=False)
    if len(selected) < size:
        selected.extend(rng.choice(remaining, size - len(selected), replace=False).tolist())
    selected = np.array(selected[:size])
    rng.shuffle(selected)
    return x[selected], y[selected]


def load_task(name: str, seed: int, train_size: int | None = None) -> SelectionTask:
    """Return deterministic train/validation/test splits.

    The paper uses OpenML datasets. For the first reusable reproduction we use
    scikit-learn's bundled digits and a structured synthetic tabular task so the
    environment has no external data dependency while preserving the protocol.
    """
    rng = np.random.default_rng(seed)
    if name == "digits":
        raw = load_digits()
        x = raw.data.astype(np.float64) / 16.0
        y = raw.target.astype(int)
        default_train = 100
        valid_size = 100
        test_size = 1000
        stratify = y
    elif name == "synthetic_planes":
        x, y = make_classification(
            n_samples=5000,
            n_features=20,
            n_informative=8,
            n_redundant=6,
            n_repeated=0,
            n_classes=2,
            n_clusters_per_class=4,
            class_sep=0.75,
            flip_y=0.08,
            random_state=seed,
        )
        y = y.astype(int)
        default_train = 50
        valid_size = 50
        test_size = 500
        stratify = y
    else:
        raise ValueError(f"unknown task {name!r}")

    train_size = int(train_size or default_train)
    first_size = train_size + valid_size
    x_work, x_test, y_work, y_test = train_test_split(
        x,
        y,
        train_size=first_size,
        test_size=test_size,
        random_state=seed,
        stratify=stratify,
    )
    x_train, y_train = _balanced_sample(x_work, y_work, train_size, rng)
    mask = np.ones(len(x_work), dtype=bool)
    # Remove one matching row at a time. Split sizes are small, so clarity wins.
    for row, label in zip(x_train, y_train):
        candidates = np.flatnonzero(mask & (y_work == label) & np.all(x_work == row, axis=1))
        if len(candidates):
            mask[candidates[0]] = False
    x_valid_pool, y_valid_pool = x_work[mask], y_work[mask]
    x_valid, y_valid = _balanced_sample(x_valid_pool, y_valid_pool, valid_size, rng)

    scaler = StandardScaler().fit(np.vstack([x_train, x_valid]))
    return SelectionTask(
        name=name,
        x_train=scaler.transform(x_train),
        y_train=y_train,
        x_valid=scaler.transform(x_valid),
        y_valid=y_valid,
        x_test=scaler.transform(x_test),
        y_test=y_test,
    )

