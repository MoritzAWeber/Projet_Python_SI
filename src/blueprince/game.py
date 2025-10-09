from blueprince.world import Manor
from blueprince.entities import Player


class Game:
    def __init__(self):
        self.manor = Manor()
        self.player = Player("Alice")

    def run(self):
        print("Game started! Your position is (0, 0).")
        print("Commands: up / down / left / right / quit")

        while True:
            print(f"Current position: {self.player.position}")
            cmd = input("where do you want to go? >> ")

            if cmd == "quit":
                print("Game stopped.")
                break

            self.player.move(cmd, self.manor)