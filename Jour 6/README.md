# Jeu de plateforme 2D

Un jeu de plateforme 2D simple créé avec Python et Pygame, doté d'un moteur physique personnalisé, d'une IA ennemie, d'un système de particules et d'un classement permanent.

## Commandes

| Touche | Action |
| Gauche / Droite | Se déplacer |
| Espace | Sauter |
| Ctrl gauche | Tirer |
| R | Redémarrer (à la fin du jeu / victoire) |
| Échap | Quitter |

## Objectif

Ramassez toutes les pièces pour gagner. Évitez ou éliminez les ennemis en chemin.

## Score

| Action | Points |
| Ramasser une pièce | +50 |
| Écraser un ennemi | +150 |
| Tirer sur un ennemi | +200 |

Votre meilleur score est automatiquement enregistré dans le fichier `highscore.txt`.

## Astuces

- Vous pouvez **écraser** un ennemi en sautant et en atterrissant dessus.
- Vous disposez de **3 vies**. Toucher un ennemi sur le côté ou tomber hors de la carte vous coûte une vie.
- Le **meilleur score est conservé** d'une session à l'autre.