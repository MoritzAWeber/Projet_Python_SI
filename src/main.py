from blueprince.world import *

def main():
    manor = Manor()
    bedroom = Room("Bedroom", color="Green", rarity=1, gem_cost=2)
    manor.place_room(0, 0, bedroom)
    room = manor.get_room(0, 0)
    print(f"Placed room: {room.name}, Color: {room.color}, Cost: {room.gem_cost}")

if __name__ == "__main__":
    main()
