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

class Room:

    def __init__(self, name, image = None, doors = None, gem_cost=0,
                 objets = None, effet_special = None, rarity=0, placement_condition = None):
        """
        :param name:
        :param image:
        :param doors:
        :param gem_cost:
        :param objets:
        :param effet_special:
        :param rarity:
        :param placement_condition:
        """
        self.name = name

    def has_door(self, direction):
        """
            True if this room has a door in the given direction.
        """
        return direction in self.doors
        
#   --------
#   Room templates
#   --------

