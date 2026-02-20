"""
JOUR 2 — Visualisation de données Multi-Graphiques
Jeu de données : Iris | Bibliothèques : matplotlib, seaborn, numpy, pandas
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import seaborn as sns

# ── 1. Chargement des données (Kaggle — uciml/iris) ──────────────────────────
df = pd.read_csv('Iris.csv')

# Nettoyer : supprimer la colonne Id, renommer les colonnes, simplifier les espèces
df.drop(columns='Id', inplace=True)
df.columns = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width', 'species']
df['species'] = df['species'].str.replace('Iris-', '', regex=False)  # "Iris-setosa" → "setosa"

# ── 2. Statistiques descriptives ─────────────────────────────────────────────
print("=" * 60)
print("         STATISTIQUES DESCRIPTIVES — IRIS")
print("=" * 60)
stats = df.groupby('species')[['sepal_length', 'sepal_width',
                                'petal_length', 'petal_width']].agg(
    ['mean', 'median', 'std',
     lambda x: x.quantile(0.25),
     lambda x: x.quantile(0.75)]
)
stats.columns = ['_'.join(c) if isinstance(c, tuple) else c for c in stats.columns]
print(stats.to_string())
print()

# Stats globales
print("─" * 60)
print("Statistiques globales (toutes espèces confondues) :")
for col in ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']:
    print(f"  {col:15s} | Moy={df[col].mean():.2f}  Méd={df[col].median():.2f}"
          f"  Éc.t={df[col].std():.2f}"
          f"  Q1={df[col].quantile(0.25):.2f}  Q3={df[col].quantile(0.75):.2f}")
print("=" * 60)

# ── 3. Palette & style ────────────────────────────────────────────────────────
PALETTE = {'setosa': '#E63946', 'versicolor': '#457B9D', 'virginica': '#2A9D8F'}
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': '#0F0F1A',
    'axes.facecolor': '#161625',
    'axes.labelcolor': '#E0E0E0',
    'xtick.color': '#A0A0B0',
    'ytick.color': '#A0A0B0',
    'text.color': '#E0E0E0',
    'grid.color': '#2A2A3E',
    'grid.linewidth': 0.5,
})

# ── 4. Tableau de bord statique (2 × 2) ──────────────────────────────────────
fig = plt.figure(figsize=(16, 12), constrained_layout=True)
fig.patch.set_facecolor('#0F0F1A')

fig.suptitle('🌸  Tableau de Bord Multi-Graphiques — Iris Dataset',
             fontsize=18, fontweight='bold', color='#F1FAEE', y=1.01)

gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

# ── 4a. Histogramme (sepal_length par espèce) ────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
for sp, color in PALETTE.items():
    ax1.hist(df[df['species'] == sp]['sepal_length'],
             bins=15, alpha=0.75, color=color, label=sp, edgecolor='none')
ax1.set_title('Histogramme — Longueur du Sépale', fontweight='bold', pad=10)
ax1.set_xlabel('Longueur du sépale (cm)')
ax1.set_ylabel('Fréquence')
ax1.legend(framealpha=0.15)
ax1.grid(True, axis='y')

# Annoter la moyenne globale
mean_sl = df['sepal_length'].mean()
ax1.axvline(mean_sl, color='#FFD166', linestyle='--', linewidth=1.5)
ax1.annotate(f'Moy. = {mean_sl:.2f}', xy=(mean_sl, ax1.get_ylim()[1] * 0.85),
             xytext=(mean_sl + 0.3, ax1.get_ylim()[1] * 0.85),
             color='#FFD166', fontsize=8,
             arrowprops=dict(arrowstyle='->', color='#FFD166', lw=1))

# ── 4b. Scatter plot avec régression ─────────────────────────────────────────
ax2 = fig.add_subplot(gs[0, 1])
for sp, color in PALETTE.items():
    sub = df[df['species'] == sp]
    ax2.scatter(sub['petal_length'], sub['petal_width'],
                color=color, alpha=0.8, s=50, label=sp, zorder=3)
    # Régression linéaire par espèce
    m, b = np.polyfit(sub['petal_length'], sub['petal_width'], 1)
    x_line = np.linspace(sub['petal_length'].min(), sub['petal_length'].max(), 50)
    ax2.plot(x_line, m * x_line + b, color=color, linewidth=1.5, linestyle='--', alpha=0.7)

ax2.set_title('Scatter + Régression — Pétale (L vs l)', fontweight='bold', pad=10)
ax2.set_xlabel('Longueur du pétale (cm)')
ax2.set_ylabel('Largeur du pétale (cm)')
ax2.legend(framealpha=0.15)
ax2.grid(True)

# ── 4c. Heatmap de corrélation ────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 0])
corr = df.drop(columns='species').corr()
mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
labels = ['Sép. L', 'Sép. l', 'Pét. L', 'Pét. l']
sns.heatmap(corr, ax=ax3, annot=True, fmt='.2f',
            cmap=sns.diverging_palette(240, 10, as_cmap=True),
            vmin=-1, vmax=1, linewidths=0.5, linecolor='#0F0F1A',
            xticklabels=labels, yticklabels=labels,
            cbar_kws={'shrink': 0.8, 'label': 'Corrélation'})
ax3.set_title('Heatmap de Corrélation', fontweight='bold', pad=10)

# Boxplot (distributions par variable)
ax4 = fig.add_subplot(gs[1, 1])
features = ['sepal_length', 'sepal_width', 'petal_length', 'petal_width']
feat_labels = ['Sép. L', 'Sép. l', 'Pét. L', 'Pét. l']
species_list = list(PALETTE.keys())
n_feat, n_sp = len(features), len(species_list)
width = 0.22
offsets = np.linspace(-(n_sp - 1) * width / 2, (n_sp - 1) * width / 2, n_sp)

for i, (sp, color) in enumerate(PALETTE.items()):
    positions = np.arange(n_feat) + offsets[i]
    data_to_plot = [df[df['species'] == sp][f].values for f in features]
    bp = ax4.boxplot(data_to_plot, positions=positions, widths=width * 0.85,
                     patch_artist=True, notch=False,
                     boxprops=dict(facecolor=color, alpha=0.7),
                     medianprops=dict(color='white', linewidth=2),
                     whiskerprops=dict(color=color, linewidth=1.2),
                     capprops=dict(color=color, linewidth=1.5),
                     flierprops=dict(marker='o', markerfacecolor=color,
                                     markersize=3, alpha=0.5, linestyle='none'))
ax4.set_xticks(np.arange(n_feat))
ax4.set_xticklabels(feat_labels)
ax4.set_title('Boxplot — Distributions par Espèce', fontweight='bold', pad=10)
ax4.set_ylabel('Valeur (cm)')
ax4.grid(True, axis='y')
patches = [mpatches.Patch(color=c, label=s) for s, c in PALETTE.items()]
ax4.legend(handles=patches, framealpha=0.15)

plt.savefig('/mnt/user-data/outputs/jour2_dashboard.png',
            dpi=150, bbox_inches='tight', facecolor='#0F0F1A')
print("Dashboard statique sauvegardé : Jour2 Dashboard.png")

# Animation : courbe animée (petal_length moyen par espèce)
fig_anim, ax_anim = plt.subplots(figsize=(9, 5))
fig_anim.patch.set_facecolor('#0F0F1A')
ax_anim.set_facecolor('#161625')
ax_anim.set_title('Animation — Évolution cumulée de la Longueur du Pétale',
                  color='#F1FAEE', fontweight='bold', pad=10)
ax_anim.set_xlabel('Index échantillon', color='#A0A0B0')
ax_anim.set_ylabel('Longueur du pétale (cm)', color='#A0A0B0')
ax_anim.tick_params(colors='#A0A0B0')
for sp in ['top', 'right']:
    ax_anim.spines[sp].set_visible(False)
ax_anim.spines['left'].set_color('#2A2A3E')
ax_anim.spines['bottom'].set_color('#2A2A3E')
ax_anim.grid(True, color='#2A2A3E', linewidth=0.5)

lines = {}
data_by_sp = {}
for sp, color in PALETTE.items():
    sub = df[df['species'] == sp].reset_index(drop=True)
    data_by_sp[sp] = sub['petal_length'].values
    lines[sp], = ax_anim.plot([], [], color=color, linewidth=2, label=sp)

ax_anim.set_xlim(0, 50)
ax_anim.set_ylim(df['petal_length'].min() - 0.3, df['petal_length'].max() + 0.3)
ax_anim.legend(framealpha=0.15, labelcolor='#E0E0E0')
frame_text = ax_anim.text(0.98, 0.97, '', transform=ax_anim.transAxes,
                           ha='right', va='top', color='#FFD166', fontsize=9)

def animate(frame):
    n = frame + 1
    for sp, line in lines.items():
        d = data_by_sp[sp]
        x = np.arange(min(n, len(d)))
        line.set_data(x, d[:min(n, len(d))])
    frame_text.set_text(f'Frame {n}/50')
    return list(lines.values()) + [frame_text]

ani = FuncAnimation(fig_anim, animate, frames=50, interval=80, blit=True)
ani.save('/mnt/user-data/outputs/jour2_animation.gif',
         writer='pillow', dpi=100, fps=15)
print("Animation sauvegardée : Jour2 Animation.gif")

plt.show()
print("\nJour 2 terminé avec succès !")
