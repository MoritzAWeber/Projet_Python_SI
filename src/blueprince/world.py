import pygame
import random
from abc import ABC, abstractmethod

from entities import (
    Coffre, Casier, EndroitCreuser, Pomme, Banane, Gateau,
    Or, Gemmes, Cles, Des, Pelle, Marteau
)

# ==============================
# 1. Classe abstraite Room
# ==============================
class Room(ABC):
    def __init__(self, name, image=None, doors=None, gem_cost=0,
                 objets=None, rarity=0, placement_condition=None):
        self.name = name
        self.image = image
        self.doors = doors if doors else []
        self.gem_cost = gem_cost
        self.objets = objets if objets else []
        self.rarity = rarity
        self.placement_condition = placement_condition

    def has_door(self, direction):
        return direction in self.doors

    def add_object(self, objet):
        self.objets.append(objet)

    def remove_object(self, objet):
        if objet in self.objets:
            self.objets.remove(objet)

    def apply_effect_on_choose(self, player):
        """Effet au moment où la pièce est choisie."""
        pass

    def apply_effect_on_enter(self, player):
        """Effet au moment où la pièce est visitée."""
        pass


# ==============================
# 2. Sous-classes concrètes
# ==============================
class EntranceHall(Room):
    def __init__(self):
        super().__init__(
            name="EntranceHall",
            image=pygame.image.load("assets/rooms/Entrance_Hall.png"),
            doors=["up", "down", "left", "right"],
            objets=[Pomme()],
            rarity=0
        )

class Vault(Room):
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/rooms/Vault.png"),
            doors=["down"],
            gem_cost=3,
            objets=[Or()],
            rarity=3
        )

class Pantry(Room):
    def __init__(self):
        super().__init__(
            name="Pantry",
            image=pygame.image.load("assets/rooms/Pantry.png"),
            doors=["up", "right"],
            objets=[Banane(), Pomme()],
            rarity=0
        )

class ConferenceRoom(Room):
    def __init__(self):
        super().__init__(
            name="Conference Room",
            image=pygame.image.load("assets/rooms/Conference_Room.png"),
            doors=["up", "down", "left", "right"],
            rarity=0
        )

class Chapel(Room):
    def __init__(self):
        super().__init__(
            name="Chapel",
            image=pygame.image.load("assets/rooms/Chapel.png"),
            doors=["up", "down"],
            gem_cost=1,
            objets=[Gemmes()],
            rarity=2
        )

    def apply_effect_on_enter(self, player):
        print(f"Effet '{self.name}': +10 pas !")
        player.gagner_pas(10)

class Antechamber(Room):
    def __init__(self):
        super().__init__(
            name="Antechamber",
            image=pygame.image.load("assets/rooms/Antechamber.png"),
            doors=["down"],
            placement_condition="haut_du_manoir"
        )


# ==============================
# 3. Catalogue global
# ==============================
ROOM_CATALOG = [
    EntranceHall(),
    Vault(),
    Pantry(),
    ConferenceRoom(),
    Chapel(),
    Antechamber(),
]


# ==============================
# 4. Classe Manor
# ==============================
class Manor:
    WIDTH = 5
    HEIGHT = 9

    def __init__(self):
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

        # --- Catalogue tirable : on exclut EntranceHall et Antechamber ---
        self.room_catalog = [
            room for room in ROOM_CATALOG
            if room.name not in ("EntranceHall", "Antechamber")
        ]

        # --- Pioche de jeu ---
        self.pioche = list(self.room_catalog)

        # --- Placement du Hall d'entrée ---
        start_room = EntranceHall()
        self.place_room(2, 8, start_room)
        print(f"Pièce de départ '{start_room.name}' placée en (2, 8).")

        # --- Placement fixe de l’Antechamber ---
        end_room = Antechamber()
        self.place_room(2, 0, end_room)
        print("Pièce de fin 'Antechamber' placée en (2, 0).")

    # ==============================
    # Méthodes utilitaires
    # ==============================
    def in_bounds(self, x, y):
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        if not self.in_bounds(x, y):
            raise ValueError("Position hors limites.")
        self.grid[y][x] = room

    def draw_three_rooms(self):
        """Tire 3 pièces au hasard (au moins une gratuite si possible)."""
        if not self.pioche:
            print("La pioche est vide !")
            return []

        free_rooms = [room for room in self.pioche if room.gem_cost == 0]
        choices = []

        # Toujours une pièce gratuite
        if free_rooms:
            choices.append(random.choice(free_rooms))
        else:
            choices.append(random.choice(self.pioche))

        remaining = [r for r in self.pioche if r not in choices]
        num_to_draw = min(2, len(remaining))
        if num_to_draw > 0:
            choices.extend(random.sample(remaining, num_to_draw))

        random.shuffle(choices)

        print("Tirage de pièces :")
        for i, room in enumerate(choices):
            print(f"  {i+1}: {room.name} (Coût: {room.gem_cost} gemmes)")
        return choices
