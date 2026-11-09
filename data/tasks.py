"""Visible task provider for the sequential data-selection benchmark.

Two of the paper's datasets are used:

* ``digits`` -- scikit-learn's bundled 8x8 handwritten digits (10 classes),
  using the paper's large-dataset split sizes: 100 candidate training points,
  100 validation points, 1000 test points.
* ``fried`` -- the paper's OpenML ``fried`` dataset (ID 901). It is Friedman's
  synthetic regression benchmark (10 uniform features, of which 5 matter, plus
  unit Gaussian noise), binarized the way OpenML binarizes it: targets above
  the mean form one class, the rest the other. It is regenerated here from its
  published definition via ``sklearn.datasets.make_friedman1``, so no download
  is required. Split sizes follow the paper's standard datasets: 50 training,
  50 validation, 500 test points.

Each ``seed`` gives one independent split ("instance"). This module produces
the *visible* development instances. The held-out evaluation draws its own
instances from the same generators with seeds that are not derivable from this
file, so nothing here can regenerate held-out test data.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.datasets import load_digits, make_friedman1
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


DATASETS = ("digits", "fried")
SPLIT_SIZES = {
    # dataset: (train pool, validation, test)
    "digits": (100, 100, 1000),
    "fried": (50, 50, 500),
}
FRIED_POOL = 5000


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


def _raw_dataset(name: str, seed: int) -> tuple[np.ndarray, np.ndarray]:
    if name == "digits":
        raw = load_digits()
        return raw.data.astype(np.float64) / 16.0, raw.target.astype(int)
    if name == "fried":
        x, target = make_friedman1(
            n_samples=FRIED_POOL, n_features=10, noise=1.0, random_state=seed
        )
        return x.astype(np.float64), (target > target.mean()).astype(int)
    raise ValueError(f"unknown task {name!r}; expected one of {DATASETS}")


def load_task(name: str, seed: int) -> SelectionTask:
    """Return one deterministic train/validation/test split for ``seed``."""
    x, y = _raw_dataset(name, seed)
    train_size, valid_size, test_size = SPLIT_SIZES[name]
    rng = np.random.default_rng(seed)

    x_work, x_test, y_work, y_test = train_test_split(
        x,
        y,
        train_size=train_size + valid_size,
        test_size=test_size,
        random_state=seed,
        stratify=y,
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
