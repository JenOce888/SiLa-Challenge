## Description
Un pipeline ETL (Extract-Transform-Load) complet développé en Python qui traite et visualise les données provenant de 4 ensembles de données différents.

## Ensembles de données utilisés
| Ensemble de données | Source | Description |
|--------|--------|-------------|
| Titanic | Kaggle | Données sur la survie des passagers |
| Iris | Kaggle | Mesures des fleurs d'iris |
| Amazon Bestsellers | Kaggle | Top 50 des livres les plus vendus entre 2009 et 2019 |
| Données météorologiques | Kaggle | Données météorologiques entre 2018 et 2022 |

## Bibliothèques utilisées
- `pandas` — chargement, nettoyage et manipulation des données
- `matplotlib` — visualisation des données
- `seaborn` — visualisation stylisée des données
- `numpy` — opérations numériques

## Étapes du pipeline

### Extraire
- Charger 4 fichiers CSV à l'aide de `pd.read_csv()`
- Attribuer des noms de colonnes lorsqu'ils sont manquants (ensemble de données Iris)

### Transformer
- Ajouter une colonne `source` à chaque ensemble de données
- Fusionner tous les ensembles de données en un seul à l'aide de `pd.concat()`
- Nettoyer les valeurs manquantes à l'aide de la méthode **médiane**
- Détecter les valeurs aberrantes à l'aide de la méthode **IQR**
- Créer des caractéristiques dérivées : `mean_numeric`, `median_numeric`, `std_numeric`

### Charger
- Exporter l'ensemble de données final nettoyé vers `final_output.csv`

### Visualiser
| Graphique | Ensemble de données | Type |
|-------|---------|------|
| Survie par sexe | Titanic | Graphique à barres |
| Longueur des pétales par espèce | Iris | Boîte à moustaches |
| Top 10 des auteurs | Amazon | Graphique à barres horizontales |
| Température au fil du temps | Météo | Graphique linéaire |

## Fichiers de sortie
- `final_output.csv` — ensemble de données nettoyé et fusionné (1 085 858 lignes, 37 colonnes)
- `titanic_survival.png` — Visualisation Titanic
- `iris_
