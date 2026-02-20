# Jour 2 — Visualisation de données Multi-Graphiques

## Description

Tableau de bord interactif et multi-graphiques basé sur le célèbre **dataset Iris**.  
Ce projet fait partie d'un défi de 30 jours en Data Science / Python.

L'objectif est de charger un jeu de données réel, calculer des statistiques descriptives,  
et produire plusieurs visualisations professionnelles avec **matplotlib** et **seaborn**.

---

## Structure du projet

```
jour2/
│
├── Iris.csv                     # Jeu de données téléchargé depuis Kaggle
├── jour2_iris_dashboard.py      # Script principal
├── jour2_dashboard.png          # Dashboard statique exporté (2x2 graphiques)
├── jour2_animation.gif          # Animation exportée
└── README.md                    # Ce fichier
```

## Bibliothèques utilisées

| Bibliothèque | Rôle |
|---|---|
| `pandas` | Chargement et manipulation des données (tableau) |
| `numpy` | Calculs mathématiques (régression, arrays) |
| `matplotlib` | Moteur principal de visualisation |
| `seaborn` | Visualisations avancées et esthétiques |

Installation :
```bash
pip install pandas numpy matplotlib seaborn
```

## Dataset — Iris (Kaggle)

- **Source :** [kaggle.com/datasets/uciml/iris](https://www.kaggle.com/datasets/uciml/iris)
- **Taille :** 150 lignes × 5 colonnes
- **Variables :**
  - `SepalLengthCm` — Longueur du sépale (cm)
  - `SepalWidthCm` — Largeur du sépale (cm)
  - `PetalLengthCm` — Longueur du pétale (cm)
  - `PetalWidthCm` — Largeur du pétale (cm)
  - `Species` — Espèce de la fleur (setosa, versicolor, virginica)

**Téléchargement via l'API Kaggle :**
```bash
kaggle datasets download -d uciml/iris -p ./data --unzip
```

