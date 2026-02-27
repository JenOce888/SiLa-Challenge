# Gestionnaire de tâches avancé — PyQt6

## Structure du projet (MVC)

```
├── Gestionnaire_Tâche_Avancé_PyQt.py            # CONTRÔLEUR — achemine les actions de l'utilisateur vers le modèle/la vue
├── Modeles.py          # MODÈLE — toute la logique métier, la validation, les statistiques
├── Database.py        # COUCHE DE DONNÉES — requêtes SQLite et migrations de schéma
├── Carte_Tache.py       # VUE — carte de tâche unique déplaçable
├── Dialog_Tache.py     # VUE — formulaire d'ajout/modification de tâche
├── Dashboard.py       # VUE — tableau de bord de statistiques avec graphiques
├── Export_Manager.py  # UTILITAIRE — export CSV et PDF
├── Logger.py          # UTILITAIRE — journalisation centralisée
└── tasks.db           # Base de données SQLite créée automatiquement
```

---

## Architecture : modèle MVC

| Couche       | Fichier(s)                          | Responsabilité                              |
|-------------|----------------------------------|---------------------------------------------|
| Modèle       | `Modèles.py` + `Database.py`      | Logique métier, validation, accès à la base de données       |
| Vue        | `Carte_Tache.py`, `Dialogue_Tach.py`, `Dashboard.py` | Rend les données, émet des signaux  |
| Contrôleur  | `Gestionnaire_Tâche_Avancé_PyQt.py`  Gestionnaire_Tâche_Avancé_PyQt                      | Relie le modèle à la vue, gère les événements utilisateur     |

**Flux :** L'utilisateur clique → Contrôleur → Le modèle valide + lit/écrit → Contrôleur → La vue affiche

---

## Fonctionnalités

| Fonctionnalité                  | Description                                                   |
|--------------------------|--------------------------------------
|--------------------------|---------------------------------------------------------------|
| 📑 Tableau Kanban           | 3 colonnes : À faire / En cours / Terminé                         |
|  Glisser-déposer           | Déplacer les cartes entre les colonnes en les faisant glisser                        |
| 🎟 Balises et priorités     | Filtres dynamiques par balise et niveau de priorité                     |
| 🔍 Recherche en direct            | Recherche en temps réel sur le titre et la description                     |
| 🔴🟢 Code couleur pour les dates d'échéance | En retard → rouge, Échéance aujourd'hui → vert, À venir → gris            |
|  Tableau de bord des statistiques   | Diagramme circulaire (par statut) + diagramme à barres (par priorité) + cartes KPI  |
|  SQLite + Migrations    | Stockage persistant avec migrations de schéma versionnées           |
|  Barre d'état système            | Notifications sur le bureau + réduction dans la barre d'état système à la fermeture            |
| Exportation CSV / PDF       | Exportation complète de toutes les tâches                                      |
|  Journalisation               | Fichier journal rotatif (`task_manager.log`) + avertissements de la console    |

---

## Journalisation

Toutes les actions sont consignées dans le fichier `task_manager.log` (créé automatiquement, rotatif à 1 Mo) :

```
[2025-03-01 10:22:01] INFO     taskmanager.models       — Tâche créée : titre=“Correction du bug de connexion”, priorité=Élevée, statut=à faire.
[2025-03-01 10:22:05] INFO     taskmanager.main         — L'utilisateur a ouvert le tableau de bord.
[2025-03-01 10:22:10] WARNING  taskmanager.task_card    — (aucun — seuls les avertissements s'affichent dans la console)
```

Pour voir tous les journaux dans la console, modifiez `console_handler.setLevel` dans `Logger.py`.

`console_handler.setLevel` dans `logger.py` à `logging.DEBUG`.

---

## Codage couleur des dates d'échéance

| Statut   | Couleur  | Condition                              |
|----------|--------|--------------------------- -------------|
| 🔴 Rouge   | `#f38ba8` | Échéance dépassée et tâche non effectuée       |
| 🟢 Vert | `#a6e3a1` | La date d'échéance est aujourd'hui                   |
| CadetBlue     | `#5f9ea0` | Date future                         |



