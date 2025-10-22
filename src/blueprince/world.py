from entities import Coffre, Casier, EndroitCreuser, Pomme, Banane 


# Classes representing the game environment
# Manor Class --> represents the 5x9 grid of rooms
class Manor:
    WIDTH = 5
    HEIGHT = 9

    def __init__(self):
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

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