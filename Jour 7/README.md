# Convertisseur de Devises avec Cache — JOUR 7

Un convertisseur de devises en ligne de commande robuste, développé en Python, avec cache SQLite, retry exponentiel, historique et graphe ASCII.

---

## Fonctionnalités

| Fonctionnalité | Détail |
|---|---|
| Taux en temps réel | Récupérés depuis `exchangerate.host` |
| Cache SQLite | TTL de 10 minutes — évite les appels inutiles |
| Retry exponentiel | Jusqu'à 5 tentatives avec délai `2ⁿ` secondes |
| Historique | 30 jours de conversions enregistrées |
| Graphe ASCII | Évolution du taux pour une paire de devises |
| CLI interactive | Menu numéroté simple et intuitif |

---

## Prérequis

- Python 3.7+
- Bibliothèques : `requests`, `sqlite3` (inclus dans Python), `json` (inclus)

## 🖥️ Interface CLI

```
╔══════════════════════════════════════════════╗
║      Convertisseur de Devises  - JOUR 7      ║
║       Cache SQLite | Retry Exponentiel       ║
╚══════════════════════════════════════════════╝

  [1] Convertir une devise
  [2] Voir l'historique des conversions
  [3] Graphe d'évolution d'une paire
  [4] Vider le cache des taux
  [5] Quitter
```

### Exemple de conversion

```
  Devise source (ex: XAF) : FCFA
  Devise cible  (ex: EUR) : EUR
  Montant : 655.54

    655.54 FCFA = 01 EUR
      (Taux : 1 XAF = 0. EUR)
```

### Exemple de graphe ASCII

```
  📈 Évolution du taux USD/EUR (30 derniers jours)

  0.9300 |      █ 
  0.9250 |    █ █   █
  0.9200 |    █ █ █ █ █
  0.9150 |█ █ █ █ █ █ █ █
         +────────────────
           01/02  10/02  20/02
```

---

## Structure de la base de données

### Table `rates` — Cache des taux

| Colonne | Type | Description |
|---|---|---|
| `base` | TEXT | Devise source (ex: USD) |
| `currency` | TEXT | Devise cible (ex: EUR) |
| `rate` | REAL | Taux de change |
| `fetched_at` | INTEGER | Timestamp Unix de récupération |

### Table `history` — Historique des conversions

| Colonne | Type | Description |
|---|---|---|
| `id` | INTEGER | Identifiant auto-incrémenté |
| `from_cur` | TEXT | Devise source |
| `to_cur` | TEXT | Devise cible |
| `amount` | REAL | Montant converti |
| `result` | REAL | Résultat de la conversion |
| `rate` | REAL | Taux utilisé |
| `converted_at` | INTEGER | Timestamp Unix de la conversion |

---

## ⚙️ Configuration

En haut du fichier `currency_converter.py` :

```python
DB_PATH      = "currency_cache.db"   # Chemin vers la base SQLite
API_URL      = "https://api.exchangerate.host/live"
API_KEY      = ""                    # Clé API si nécessaire
TTL_SECONDS  = 600                   # Durée du cache (10 min)
MAX_RETRIES  = 5                     # Nombre max de tentatives
HISTORY_DAYS = 30                    # Profondeur de l'historique
```

> **Alternative API gratuite sans clé :**
> Remplacer `API_URL` par `https://open.er-api.com/v6/latest/` et adapter le parsing.

---

## Fonctionnement du Cache

```
Requête de taux
     │
     ▼
Cache SQLite valide ? ──── OUI ──▶ Retourner le taux
     │
    NON
     │
     ▼
Appel API (avec retry)
     │
     ▼
Sauvegarder en cache
     │
     ▼
Retourner le taux
```

---

## Retry Exponentiel

En cas d'échec de l'API, le système retente automatiquement avec un délai croissant :

| Tentative | Délai d'attente |
|---|---|
| 1 | 2 secondes |
| 2 | 4 secondes |
| 3 | 8 secondes |
| 4 | 16 secondes |
| 5 | 32 secondes |

## Technologies utilisées

- **Python 3** — Langage principal
- **requests** — Appels HTTP vers l'API
- **sqlite3** — Cache local et historique
- **json** — Parsing des réponses API

