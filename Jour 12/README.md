# Jour 12 — Analyse de Sentiment NLP Avancée

Système bi-niveau qui classifie des avis de livres en **positif** ou **négatif**.

---

## Stack

| Outil | Rôle |
|---|---|
| `VADER` | Analyse basée sur des règles, sans entraînement |
| `TF-IDF + Naive Bayes` | ML classique supervisé |
| `DistilBERT` | Transformer pré-entraîné (HuggingFace) |
| `Flask` | API REST pour tester en temps réel |

---

### Tester l'API

```bash
# Comparer les 3 modèles
curl -X POST http://localhost:5000/compare \
     -H "Content-Type: application/json" \
     -d '{"text": "Ce livre était absolument incroyable!"}'

# Utiliser un modèle spécifique
curl -X POST http://localhost:5000/predict \
     -H "Content-Type: application/json" \
     -d '{"text": "Je n'\''ai pas aimé ce livre.", "model": "bert"}'
```

---

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/health` | Vérifier que l'API tourne |
| `POST` | `/predict` | Prédire avec un modèle (`vader`, `naive_bayes`, `bert`) |
| `POST` | `/compare` | Comparer les 3 modèles sur le même texte |

---

## Dataset

**Amazon Book Reviews** — 50 000 avis labellisés (positif / négatif)  
Chargé via la bibliothèque `datasets` de HuggingFace.

---

