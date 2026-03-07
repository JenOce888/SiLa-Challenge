# Moteur de Recherche — Jour 13

Moteur de recherche full-text en ligne de commande. Index inversé, regex avancées, recherche par phrase, ranking TF-IDF, persistance pickle.

---

## Utilisation

### 1. Indexer un répertoire

```bash
python search_engine.py index ./mes_docs --save index.pkl
```

Parcourt récursivement tous les fichiers `.txt` et construit l'index inversé.

###  Rechercher

```bash
# Recherche regex
python search_engine.py search "python" --load index.pkl

# Recherche par phrase exacte (guillemets)
python search_engine.py search '"data science"' --load index.pkl

# Forcer le mode phrase sans guillemets
python search_engine.py search "machine learning" --phrase --load index.pkl

# Limiter les résultats
python search_engine.py search "import" --top 5 --load index.pkl
```

###  Mode interactif (REPL)

```bash
python search_engine.py search --load index.pkl
```

| Commande | Effet |
|---|---|
| `"phrase exacte"` | Recherche positionnelle |
| `(?P<nom>\w+)` | Groupe nommé regex |
| `(?<=def )\w+` | Lookbehind |
| `import (?=os\|re)` | Lookahead |
| `:stats` | Statistiques de l'index |
| `:help` | Aide complète |
| `:quit` | Quitter |

---

## Architecture

```
Posting          — (doc_id, positions[])
InvertedIndex    — token → Posting[], find_phrase() pour la recherche positionnelle
Indexer          — parcours récursif os.walk, tokenisation re.split
TFIDFRanker      — score TF-IDF lissé pour le classement
SearchEngine     — orchestration, pickle save/load, highlighting, CLI
```

---

## Fonctionnalités

- **Index inversé** avec positions des tokens (dict mot → fichiers + positions)
- **Regex PCRE avancées** — lookahead, lookbehind, groupes nommés
- **Recherche par phrase** — intersection positionnelle, aucune lecture disque
- **Highlighting** — correspondances surlignées dans les extraits
- **Ranking TF-IDF** — classement par pertinence
- **Persistance** — sérialisation/désérialisation via `pickle`

---

> *"Je l'ai entendu, je l'ai oublier. Je l'ai vu, je l'ai compris. Je l'ai fait, je l'ai appris."*