# all the entities who will be populating the game

class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = Inventory()
        self.position = [2, 8]  # Starting position

    def move(self, direction, manor):
        x, y = self.position
        directions = {"up": [0, -1], "down": [0, 1], "left": [-1, 0], "right": [1, 0]}

        if direction.lower() in directions:
            x += directions[direction][0]
            y += directions[direction][1]
        else:
            print("invalid entry")

        if manor.in_bounds(x, y):
            print(f"{self.name} moves to ({x}, {y})")
            self.position = [x, y]
        else:
            print("You can't go out of bounds.")

    def pick_up(self, item):
        pass

    def use_item(self, item):
        pass


class Inventory:
    pass


class PermanentItem:
    def __init__(self, name):
        self.name = name

    def on_pickup(self):
        pass

    def on_use(self):
        pass