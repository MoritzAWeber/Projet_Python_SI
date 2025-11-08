# Fichier: src/blueprince/world.py
# VERSION DE TEST (5 pièces + Héritage + Images)

import pygame  # <--- AJOUTÉ (pour charger les images)
import random  # <--- AJOUTÉ (pour la pioche)
from abc import ABC, abstractmethod  # <--- AJOUTÉ (pour l'héritage)

# --- 1. LES IMPORTS D'ENTITÉS ---
from .entities import (
    Coffre, Casier, EndroitCreuser, Pomme, Banane, Gateau,
    Or, Gemmes, Cles, Des, Pelle, Marteau 
)

# --- 2. LA CLASSE PARENTE "Room" (Abstraite) ---
# (C'est la classe "Room" de votre code, mais rendue abstraite)
class Room(ABC):
    def __init__(self, name, image=None, doors=None, gem_cost=0,
                 objets=None, rarity=0, placement_condition=None):
        
        self.name = name
        self.image = image # L'image sera chargée par les classes enfants
        self.doors = doors if doors is not None else []
        self.gem_cost = gem_cost
        self.objets = objets if objets is not None else []
        self.rarity = rarity
        self.placement_condition = placement_condition

    def has_door(self, direction):
        return direction in self.doors

    def add_object(self, objet):
        self.objets.append(objet)

    def remove_object(self, objet):
        if objet in self.objets:
            self.objets.remove(objet)

    # --- Méthodes pour les effets (POO) ---
    def apply_effect_on_choose(self, player):
        """Applique un effet au moment où le joueur CHOISIT la pièce."""
        pass # La plupart des pièces ne font rien

    def apply_effect_on_enter(self, player):
        """Applique un effet au moment où le joueur ENTRE dans la pièce."""
        pass # La plupart des pièces ne font rien

# --- 3. LES 5 SOUS-CLASSES DE TEST (Héritage) ---
# (C'est votre code, tout est correct !)

# Pièce 1: Le début (Gratuite)
class EntranceHall(Room):
    def __init__(self):
        super().__init__(
            name="EntranceHall",
            image=pygame.image.load("assets/Entrance_Hall.png"), # CHARGEMENT IMAGE
            doors=["up", "down", "left", "right"],
            objets=[Pomme()],
            rarity=0
        )

# Pièce 2: Une pièce payante (Coût 3)
class Vault(Room):
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/Vault.png"), # CHARGEMENT IMAGE
            doors=["down"], # Cul-de-sac
            gem_cost=3,
            objets=[Or()],
            rarity=3
        )

# Pièce 3: Une autre pièce gratuite
class Pantry(Room):
    def __init__(self):
        super().__init__(
            name="Pantry",
            image=pygame.image.load("assets/Pantry.png"), # CHARGEMENT IMAGE
            doors=["up", "right"],
            objets=[Banane(), Pomme()],
            rarity=0
        )

# Pièce 4: Une pièce "carrefour" (Gratuite)
class ConferenceRoom(Room):
    def __init__(self):
        super().__init__(
            name="Conference Room",
            image=pygame.image.load("assets/Conference_Room.png"), # CHARGEMENT IMAGE
            doors=["up", "down", "left", "right"],
            rarity=0
        )
        
# Pièce 5: Une pièce à effet (Payante)
class Chapel(Room):
    def __init__(self):
        super().__init__(
            name="Chapel",
            image=pygame.image.load("assets/Chapel.png"), # CHARGEMENT IMAGE
            doors=["up", "down"],
            gem_cost=1,
            objets=[Gemmes()],
            rarity=2
        )
    
    # Redéfinition (override) de la méthode parente
    def apply_effect_on_enter(self, player):
        print(f"Effet '{self.name}': +10 pas !")
        player.gagner_pas(10)

# Pièce 6: La Fin (pour tester la victoire)
class Antechamber(Room):
    def __init__(self):
        super().__init__(
            name="Antechamber",
            # Laissez l'image à None si vous ne l'avez pas encore
            image=pygame.image.load("assets/Antechamber.png"), # CHARGEMENT IMAGE
            doors=["down"],
            placement_condition="haut_du_manoir"
        )

# --- 4. LE CATALOGUE DE TEST (6 pièces) ---
ROOM_CATALOG = [
    EntranceHall(),
    Vault(),
    Pantry(),
    ConferenceRoom(),
    Chapel(),
    Antechamber(), # On inclut la fin
]


# --- 5. LA CLASSE MANOR (MAINTENANT DÉFINIE *APRÈS* LE CATALOGUE) ---
# (C'est votre classe Manor, légèrement modifiée pour le test)
class Manor:
    WIDTH = 5
    HEIGHT = 9

    def __init__(self):
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        
        # 1. On copie le catalogue de 6 pièces
        self.pioche = list(ROOM_CATALOG)
        
        # 2. On cherche et place "Entrance Hall"
        start_room = None
        for room in self.pioche:
            if room.name == "EntranceHall":
                start_room = room
                break 
        
        if start_room:
            start_x, start_y = 2, 8 
            self.place_room(start_x, start_y, start_room)
            self.pioche.remove(start_room) # On retire le Hall de la pioche
            print(f"Pièce de départ '{start_room.name}' placée en ({start_x}, {start_y}).")
        else:
            print("ERREUR: 'EntranceHall' non trouvé !")

        # 3. ON RETIRE ET PLACE "Antechamber" de la pioche
        antechamber = None
        for room in self.pioche:
            if room.name == "Antechamber":
                antechamber = room
                break
        if antechamber:
            self.pioche.remove(antechamber)
            self.place_room(2, 0, antechamber) # On la place en haut au milieu
            print("Pièce de fin 'Antechamber' placée en (2, 0).")
        else:
            print("ERREUR: 'Antechamber' non trouvée !")

    def in_bounds(self, x, y):
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        if not self.in_bounds(x, y):
            raise ValueError("Position out of bounds.")
        self.grid[y][x] = room
        
    def draw_three_rooms(self):
        """
        Tire 3 pièces au sort (ou moins si la pioche est petite)
        """
        if not self.pioche:
            print("La pioche est vide !")
            return []

        # 1. Séparer les pièces
        free_rooms = [room for room in self.pioche if room.gem_cost == 0]
        
        choices = []
        
        # [cite_start]2. Assurer une pièce gratuite (Règle du PDF [cite: 378])
        if free_rooms:
            choices.append(random.choice(free_rooms))
        else:
            # S'il n'y a plus de pièces gratuites, on prend ce qui reste
            if not self.pioche: return []
            print("Avertissement: Plus de pièces gratuites.")
            choices.append(random.choice(self.pioche))

        # 3. Choisir les autres
        remaining_pioche = [room for room in self.pioche if room not in choices]
        
        # On prend 2 autres pièces si possible
        num_to_draw = min(2, len(remaining_pioche))
        if num_to_draw > 0:
            choices.extend(random.sample(remaining_pioche, num_to_draw))
        
        random.shuffle(choices)
        
        print("Tirage de pièces :")
        for i, room in enumerate(choices):
            print(f"  {i+1}: {room.name} (Coût: {room.gem_cost} gemmes)")
            
        return choices