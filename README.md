# Blue Prince – Projet POO

Ce projet est une implémentation simplifiée du jeu *Blue Prince* dans le cadre de l’UE  
**Programmation Orientée Objet (POO)** – Master Systèmes Intelligents, Sorbonne Université.

Le jeu est développé en **Python** avec **Pygame** et repose sur une architecture orientée objet
modulaire : salles, effets, inventaire, génération dynamique du manoir, HUD, tirage des pièces…

---

## 1. Installation
### les bibliothèques
- Python 
- Pygame installé

### Installer les dépendances
Ouvrir un terminal dans le dossier du projet :

```bash
pip install -r requirements.txt
```

## 2. Lancer le jeu

Le jeu se lance via le fichier **main.py** :

```bash
python main.py
```
Une fenêtre Pygame s’ouvre avec le manoir à gauche et le HUD à droite.

## 3. Contrôles du jeu

### Déplacements
- **Z / ↑** : haut  
- **S / ↓** : bas  
- **Q / ←** : gauche  
- **D / →** : droite  

### Ouverture des portes
- **ESPACE** pour interagir  
- **O** = Ouvrir  
- **A** = Annuler  

### Tirage des salles
- **← / →** pour naviguer  
- **ESPACE** pour valider  
- **R** pour relancer (si dés)

### Ramasser des objets
- **E** pour ouvrirr/fermer (menu)
- **↑ / ↓**  
- **ESPACE** pour prendre

### Magasin (room jaunes)
- **M** pour ouvrir/fermer  (menu)
- **↑ / ↓** pour naviguer  
- **ESPACE** pour acheter

### Fin de partie
- **R** pour recommencer  
- **ESC** pour quitter  



## 4. Architecture du projet
```
 projet/
│
├── main.py              
├── game.py              
├── world.py             
├── entities.py          
├── interface.py          
│
└── assets/               Icônes + images des salles
```
---

## 5. Travail d’équipe
Le développement a été réalisé de manière collaborative via **Git/GitHub** :  
- commits et push réguliers  
- résolution propre des conflits  
- revue du code avant fusion  

---

