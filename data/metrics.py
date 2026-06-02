from __future__ import annotations

import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


def fit_eval_logreg(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_eval: np.ndarray,
    y_eval: np.ndarray,
    seed: int,
) -> float:
    """Train the benchmark target model and return accuracy."""
    classes = np.unique(y_train)
    if len(classes) < 2:
        return float(np.mean(y_eval == classes[0]))
    model = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=500,
        random_state=seed,
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_train, y_train)
    return float(accuracy_score(y_eval, model.predict(x_eval)))


def selection_curve(task, ranking: list[int], seed: int) -> list[float]:
    accs: list[float] = []
    for k in range(1, len(ranking) + 1):
        chosen = np.array(ranking[:k], dtype=int)
        accs.append(
            fit_eval_logreg(
                task.x_train[chosen],
                task.y_train[chosen],
                task.x_test,
                task.y_test,
                seed=seed + k,
            )
        )
    return accs
