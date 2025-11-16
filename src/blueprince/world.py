import pygame
import random
from abc import ABC, abstractmethod

from .entities import (
    Pomme, Banane, Or, Gemmes, Cles, Des, Pelle, Marteau, EndroitCreuser
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
        self.original_doors = self.doors.copy()  # Store original door configuration
        self.gem_cost = gem_cost
        self.objets = objets if objets else []
        self.rarity = rarity
        self.placement_condition = placement_condition
        self.rotation = 0  # Track current rotation (0, 90, 180, 270)

    def has_door(self, direction):
        return direction in self.doors

    def create_rotated_copy(self, num_rotations):
        """Effect:
        Creates a rotated logical copy preserving the subclass. Performs a
        clockwise rotation num_rotations * 90° of doors and image. Returns self
        unchanged if num_rotations == 0. Each rotated copy gets its own objets
        list (shallow copy) and rotation angle.

        Parameters:
        - num_rotations (int): Number of clockwise quarter turns (0–3).

        Returns:
        - Room: New instance of the same subclass with rotated doors/image.
        """
        if num_rotations == 0:
            return self
        rotated_doors = self.original_doors.copy()
        for _ in range(num_rotations):
            rotation_map = {"up": "right", "right": "down", "down": "left", "left": "up"}
            rotated_doors = [rotation_map[d] for d in rotated_doors]

        rotated_image = pygame.transform.rotate(self.image, -90 * num_rotations) if self.image else None

        # Instantiate without calling subclass __init__ to be able to set fields manually
        rotated = self.__class__.__new__(self.__class__)
        # Copy scalar & mutable attributes
        rotated.name = self.name
        rotated.image = rotated_image
        rotated.doors = rotated_doors
        rotated.original_doors = self.original_doors.copy()
        rotated.gem_cost = self.gem_cost
        rotated.objets = self.objets.copy()
        rotated.rarity = self.rarity
        rotated.placement_condition = self.placement_condition
        rotated.rotation = (num_rotations * 90) % 360
        return rotated
    
    def get_all_rotations(self):
        """Returns a list of all possible rotations of this room."""
        return [self.create_rotated_copy(i) for i in range(4)]

    def apply_effect_on_choose(self, player):
        pass

    def apply_effect_on_enter(self, player, manor=None):
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
            placement_condition="bottom",
            objets=[]
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
            objets=[Gemmes(1)],
            rarity=2
        )
    def apply_effect_on_enter(self, player, manor=None):
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
            objets=[Gemmes(1)],
            rarity=1
        )

class Vault(Room):
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/rooms/Vault.png"),
            doors=["down"],  # cul-de-sac
            gem_cost=3,
            objets=[Or(1)],
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
    def apply_effect_on_enter(self, player, manor=None):
        player.perdre_pas(5, manor)

class Greenhouse(Room):
    def __init__(self):
        super().__init__(
            name="Greenhouse",
            image=pygame.image.load("assets/rooms/Greenhouse.png"),
            doors=["down"],
            objets=[Gemmes(1)],
            rarity=1,
            placement_condition="edge"
        )

class SecretGarden(Room):
    def __init__(self):
        super().__init__(
            name="SecretGarden",
            image=pygame.image.load("assets/rooms/Secret_Garden.png"),
            doors=["left", "right", "down"],
            objets=[Gemmes(1)],
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
            objets=[Cles(1)],
            rarity=1,
            placement_condition="edge"
        )

