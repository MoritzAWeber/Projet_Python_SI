import pygame
import random
from abc import ABC, abstractmethod

from .entities import (
    Pomme, Banane, Or, Gemmes, Cles, Des, Pelle, Marteau, EndroitCreuser
)


# ==============================
# Classe abstraite Room
# ==============================
class Room(ABC):
    def __init__(self, name, image=None, doors=None, gem_cost=0,
                 objets=None, rarity=0, placement_condition="any",
                 color="blue", base_weight=1.0):
        """
        name : nom interne de la pièce
        image : surface pygame (image de la pièce)
        doors : liste de directions accessibles ["up","down","left","right"]
        gem_cost : coût en gemmes pour tirer cette pièce
        objets : liste d'objets présents dans la pièce
        rarity : niveau de rareté (0=commun, 3=très rare)
        placement_condition : "any", "edge", "center", "top", "bottom"
        color : "blue", "green", "purple", "yellow", "orange", "red"
        """
        self.base_weight = base_weight
        self.name = name
        self.image = image
        self.doors = doors if doors else []
        self.original_doors = self.doors.copy()  # Store original door configuration
        self.gem_cost = gem_cost
        self.objets = objets if objets else []
        self.rarity = rarity
        self.placement_condition = placement_condition
        self.color = color
        self.rotation = 0  # Track current rotation (0, 90, 180, 270)

    def has_door(self, direction):
        return direction in self.doors

    def create_rotated_copy(self, num_rotations):
        """Effect:
        Creates a rotated logical copy preserving the subclass. Performs a
        clockwise rotation num_rotations * 90° of doors and image. Returns self
        unchanged if num_rotations == 0. Each rotated copy gets its own objets
        list (shallow copy) and rotation angle.

        Parameters:
        - num_rotations (int): Number of clockwise quarter turns (0–3).

        Returns:
        - Room: New instance of the same subclass with rotated doors/image.
        """
        if num_rotations == 0:
            return self
        rotated_doors = self.original_doors.copy()
        for _ in range(num_rotations):
            rotation_map = {"up": "right", "right": "down", "down": "left", "left": "up"}
            rotated_doors = [rotation_map[d] for d in rotated_doors]

        rotated_image = pygame.transform.rotate(self.image, -90 * num_rotations) if self.image else None

        # Instantiate without calling subclass __init__ to be able to set fields manually
        rotated = self.__class__.__new__(self.__class__)
        # Copy scalar & mutable attributes
        rotated.name = self.name
        rotated.image = rotated_image
        rotated.doors = rotated_doors
        rotated.original_doors = self.original_doors.copy()
        rotated.gem_cost = self.gem_cost
        rotated.objets = self.objets.copy()
        rotated.rarity = self.rarity
        rotated.placement_condition = self.placement_condition
        rotated.rotation = (num_rotations * 90) % 360
        return rotated
    
    def get_all_rotations(self):
        """Returns a list of all possible rotations of this room."""
        return [self.create_rotated_copy(i) for i in range(4)]

    def apply_effect_on_choose(self, player):
        """Effet éventuel déclenché au moment où la pièce est choisie dans le tirage."""
        pass

    def apply_effect_on_enter(self, player):
        pass


# ==============================
# Pièces fixes : début / fin
# ==============================
class EntranceHall(Room):
    def __init__(self):
        super().__init__(
            name="EntranceHall",
            image=pygame.image.load("assets/rooms/Blue/Entrance_Hall.png"),
            doors=["up", "left", "right"],
            placement_condition="bottom",
            color="blue",
            objets=[]
        )


class Antechamber(Room):
    def __init__(self):
        super().__init__(
            name="Antechamber",
            image=pygame.image.load("assets/rooms/Blue/Antechamber.png"),
            doors=["down"],
            placement_condition="top",
            color="blue"
        )


# ==============================
# GREEN ROOMS (pièces vertes)
# ==============================

