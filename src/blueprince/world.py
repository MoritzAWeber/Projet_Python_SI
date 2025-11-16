import pygame
import random
from abc import ABC, abstractmethod

from .entities import (
    Pomme, Banane, Or, Gemmes, Cles, Des, Pelle, Marteau, EndroitCreuser,
    DetecteurMetaux, PatteLapin, Coffre, Casier, KitCrochetage, Gateau, Sandwich, Repas
)


# ==============================
# Helper function for random loot
# ==============================
def generate_random_loot(player, item_pool, found_permanents=None):
    """Generates a random subset of pre-instantiated items.

    Parameters:
    - player: Player instance or None. If None, luck modifiers are ignored.
    - item_pool: list[Objet] of candidate instances (duplicates model max quantity).
    - dig_spots_range: optional (min,max) tuple to append that many EndroitCreuser instances.
    - found_permanents: optional set of permanent class names already found.

    Returns:
    - list[Objet]: randomly selected instances (subset of item_pool plus dig spots).
    """
    result = []
    if found_permanents is None:
        found_permanents = set()

    # Safely determine luck modifiers (only if player provided)
    has_rabbits_foot = False
    has_metal_detector = False
    if player is not None:
        try:
            has_rabbits_foot = any(isinstance(item, PatteLapin) for item in player.inventory.permanents)
            has_metal_detector = any(isinstance(item, DetecteurMetaux) for item in player.inventory.permanents)
        except Exception:
            pass

    luck_multiplier = 1.15 if has_rabbits_foot else 1.0

    for item in item_pool:
        # Skip permanents bereits gefunden
        if getattr(item, 'type', None) == 'permanent' and item.__class__.__name__ in found_permanents:
            continue
        
        base_chance = getattr(item, 'base_find_chance', 0.5)
        is_metallic = getattr(item, 'is_metallic', False)
        chance = base_chance * luck_multiplier
        if is_metallic and has_metal_detector:
            chance *= 1.25
        if random.random() < chance:
            result.append(item)

    return result


# ==============================
# Classe abstraite Room
# ==============================

# ==============================
# SHOP EFFECT (effet commun à toutes les pièces jaunes)
# ==============================

class ShopEffect:
    """Effet commun à toutes les pièces jaunes : achat automatique du meilleur objet que le joueur peut se payer."""

    SHOP_ITEMS = [
        ("Pomme", 2, lambda player: player.gagner_pas(2)),
        ("Banane", 3, lambda player: player.gagner_pas(3)),
        ("Gâteau", 8, lambda player: player.gagner_pas(10)),
        ("Sandwich", 12, lambda player: player.gagner_pas(15)),
        ("Repas", 20, lambda player: player.gagner_pas(25)),

        ("Clé", 10, lambda player: setattr(player, "cles", player.cles + 1)),
        ("Gemme", 3, lambda player: setattr(player, "gemmes", player.gemmes + 1)),
        ("Pelle", 6, lambda player: player.inventory.add_item(Pelle())),
    ]

    def apply_effect_on_enter(self, player):
        # Ne plus ouvrir automatiquement le menu du shop; uniquement préparer via appel existant.
        if hasattr(player, "game"):
            try:
                player.game.open_shop_menu(self)  # prépare les items sans activation
                player.add_message("Magasin disponible: appuyez sur M pour ouvrir.")
            except Exception:
                pass