class BoilerRoom(Room):
    def __init__(self):
        super().__init__(
            name="Boiler Room",
            image=pygame.image.load("assets/rooms/Boiler_Room.png"),
            doors=["left", "down", "right"],
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
            doors=["down", "left"],
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
    opposite_direction = {"up": "down",
                          "down": "up",
                          "right": "left",
                          "left": "right"}

    def __init__(self):
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

        # Exclure les pièces fixes du tirage
        self.room_catalog = [
            r for r in ROOM_CATALOG if r.name not in ("EntranceHall", "Antechamber")
        ]
        self.pioche = self.room_catalog

        # Placement fixe du Hall d'entrée et de l'Antechamber
        self.place_room(2, 8, EntranceHall())
        self.place_room(2, 0, Antechamber())

    def in_bounds(self, x, y):
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        """Effect:
        Places a room instance at grid coordinate (x, y) after bounds
        validation, then removes the original (unrotated) room definition
        from the `room_catalog`.

        Parameters:
        - x (int): Column index in manor grid.
        - y (int): Row index in manor grid.
        room (Room): The room instance (may be a rotated copy) to store.
        """
        if not self.in_bounds(x, y):
            raise ValueError("Position hors limites.")
        self.grid[y][x] = room

        # Remove original catalog entry (by name) to prevent future draws.
        for catalog_room in self.room_catalog[:]:
            if catalog_room.name == room.name:
                self.room_catalog.remove(catalog_room)
                break

    def draw_three_rooms(self, current_pos, direction, room_catalog):
        """Effect:
        Builds up to three choices of possible rooms and enforces the
        at-least-one-free rule if any free options exist.

        Parameters:
        - current_pos (tuple[int,int]): Origin (x,y).
        - direction (str): Move direction ('up','down','left','right').
        - room_catalog (list[Room]): Remaining unplaced room prototypes.

        Returns:
        - list[Room]: Up to three room instances from the filtered possibilities.
        """
        possible_rooms = self.get_possible_rooms(current_pos, direction, room_catalog)

        # If no compatible rooms, return empty (should not happen normally)
        if not possible_rooms:
            return []

        # Separate free and paid rooms
        free_rooms = [r for r in possible_rooms if r.gem_cost == 0]
        paid_rooms = [r for r in possible_rooms if r.gem_cost > 0]
        
        choices = []

        # Forcer au moins une gratuite
        if free_rooms:
            choices.append(random.choice(free_rooms))
        
        # Add up to 2 more rooms (can be free or paid)
        remaining = [r for r in possible_rooms if r not in choices]
        num_to_draw = min(2, len(remaining))
        if num_to_draw > 0:
            choices.extend(random.sample(remaining, num_to_draw))
        
        # If we have less than 3 choices, fill with what we have
        random.shuffle(choices)
        
        return choices[:3]  # Return maximum 3 rooms
    
    def get_direction_offset(self, direction):
        """Returns (dx, dy) for given direction."""
        if direction == "up": return (0, -1)
        elif direction == "down": return (0, 1)
        elif direction == "left": return (-1, 0)
        elif direction == "right": return (1, 0)
        return (0, 0)
    
    def get_possible_rooms(self, position, direction, room_catalog):
        """Effect:
        Returns all room instances (including a single valid rotation per base
        room) that can be legally placed adjacent to `position` in `direction`.

        Parameters:
        - position (tuple[int, int]): (x, y) origin cell.
        - direction (str): Direction of movement ('up','down','left','right').
        - room_catalog (list[Room]): Remaining unplaced rooms in the catalog.

        Returns:
        - list[Room]: Rotated room instances valid for placement; empty if none.
        """
        x, y = position
        dx, dy = self.get_direction_offset(direction)
        nx, ny = x + dx, y + dy

        # Target must be in-bounds and empty
        if not self.in_bounds(nx, ny) or self.get_room(nx, ny):
            return []

        required_door = self.opposite_direction[direction]
        possible_rooms = []

        for room in room_catalog:
            for rotated_room in room.get_all_rotations():
                if required_door not in rotated_room.doors:
                    continue

                # Enforce placement condition on the TARGET (nx, ny)
                cond = rotated_room.placement_condition
                if cond == "edge" and not (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                    continue
                if cond == "center" and (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                    continue
                if cond == "top" and ny != 0:
                    continue
                if cond == "bottom" and ny != self.HEIGHT - 1:
                    continue

                # Reject rotations whose doors would lead outside the manor
                valid_doors = True
                for door in rotated_room.doors:
                    door_dx, door_dy = self.get_direction_offset(door)
                    check_x, check_y = nx + door_dx, ny + door_dy
                    if not self.in_bounds(check_x, check_y):
                        valid_doors = False
                        break
                if not valid_doors:
                    continue

                possible_rooms.append(rotated_room)
                break  # Only keep the first valid rotation per room

        return possible_rooms
    
    def can_advance(self):
        """Effect:
        Scans the entire manor grid to determine if at least one legal
        move remains.

        Parameters:
        - None

        Returns:
        - bool: True if at least one expansion position exists; False otherwise.
        """
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                room = self.get_room(x, y)
                if isinstance(room, Antechamber):
                    continue
                if room:
                    for direction in room.doors:
                        dx, dy = self.get_direction_offset(direction)
                        nx, ny = x + dx, y + dy
                        if self.in_bounds(nx, ny) and not self.get_room(nx, ny):
                            if self.get_possible_rooms((x, y), direction, self.room_catalog):
                                return True
        return False
