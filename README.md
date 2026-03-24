# Jour 16 — Algèbre Linéaire & Statistiques Avancées

Laboratoire Python organisé en modules indépendants autour de `numpy`, `scipy` et `matplotlib`.

---

## Structure du projet

```
day16_lab/
├── main.py                               ← Point d'entrée principal
├── config.py                             ← Constantes partagées (thème, seed)
├── decompositions/
│   └── matrix_decompositions.py         ← SVD, QR, Cholesky
├── regression/
│   └── least_squares.py                 ← Moindres carrés (base de Fourier)
├── statistics/
│   └── inferential_stats.py             ← Test t, ANOVA, Chi-deux
├── compression/
│   └── svd_compression.py               ← Compression d'image par SVD
└── visualization/
    └── linear_transform_3d.py           ← Transformation linéaire 3D
```

---

## Prérequis

- Python 3.10+
- numpy
- scipy
- matplotlib

Installation des dépendances :

```bash
pip install numpy scipy matplotlib
```

---

## Lancer le laboratoire

```bash
python main.py
```

Chaque module peut aussi être exécuté de manière indépendante :

```bash
python decompositions/matrix_decompositions.py
python regression/least_squares.py
python statistics/inferential_stats.py
python compression/svd_compression.py
python visualization/linear_transform_3d.py
```

---

## Contenu des modules

### 1. `decompositions/` — Décompositions matricielles

Trois décompositions classiques appliquées à une matrice aléatoire 4×4 :

- **SVD** (`U·Σ·Vᵀ`) — factorisation en valeurs singulières
- **QR** (`Q·R`) — factorisation orthogonale, vérification de l'orthogonalité de Q
- **Cholesky** (`L·Lᵀ`) — sur matrice symétrique définie positive `AᵀA + 4I`

L'erreur de reconstruction est vérifiée numériquement pour chaque décomposition (ordre `~1e-15`).

---

### 2. `regression/` — Moindres carrés

Résolution d'un système surdéterminé par pseudo-inverse (SVD interne de `numpy.linalg.lstsq`) :

- Génération d'un signal sinusoïdal bruité sur 40 points
- Construction d'une **matrice de design de Fourier** d'ordre 3
- Calcul du coefficient de détermination **R²**
- Visualisation du signal ajusté et des résidus

---

### 3. `statistics/` — Statistiques inférentielles

Trois tests statistiques avec p-value et verdict automatique (seuil α = 0.05) :

| Test | Hypothèse nulle H₀ | Statistique |
|------|-------------------|-------------|
| **Test t de Student** | μ_A = μ_B | t |
| **ANOVA à un facteur** | μ_1 = μ_2 = μ_3 | F |
| **Chi-deux** | Indépendance des variables | χ² |

---

### 4. `compression/` — Compression d'image par SVD

Compression d'une image synthétique 128×128 à différents rangs :

| Rang | Stockage | Erreur |
|------|----------|--------|
| 1    | ~1.6%    | 0.53   |
| 5    | ~7.8%    | ≈ 0    |
| 15   | ~23.5%   | ≈ 0    |
| 40   | ~62.7%   | ≈ 0    |

La courbe d'énergie cumulée des valeurs singulières montre qu'un rang faible suffit à capturer l'essentiel de l'information.

---

### 5. `visualization/` — Transformation linéaire 3D

Visualisation de l'effet d'une matrice 3×3 sur la sphère unité S² avec `mpl_toolkits` :

- Sphère originale vs ellipsoïde transformé
- Tracé des **vecteurs propres** (directions invariantes)
- Affichage du déterminant et du conditionnement de la matrice

---

## Résultats

Les figures sont sauvegardées dans `outputs/Jour 16/` :

| Fichier | Contenu |
|---------|---------|
| `decompositions.png` | Valeurs singulières, erreurs de reconstruction |
| `regression.png` | Signal ajusté + résidus |
| `statistics.png` | Distributions des groupes, table de contingence |
| `compression.png` | Approximations SVD à différents rangs |
| `linear_transform_3d.png` | Sphère unité vs ellipsoïde transformé |
| `day16_dashboard.png` | Dashboard récapitulatif |

---

## Concepts clés

- La **SVD** est au cœur de trois applications distinctes : décomposition, moindres carrés et compression
- Les **décompositions QR et Cholesky** ont des propriétés numériques spécifiques (stabilité, efficacité)
- Les **tests statistiques** reposent sur des distributions théoriques (t, F, χ²) pour calculer les p-values
- La **compression par SVD** exploite la décroissance rapide des valeurs singulières

---

*Challenge 30 jours — Jour 16/30*