class Greenhouse(Room):
    """
    Greenhouse : dans le jeu original, augmente la probabilité
    de tirer des pièces vertes.
    Ici : on met en place un bonus global dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="Greenhouse",
            image=pygame.image.load("assets/rooms/Green/Greenhouse.png"),
            doors=["down"],
            objets=[Gemmes(1)],
            rarity=1,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        if not hasattr(manor, "green_draw_bonus"):
            manor.green_draw_bonus = 0
        manor.green_draw_bonus += 1
        print("Greenhouse : bonus de tirage de pièces vertes augmenté.")


class MorningRoom(Room):
    """
    Morning Room : donne des gemmes.
    Version simple : +2 gemmes à l'entrée.
    """
    def __init__(self):
        super().__init__(
            name="Morning Room",
            image=pygame.image.load("assets/rooms/Green/Morning_Room.png"),
            doors=["down", "left"],
            rarity=1,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        player.gemmes += 2
        print("Morning Room : vous gagnez 2 gemmes.")


class SecretGarden(Room):
    """
    Secret Garden : disperse des fruits (Pomme, Banane) dans
    plusieurs autres pièces déjà placées dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="SecretGarden",
            image=pygame.image.load("assets/rooms/Green/Secret_Garden.png"),
            doors=["left", "right", "down"],
            objets=[Gemmes(1)],
            rarity=2,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        fruits = [Pomme(), Banane()]
        target_conf = getattr(manor, "redirect_spread_to_conference", None)

        if target_conf is not None:
            print("Secret Garden : les fruits sont redirigés vers la Conference Room.")
            for _ in range(manor.WIDTH * manor.HEIGHT):
                if random.random() < 0.20:
                    target_conf.objets.append(random.choice(fruits))
        else:
            print("Secret Garden : ajout de fruits dans plusieurs pièces existantes.")
            for y in range(manor.HEIGHT):
                for x in range(manor.WIDTH):
                    room = manor.get_room(x, y)
                    if room and room is not self:
                        if random.random() < 0.20:
                            room.objets.append(random.choice(fruits))



class Veranda(Room):
    """
    Veranda : augmente les chances de trouver des objets
    dans les futures pièces vertes.
    Ici : on active un flag global dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="Veranda",
            image=pygame.image.load("assets/rooms/Green/Veranda.png"),
            doors=["up", "down"],
            gem_cost=2,
            rarity=1,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        manor.green_item_bonus = True
        print("Veranda : bonus d'objets dans les futures pièces vertes activé.")


class Cloister(Room):
    """
    Cloister : pas d'effet particulier, seulement une pièce verte.
    """
    def __init__(self):
        super().__init__(
            name="Cloister",
            image=pygame.image.load("assets/rooms/Green/Cloister.png"),
            doors=["left", "right", "up", "down"],
            gem_cost=3,
            rarity=1,
            placement_condition="center",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        # Aucun effet pour cette pièce
        pass


class Courtyard(Room):
    """
    Courtyard : pas d'effet particulier, pièce verte neutre.
    """
    def __init__(self):
        super().__init__(
            name="Courtyard",
            image=pygame.image.load("assets/rooms/Green/Courtyard.png"),
            doors=["left", "right", "down"],
            rarity=1,
            placement_condition="center",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        # Aucun effet pour cette pièce
        pass


class Patio(Room):
    """
    Patio : ajoute des gemmes dans chaque pièce verte déjà
    existante sur le manoir.
    """
    def __init__(self):
        super().__init__(
            name="Patio",
            image=pygame.image.load("assets/rooms/Green/Patio.png"),
            doors=["left", "down"],
            rarity=2,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        print("Patio : ajout d'une gemme dans chaque pièce verte déjà placée.")
        for y in range(manor.HEIGHT):
            for x in range(manor.WIDTH):
                room = manor.get_room(x, y)
                if room and getattr(room, "color", "") == "green":
                    room.objets.append(Gemmes(1))


class Terrace(Room):
    """
    Terrace : les pièces vertes deviennent gratuites à tirer.
    Ici : on active un flag dans le manoir, et draw_three_rooms
    met gem_cost = 0 pour toutes les pièces vertes.
    """
    def __init__(self):
        super().__init__(
            name="Terrace",
            image=pygame.image.load("assets/rooms/Green/Terrace.png"),
            doors=["down"],
            rarity=1,
            placement_condition="edge",
            color="green"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return
        manor.green_rooms_free = True
        print("Terrace : toutes les pièces vertes deviennent gratuites à tirer.")


# ==============================
# --- PURPLE ROOMS (chambres) ---
# ==============================

class HerLadyshipsChamber(Room):
    """
    Effets :
    - Le prochain passage dans Boudoir donne +10 pas
    - Le prochain passage dans Walk-in Closet donne +3 gemmes
    Effets à usage unique.
    """
    def __init__(self):
        super().__init__(
            name="HerLadyshipsChamber",
            image=pygame.image.load("assets/rooms/Purple/Her_Ladyships_Chamber.png"),
            doors=["down"],
            rarity=2,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor

        # Activer deux bonus one-shot
        manor.bonus_next_boudoir_steps = 10
        manor.bonus_next_walkin_gems = 3

        print("Her Ladyship’s Chamber : prochain Boudoir = +10 pas, prochain Walk-in Closet = +3 gemmes.")


class MasterBedroom(Room):
    """
    Effet :
    - Quand on entre : +1 pas pour chaque pièce déjà placée dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="MasterBedroom",
            image=pygame.image.load("assets/rooms/Purple/Master_Bedroom.png"),
            doors=["down"],
            gem_cost=2,
            rarity=2,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor

        # Compter les pièces placées (sauf None)
        count = sum(1 for y in range(manor.HEIGHT) for x in range(manor.WIDTH) if manor.get_room(x, y))

        player.gagner_pas(count)
        print(f"Master Bedroom : +{count} pas (nombre total de pièces placées).")


