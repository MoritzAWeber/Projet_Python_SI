from .entities import (
    Coffre, Casier, EndroitCreuser, Pomme, Banane, Gateau,
    Or, Gemmes, Cles, Des, Pelle, Marteau 
)

# Classes representing the game environment
# Manor Class --> represents the 5x9 grid of rooms
class Manor:
    WIDTH = 5
    HEIGHT = 9

    def __init__(self):
        """Initialise le manoir, la pioche, et place la pièce de départ."""
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]
        
        # --- AJOUT: INITIALISER LA PIOCHE ET LA PIÈCE DE DÉPART ---
        
        # 1. On copie le catalogue pour créer la pioche du jeu
        #    Note: ROOM_CATALOG est défini à la fin de ce fichier
        self.pioche = list(ROOM_CATALOG)
        
        # 2. On cherche la pièce de départ ("Entrance Hall")
        start_room = None
        for room in self.pioche:
            if room.name == "Entrance Hall":
                start_room = room
                break # On l'a trouvée
        
        # 3. On la place sur la grille et on la retire de la pioche
        if start_room:
            # Le joueur commence en [2, 8] (x=2, y=8)
            start_x, start_y = 2, 8 
            self.place_room(start_x, start_y, start_room)
            
            # Une pièce placée est retirée de la pioche (Section 2.3)
            self.pioche.remove(start_room)
            print(f"Pièce de départ '{start_room.name}' placée en ({start_x}, {start_y}).")
        else:
            # Sécurité au cas où on oublie de la mettre dans le catalogue
            print("ERREUR: 'Entrance Hall' non trouvé dans le ROOM_CATALOG !")

    def in_bounds(self, x, y):
        """Return True if (x, y) is inside the 5x9 grid."""
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        """Return the room at (x, y), or None."""
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        """Place a Room in the manor at (x, y)."""
        if not self.in_bounds(x, y):
            raise ValueError("Position out of bounds.")
        self.grid[y][x] = room


# Room Class --> represents a room in the manor

 # exemple

class Room:
    def __init__(self, name, image=None, doors=None, gem_cost=0,
                 objets=None, effet_special=None, rarity=0, placement_condition=None):
        self.name = name
        self.image = image
        self.doors = doors if doors is not None else []
        self.gem_cost = gem_cost
        self.objets = objets if objets is not None else []
        self.effet_special = effet_special
        self.rarity = rarity
        self.placement_condition = placement_condition

    def has_door(self, direction):
        return direction in self.doors

    def add_object(self, objet):
        """Ajoute un objet (Coffre, Pomme ...) dans la salle."""
        self.objets.append(objet)

    def remove_object(self, objet):
        if objet in self.objets:
            self.objets.remove(objet)

        
#   --------
#   Room templates
#   --------

