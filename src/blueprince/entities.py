# all the entities who will be populating the game

class Player:
    def __init__(self, name):
        self.inventory = Inventory()
        self.position = [0, 0]  # Starting position

    def move(self, direction, manor):
        directions = {"up": [0, -1], "down": [0, 1], "left": [-1, 0], "right": [1, 0]}
        if direction.lower() in directions:
            self.position[0] += directions[direction][0]
            self.position[1] += directions[direction][1]
        else:
            print("invalid entry")


class Inventory:
    pass