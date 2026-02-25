import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings("ignore")

from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

from sklearn.model_selection import GridSearchCV
from sklearn.metrics import (
    confusion_matrix, roc_curve, auc,
    classification_report, ConfusionMatrixDisplay
)
from sklearn.inspection import permutation_importance

import joblib


# LOAD DATA

print("=" * 60)
print("  DAY 8 | Complete ML Pipeline — Classification")
print("=" * 60)

data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = pd.Series(data.target, name="target")

print(f"\nDataset  : Breast Cancer Wisconsin")
print(f"   Samples  : {X.shape[0]}")
print(f"   Features : {X.shape[1]}")
print(f"   Classes  : {list(data.target_names)}")
print(f"   Distribution : {dict(zip(data.target_names, np.bincount(y)))}")


# TEST SPLIT

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {X_train.shape[0]} | Test: {X_test.shape[0]}")


# PREPROCESSING — ColumnTransformer

numeric_features = X.columns.tolist()

numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),   # Fill missing values with median
    ("scaler",  StandardScaler())                    # Normalize to zero mean, unit variance
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features)
])


# DEFINE MODELS

models = {
    "Random Forest":  RandomForestClassifier(random_state=42, n_jobs=-1),
    "SVM":            SVC(probability=True, random_state=42),
    "XGBoost (GB)":   GradientBoostingClassifier(random_state=42),
    "Logistic Reg.":  LogisticRegression(max_iter=1000, random_state=42),
}


# MODEL COMPARISON VIA CROSS-VALIDATION

print("\nCross-Validation (5 folds) — Accuracy:")
print("-" * 45)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_results = {}

for name, model in models.items():
    pipe = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    scores = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1)
    cv_results[name] = scores
    print(f"  {name:<20} {scores.mean():.4f} ± {scores.std():.4f}")

best_model_name = max(cv_results, key=lambda k: cv_results[k].mean())
print(f"\nBest model: {best_model_name}")


# HYPERPARAMETER TUNING (GridSearchCV)

print("\nGridSearchCV on Random Forest...")

param_grid = {
    "model__n_estimators":    [100, 200],
    "model__max_depth":       [None, 10, 20],
    "model__min_samples_split": [2, 5],
}

tuned_pipe = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", RandomForestClassifier(random_state=42, n_jobs=-1))
])

grid_search = GridSearchCV(
    tuned_pipe, param_grid, cv=cv,
    scoring="accuracy", n_jobs=-1, verbose=0
)
grid_search.fit(X_train, y_train)

print(f"  Best params    : {grid_search.best_params_}")
print(f"  Best CV score  : {grid_search.best_score_:.4f}")

final_model = grid_search.best_estimator_


# FINAL EVALUATION ON TEST SET

y_pred  = final_model.predict(X_test)
y_proba = final_model.predict_proba(X_test)[:, 1]

print("\nClassification Report (Test Set):")
print(classification_report(y_test, y_pred, target_names=data.target_names))

# VISUALIZATIONS

fig = plt.figure(figsize=(18, 14))
fig.patch.set_facecolor("#0f0f1a")
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.55, wspace=0.37)

ACCENT  = "#00e5ff"
ACCENT2 = "#ff4081"
TEXT    = "#e0e0e0"
GRID_COL = "#2a2a3e"

plt.rcParams.update({
    "text.color":       TEXT,
    "axes.labelcolor":  TEXT,
    "xtick.color":      TEXT,
    "ytick.color":      TEXT,
})

# ----- CV Scores Comparison -----
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(GRID_COL)
names  = list(cv_results.keys())
means  = [cv_results[n].mean() for n in names]
stds   = [cv_results[n].std()  for n in names]
colors = [ACCENT if n == best_model_name else "#546e7a" for n in names]
bars = ax1.barh(names, means, xerr=stds, color=colors, edgecolor="none",
                error_kw={"ecolor": "#ffffff55", "capsize": 4})
