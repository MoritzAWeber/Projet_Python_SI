# Fichier: src/blueprince/world.py
# VERSION DE TEST (5 pièces + Héritage + Images)

import pygame  # <--- AJOUTÉ (pour charger les images)
import random  # <--- AJOUTÉ (pour la pioche)
from abc import ABC, abstractmethod  # <--- AJOUTÉ (pour l'héritage)

# --- 1. LES IMPORTS D'ENTITÉS ---
from entities import (
    Coffre, Casier, EndroitCreuser, Pomme, Banane, Gateau,
    Or, Gemmes, Cles, Des, Pelle, Marteau 
)

# ==============================
# Classe abstraite Room
# ==============================
class Room(ABC):
    def __init__(self, name, image=None, doors=None, gem_cost=0,
                 objets=None, rarity=0, placement_condition="any"):
        self.name = name
        self.image = image
        self.doors = doors if doors else []
        self.gem_cost = gem_cost
        self.objets = objets if objets else []
        self.rarity = rarity
        self.placement_condition = placement_condition

    def has_door(self, direction):
        return direction in self.doors

    def apply_effect_on_choose(self, player):
        pass

    def apply_effect_on_enter(self, player):
        pass


# ==============================
# Sous-classes de pièces
# ==============================

class EntranceHall(Room):
    def __init__(self):
        super().__init__(
            name="EntranceHall",
            image=pygame.image.load("assets/rooms/Entrance_Hall.png"),
            doors=["up", "left", "right"],
            placement_condition="bottom"
        )

class Antechamber(Room):
    def __init__(self):
        super().__init__(
            name="Antechamber",
            image=pygame.image.load("assets/rooms/Antechamber.png"),
            doors=["down"],
            placement_condition="top"
        )

class Bedroom(Room):
    def __init__(self):
        super().__init__(
            name="Bedroom",
            image=pygame.image.load("assets/rooms/Bedroom.png"),
            doors=["left", "down"],
            objets=[Pomme()],
            rarity=1,
            placement_condition="any"
        )

class GuestBedroom(Room):
    def __init__(self):
        super().__init__(
            name="GuestBedroom",
            image=pygame.image.load("assets/rooms/GuestBedroom.png"),
            doors=["down"],
            objets=[Pomme()],
            rarity=1,
            placement_condition="any"
        )

class Chapel(Room):
    def __init__(self):
        super().__init__(
            name="Chapel",
            image=pygame.image.load("assets/rooms/Chapel.png"),
            doors=["left", "right", "down"],
            gem_cost=1,
            objets=[Gemmes()],
            rarity=2
        )
    def apply_effect_on_enter(self, player):
        print(f"Effet '{self.name}': +10 pas.")
        player.gagner_pas(10)

class Kitchen(Room):
    def __init__(self):
        super().__init__(
            name="Kitchen",
            image=pygame.image.load("assets/rooms/Kitchen.png"),
            doors=["left", "down"],
            objets=[Banane(), Pomme()],
            rarity=1,
            placement_condition="any"
        )

class Pantry(Room):
    def __init__(self):
        super().__init__(
            name="Pantry",
            image=pygame.image.load("assets/rooms/Pantry.png"),
            doors=["left", "down"],
            objets=[Banane(), Pomme()],
            rarity=1,
            placement_condition="any"
        )

class Corridor(Room):
    def __init__(self):
        super().__init__(
            name="Corridor",
            image=pygame.image.load("assets/rooms/Corridor.png"),
            doors=["up", "down"],
            rarity=0,
            placement_condition="any"
        )

class ConferenceRoom(Room):
    def __init__(self):
        super().__init__(
            name="Conference Room",
            image=pygame.image.load("assets/rooms/Conference_Room.png"),
            doors=["down", "left", "right"],
            rarity=1,
            placement_condition="center"
        )

class Workshop(Room):
    def __init__(self):
        super().__init__(
            name="Workshop",
            image=pygame.image.load("assets/rooms/Workshop.png"),
            doors=["up", "down"],
            objets=[Marteau()],
            rarity=2,
            placement_condition="center"
        )

class Library(Room):
    def __init__(self):
        super().__init__(
            name="Library",
            image=pygame.image.load("assets/rooms/Library.png"),
            doors=["left", "down"],
            objets=[Gemmes()],
            rarity=1
        )

class Vault(Room):
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/rooms/Vault.png"),
            doors=["down"],  # cul-de-sac
            gem_cost=3,
            objets=[Or()],
            rarity=3,
            placement_condition="edge"
        )

class Furnace(Room):
    def __init__(self):
        super().__init__(
            name="Furnace",
            image=pygame.image.load("assets/rooms/Furnace.png"),
            doors=["down"],
            rarity=2,
            placement_condition="center"
        )
    def apply_effect_on_enter(self, player):
        print("🔥 Fournaise : vous perdez 5 pas.")
        player.perdre_pas(5)

class Greenhouse(Room):
    def __init__(self):
        super().__init__(
            name="Greenhouse",
            image=pygame.image.load("assets/rooms/Greenhouse.png"),
            doors=["down"],
            objets=[Gemmes()],
            rarity=1,
            placement_condition="edge"
        )

class SecretGarden(Room):
    def __init__(self):
        super().__init__(
            name="SecretGarden",
            image=pygame.image.load("assets/rooms/Secret_Garden.png"),
            doors=["left", "right", "down"],
            objets=[Gemmes()],
            rarity=2,
            placement_condition="edge"
        )

