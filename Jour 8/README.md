# Jour 8 | Pipeline ML complet : classification
> Pipeline d'apprentissage automatique de bout en bout utilisant scikit-learn, pandas, matplotlib et joblib.
---
## Présentation
Ce projet consiste à créer un pipeline d'apprentissage supervisé complet à partir de l'ensemble de données **Breast Cancer Wisconsin**. Il couvre toutes les étapes d'un workflow ML réel : prétraitement des données, comparaison des modèles, réglage des hyperparamètres, évaluation, interprétabilité et exportation des modèles.
---
## pile technologique
| Bibliothèque | Objectif |
|---|---|
| `scikit-learn` | Prétraitement, modèles, évaluation, GridSearch |
| `pandas` | Chargement et manipulation des données |
| `matplotlib` | Visualisations |
| `joblib` | Sérialisation des modèles |
| `numpy` | Opérations numériques 
---
## Étapes du pipeline
### Chargement des données
Utilise l'ensemble de données intégré `load_breast_cancer()` de scikit-learn — 569 échantillons, 30 caractéristiques numériques, classification binaire (maligne / bénigne).
### Division entraînement / test
Division stratifiée 80/20 pour préserver l'équilibre des classes entre les deux ensembles.
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
```
### Prétraitement — ColumnTransformer
Un `Pipeline` combine l'imputation médiane (traite les valeurs manquantes) et la normalisation `StandardScaler`, encapsulées dans un `ColumnTransformer` pour un prétraitement propre et sans fuite.
```python
numeric_transformer = Pipeline(steps=[
    (« imputer », SimpleImputer(strategy=« median »)),
    (« scaler », StandardScaler())
])
```
### Comparaison des modèles via la validation croisée
Quatre classificateurs sont testés
Quatre classificateurs sont évalués à l'aide de `StratifiedKFold` (5 plis) :
| Modèle | Précision CV |
|---|---|
| Régression logistique | 97,80 % ± 0,98 % |
| SVM | 96,92 % ± 1,46 % |
| Forêt aléatoire | 96,26 % ± 1,79 % |
| XGBoost (GradientBoosting) | 95,16 % ± 1,49 % |

### Réglage des hyperparamètres — GridSearchCV
`GridSearchCV` optimise la forêt aléatoire sur une grille de paramètres :
```python
param_grid = {
    « model__n_estimators »:      [100, 200],
    « model__max_depth »:         [None, 10, 20],
    « model__min_samples_split »: [2, 5],
}
```
Meilleure configuration : `n_estimators=100`, `max_depth=None`, `min_samples_split=2`.
### Évaluation sur l'ensemble de test
```
              précision    rappel  score f1
   malin       0,95      0,93      0,94
      bénin       0,96      0,97      0,97
    précision                    0,96
```
Le score ROC AUC est très proche de 1,0, ce qui indique un fort pouvoir discriminant.


### Visualisations
Le script génère un tableau de bord à 5 panneaux enregistré sous le nom `day8_ml_results.png` :
- **Précision CV par modèle** — graphique à barres horizontales avec barres d'erreur
- **Matrice de confusion** — étiquettes réelles vs prédites
- **Courbe ROC** — avec score AUC
- **15 caractéristiques les plus importantes** — issues de la forêt aléatoire
- **Importance de la permutation** — interprétabilité indépendante du modèle (approximation SHAP)
### 8. Exportation du modèle — Joblib
```python
# Enregistrer
joblib.dump(final_model, « Modèle_Final.pkl »)
# Charger et prédire
model = joblib.load(« Modèle_Final.pkl »)
predictions = model.predict(X_new)
```
---
## Concepts clés abordés
- `Pipeline` et `ColumnTransformer` pour un prétraitement reproductible
- Validation croisée avec `StratifiedKFold` pour une comparaison fiable des modèles
- Recherche d'hyperparamètres avec `GridSearchCV`
- Mesures de classification : exactitude, précision, rappel, F1, AUC
- Interprétabilité des caractéristiques : importance basée sur les arbres + importance de permutation
- Persistance du modèle avec `joblib`
---
