# all the entities who will be populating the game

class Player:
    def __init__(self, name):
        self.inventory = Inventory()
        self.position = [0, 0]  # Starting position


class Inventory:
    pass