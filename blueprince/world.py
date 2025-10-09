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

    def __init__(self, name, color="Blue", rarity=0, gem_cost=0, doors=None):
        """
        Parameters:
            name (str): Name of the room (e.g., 'Bedroom', 'Chapel')
            color (str): Room color category (Blue, Green, etc.)
            rarity (int): 0 = common, up to 3 = rare
            gem_cost (int): Cost in gems to place this room
            doors (dict): Optional dict of directions to door data
        """
        self.name = name
        self.color = color
        self.rarity = rarity
        self.gem_cost = gem_cost
        self.doors = doors or {}

        def has_door(self, direction):
            """
                True if this room has a door in the given direction.
            """
            return direction in self.doors
        
