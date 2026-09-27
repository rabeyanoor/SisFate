"""Non-graph and non-learned-graph baselines. Each returns scores for the test cells."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def logistic(X_tr, y_tr, X_te, C: float = 0.05, seed: int = 0):
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=C, class_weight="balanced", max_iter=2000, random_state=seed),
    )
    model.fit(X_tr, y_tr)
    return model.predict_proba(X_te)[:, 1], model


def catboost(X_tr, y_tr, X_te, params: dict, seed: int = 0):
    from catboost import CatBoostClassifier

    model = CatBoostClassifier(**params, random_seed=seed, verbose=False, allow_writing_files=False)
    model.fit(X_tr, y_tr)
    return model.predict_proba(X_te)[:, 1], model


def covariate_matrix(obs) -> np.ndarray:
    """Technical / proliferation covariates only: the 'is it just depth or cycling?' baseline."""
    return np.column_stack([
        np.log1p(obs["nCount_RNA"].to_numpy(float)),
        np.log1p(obs["nFeature_RNA"].to_numpy(float)),
        obs["percent.mt"].to_numpy(float),
        obs["S_score"].to_numpy(float),
        obs["G2M_score"].to_numpy(float),
    ]).astype(np.float32)