ROOM_CATALOG = [
    
    # --- Pièce 001: Antechamber ---
    Room(
        name="Antechamber",
        image=None, 
        doors=["down"],
        gem_cost=0,
        objets=[],
        effet_special="fin_du_jeu",
        rarity=0,
        placement_condition="haut_du_manoir"
    ),
    
    # --- Pièce 002: Audience Chamber ---
    Room(
        name="Audience Chamber",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=1,
        objets=[],
        effet_special="reveal_adjacent_room_name",
        rarity=1
    ),
    
    # --- Pièce 003: Balcony ---
    Room(
        name="Balcony",
        image=None,
        doors=["down"],
        gem_cost=1,
        objets=[Gemmes()],
        effet_special=None,
        rarity=1,
        placement_condition="bordure"
    ),

    # --- Pièce 004: Ballroom ---
    Room(
        name="Ballroom",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=2,
        objets=[],
        effet_special="gain_5_steps_on_choose",
        rarity=2
    ),
    
    # --- Pièce 005: Belfry ---
    Room(
        name="Belfry",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=1,
        objets=[Cles()],
        effet_special=None,
        rarity=1
    ),
    
    # --- Pièce 006: Boudoir ---
    Room(
        name="Boudoir",
        image=None,
        doors=["left", "right"],
        gem_cost=1,
        objets=[Coffre()],
        effet_special=None,
        rarity=1
    ),
    
    # --- Pièce 007: Butler's Room ---
    Room(
        name="Butler's Room",
        image=None,
        doors=["up", "left", "right"],
        gem_cost=0,
        objets=[Pomme()],
        effet_special=None,
        rarity=0
    ),
    
    # --- Pièce 008: Cellar ---
    Room(
        name="Cellar",
        image=None,
        doors=["up", "right"],
        gem_cost=0,
        objets=[Pomme()],
        effet_special=None,
        rarity=0
    ),
    
    # --- Pièce 009: Chamber of Mirrors ---
    Room(
        name="Chamber of Mirrors",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=1,
        objets=[],
        effet_special="add_3_mirrored_room_to_deck",
        rarity=2
    ),
    
    # --- Pièce 010: Chapel ---
    Room(
        name="Chapel",
        image=None,
        doors=["up", "down"],
        gem_cost=1,
        objets=[Gemmes()],
        effet_special="gain_10_steps_on_enter",
        rarity=2
    ),
    
    # --- Pièce 011: Cloakroom ---
    Room(
        name="Cloakroom",
        image=None,
        doors=["up", "down"],
        gem_cost=0,
        objets=[Or()],
        effet_special=None,
        rarity=0
    ),
    
    # --- Pièce 012: Conference Room ---
    Room(
        name="Conference Room",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[],
        effet_special=None,
        rarity=0
    ),
    
    # --- Pièce 013: Entrance Hall ---
    Room(
        name="Entrance Hall",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[Pomme()],
        effet_special=None,
        rarity=0
    ),
    
    # --- Pièce 014: Furnace ---
    Room(
        name="Furnace",
        image=None,
        doors=["up", "down"],
        gem_cost=1,
        objets=[],
        effet_special="augmente_chance_pieces_rouges",
        rarity=1
    ),

    # --- Pièce 015: Gallery ---
    Room(
        name="Gallery",
        image=None,
        doors=["left", "right"],
        gem_cost=1,
        objets=[Or()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 016: Game Room ---
    Room(
        name="Game Room",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[Des()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 017: Garden ---
    Room(
        name="Garden",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=1,
        objets=[Gemmes(), EndroitCreuser()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 018: Greenhouse ---
    Room(
        name="Greenhouse",
        image=None,
        doors=["up", "down"],
        gem_cost=2,
        objets=[],
        effet_special="augmente_chance_pieces_vertes",
        rarity=2,
        placement_condition="bordure"
    ),

    # --- Pièce 019: Hall ---
    Room(
        name="Hall",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 020: Kitchen ---
    Room(
        name="Kitchen",
        image=None,
        doors=["up", "left"],
        gem_cost=0,
        objets=[Pomme()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 021: Laboratory ---
    Room(
        name="Laboratory",
        image=None,
        doors=["up", "down"],
        gem_cost=1,
        objets=[],
        effet_special="convertit_adjacent_en_salle_aleatoire",
        rarity=1
    ),

    # --- Pièce 022: Lavatory ---
    Room(
        name="Lavatory",
        image=None,
        doors=["up"],
        gem_cost=0,
        objets=[],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 023: Library ---
    Room(
        name="Library",
        image=None,
        doors=["up", "left", "right"],
        gem_cost=1,
        objets=[],
        effet_special="gagne_1_de_en_choisissant",
        rarity=1
    ),

    # --- Pièce 024: Living Room ---
    Room(
        name="Living Room",
        image=None,
        doors=["up", "down", "left"],
        gem_cost=0,
        objets=[Pomme()],
        effet_special=None,
        rarity=0
    ),
    # piece 025 : "Locker Room"
    Room(
        name="Locker Room",
        image=None,
        doors=["left", "right"],
        gem_cost=1,
        objets=[Casier(), Casier(), Casier()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 026: Maid's Chamber ---
    Room(
        name="Maid's Chamber",
        image=None,
        doors=["up", "right"],
        gem_cost=1,
        objets=[],
        effet_special="augmente_chance_trouver_objets",
        rarity=1
    ),

    # --- Pièce 027: Master Bedroom ---
    Room(
        name="Master Bedroom",
        image=None,
        doors=["up", "left", "right"],
        gem_cost=2,
        objets=[Coffre()],
        effet_special="gagne_10_pas_en_choisissant",
        rarity=2
    ),

    # --- Pièce 028: Office ---
    Room(
        name="Office",
        image=None,
        doors=["up", "right"],
        gem_cost=1,
        objets=[Cles()],
        effet_special="genere_20_or_salle_adjacente",
        rarity=1
    ),

    # --- Pièce 029: Pantry ---
    Room(
        name="Pantry",
        image=None,
        doors=["up", "right"],
        gem_cost=0,
        objets=[Banane()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 030: Patio ---
    Room(
        name="Patio",
        image=None,
        doors=["left", "right"],
        gem_cost=1,
        objets=[Gemmes()],
        effet_special="genere_2_gemmes_salles_adjacentes",
        rarity=1,
        placement_condition="bordure"
    ),

    # --- Pièce 031: Pool ---
    Room(
        name="Pool",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=1,
        objets=[],
        effet_special="ajoute_3_salles_humides_pioche",
        rarity=1
    ),

    # --- Pièce 032: Servant's Quarters ---
    Room(
        name="Servant's Quarters",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[Banane()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 033: Shed ---
    Room(
        name="Shed",
        image=None,
        doors=["up"],
        gem_cost=0,
        objets=[Pelle()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 034: Solarium ---
    Room(
        name="Solarium",
        image=None,
        doors=["up", "down"],
        gem_cost=2,
        objets=[],
        effet_special="augmente_chance_pieces_jaunes",
        rarity=2,
        placement_condition="bordure"
    ),

    # --- Pièce 035: Stairwell ---
    Room(
        name="Stairwell",
        image=None,
        doors=["up", "down"],
        gem_cost=0,
        objets=[],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 036: Storeroom ---
    Room(
        name="Storeroom",
        image=None,
        doors=["up", "left"],
        gem_cost=0,
        objets=[Cles()],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 037: Study ---
    Room(
        name="Study",
        image=None,
        doors=["up", "left"],
        gem_cost=1,
        objets=[Gemmes()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 038: Terrace ---
    Room(
        name="Terrace",
        image=None,
        doors=["up", "down"],
        gem_cost=1,
        objets=[Gemmes(), EndroitCreuser()],
        effet_special=None,
        rarity=1,
        placement_condition="bordure"
    ),

    # --- Pièce 039: Vault ---
    Room(
        name="Vault",
        image=None,
        doors=["down"],
        gem_cost=3,
        objets=[Or()],
        effet_special=None,
        rarity=3
    ),

    # --- Pièce 040: Veranda ---
    Room(
        name="Veranda",
        image=None,
        doors=["up", "down"],
        gem_cost=2,
        objets=[Gemmes(), EndroitCreuser()],
        effet_special="augmente_chance_pieces_vertes",
        rarity=2,
        placement_condition="bordure"
    ),

    # --- Pièce 041: Vestibule ---
    Room(
        name="Vestibule",
        image=None,
        doors=["up", "down", "left", "right"],
        gem_cost=0,
        objets=[],
        effet_special=None,
        rarity=0
    ),

    # --- Pièce 042: Weight Room ---
    Room(
        name="Weight Room",
        image=None,
        doors=["up", "down"],
        gem_cost=1,
        objets=[],
        effet_special="perd_5_pas_en_choisissant",
        rarity=1
    ),

    # --- Pièce 043: Wine Cellar ---
    Room(
        name="Wine Cellar",
        image=None,
        doors=["down", "right"],
        gem_cost=1,
        objets=[Gateau()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 044: Workshop ---
    Room(
        name="Workshop",
        image=None,
        doors=["up", "left", "right"],
        gem_cost=1,
        objets=[Marteau()],
        effet_special=None,
        rarity=1
    ),

    # --- Pièce 045: Den ---
    Room(
        name="Den",
        image=None,
        doors=["up", "down", "right"],
        gem_cost=1,
        objets=[Gemmes()],
        effet_special=None,
        rarity=1
    )
] # --- FIN DE LA LISTE ROOM_CATALOG ---