class Room(ABC):
    def __init__(self, name, image=None, doors=None, gem_cost=0, item_pool=None,
                 objets=None, rarity=0, placement_condition="any",
                 color="blue", base_weight=1.0):
        """
        name : nom interne de la pièce
        image : surface pygame (image de la pièce)
        doors : liste de directions accessibles ["up","down","left","right"]
        gem_cost : coût en gemmes pour tirer cette pièce
        objets : liste d'objets présents dans la pièce
        rarity : niveau de rareté (0=commun, 3=très rare)
        placement_condition : "any", "edge", "center", "top", "bottom"
        color : "blue", "green", "purple", "yellow", "orange", "red"
        """
        self.base_weight = base_weight
        self.name = name
        self.image = image
        self.doors = doors if doors else []
        self.original_doors = self.doors.copy()  # Store original door configuration
        self.gem_cost = gem_cost
        self.item_pool = item_pool if item_pool else []
        self.objets = objets if objets else []
        # Loot will be generated on first entry with player luck
        self.loot_generated = False
        self.rarity = rarity
        self.placement_condition = placement_condition
        self.color = color
        self.rotation = 0  # Track current rotation (0, 90, 180, 270)
        # Default flag for one-shot effects; subclasses may override
        self.effect_triggered = False

    def has_door(self, direction):
        return direction in self.doors
    

    def generate_loot_on_enter(self, player):
        """Generate loot with player luck modifiers on first room entry."""
        if not self.loot_generated and self.item_pool:
            manor = getattr(player, "manor", None)
            found_perms = getattr(manor, 'found_permanents', set()) if manor else set()
            loot = generate_random_loot(player, self.item_pool, found_permanents=found_perms)
            self.objets.extend(loot)
            self.loot_generated = True

    def create_rotated_copy(self, num_rotations):
        """Creates a copy of this room rotated by num_rotations * 90 degrees."""
        if num_rotations == 0:
            return self  # No rotation needed, return self
        
        # Manually create a new room instance with rotated attributes
        rotated_doors = self.original_doors.copy()
        
        # Apply rotation num_rotations times
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
        rotated.item_pool = self.item_pool  # Copy item_pool reference
        rotated.objets = self.objets.copy()
        rotated.loot_generated = self.loot_generated  # Copy loot generation flag
        rotated.rarity = self.rarity
        rotated.placement_condition = self.placement_condition
        rotated.color = self.color  # Copy color
        rotated.base_weight = self.base_weight  # Copy base_weight
        rotated.rotation = (num_rotations * 90) % 360
        rotated.effect_triggered = self.effect_triggered  # Always copy this flag
            
        return rotated

    
    def get_all_rotations(self):
        """Returns a list of all possible rotations of this room."""
        return [self.create_rotated_copy(i) for i in range(4)]

    def apply_effect_on_choose(self, player):
        """Effet éventuel déclenché au moment où la pièce est choisie dans le tirage."""
        pass

    def apply_effect_on_enter(self, player):
        """Default behavior: generate loot on first entry."""
        self.generate_loot_on_enter(player)


# ==============================
# Pièces fixes : début / fin
# ==============================
class EntranceHall(Room):
    def __init__(self):
        super().__init__(
            name="EntranceHall",
            image=pygame.image.load("assets/rooms/Blue/Entrance_Hall.png"),
            doors=["up", "left", "right"],
            placement_condition="bottom",
            color="blue",
            objets=[]
        )


class Antechamber(Room):
    def __init__(self):
        super().__init__(
            name="Antechamber",
            image=pygame.image.load("assets/rooms/Blue/Antechamber.png"),
            doors=["down", "left", "right"],
            placement_condition="top",
            color="blue",
        )


# ==============================
# GREEN ROOMS (pièces vertes)
# ==============================

