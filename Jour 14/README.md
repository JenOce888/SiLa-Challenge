# Bot de Scraping Web — Selenium + BeautifulSoup

Bot de scraping robuste avec contournement anti-bot, gestion des cookies, interaction AJAX, stockage SQLite et planification automatique.

---

##  Structure du projet

```
selenium_bot/
├── main.py        # Point d'entrée
├── config.py      # Paramètres globaux
├── driver.py      # Navigateur & anti-bot
├── browser.py     # Interaction AJAX / formulaires
├── extractor.py   # Parsing HTML (BeautifulSoup)
├── storage.py     # Persistance SQLite
├── scraper.py     # Tâche de scraping principale
├── scheduler.py   # Planification (APScheduler)
```

---


##  Fonctionnalités anti-bot

| Technique | Fichier |
|---|---|
| User-Agent rotatif | `driver.py` |
| Suppression de `navigator.webdriver` | `driver.py` |
| Délais aléatoires entre actions | `utils.py` |
| Réutilisation des cookies de session | `driver.py` |

---

##  Données collectées

Les données sont stockées dans `scraped_data.db` (SQLite), table `books` :

| Colonne | Description |
|---|---|
| `title` | Titre du livre |
| `price` | Prix |
| `rating` | Note (One → Five) |
| `available` | Disponibilité |
| `scraped_at` | Horodatage ISO 8601 |

---

##  Dépendances

```
selenium>=4.20.0
beautifulsoup4>=4.12.0
pandas>=2.2.0
apscheduler>=3.10.0
lxml>=5.2.0
```

---

##  Configuration

Modifier `config.py` pour changer la cible, la fréquence ou le nombre de pages :

```python
TARGET_URL = "https://votre-site-cible.com/"
MAX_PAGES  = 5
SCHEDULE_INTERVAL_MINUTES = 60
```
