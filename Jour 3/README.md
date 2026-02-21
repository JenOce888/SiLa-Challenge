# Calculatrice Scientifique Tkinter 

## Description

Une calculatrice scientifique complète avec interface graphique Tkinter, supportant les opérations de base, les fonctions trigonométriques et logarithmiques, un historique scrollable, et un système de thèmes clair/sombre.

## Fonctionnalités

- **Opérations de base** : addition, soustraction, multiplication, division
- **Fonctions scientifiques** : `sin`, `cos`, `tan` (en degrés), `log`, `ln`, `√`, `x²`, `x³`
- **Constantes** : `π` et `e`
- **Parenthèses imbriquées** avec fermeture automatique
- **Historique scrollable** des 50 derniers calculs
- **Thème clair / sombre** avec bouton bascule
- **Gestion des erreurs** : division par zéro, expression invalide
- **Saisie clavier** : chiffres, opérateurs, `Entrée`, `Backspace`
- **Évaluation sécurisée** via `ast.parse()` (pas de `eval()` dangereux)

## Structure du code


Calculator (classe principale)
│
├── safe_eval()       → Évaluation sécurisée via ast (pas d'eval())
├── __init__()        → Initialisation des variables + lancement UI
├── _build_ui()       → Construction de tous les widgets Tkinter
├── _make_button()    → Création d'un bouton stylisé avec hover
├── _on_click()       → Gestion des clics boutons (logique principale)
├── _calculate()      → Calcul et gestion des erreurs
├── _update_history() → Mise à jour de l'historique
├── _on_key()         → Binding clavier
└── _toggle_theme()   → Bascule clair / sombre

## Sécurité

L'évaluation des expressions utilise `ast.parse()` au lieu de `eval()`, ce qui garantit que seules les opérations mathématiques autorisées sont exécutées. Aucun code arbitraire ne peut être injecté.