class Greenhouse(Room):
    """
    Effet : Augmente le bonus de tirage (RÉPÉTABLE).
    """
    def __init__(self):
        super().__init__(
            name="Greenhouse",
            image=pygame.image.load("assets/rooms/Green/Greenhouse.png"),
            doors=["down"],
            # Ajout PatteLapin pour disponibilité théorique des permanents
            item_pool=[Gemmes(4), PatteLapin(), EndroitCreuser(), EndroitCreuser(), Pomme(), Pomme(), Banane(), Banane()],
            objets=[],
            rarity=1,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        if not hasattr(manor, "green_draw_bonus"):
            manor.green_draw_bonus = 0
        manor.green_draw_bonus += 1
        player.add_message("Greenhouse: bonus de tirage vert +1")
        # Generate loot with player luck
        self.generate_loot_on_enter(player)

class MorningRoom(Room):
    """
    Effet : Donne +2 gemmes (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Morning Room",
            image=pygame.image.load("assets/rooms/Green/Morning_Room.png"),
            doors=["down", "left"],
            item_pool=[Gemmes(2), EndroitCreuser(), Pelle(), Coffre()],
            rarity=1,
            placement_condition="edge",
            color="green"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gemmes += 2
        player.add_message("Morning Room: +2 gemmes")
        self.effect_triggered = True 


class SecretGarden(Room):
    """
    Effet : Disperse des fruits (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="SecretGarden",
            image=pygame.image.load("assets/rooms/Green/Secret_Garden.png"),
            doors=["left", "right", "down"],
            item_pool=[Gemmes(1), Pomme(), Pomme(), Pomme(), Banane(), Banane(), Banane(), EndroitCreuser(), EndroitCreuser()],
            rarity=2,
            placement_condition="edge",
            color="green"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        fruits = [Pomme(), Banane()]
        target_conf = getattr(manor, "redirect_spread_to_conference", None)

        if target_conf is not None:
            for _ in range(manor.WIDTH * manor.HEIGHT):
                if random.random() < 0.20:
                    target_conf.objets.append(random.choice(fruits))
            player.add_message("Secret Garden: fruits envoyés vers la Conference Room")
        else:
            for y in range(manor.HEIGHT):
                for x in range(manor.WIDTH):
                    room = manor.get_room(x, y)
                    if room and room is not self:
                        if random.random() < 0.20:
                            room.objets.append(random.choice(fruits))
            player.add_message("Secret Garden: des fruits se répandent dans le manoir")
        
        self.effect_triggered = True 


class Veranda(Room):
    """
    Effet : Active un flag (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Veranda",
            image=pygame.image.load("assets/rooms/Green/Veranda.png"),
            doors=["up", "down"],
            gem_cost=2,
            item_pool=[Gemmes(1), EndroitCreuser()],
            rarity=1,
            placement_condition="edge",
            color="green"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        manor.green_item_bonus = True
        player.add_message("Veranda: bonus d'objets verts activé")
        self.effect_triggered = True 


class Cloister(Room):
    def __init__(self):
        super().__init__(
            name="Cloister",
            image=pygame.image.load("assets/rooms/Green/Cloister.png"),
            doors=["left", "right", "up", "down"],
            gem_cost=3,
            item_pool=[Gemmes(2), EndroitCreuser(), EndroitCreuser(), Cles(1), Pelle()],
            rarity=1,
            placement_condition="center",
            color="green"
        )

class Courtyard(Room):
    def __init__(self):
        super().__init__(
            name="Courtyard",
            image=pygame.image.load("assets/rooms/Green/Courtyard.png"),
            doors=["left", "right", "down"],
            item_pool=[Or(3), EndroitCreuser(), EndroitCreuser(), Pomme(), Pomme(), Banane(), Banane(), Pelle()],
            rarity=1,
            placement_condition="center",
            color="green"
        )

class Patio(Room):
    """
    Effet : Ajoute des gemmes aux pièces (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Patio",
            image=pygame.image.load("assets/rooms/Green/Patio.png"),
            doors=["left", "down"],
            item_pool=[Gemmes(1), EndroitCreuser(), EndroitCreuser()],
            rarity=2,
            placement_condition="edge",
            color="green"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        for y in range(manor.HEIGHT):
            for x in range(manor.WIDTH):
                room = manor.get_room(x, y)
                if room and getattr(room, "color", "") == "green":
                    room.objets.append(Gemmes(1))
        player.add_message("Patio: +1 gemme ajoutée à chaque pièce verte")
        
        self.effect_triggered = True # <-- CORRECTION


class Terrace(Room):
    """
    Effet : Active un flag (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Terrace",
            image=pygame.image.load("assets/rooms/Green/Terrace.png"),
            doors=["down"],
            item_pool=[Or(2), EndroitCreuser()],
            rarity=1,
            placement_condition="edge",
            color="green"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        manor.green_rooms_free = True
        player.add_message("Terrace: les pièces vertes deviennent gratuites")
        self.effect_triggered = True 


# ==============================
# --- PURPLE ROOMS (chambres) ---
# ==============================

class HerLadyshipsChamber(Room):
    """
    Effet : Active des bonus (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="HerLadyshipsChamber",
            image=pygame.image.load("assets/rooms/Purple/Her_Ladyships_Chamber.png"),
            doors=["down"],
            item_pool=[Gemmes(2), Cles(1), Des(1), Coffre()],
            rarity=2,
            placement_condition="any",
            color="purple"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        manor = player.manor
        manor.bonus_next_boudoir_steps = 10
        manor.bonus_next_walkin_gems = 3
        player.add_message("Her Ladyship’s Chamber: prochains bonus activés")
        self.effect_triggered = True 


class MasterBedroom(Room):
    """
    Effet : Donne des pas
    """
    def __init__(self):
        super().__init__(
            name="MasterBedroom",
            image=pygame.image.load("assets/rooms/Purple/Master_Bedroom.png"),
            doors=["down"],
            gem_cost=2,
            item_pool=[Gemmes(1), Cles(1), Coffre()],
            rarity=2,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = player.manor
        count = sum(1 for y in range(manor.HEIGHT) for x in range(manor.WIDTH) if manor.get_room(x, y))
        player.gagner_pas(count)
        player.add_message(f"Master Bedroom: +{count} pas (pièces posées)")


class Nursery(Room):
    """
    Effet : Active un bonus 
    """
    def __init__(self):
        super().__init__(
            name="Nursery",
            image=pygame.image.load("assets/rooms/Purple/Nursery.png"),
            doors=["down"],
            item_pool=[Pomme(), Des(1)],
            rarity=1,
            placement_condition="any",
            color="purple"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.manor.bonus_on_draft_bedroom = True
        player.add_message("Nursery: les prochains tirages de Bedroom donnent +5 pas")
        self.effect_triggered = True 


class ServantsQuarters(Room):
    """
    Effet : Donne des clés (RÉPÉTABLE).
    """
    def __init__(self):
        super().__init__(
            name="ServantsQuarters",
            image=pygame.image.load("assets/rooms/Purple/Servants_Quarters.png"),
            doors=["down"],
            item_pool=[Cles(2)],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = player.manor
        count = 0
        for y in range(manor.HEIGHT):
            for x in range(manor.WIDTH):
                room = manor.get_room(x, y)
                if not room:
                    continue
                if room.name == "Bedroom":
                    count += 1
                elif room.name == "BunkRoom":
                    count += 2  

        player.cles += count
        player.add_message(f"Servants’ Quarters: +{count} clé(s)")


class Bedroom(Room):
    """
    Effet : Donne +2 pas 
    """
    def __init__(self):
        super().__init__(
            name="Bedroom",
            image=pygame.image.load("assets/rooms/Purple/Bedroom.png"),
            doors=["left", "down"],
            item_pool=[Gemmes(1), Des(1)],
            rarity=0,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gagner_pas(2)
        # gagner_pas affiche déjà un message


class Boudoir(Room):
    """
    Effet : Consomme un bonus 
    """
    def __init__(self):
        super().__init__(
            name="Boudoir",
            image=pygame.image.load("assets/rooms/Purple/Boudoir.png"),
            doors=["down", "left"],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = player.manor
        # Bonus one-shot (consomme le flag, donc doit être vérifié à chaque fois)
        if getattr(manor, "bonus_next_boudoir_steps", 0) > 0:
            bonus = manor.bonus_next_boudoir_steps
            player.gagner_pas(bonus)
            manor.bonus_next_boudoir_steps = 0
            player.add_message(f"Boudoir: bonus spécial de +{bonus} pas consommé")


class BunkRoom(Room):
    def __init__(self):
        super().__init__(
            name="BunkRoom",
            image=pygame.image.load("assets/rooms/Purple/Bunk_Room.png"),
            doors=["down"],
            item_pool=[Or(2), Des(1)],
            rarity=2,
            placement_condition="any",
            color="purple"
        )

class GuestBedroom(Room):
    """
    Effet : Donne +10 pas (UNE SEULE FOIS, selon votre règle).
    """
    def __init__(self):
        super().__init__(
            name="GuestBedroom",
            image=pygame.image.load("assets/rooms/Purple/GuestBedroom.png"),
            doors=["down"],
            item_pool=[Gemmes(1), Or(4)],
            rarity=1,
            placement_condition="any",
            color="purple"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gagner_pas(10)
        # gagner_pas affiche déjà un message
        self.effect_triggered = True 


# ==============================
# ORANGE ROOMS (Hallways)
# ==============================

class Corridor(Room):
    def __init__(self):
        super().__init__(
            name="Corridor",
            image=pygame.image.load("assets/rooms/Orange/Corridor.png"),
            doors=["up", "down"],
            item_pool=[Or(3), Cles(1), DetecteurMetaux(), Pelle(), Coffre()],
            rarity=0,
            placement_condition="any",
            color="orange"
        )

class EastWingHall(Room):
    def __init__(self):
        super().__init__(
            name="EastWingHall",
            image=pygame.image.load("assets/rooms/Orange/East_Wing_Hall.png"),
            doors=["left", "right", "down"],
            item_pool=[Or(3), Cles(1), EndroitCreuser(), Pelle(), Coffre(), Gateau()],
            rarity=1,
            placement_condition="any",
            color="orange"
        )

class WestWingHall(Room):
    def __init__(self):
        super().__init__(
            name="WestWingHall",
            image=pygame.image.load("assets/rooms/Orange/West_Wing_Hall.png"),
            doors=["left", "right", "down"],
            item_pool=[Or(4), Cles(2), EndroitCreuser(), EndroitCreuser(), Pelle(), Coffre(), Repas()],
            rarity=1,
            placement_condition="any",
            color="orange"
        )

class Hallway(Room):
    def __init__(self):
        super().__init__(
            name="Hallway",
            image=pygame.image.load("assets/rooms/Orange/Hallway.png"),
            doors=["left", "right", "down"],
            item_pool=[Or(2), Cles(2), Des(1), Coffre(), Sandwich()],
            rarity=0,
            placement_condition="any",
            color="orange"
        )

class Passageway(Room):
    def __init__(self):
        super().__init__(
            name="Passageway",
            image=pygame.image.load("assets/rooms/Orange/Passageway.png"),
            doors=["left", "right", "up", "down"],
            item_pool=[Or(2), Cles(1), Coffre(), KitCrochetage()],
            rarity=0,
            placement_condition="any",
            color="orange"
        )

class GreatHall(Room):
    def __init__(self):
        super().__init__(
            name="GreatHall",
            image=pygame.image.load("assets/rooms/Orange/Great_Hall.png"),
            doors=["left", "right", "up", "down"],
            item_pool=[Or(5), Gemmes(2), Cles(2), Repas()],
            rarity=2,
            placement_condition="any",
            color="orange"
        )

class Foyer(Room):
    """
    Effet : Active un flag (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Foyer",
            image=pygame.image.load("assets/rooms/Orange/Foyer.png"),
            doors=["up", "down"],
            gem_cost=2,
            item_pool=[Or(3), Cles(1), Casier()],
            rarity=2,
            placement_condition="any",
            color="orange"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.manor.hallway_doors_unlocked = True
        player.add_message("Foyer: portes de Hallway déverrouillées")
        self.effect_triggered = True 


class SecretPassage(Room):
    """
    Effet : Active un flag (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="SecretPassage",
            image=pygame.image.load("assets/rooms/Orange/Secret_Passage.png"),
            doors=["down"],
            item_pool=[Gemmes(1), Des(1), Casier()],
            rarity=3,
            placement_condition="any",
            color="orange"
        )
        self.effect_triggered = False

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.manor.next_room_color_choice = True
        player.add_message("Secret Passage: choix de la couleur au prochain tirage")
        self.effect_triggered = True 


# ==============================
# BLUE ROOMS
# ==============================

class LockerRoom(Room):
    """
    Effet : Répartit des clés (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="LockerRoom",
            image=pygame.image.load("assets/rooms/Blue/Locker_Room.png"),
            doors=["up", "down"],
            item_pool=[Or(3), Gemmes(2), Cles(4), Casier(), KitCrochetage()],
            rarity=1,
            placement_condition="any",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        target_conf = getattr(manor, "redirect_spread_to_conference", None)

        if target_conf is not None:
            for _ in range(manor.WIDTH * manor.HEIGHT):
                if random.random() < 0.20:
                    target_conf.objets.append(Cles(1))
            player.add_message("Locker Room: clés envoyées vers la Conference Room")
        else:
            for y in range(manor.HEIGHT):
                for x in range(manor.WIDTH):
                    room = manor.get_room(x, y)
                    if room and room is not self:
                        if random.random() < 0.20:
                            room.objets.append(Cles(1))
            player.add_message("Locker Room: des clés apparaissent dans plusieurs pièces")
                            
        self.effect_triggered = True 


class Vault(Room):
    """
    Effet : Donne +40 Or (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/rooms/Blue/Vault.png"),
            doors=["down"],  # cul-de-sac
            gem_cost=3,
            item_pool=[Or(40), Gemmes(3), Cles(1), Coffre()],
            rarity=3,
            placement_condition="edge",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.or_ += 40
        player.add_message("Vault: +40 or")
        self.effect_triggered = True 


class Workshop(Room):
    """
    Effet : Donne un objet permanent (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Workshop",
            image=pygame.image.load("assets/rooms/Blue/Workshop.png"),
            doors=["up", "down"],
            item_pool=[Pelle(), Marteau(), DetecteurMetaux(), PatteLapin(), KitCrochetage(), Casier()],
            rarity=2,
            placement_condition="center",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        permanents = [Pelle(), Marteau(), DetecteurMetaux(), PatteLapin()]
        item = random.choice(permanents)
        player.inventory.add_item(item)
        player.add_message(f"Workshop: objet permanent obtenu ({item.nom})")
        self.effect_triggered = True 


class BoilerRoom(Room):
    """
    Effet : Donne +3 pas (RÉPÉTABLE).
    """
    def __init__(self):
        super().__init__(
            name="BoilerRoom",
            image=pygame.image.load("assets/rooms/Blue/Boiler_Room.png"),
            doors=["left", "down", "right"],
            item_pool=[EndroitCreuser(), DetecteurMetaux(), Or(3), Pelle(), KitCrochetage()],
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gagner_pas(3)
        # gagner_pas affiche déjà un message


class ConferenceRoom(Room):
    """
    Effet : Active un 'aimant' (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="ConferenceRoom",
            image=pygame.image.load("assets/rooms/Blue/Conference_Room.png"),
            doors=["down", "left", "right"],
            item_pool=[Or(4), Gemmes(1), Cles(1), DetecteurMetaux(), Pelle(), KitCrochetage()],
            rarity=2,
            placement_condition="center",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = player.manor
        manor.redirect_spread_to_conference = self
        player.add_message("Conference Room: les futurs effets de dispersion convergeront ici")
        self.effect_triggered = True 


class Gallery(Room):
    """
    Effet : Donne +1 gemme (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Gallery",
            image=pygame.image.load("assets/rooms/Blue/Gallery.png"),
            doors=["up", "down"],
            item_pool=[Gemmes(1), Or(2)],
            rarity=1,
            placement_condition="center",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gemmes += 1
        player.add_message("Gallery: +1 gemme")
        self.effect_triggered = True 


class Garage(Room):
    """
    Effet : Donne +3 clés (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Garage",
            image=pygame.image.load("assets/rooms/Blue/Garage.png"),
            doors=["down"],
            item_pool=[Or(2), KitCrochetage()],
            rarity=1,
            placement_condition="any",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.cles += 3
        player.add_message("Garage: +3 clés")
        self.effect_triggered = True 


class Library(Room):
    """
    Effet : Augmente le bonus de rareté (RÉPÉTABLE).
    """
    def __init__(self):
        super().__init__(
            name="Library",
            image=pygame.image.load("assets/rooms/Blue/Library.png"),
            doors=["left", "down"],
            item_pool=[Gemmes(1), Des(1), PatteLapin()],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        manor = player.manor
        manor.rarity_bias += 1
        player.add_message("Library: biais de rareté augmenté")


class RumpusRoom(Room):
    """
    Effet : Donne +8 Or (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="RumpusRoom",
            image=pygame.image.load("assets/rooms/Blue/Rumpus_Room.png"),
            doors=["up", "down"],
            item_pool=[Or(8), Banane(), Des(2), Cles(2), Gemmes(1), Sandwich()],
            rarity=1,
            placement_condition="any",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.or_ += 8
        player.add_message("Rumpus Room: +8 or")
        self.effect_triggered = True 


class Pantry(Room):
    """
    Effet : Donne +4 Or (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Pantry",
            image=pygame.image.load("assets/rooms/Blue/Pantry.png"),
            doors=["left", "down"],
            item_pool=[Or(4), Pomme(), Banane(), Gateau(), Sandwich()],
            rarity=0,
            placement_condition="any",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.or_ += 4
        player.add_message("Pantry: +4 or")
        self.effect_triggered = True 


class Room8(Room):
    """
    Effet : Donne +1 gemme (UNE SEULE FOIS).
    """
    def __init__(self):
        super().__init__(
            name="Room8",
            image=pygame.image.load("assets/rooms/Blue/Room_8.png"),
            doors=["left", "down"],
            item_pool=[Or(5), Gemmes(2), Banane(), Cles(1)],
            rarity=1,
            placement_condition="any",
            color="blue"
        )
        self.effect_triggered = False 

    def apply_effect_on_enter(self, player):
        if self.effect_triggered: return 
        
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        player.gemmes += 1
        player.add_message("Room 8: +1 gemme")
        self.effect_triggered = True 


class Rotunda(Room):
    """
    Effet : Fait tourner les portes (RÉPÉTABLE).
    """
    def __init__(self):
        super().__init__(
            name="Rotunda",
            image=pygame.image.load("assets/rooms/Blue/Rotunda.png"),
            doors=["down", "left"],
            gem_cost=3,
            item_pool=[Or(4), Gemmes(1)],
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        # Generate loot with player luck
        self.generate_loot_on_enter(player)
        
        # rotation des portes : up->right->down->left
        new_doors = []
        mapping = {"up": "right", "right": "down", "down": "left", "left": "up"}
        for d in self.doors:
            new_doors.append(mapping.get(d, d))
        self.doors = new_doors
        player.add_message("Rotunda: les portes ont tourné")
        


# ==============================
# YELLOW ROOMS (Magasins unifiés)
# ==============================

class Bookshop(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Bookshop",
            image=pygame.image.load("assets/rooms/Yellow/Bookshop.png"),
            doors=["left", "down"],
            rarity=1,
            placement_condition="any",
            color="yellow"
        )


class Commissary(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Commissary",
            image=pygame.image.load("assets/rooms/Yellow/Commissary.png"),
            doors=["left", "down"],
            rarity=1,
            placement_condition="any",
            color="yellow"
        )


class Kitchen(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Kitchen",
            image=pygame.image.load("assets/rooms/Yellow/Kitchen.png"),
            doors=["down", "left"],
            rarity=0,
            placement_condition="any",
            color="yellow"
        )


class LaundryRoom(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="LaundryRoom",
            image=pygame.image.load("assets/rooms/Yellow/Laundry_Room.png"),
            doors=["down"],
            rarity=1,
            placement_condition="any",
            color="yellow"
        )


class Locksmith(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Locksmith",
            image=pygame.image.load("assets/rooms/Yellow/Locksmith.png"),
            doors=["down"],
            rarity=2,
            placement_condition="any",
            color="yellow"
        )


class GiftShop(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="GiftShop",
            image=pygame.image.load("assets/rooms/Yellow/Mount_Holly_Gift_Shop.png"),
            doors=["left", "down", "right"],
            rarity=1,
            placement_condition="any",
            color="yellow"
        )


class Showroom(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Showroom",
            image=pygame.image.load("assets/rooms/Yellow/Showroom.png"),
            doors=["up", "down"],
            rarity=2,
            placement_condition="any",
            color="yellow"
        )


class Armory(ShopEffect, Room):
    def __init__(self):
        super().__init__(
            name="Armory",
            image=pygame.image.load("assets/rooms/Yellow/The_Armory.png"),
            doors=["down", "left"],
            rarity=2,
            placement_condition="any",
            color="yellow"
        )



# ==============================
# Catalogue / Factory
# ==============================
def build_room_catalog():
    """Construit un nouveau catalogue d'instances fraîches pour une partie.
    Évite la réutilisation d'objets mutés entre plusieurs runs (ROOM_CATALOG global)."""
    return [
        EntranceHall(),
        Antechamber(),

        # ---- GREEN ----
        Greenhouse(),
        Greenhouse(),
        MorningRoom(),
        MorningRoom(),
        SecretGarden(),
        SecretGarden(),
        Veranda(),
        Veranda(),
        Cloister(),
        Cloister(),
        Courtyard(),
        Courtyard(),
        Patio(),
        Patio(),
        Terrace(),
        Terrace(),

        # ---- PURPLE ----
        HerLadyshipsChamber(),
        HerLadyshipsChamber(),
        MasterBedroom(),
        MasterBedroom(),
        Nursery(),
        Nursery(),
        ServantsQuarters(),
        ServantsQuarters(),
        Bedroom(),
        Bedroom(),
        Boudoir(),
        Boudoir(),
        BunkRoom(),
        BunkRoom(),
        GuestBedroom(),
        GuestBedroom(),

        # ---- ORANGE ROOMS ----
        Corridor(),
        Corridor(),
        EastWingHall(),
        EastWingHall(),
        WestWingHall(),
        WestWingHall(),
        Hallway(),
        Hallway(),
        Passageway(),
        Passageway(),
        GreatHall(),
        GreatHall(),
        Foyer(),
        Foyer(),
        SecretPassage(),
        SecretPassage(),

        # Blue rooms
        LockerRoom(),
        LockerRoom(),
        Vault(),
        Vault(),
        Workshop(),
        Workshop(),
        BoilerRoom(),
        BoilerRoom(),
        ConferenceRoom(),
        ConferenceRoom(),
        Gallery(),
        Gallery(),
        Garage(),
        Garage(),
        Library(),
        Library(),
        RumpusRoom(),
        RumpusRoom(),
        Pantry(),
        Pantry(),
        Room8(),
        Room8(),
        Rotunda(),
        Rotunda(),

        # Yellow
        Bookshop(),
        Commissary(),
        Kitchen(),
        LaundryRoom(),
        Locksmith(),
        GiftShop(),
        Showroom(),
        Armory(),
    ]

# Garder un catalogue initial si besoin ailleurs (non utilisé pour les nouvelles parties)
ROOM_CATALOG = build_room_catalog()


# ==============================
# Classe Manor
# ==============================
class Manor:
    WIDTH = 5
    HEIGHT = 9

    opposite_direction = {
        "up": "down",
        "down": "up",
        "right": "left",
        "left": "right"
    }

    def __init__(self):
        # Grille de pièces
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

        # Catalogue frais pour cette instance
        fresh_catalog = build_room_catalog()
        self.room_catalog = [r for r in fresh_catalog if r.name not in ("EntranceHall", "Antechamber")]
        self.pioche = self.room_catalog

        # Effets globaux liés aux pièces vertes
        self.green_draw_bonus = 0      # utilisé pour favoriser les pièces vertes
        self.green_item_bonus = False  # futur bonus d'objets dans les pièces vertes
        self.green_rooms_free = False  # si True, les pièces vertes coûtent 0 gemme

        # Effets globaux liés aux pièces violetes
        self.bonus_next_boudoir_steps = 0
        self.bonus_next_walkin_gems = 0
        self.bonus_on_draft_bedroom = False

        # Effets globaux liés aux pièces oranges / bleues
        self.hallway_doors_unlocked = False
        self.next_room_color_choice = False

        # Redirecteur pour les effets de type "spread"
        self.redirect_spread_to_conference = None

        # Biais de rareté (Library)
        self.rarity_bias = 0

        # Tracking für gefundene permanente Objekte (wird von Game gesetzt)
        self.found_permanents = set()



        # Placement fixe du Hall d'entrée et de l'Antechamber
        # Placer de nouvelles instances fraîches (pas celles du catalogue supprimées)
        self.place_room(2, 8, EntranceHall())
        self.place_room(2, 0, Antechamber())

    # ---------------- utilitaires de grille ----------------
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
        
        # Remove the original room from room_catalog (not rotated copies)
        # Find the original room by name in the catalog
        for catalog_room in self.room_catalog[:]:  # Use slice to iterate over copy
            if catalog_room.name == room.name:
                self.room_catalog.remove(catalog_room)
                break

    def get_room_weight(self, room):
        """Poids = base_weight × (1/3)^rarity × bonus verts × bonus rareté."""
        w = room.base_weight * (1.0 / 3.0) ** room.rarity

        # Bonus Greenhouse
        if getattr(self, "green_draw_bonus", 0) > 0 and room.color == "green":
            w *= (1 + self.green_draw_bonus)

        # Bonus Library (pièces rarity >= 2)
        if getattr(self, "rarity_bias", 0) > 0 and room.rarity >= 2:
            w *= (1 + self.rarity_bias)

        return w



    # ---------------- tirage de pièces ----------------
    def draw_three_rooms(self, current_pos, direction, room_catalog):
        """
        Tire 3 pièces compatibles selon la position du joueur et la direction choisie.
        - Respecte les portes compatibles (avec rotation)
        - Évite les murs du manoir
        - Respecte les conditions de placement (edge, center, top, bottom)
        - Pas de doublons dans le tirage
        - Garantit au moins une pièce gratuite (gem_cost == 0)
        - Prend en compte certains effets globaux (Terrace, Greenhouse)
        """
        x, y = current_pos
        dx, dy = self.get_direction_offset(direction)
        nx, ny = x + dx, y + dy
        
        # Get all possible room rotations that match the required door
        required_door = self.opposite_direction[direction]
        possible_rooms = []
        
        for room in room_catalog:
            # Try all rotations of each room
            for rotated_room in room.get_all_rotations():
                if required_door in rotated_room.doors:
                    # Check placement condition on TARGET position (nx, ny)
                    cond = rotated_room.placement_condition
                    
                    if cond == "edge" and not (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                        continue
                    if cond == "center" and (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                        continue
                    if cond == "top" and ny != 0:
                        continue
                    if cond == "bottom" and ny != self.HEIGHT - 1:
                        continue
                    
                    # Check that no doors point outside the manor bounds
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
                    break  # Only add one rotation per room to avoid duplicates

        # Filtrer selon les conditions de placement
        filtered_rooms = []
        for room in possible_rooms:
            cond = room.placement_condition

            if cond == "edge" and not (x in (0, self.WIDTH - 1) or y in (0, self.HEIGHT - 1)):
                continue
            if cond == "center" and (x in (0, self.WIDTH - 1) or y in (0, self.HEIGHT - 1)):
                continue
            if cond == "top" and y != 0:
                continue
            if cond == "bottom" and y != self.HEIGHT - 1:
                continue

            filtered_rooms.append(room)

        # Si aucune pièce compatible, on propose la pioche complète
        if not filtered_rooms:
            filtered_rooms = self.pioche.copy()

        # Effet Terrace : toutes les pièces vertes deviennent gratuites
        if self.green_rooms_free:
            for r in filtered_rooms:
                if getattr(r, "color", "") == "green":
                    r.gem_cost = 0

        # Assurer au moins une pièce gratuite
        free_rooms = [r for r in filtered_rooms if r.gem_cost == 0]
        if not free_rooms:
            # Si vraiment aucune gratuite, on force la première à coûter 0
            # (choix arbitraire mais conforme à la règle du projet)
            filtered_rooms[0].gem_cost = 0
            free_rooms = [filtered_rooms[0]]

        # garantir une pièce gratuite
        choices = []
        first_pick = random.choice(free_rooms)
        choices.append(first_pick)

        # calcul des poids
        pool = [r for r in filtered_rooms if r not in choices]
        weights = [self.get_room_weight(r) for r in pool]

        # tirage des 2 autres rooms
        for _ in range(2):
            if not pool:
                break
            total_w = sum(weights)
            r = random.random() * total_w

            cum = 0
            idx = 0
            for i, w in enumerate(weights):
                cum += w
                if r <= cum:
                    idx = i
                    break

            # Ajouter la pièce tirée
            choices.append(pool[idx])

            # Retirer du pool
            del pool[idx]
            del weights[idx]


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

        # removed debug: listing compatible drawn rooms
        for r in choices:
            pass  # removed debug per-room listing

        
        return choices[:3]  # Return maximum 3 rooms
    
    def get_direction_offset(self, direction):
        """Retourne (dx, dy) pour une direction donnée."""
        if direction == "up":
            return (0, -1)
        elif direction == "down":
            return (0, 1)
        elif direction == "left":
            return (-1, 0)
        elif direction == "right":
            return (1, 0)
        return (0, 0)

    def get_possible_rooms(self, position, direction, room_catalog):
        """
        Retourne les pièces qui peuvent être placées dans la
        direction donnée depuis la position actuelle :
        - la case cible doit être vide
        - la pièce doit avoir une porte dans la direction opposée
        """
        x, y = position
        dx, dy = self.get_direction_offset(direction)
        nx, ny = x + dx, y + dy

        if not self.in_bounds(nx, ny) or self.get_room(nx, ny):
            return []

        required_door = self.opposite_direction[direction]
        return [r for r in room_catalog if required_door in getattr(r, "doors", [])]

    def can_advance(self):
        """
        Vérifie s'il reste au moins un déplacement possible
        (pour les conditions de fin de partie).
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