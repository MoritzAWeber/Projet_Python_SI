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
    """Mixin for yellow rooms providing shop functionality.
    
    Yellow rooms allow players to purchase items with gold.
    Shop menu is opened via M key when in yellow room.
    """

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
        """Prepare shop menu when entering yellow room.
        
        Parameters:
        - player: Player instance with game reference
        
        Side effects:
        - Calls game.open_shop_menu to initialize items
        - Shows message prompting player to press M
        """
        # Ne plus ouvrir automatiquement le menu du shop; uniquement préparer via appel existant.
        if hasattr(player, "game"):
            try:
                player.game.open_shop_menu(self)  # prépare les items sans activation
                player.add_message("Magasin disponible: appuyez sur M pour ouvrir.")
            except Exception:
                pass



class Room(ABC):
    """Abstract base class for all manor rooms.
    
    Handles room properties, door connections, item generation,
    rotation mechanics, and room-specific effects.
    """
    def __init__(self, name, image=None, doors=None, gem_cost=0, item_pool=None,
                 objets=None, rarity=0, placement_condition="any",
                 color="blue", base_weight=1.0):
        """Initialize room with properties and configuration.
        
        Parameters:
        - name: str, internal room identifier
        - image: pygame.Surface, room background sprite
        - doors: list[str], available directions ["up", "down", "left", "right"]
        - gem_cost: int, gems required to draft this room (default 0)
        - item_pool: list[Objet], candidate items for loot generation
        - objets: list[Objet], items currently in room
        - rarity: int, 0=common, 1-3=increasingly rare
        - placement_condition: str, "any"/"edge"/"center"/"top"/"bottom"
        - color: str, room type: "blue"/"green"/"purple"/"yellow"/"orange"/"red"
        - base_weight: float, base probability multiplier for room draws
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
        """Check if room has door in specified direction.
        
        Parameters:
        - direction: str, one of "up", "down", "left", "right"
        
        Returns:
        - bool: True if door exists
        """
        return direction in self.doors
    

    def generate_loot_on_enter(self, player):
        """Generate loot with player luck modifiers on first room entry.
        
        Parameters:
        - player: Player instance for luck modifiers
        
        Effects:
        - Calls generate_random_loot with player luck bonuses
        - Extends self.objets with generated items
        - Sets loot_generated flag to prevent regeneration
        """
        if not self.loot_generated and self.item_pool:
            manor = getattr(player, "manor", None)
            found_perms = getattr(manor, 'found_permanents', set()) if manor else set()
            loot = generate_random_loot(player, self.item_pool, found_permanents=found_perms)
            self.objets.extend(loot)
            self.loot_generated = True

    def create_rotated_copy(self, num_rotations):
        """Creates a copy of this room rotated by num_rotations * 90 degrees.
        
        Parameters:
        - num_rotations: int, number of 90-degree clockwise rotations (0-3)
        
        Returns:
        - Room: new instance with rotated doors and image
        
        Door rotation mapping:
        - up → right → down → left → up
        """
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
        """Returns a list of all possible rotations of this room.
        
        Returns:
        - list[Room]: 4 versions (0°, 90°, 180°, 270°)
        """
        return [self.create_rotated_copy(i) for i in range(4)]

    def apply_effect_on_choose(self, player):
        """Effect triggered when room is chosen during draft.
        
        Parameters:
        - player: Player instance
        
        Note: Override in subclasses for rooms with draft-time effects.
        """
        pass

    def apply_effect_on_enter(self, player):
        """Effect triggered when player enters room.
        
        Parameters:
        - player: Player instance
        
        Default behavior: Generate loot on first entry.
        Override in subclasses for additional room-specific effects.
        """
        self.generate_loot_on_enter(player)


# ==============================
# Pièces fixes : début / fin
# ==============================
class EntranceHall(Room):
    """Starting room at bottom of manor (Y=8).
    
    Fixed placement, always present at game start.
    Doors: up, left, right.
    """
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
    """Victory room at top of manor (Y=0).
    
    Fixed placement, reaching this room wins the game.
    Doors: down, left, right.
    """
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
    """Green room that increases draft bonus for green rooms (repeatable).
    
    Effect: Increments manor.green_draw_bonus by 1 on each entry.
    This multiplier increases weight of green rooms in future drafts.
    
    Rarity: 1 (uncommon)
    Placement: Edge only
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
    """Green room that grants +2 gems (one-time effect).
    
    Rarity: 1 (uncommon)
    Placement: Edge only
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
    """Green room that spreads fruit items throughout manor (one-time effect).
    
    Effect: 20% chance per room to receive Pomme or Banane.
    Redirected to ConferenceRoom if that redirect is active.
    
    Rarity: 2 (rare)
    Placement: Edge only
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
    """Green room that activates green item bonus flag (one-time effect).
    
    Effect: Sets manor.green_item_bonus to True.
    
    Rarity: 1 (uncommon)
    Placement: Edge only
    Cost: 2 gems
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
    """Green crossroads room with 4 doors.
    
    Rarity: 1 (uncommon)
    Placement: Center only
    Cost: 3 gems
    """
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
    """Green room with 3 doors and dig spots.
    
    Rarity: 1 (uncommon)
    Placement: Center only
    """
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
    """Green room that adds +1 gem to all green rooms (one-time effect).
    
    Effect: Appends Gemmes(1) to objets of every green room in manor.
    
    Rarity: 2 (rare)
    Placement: Edge only
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
    """Green room that makes all green rooms free (one-time effect).
    
    Effect: Sets manor.green_rooms_free flag, zeroing gem_cost for green rooms.
    
    Rarity: 1 (uncommon)
    Placement: Edge only
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
    """Purple room that activates bonuses for Boudoir and WalkInCloset (one-time).
    
    Effect:
    - Sets manor.bonus_next_boudoir_steps to 10
    - Sets manor.bonus_next_walkin_gems to 3
    
    Rarity: 2 (rare)
    Placement: Any
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
    """Purple room granting steps equal to number of placed rooms (repeatable).
    
    Effect: Grants +1 step per room in manor on each entry.
    
    Rarity: 2 (rare)
    Placement: Any
    Cost: 2 gems
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
    """Purple room that grants +5 steps when drafting bedrooms (one-time flag).
    
    Effect: Sets manor.bonus_on_draft_bedroom flag.
    Bedroom, BunkRoom, and GuestBedroom grant +5 steps when chosen.
    
    Rarity: 1 (uncommon)
    Placement: Any
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
    """Purple room granting keys based on bedrooms in manor (repeatable).
    
    Effect: +1 key per Bedroom, +2 keys per BunkRoom.
    
    Rarity: 1 (uncommon)
    Placement: Any
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
    """Common purple room granting +2 steps (repeatable).
    
    Rarity: 0 (common)
    Placement: Any
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
    """Purple room that consumes HerLadyshipsChamber bonus for extra steps.
    
    Effect: If manor.bonus_next_boudoir_steps > 0, grant that many steps
    and reset bonus to 0.
    
    Rarity: 1 (uncommon)
    Placement: Any
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
    """Purple bedroom with gold and dice.
    
    Rarity: 2 (rare)
    Placement: Any
    """
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
    """Purple room granting +10 steps (one-time effect).
    
    Rarity: 1 (uncommon)
    Placement: Any
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
    """Build fresh room catalog for a new game.
    
    Returns:
    - list[Room]: Complete set of room instances
    
    Creates new instances to avoid state mutation between runs.
    Includes duplicates for common rooms to adjust draw probabilities
    and to be able to draw rooms multiple times.
    """
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
    """Represents the 5x9 manor grid and manages room placement and drafting.
    
    Handles:
    - Room placement with door compatibility
    - Room draft mechanics with rotation and filtering
    - Global effect flags (green bonuses, bedroom bonuses, etc.)
    - Weight calculations for room draw probabilities
    """
    WIDTH = 5
    HEIGHT = 9

    opposite_direction = {
        "up": "down",
        "down": "up",
        "right": "left",
        "left": "right"
    }

    def __init__(self):
        """Initialize manor with empty grid and fresh room catalog.
        
        Sets up:
        - 5x9 grid initialized to None
        - Fresh room catalog (excluding EntranceHall and Antechamber)
        - Global effect flags for room bonuses
        - Fixed placement of EntranceHall (2, 8) and Antechamber (2, 0)
        """
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
        """Check if coordinates are within manor grid.
        
        Parameters:
        - x: int, column (0-4)
        - y: int, row (0-8)
        
        Returns:
        - bool: True if valid position
        """
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        """Get room at specified grid position.
        
        Parameters:
        - x: int, column
        - y: int, row
        
        Returns:
        - Room or None: room instance if present
        """
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        """Place room at grid position and remove from catalog.
        
        Parameters:
        - x: int, column
        - y: int, row
        - room: Room instance to place
        
        Side effects:
        - Sets grid[y][x] to room
        - Removes original room from room_catalog by name
        
        Raises:
        - ValueError: if position out of bounds
        """
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
        """Calculate weighted probability for room draw.
        
        Parameters:
        - room: Room instance
        
        Returns:
        - float: weight = base_weight × (1/3)^rarity × bonuses
        
        Bonuses:
        - Greenhouse: green rooms get (1 + green_draw_bonus) multiplier
        - Library: rarity ≥ 2 rooms get (1 + rarity_bias) multiplier
        """
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
        """Draw 3 compatible rooms for placement at target position.
        
        Parameters:
        - current_pos: tuple[int, int], player's (x, y) position
        - direction: str, direction player is opening ("up"/"down"/"left"/"right")
        - room_catalog: list[Room], available rooms
        
        Returns:
        - list[Room]: up to 3 room instances (may include rotations)
        
        Filtering rules:
        - Rooms must have compatible door (opposite of direction)
        - All room doors must point within manor bounds
        - Respects placement_condition (edge/center/top/bottom)
        - No duplicate room names in draw
        - Guarantees at least one free room (gem_cost == 0)
        
        Weight modifiers:
        - Terrace effect: green rooms become free
        - Greenhouse effect: green rooms weighted higher
        - Library effect: rare rooms weighted higher
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
        """Convert direction string to grid offset.
        
        Parameters:
        - direction: str, one of "up"/"down"/"left"/"right"
        
        Returns:
        - tuple[int, int]: (dx, dy) offset
        """
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
        """Get rooms that can be placed in specified direction.
        
        Parameters:
        - position: tuple[int, int], current (x, y)
        - direction: str, movement direction
        - room_catalog: list[Room], available rooms
        
        Returns:
        - list[Room]: rooms with compatible opposite door
        
        Requirements:
        - Target cell must be empty and in bounds
        - Room must have door in opposite direction
        """
        x, y = position
        dx, dy = self.get_direction_offset(direction)
        nx, ny = x + dx, y + dy

        if not self.in_bounds(nx, ny) or self.get_room(nx, ny):
            return []

        required_door = self.opposite_direction[direction]
        return [r for r in room_catalog if required_door in getattr(r, "doors", [])]

    def can_advance(self):
        """Check if any movement is possible (for game over condition).
        
        Returns:
        - bool: True if at least one room can be placed from any current room
        
        Scans all placed rooms (except Antechamber) for available expansions.
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