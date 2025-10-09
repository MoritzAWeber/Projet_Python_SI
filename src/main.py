from blueprince.world import *
from blueprince.entities import *


def main():
    manor = Manor()
    player = Player("Alice")

    print("Game started! Your position is (0, 0).")
    print("Commands: up / down / left / right / quit")

    while True:
        print(f"Current position: {player.position}")
        cmd = input("where do you want to go? >> ")

        if cmd == "quit":
            print("Game stopped.")
            break

        player.move(cmd, manor)


if __name__ == "__main__":
    main()