class Nursery(Room):
    """
    Effet :
    - À chaque fois que vous draft une pièce Bedroom : +5 pas
    Bonus persistant.
    """
    def __init__(self):
        super().__init__(
            name="Nursery",
            image=pygame.image.load("assets/rooms/Purple/Nursery.png"),
            doors=["down"],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        player.manor.bonus_on_draft_bedroom = True
        print("Nursery : désormais, chaque draft d'une Bedroom donne +5 pas.")


class ServantsQuarters(Room):
    """
    Effet :
    - À l'entrée : +1 clé pour chaque Bedroom dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="ServantsQuarters",
            image=pygame.image.load("assets/rooms/Purple/Servants_Quarters.png"),
            doors=["down"],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor

        # Compter les pièces Bedroom et Bunk Room (qui compte comme 2)
        count = 0
        for y in range(manor.HEIGHT):
            for x in range(manor.WIDTH):
                room = manor.get_room(x, y)
                if not room:
                    continue
                if room.name == "Bedroom":
                    count += 1
                elif room.name == "BunkRoom":
                    count += 2  # Compte double

        player.cles += count
        print(f"Servant’s Quarters : +{count} clés (nombre total de Bedrooms).")


class Bedroom(Room):
    """
    Effet :
    - Chaque fois qu'on entre dans cette pièce : +2 pas
    """
    def __init__(self):
        super().__init__(
            name="Bedroom",
            image=pygame.image.load("assets/rooms/Purple/Bedroom.png"),
            doors=["left", "down"],
            rarity=0,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        player.gagner_pas(2)
        print("Bedroom : +2 pas.")


class Boudoir(Room):
    """
    Effet : aucun par défaut.
    Mais si Her Ladyship’s Chamber a activé un bonus :
    - +10 pas la prochaine fois
    """
    def __init__(self):
        super().__init__(
            name="Boudoir",
            image=pygame.image.load("assets/rooms/Purple/Boudoir.png"),
            doors=["down", "left"],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor
        # Bonus one-shot depuis Ladyship
        if getattr(manor, "bonus_next_boudoir_steps", 0) > 0:
            bonus = manor.bonus_next_boudoir_steps
            player.gagner_pas(bonus)
            manor.bonus_next_boudoir_steps = 0
            print(f"Boudoir : bonus spécial +{bonus} pas consommé.")


class BunkRoom(Room):
    """
    Effet :
    - Cette pièce compte comme 2 Bedrooms
    Effet géré par les autres pièces (Servant’s Quarters, Nursery).
    """
    def __init__(self):
        super().__init__(
            name="BunkRoom",
            image=pygame.image.load("assets/rooms/Purple/Bunk_Room.png"),
            doors=["down"],
            rarity=2,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        # Aucun effet direct
        print("Bunk Room : compte comme 2 Bedrooms.")


class GuestBedroom(Room):
    """
    Effet :
    - À l'entrée : +10 pas
    """
    def __init__(self):
        super().__init__(
            name="GuestBedroom",
            image=pygame.image.load("assets/rooms/Purple/GuestBedroom.png"),
            doors=["down"],
            rarity=1,
            placement_condition="any",
            color="purple"
        )

    def apply_effect_on_enter(self, player):
        player.gagner_pas(10)
        print("Guest Bedroom : +10 pas.")


# ==============================
# ORANGE ROOMS (Hallways)
# ==============================

class Corridor(Room):
    """
    Corridor : toujours non verrouillé.
    Dans ta version : aucun système de portes verrouillées,
    donc effet passif neutre.
    """
    def __init__(self):
        super().__init__(
            name="Corridor",
            image=pygame.image.load("assets/rooms/Orange/Corridor.png"),
            doors=["up", "down"],
            rarity=0,
            placement_condition="any",
            color="orange"
        )

    def apply_effect_on_enter(self, player):
        # Aucun effet actif dans ta version actuelle
        print("Corridor : portes toujours considérées ouvertes.")


class EastWingHall(Room):
    def __init__(self):
        super().__init__(
            name="EastWingHall",
            image=pygame.image.load("assets/rooms/Orange/East_Wing_Hall.png"),
            doors=["left", "right", "down"],
            rarity=1,
            placement_condition="any",
            color="orange"
        )


class WestWingHall(Room):
    def __init__(self):
        super().__init__(
            name="WestWingHall",
            image=pygame.image.load("assets/rooms/Orange/West_Wing_Hall.png"),
            doors=["left", "right", "down"],
            rarity=1,
            placement_condition="any",
            color="orange"
        )


class Hallway(Room):
    def __init__(self):
        super().__init__(
            name="Hallway",
            image=pygame.image.load("assets/rooms/Orange/Hallway.png"),
            doors=["left", "right", "down"],
            rarity=0,
            placement_condition="any",
            color="orange"
        )


class Passageway(Room):
    def __init__(self):
        super().__init__(
            name="Passageway",
            image=pygame.image.load("assets/rooms/Orange/Passageway.png"),
            doors=["left", "right", "up", "down"],
            rarity=0,
            placement_condition="any",
            color="orange"
        )


class GreatHall(Room):
    """
    Great Hall : "7 locked doors" dans le vrai jeu.
    Pour l’instant : pièce orange normale.
    """
    def __init__(self):
        super().__init__(
            name="GreatHall",
            image=pygame.image.load("assets/rooms/Orange/Great_Hall.png"),
            doors=["left", "right", "up", "down"],
            rarity=2,
            placement_condition="any",
            color="orange"
        )


class Foyer(Room):
    """
    Foyer : Les portes de Hallways sont toujours déverrouillées.
    """
    def __init__(self):
        super().__init__(
            name="Foyer",
            image=pygame.image.load("assets/rooms/Orange/Foyer.png"),
            doors=["up", "down"],
            gem_cost=2,
            rarity=2,
            placement_condition="any",
            color="orange"
        )

    def apply_effect_on_enter(self, player):
        player.manor.hallway_doors_unlocked = True
        print("Foyer : toutes les portes de Hallway sont déverrouillées.")


class SecretPassage(Room):
    """
    Secret Passage :
    - Permet de choisir la prochaine couleur de pièce à tirer.
    On active un flag dans le manoir, géré plus tard.
    """
    def __init__(self):
        super().__init__(
            name="SecretPassage",
            image=pygame.image.load("assets/rooms/Orange/Secret_Passage.png"),
            doors=["down"],
            rarity=3,
            placement_condition="any",
            color="orange"
        )

    def apply_effect_on_enter(self, player):
        player.manor.next_room_color_choice = True
        print("Secret Passage : vous pourrez choisir la couleur du prochain tirage.")


# ==============================
# BLUE ROOMS
# ==============================

class LockerRoom(Room):
    """
    Locker Room :
    Effet : "Spread keys throughout the house."
    -> Répartit des clés dans plusieurs pièces.
    -> Si ConferenceRoom a été visitée, toutes ces clés vont
       dans cette ConferenceRoom (redirection globale).
    """
    def __init__(self):
        super().__init__(
            name="LockerRoom",
            image=pygame.image.load("assets/rooms/Blue/Locker_Room.png"),
            doors=["up", "down"],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        manor = getattr(player, "manor", None)
        if manor is None:
            return

        target_conf = getattr(manor, "redirect_spread_to_conference", None)

        if target_conf is not None:
            print("Locker Room : les clés sont redirigées vers la Conference Room.")
            # On simule une "répartition" en ajoutant plusieurs clés dans la Conference Room
            for _ in range(manor.WIDTH * manor.HEIGHT):
                if random.random() < 0.20:
                    target_conf.objets.append(Cles(1))
        else:
            print("Locker Room : répartition de clés dans plusieurs pièces.")
            for y in range(manor.HEIGHT):
                for x in range(manor.WIDTH):
                    room = manor.get_room(x, y)
                    if room and room is not self:
                        if random.random() < 0.20:
                            room.objets.append(Cles(1))


class Vault(Room):
    """
    Vault :
    Effet : "+40 coins" lorsqu'on entre dans la salle.
    """
    def __init__(self):
        super().__init__(
            name="Vault",
            image=pygame.image.load("assets/rooms/Blue/Vault.png"),
            doors=["down"],  # cul-de-sac
            gem_cost=3,
            rarity=3,
            placement_condition="edge",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.or_ += 40
        print("Vault : vous gagnez 40 pièces d'or.")


class Workshop(Room):
    """
    Workshop :
    Effet simplifié : donne un objet permanent aléatoire au joueur.
    """
    def __init__(self):
        super().__init__(
            name="Workshop",
            image=pygame.image.load("assets/rooms/Blue/Workshop.png"),
            doors=["up", "down"],
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        permanents = [Pelle(), Marteau()]
        item = random.choice(permanents)
        player.inventory.add_item(item)
        print(f"Workshop : vous obtenez un objet permanent ({item.nom}).")


class BoilerRoom(Room):
    """
    Boiler Room :
    Effet simplifié : source d'énergie -> +3 pas.
    """
    def __init__(self):
        super().__init__(
            name="BoilerRoom",
            image=pygame.image.load("assets/rooms/Blue/Boiler_Room.png"),
            doors=["left", "down", "right"],
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.gagner_pas(3)
        print("Boiler Room : +3 pas.")


class ConferenceRoom(Room):
    """
    Conference Room :
    Effet : "Whenever items would be spread throughout the house,
             they are placed in this room instead."
    -> Active un pointeur global dans le manoir pour rediriger
       tous les effets de type 'spread' (SecretGarden, LockerRoom).
    """
    def __init__(self):
        super().__init__(
            name="ConferenceRoom",
            image=pygame.image.load("assets/rooms/Blue/Conference_Room.png"),
            doors=["down", "left", "right"],
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor
        manor.redirect_spread_to_conference = self
        print("Conference Room : tous les futurs effets 'spread' seront redirigés ici.")


class Gallery(Room):
    """
    Gallery :
    Effet simplifié : +1 gemme à l'entrée.
    """
    def __init__(self):
        super().__init__(
            name="Gallery",
            image=pygame.image.load("assets/rooms/Blue/Gallery.png"),
            doors=["up", "down"],
            rarity=1,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.gemmes += 1
        print("Gallery : vous gagnez 1 gemme.")


class Garage(Room):
    """
    Garage :
    Effet : +3 clés.
    """
    def __init__(self):
        super().__init__(
            name="Garage",
            image=pygame.image.load("assets/rooms/Blue/Garage.png"),
            doors=["down"],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.cles += 3
        print("Garage : vous gagnez 3 clés.")


class Library(Room):
    """
    Library :
    Effet : "Discover less common floor plans while drafting"
    -> augmente un biais de rareté dans le manoir.
    """
    def __init__(self):
        super().__init__(
            name="Library",
            image=pygame.image.load("assets/rooms/Blue/Library.png"),
            doors=["left", "down"],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        manor = player.manor
        manor.rarity_bias += 1
        print("Library : biais de rareté augmenté (tirage de pièces rares favorisé).")


class RumpusRoom(Room):
    """
    Rumpus Room :
    Effet : +8 pièces.
    """
    def __init__(self):
        super().__init__(
            name="RumpusRoom",
            image=pygame.image.load("assets/rooms/Blue/Rumpus_Room.png"),
            doors=["up", "down"],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.or_ += 8
        print("Rumpus Room : +8 pièces d'or.")


class Pantry(Room):
    """
    Pantry (version bleue) :
    Effet : +4 pièces.
    """
    def __init__(self):
        super().__init__(
            name="Pantry",
            image=pygame.image.load("assets/rooms/Blue/Pantry.png"),
            doors=["left", "down"],
            rarity=0,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.or_ += 4
        print("Pantry : +4 pièces d'or.")


class Room8(Room):
    """
    Room 8 :
    Effet simplifié : +1 gemme.
    """
    def __init__(self):
        super().__init__(
            name="Room8",
            image=pygame.image.load("assets/rooms/Blue/Room_8.png"),
            doors=["left", "down"],
            rarity=1,
            placement_condition="any",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        player.gemmes += 1
        print("Room 8 : +1 gemme.")


class Rotunda(Room):
    """
    Rotunda :
    Effet : "Can rotate" -> on fait tourner ses portes.
    """
    def __init__(self):
        super().__init__(
            name="Rotunda",
            image=pygame.image.load("assets/rooms/Blue/Rotunda.png"),
            doors=["down", "left"],
            gem_cost=3,
            rarity=2,
            placement_condition="center",
            color="blue"
        )

    def apply_effect_on_enter(self, player):
        # rotation des portes : up->right->down->left
        new_doors = []
        mapping = {"up": "right", "right": "down", "down": "left", "left": "up"}
        for d in self.doors:
            new_doors.append(mapping.get(d, d))
        self.doors = new_doors
        print(f"Rotunda : les portes ont tourné, nouvelles portes = {self.doors}")



# ==============================
# Catalogue complet
# ==============================
ROOM_CATALOG = [
    EntranceHall(),
    Antechamber(),

    # ---- GREEN ----
    Greenhouse(),
    MorningRoom(),
    SecretGarden(),
    Veranda(),
    Cloister(),
    Courtyard(),
    Patio(),
    Terrace(),

    # ---- PURPLE ----
    HerLadyshipsChamber(),
    MasterBedroom(),
    Nursery(),
    ServantsQuarters(),
    Bedroom(),
    Boudoir(),
    BunkRoom(),
    GuestBedroom(),

    # ---- ORANGE ROOMS ----
    Corridor(),
    EastWingHall(),
    WestWingHall(),
    Hallway(),
    Passageway(),
    GreatHall(),
    Foyer(),
    SecretPassage(),

    # Blue rooms
    LockerRoom(),
    Vault(),
    Workshop(),
    BoilerRoom(),
    ConferenceRoom(),
    Gallery(),
    Garage(),
    Library(),
    RumpusRoom(),
    Pantry(),
    Room8(),
    Rotunda(),

]


# ==============================
# Classe Manor
# ==============================
class Manor:
    WIDTH = 5
    HEIGHT = 9

    opposite_direction = {
        "up": "down",
        "down": "up",
        "right": "left",
        "left": "right"
    }

    def __init__(self):
        # Grille de pièces
        self.grid = [[None for _ in range(self.WIDTH)] for _ in range(self.HEIGHT)]

        # Catalogue sans les pièces fixes
        self.room_catalog = [
            r for r in ROOM_CATALOG if r.name not in ("EntranceHall", "Antechamber")
        ]
        self.pioche = self.room_catalog

        # Effets globaux liés aux pièces vertes
        self.green_draw_bonus = 0      # utilisé pour favoriser les pièces vertes
        self.green_item_bonus = False  # futur bonus d'objets dans les pièces vertes
        self.green_rooms_free = False  # si True, les pièces vertes coûtent 0 gemme

        # Effets globaux liés aux pièces violetes
        self.bonus_next_boudoir_steps = 0
        self.bonus_next_walkin_gems = 0
        self.bonus_on_draft_bedroom = False

        # Effets globaux liés aux pièces oranges / bleues
        self.hallway_doors_unlocked = False
        self.next_room_color_choice = False

        # Redirecteur pour les effets de type "spread"
        self.redirect_spread_to_conference = None

        # Biais de rareté (Library)
        self.rarity_bias = 0




        # Placement fixe du Hall d'entrée et de l'Antechamber
        self.place_room(2, 8, EntranceHall())
        self.place_room(2, 0, Antechamber())

    # ---------------- utilitaires de grille ----------------
    def in_bounds(self, x, y):
        return 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT

    def get_room(self, x, y):
        if self.in_bounds(x, y):
            return self.grid[y][x]
        return None

    def place_room(self, x, y, room):
        """Effect:
        Places a room instance at grid coordinate (x, y) after bounds
        validation, then removes the original (unrotated) room definition
        from the `room_catalog`.

        Parameters:
        - x (int): Column index in manor grid.
        - y (int): Row index in manor grid.
        room (Room): The room instance (may be a rotated copy) to store.
        """
        if not self.in_bounds(x, y):
            raise ValueError("Position hors limites.")
        self.grid[y][x] = room

        # Remove original catalog entry (by name) to prevent future draws.
        for catalog_room in self.room_catalog[:]:
            if catalog_room.name == room.name:
                self.room_catalog.remove(catalog_room)
                break

    def get_room_weight(self, room):
        """Poids = base_weight × (1/3)^rarity × bonus verts × bonus rareté."""
        w = room.base_weight * (1.0 / 3.0) ** room.rarity

        # Bonus Greenhouse
        if getattr(self, "green_draw_bonus", 0) > 0 and room.color == "green":
            w *= (1 + self.green_draw_bonus)

        # Bonus Library (pièces rarity >= 2)
        if getattr(self, "rarity_bias", 0) > 0 and room.rarity >= 2:
            w *= (1 + self.rarity_bias)

        return w



    # ---------------- tirage de pièces ----------------
    def draw_three_rooms(self, current_pos, direction, room_catalog):
        """Effect:
        Builds up to three choices of possible rooms and enforces the
        at-least-one-free rule if any free options exist.

        Parameters:
        - current_pos (tuple[int,int]): Origin (x,y).
        - direction (str): Move direction ('up','down','left','right').
        - room_catalog (list[Room]): Remaining unplaced room prototypes.

        Returns:
        - list[Room]: Up to three room instances from the filtered possibilities.
        """
        possible_rooms = self.get_possible_rooms(current_pos, direction, room_catalog)

        # If no compatible rooms, return empty (should not happen normally)
        if not possible_rooms:
            return []

        # Guarantee at least one free option: if none free, make one free
        free_rooms = [r for r in possible_rooms if r.gem_cost == 0]
        if not free_rooms:
            possible_rooms[0].gem_cost = 0
            free_rooms = [possible_rooms[0]]

        choices = []
        # Always include one free room if available
        if free_rooms:
            choices.append(random.choice(free_rooms))

        # Weighted selection for remaining up to 2 choices, without replacement
        def weighted_pick(pool):
            weights = []
            total = 0.0
            for r in pool:
                w = getattr(r, "draw_weight", None)
                if w is None:
                    try:
                        w = self.get_room_weight(r)
                    except Exception:
                        w = 1.0
                weights.append(w)
                total += w
            if total <= 0:
                return random.choice(pool)
            target = random.random() * total
            acc = 0.0
            for idx, w in enumerate(weights):
                acc += w
                if target <= acc:
                    return pool[idx]
            return pool[-1]

        remaining = [r for r in possible_rooms if r not in choices]
        for _ in range(2):
            if not remaining:
                break
            pick = weighted_pick(remaining)
            choices.append(pick)
            remaining.remove(pick)

        random.shuffle(choices)
        return choices[:3]  # Return maximum 3 rooms
    
    def get_direction_offset(self, direction):
        """Retourne (dx, dy) pour une direction donnée."""
        if direction == "up":
            return (0, -1)
        elif direction == "down":
            return (0, 1)
        elif direction == "left":
            return (-1, 0)
        elif direction == "right":
            return (1, 0)
        return (0, 0)

    def get_possible_rooms(self, position, direction, room_catalog):
        """Effect:
        Returns all room instances (including a single valid rotation per base
        room) that can be legally placed adjacent to `position` in `direction`.

        Parameters:
        - position (tuple[int, int]): (x, y) origin cell.
        - direction (str): Direction of movement ('up','down','left','right').
        - room_catalog (list[Room]): Remaining unplaced rooms in the catalog.

        Returns:
        - list[Room]: Rotated room instances valid for placement; empty if none.

        Notes:
        - Applies color-based deterministic effects at candidate time (e.g.,
          Terrace makes green rooms free) so selection can remain simple.
        - Computes a transient `draw_weight` per candidate using `get_room_weight`
          to encapsulate color/rarity bonuses for weighted draws.
        """
        x, y = position
        dx, dy = self.get_direction_offset(direction)
        nx, ny = x + dx, y + dy

        # Target must be in-bounds and empty
        if not self.in_bounds(nx, ny) or self.get_room(nx, ny):
            return []

        required_door = self.opposite_direction[direction]
        possible_rooms = []

        for room in room_catalog:
            for rotated_room in room.get_all_rotations():
                if required_door not in rotated_room.doors:
                    continue

                # Enforce placement condition on the TARGET (nx, ny)
                cond = rotated_room.placement_condition
                if cond == "edge" and not (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                    continue
                if cond == "center" and (nx in (0, self.WIDTH - 1) or ny in (0, self.HEIGHT - 1)):
                    continue
                if cond == "top" and ny != 0:
                    continue
                if cond == "bottom" and ny != self.HEIGHT - 1:
                    continue

                # Reject rotations whose doors would lead outside the manor
                valid_doors = True
                for door in rotated_room.doors:
                    door_dx, door_dy = self.get_direction_offset(door)
                    check_x, check_y = nx + door_dx, ny + door_dy
                    if not self.in_bounds(check_x, check_y):
                        valid_doors = False
                        break
                if not valid_doors:
                    continue

                possible_rooms.append(rotated_room)
                break  # Only keep the first valid rotation per room

        # Apply color-based effects to candidates (does not mutate prototypes)
        if getattr(self, "green_rooms_free", False):
            for r in possible_rooms:
                if getattr(r, "color", "") == "green":
                    r.gem_cost = 0

        # Compute transient draw weights to carry color/rarity bonuses forward
        for r in possible_rooms:
            try:
                r.draw_weight = self.get_room_weight(r)
            except Exception:
                r.draw_weight = 1.0

        return possible_rooms

    def can_advance(self):
        """Effect:
        Scans the entire manor grid to determine if at least one legal
        move remains.

        Parameters:
        - None

        Returns:
        - bool: True if at least one expansion position exists; False otherwise.
        """
        for y in range(self.HEIGHT):
            for x in range(self.WIDTH):
                room = self.get_room(x, y)
                if isinstance(room, Antechamber):
                    continue
                if room:
                    for direction in room.doors:
                        dx, dy = self.get_direction_offset(direction)
                        nx, ny = x + dx, y + dy
                        if self.in_bounds(nx, ny) and not self.get_room(nx, ny):
                            if self.get_possible_rooms((x, y), direction, self.room_catalog):
                                return True
        return False