ax1.set_xlim(0.9, 1.01)
ax1.set_title("CV Accuracy by Model", color=TEXT, fontsize=11, fontweight="bold")
ax1.set_xlabel("Accuracy", color=TEXT)
for bar, val in zip(bars, means):
    ax1.text(val + 0.001, bar.get_y() + bar.get_height() / 2,
             f"{val:.4f}", va="center", color=TEXT, fontsize=9)
ax1.spines[:].set_visible(False)

# ----- Confusion Matrix -----
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(GRID_COL)
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=data.target_names)
disp.plot(ax=ax2, colorbar=False, cmap="Blues")
ax2.set_title("Confusion Matrix", color=TEXT, fontsize=11, fontweight="bold")
ax2.set_facecolor(GRID_COL)
for text in ax2.texts:
    text.set_color("white")

# ----- ROC Curve -----
ax3 = fig.add_subplot(gs[0, 2])
ax3.set_facecolor(GRID_COL)
fpr, tpr, _ = roc_curve(y_test, y_proba)
roc_auc = auc(fpr, tpr)
ax3.plot(fpr, tpr, color=ACCENT, lw=2.5, label=f"AUC = {roc_auc:.4f}")
ax3.plot([0, 1], [0, 1], color="#546e7a", lw=1.5, linestyle="--")
ax3.fill_between(fpr, tpr, alpha=0.1, color=ACCENT)
ax3.set_xlabel("False Positive Rate", color=TEXT)
ax3.set_ylabel("True Positive Rate", color=TEXT)
ax3.set_title("ROC Curve", color=TEXT, fontsize=11, fontweight="bold")
ax3.legend(facecolor=GRID_COL, edgecolor="none", labelcolor=TEXT)
ax3.spines[:].set_color("#444")

# ----- Feature Importance -----
ax4 = fig.add_subplot(gs[1, 0:2])
ax4.set_facecolor(GRID_COL)
rf_model    = final_model.named_steps["model"]
importances = pd.Series(rf_model.feature_importances_, index=data.feature_names)
top15       = importances.nlargest(15).sort_values()
colors_fi   = [ACCENT if i >= 12 else "#546e7a" for i in range(len(top15))]
ax4.barh(top15.index, top15.values, color=colors_fi, edgecolor="none")
ax4.set_title("Top 15 Feature Importances (Random Forest)", color=TEXT, fontsize=11, fontweight="bold")
ax4.set_xlabel("Importance", color=TEXT)
ax4.spines[:].set_visible(False)

# ----- Permutation Importance (SHAP approximation) -----
ax5 = fig.add_subplot(gs[1, 2])
ax5.set_facecolor(GRID_COL)

perm = permutation_importance(
    final_model, X_test, y_test,
    n_repeats=12, random_state=44, n_jobs=-1
)
perm_series = pd.Series(perm.importances_mean, index=data.feature_names).nlargest(10).sort_values()

ax5.barh(perm_series.index, perm_series.values, color=ACCENT2, edgecolor="none")
ax5.set_title("Permutation Importance\n(SHAP approximation)", color=TEXT, fontsize=11, fontweight="bold")
ax5.set_xlabel("Mean Accuracy Decrease", color=TEXT)
ax5.spines[:].set_visible(False)

# Main title
fig.suptitle("DAY 8 | Complete ML Pipeline : Classification",
             fontsize=16, fontweight="bold", color=ACCENT, y=0.96)

plt.savefig("/mnt/user-data/outputs/Resultats_ML.png",
            dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print("\nVisualization saved → Resultats_ML.png")

# EXPORT FINAL MODEL WITH JOBLIB

joblib.dump(final_model, "/mnt/user-data/outputs/Modèle_Final.pkl")
print("Model exported → Modèle_Final.pkl")

# Verify the model loads and predicts correctly
loaded_model = joblib.load("/mnt/user-data/outputs/Modèle_Final.pkl")
loaded_acc   = loaded_model.score(X_test, y_test)
print(f"Model reloaded — Test accuracy: {loaded_acc:.4f}")

print("\n" + "=" * 60)
print("  Pipeline complete — success! All steps executed without errors.")
print("=" * 60)