class Gallery(Room):
    def __init__(self):
        super().__init__(
            name="Gallery",
            image=pygame.image.load("assets/rooms/Gallery.png"),
            doors=["up", "down"],
            rarity=1,
            placement_condition="center"
        )

class Archives(Room):
    def __init__(self):
        super().__init__(
            name="Archives",
            image=pygame.image.load("assets/rooms/Archives.png"),
            doors=["left", "right", "up", "down"],
            rarity=2,
            placement_condition="center"
        )

class LockerRoom(Room):
    def __init__(self):
        super().__init__(
            name="Locker Room",
            image=pygame.image.load("assets/rooms/Locker_Room.png"),
            doors=["up", "down"],
            objets=[Cles()],
            rarity=1,
            placement_condition="edge"
        )

class BoilerRoom(Room):
    def __init__(self):
        super().__init__(
            name="Boiler Room",
            image=pygame.image.load("assets/rooms/Boiler_Room.png"),
            doors=["left", "down", "down"],
            rarity=2,
            placement_condition="center"
        )

class Gymnasium(Room):
    def __init__(self):
        super().__init__(
            name="Gymnasium",
            image=pygame.image.load("assets/rooms/Gymnasium.png"),
            doors=["left", "right", "down"],
            rarity=1,
            placement_condition="any"
        )

class MaidsChamber(Room):
    def __init__(self):
        super().__init__(
            name="MaidsChamber",
            image=pygame.image.load("assets/rooms/Maids_Chamber.png"),
            doors=["down", "left"],
            rarity=1,
            placement_condition="edge"
        )

class MorningRoom(Room):
    def __init__(self):
        super().__init__(
            name="Morning Room",
            image=pygame.image.load("assets/rooms/Morning_Room.png"),
            doors=["down", "right"],
            rarity=1,
            placement_condition="edge"
        )


# ==============================
# Catalogue complet
# ==============================
ROOM_CATALOG = [
    EntranceHall(), Antechamber(),
    Bedroom(), GuestBedroom(), Chapel(), Kitchen(), Pantry(), Corridor(),
    ConferenceRoom(), Workshop(), Library(), Vault(), Furnace(),
    Greenhouse(), SecretGarden(), Gallery(), Archives(),
    LockerRoom(), BoilerRoom(), Gymnasium(), MaidsChamber(), MorningRoom()
]


# ==============================
# Classe Manor
# ==============================
class Manor:
    WIDTH = 5
    HEIGHT = 9

    def __init__(self):
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

        # Exclure les pièces fixes du tirage
        self.room_catalog = [
            r for r in ROOM_CATALOG if r.name not in ("EntranceHall", "Antechamber")
        ]
        self.pioche = list(self.room_catalog)

        # Placement fixe du Hall d'entrée et de l'Antechamber
        self.place_room(2, 8, EntranceHall())
        print("Pièce de départ 'EntranceHall' placée en (2, 8).")
        self.place_room(2, 0, Antechamber())
        print("Pièce de fin 'Antechamber' placée en (2, 0).")

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

    def draw_three_rooms(self, current_pos, direction):
        """
        Tire 3 pièces compatibles selon la position du joueur et la direction choisie.
        - Respecte les portes compatibles
        - Évite les murs du manoir
        - Pas de doublons dans le tirage
        - Garantit une pièce gratuite
        """
        x, y = current_pos
        possible_rooms = []
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}

        for room in self.pioche:
            cond = room.placement_condition

            # 1️⃣ Éviter les pièces qui sortent de la grille (bords)
            if direction == "up" and y == 0:
                continue
            if direction == "down" and y == self.HEIGHT - 1:
                continue
            if direction == "left" and x == 0:
                continue
            if direction == "right" and x == self.WIDTH - 1:
                continue

            # 2️⃣ Vérifier la condition de placement
            if cond == "edge" and not (x in (0, self.WIDTH - 1) or y in (0, self.HEIGHT - 1)):
                continue
            if cond == "center" and (x in (0, self.WIDTH - 1) or y in (0, self.HEIGHT - 1)):
                continue
            if cond == "top" and y != 0:
                continue
            if cond == "bottom" and y != self.HEIGHT - 1:
                continue

            # 3️⃣ Vérifier compatibilité de porte (ex : on monte → la nouvelle pièce doit avoir "down")
            if opposite[direction] not in room.doors:
                continue

            possible_rooms.append(room)

        # 4️⃣ S'il n'y a aucune pièce compatible, proposer toute la pioche
        if not possible_rooms:
            possible_rooms = self.pioche.copy()

        # 5️⃣ Tirage sans doublons et avec au moins une pièce gratuite
        free_rooms = [r for r in possible_rooms if r.gem_cost == 0]
        choices = []

        # Forcer au moins une gratuite
        if free_rooms:
            choices.append(random.choice(free_rooms))

        remaining = [r for r in possible_rooms if r not in choices]

        # Tirer les autres sans doublons
        num_to_draw = min(2, len(remaining))
        if num_to_draw > 0:
            choices.extend(random.sample(remaining, num_to_draw))

        random.shuffle(choices)

        print("🎲 Tirage de pièces compatibles :")
        for r in choices:
            print(f" - {r.name} | portes: {r.doors} | condition: {r.placement_condition}")

        return choices
