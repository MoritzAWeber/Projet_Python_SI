# all the entities who will be populating the game
from abc import ABC, abstractmethod


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
    def __init__(self):
        self.consumables = []
        self.permanents = []

    def add_item(self, item):
        if item.type == "consommable":
            self.consumables.append(item)
        elif item.type == "permanent":
            self.permanents.append(item)

    def use_item(self, item_name, player):
        # Cherche l’objet dans les consommables
        for item in self.consumables:
            if item.nom.lower() == item_name.lower():
                item.utiliser(player)
                self.consumables.remove(item)
                return

        print(f"{item_name} not found in inventory.")


class Objet(ABC):
    """Classe abstraite représentant tout objet du jeu"""
    def __init__(self, nom, description, type_objet):
        self.nom = nom
        self.description = description
        self.type = type_objet

    @abstractmethod
    def utiliser(self, joueur):
        """Chaque sous class definit comment l'objet est utilisé"""
        pass

##### Objets Consommables
class ObjetConsommable(Objet):
    def __init__(self, nom, description, valeur):
        Objet.__init__(self, nom, description, "consommable")
        self.valeur = valeur  # intensite de l’effet
        pass

    def utiliser(self, joueur):
        """Applique l'effet de l'objet sur le joueur"""
        self.effet(joueur)
        pass

    def effet(self, joueur):
        pass


class Pas(ObjetConsommable):
    """Représente le nombre de pas disponibles"""
    def __init__(self):
        ObjetConsommable.__init__(self, "Pas", "Permet de se deplacer", 70)

    def effet(self, joueur):
        print("Le joueur regagne des pas")


class Or(ObjetConsommable):
    """Pieces d'or utilisées dans les magasins"""
    def __init__(self):
        ObjetConsommable.__init__(self, "Or", "Monnaie utilisée pour acheter des objets", 0)

    def effet(self, joueur):
        print("Le joueur obtient des pieces d'or")


class Gemmes(ObjetConsommable):
    """Gemmes pour tirer des pieces speciales"""
    def __init__(self):
        ObjetConsommable.__init__(self, "Gemmes", "Permet de choisir certaines pieces", 2)

    def effet(self, joueur):
        print("Le joueur obtient des gemmes.")


class Cles(ObjetConsommable):
    """Clés permettant d'ouvrir portes et coffres."""
    def __init__(self):
        ObjetConsommable.__init__(self, "Cles", "Permet d'ouvrir des portes verrouillées", 0)

    def effet(self, joueur):
        print("Le joueur obtient une clé")


class Des(ObjetConsommable):
    """Dés pour relancer le tirage de pieces"""
    def __init__(self):
        ObjetConsommable.__init__(self, "Dés", "Permet de relancer un tirage de pieces", 0)

    def effet(self, joueur):
        print("Le joueur obtient un dé")



class ObjetPermanent(Objet):
    """Classe mère pour les objets permanents"""

    def __init__(self, nom, description):
        Objet.__init__(self, nom, description, "permanent")

    def utiliser(self, joueur):
        self.appliquer_effet(joueur)

    def appliquer_effet(self, joueur):
        pass



class Pelle(ObjetPermanent):
    """Permet de creuser certains endroits"""
    def __init__(self):
        ObjetPermanent.__init__(self, "Pelle", "Permet de creuser à certains endroits.")

    def appliquer_effet(self, joueur):
        print("Le joueur peut maintenant creuser des trous")


class Marteau(ObjetPermanent):
    """Permet d’ouvrir les coffres sans clé"""
    def __init__(self):
        ObjetPermanent.__init__(self, "Marteau", "Permet d’ouvrir des coffres sans clé")

    def appliquer_effet(self, joueur):
        print("Le joueur peut ouvrir les coffres sans clé")


class KitCrochetage(ObjetPermanent):
    """Permet d’ouvrir les portes de niveau 1 sans clé"""
    def __init__(self):
        ObjetPermanent.__init__(self, "Kit de crochetage", "Permet d’ouvrir les portes de niveau 1 sans clé")

    def appliquer_effet(self, joueur):
        print("Le joueur peut crocheter les portes de niveau 1")


class DetecteurMetaux(ObjetPermanent):
    """Augmente les chances de trouver des clés et des pieces"""
    def __init__(self):
        ObjetPermanent.__init__(self, "Détecteur de métaux", "Augmente les chances de trouver des clés et de l'or")

    def appliquer_effet(self, joueur):
        print("Le joueur augmente ses chances de trouver des objets utiles")


class PatteLapin(ObjetPermanent):
    """Augmente la probabilité de trouver des objets rares"""
    def __init__(self):
        ObjetPermanent.__init__(self, "Patte de lapin", "Augmente la chance de trouver des objets rares")

    def appliquer_effet(self, joueur):
        print("Le joueur devient plus chanceux")


class AutreObjet(Objet):
    """Class mere pour les objets speciaux"""

    def __init__(self, nom, description):
        Objet.__init__(self, nom, description, "autre")

    def utiliser(self, joueur):
        self.effet(joueur)

    def effet(self, joueur):
        pass



##### Autres Objets
class Pomme(AutreObjet):
    """Redonne 2 pas"""
    def __init__(self):
        AutreObjet.__init__(self, "Pomme", "Redonne 2 pas")

    def effet(self, joueur):
        print("Le joueur regagne 2 pas")


class Banane(AutreObjet):
    """Redonne 3 pas"""
    def __init__(self):
        AutreObjet.__init__(self, "Banane", "Redonne 3 pas")

    def effet(self, joueur):
        print("Le joueur regagne 3 pas")


class Gateau(AutreObjet):
    """Redonne 10 pas"""
    def __init__(self):
        AutreObjet.__init__(self, "Gâteau", "Redonne 10 pas")

    def effet(self, joueur):
        print("Le joueur regagne 10 pas")


class Sandwich(AutreObjet):
    """Redonne 15 pas"""
    def __init__(self):
        AutreObjet.__init__(self, "Sandwich", "Redonne 15 pas")

    def effet(self, joueur):
        print("Le joueur regagne 15 pas")


class Repas(AutreObjet):
    """Redonne 25 pas"""
    def __init__(self):
        AutreObjet.__init__(self, "Repas", "Redonne 25 pas")

    def effet(self, joueur):
        print("Le joueur regagne 25 pas")



#### Autres Objets liée a l'environement et vont etre appelés dans world
class Coffre(AutreObjet):
    """Contient des objets peut etre ouvert avec une clé ou un marteau"""
    def __init__(self):
        AutreObjet.__init__(self, "Coffre", "Peut contenir des objets aléatoires")

    def effet(self, joueur):
        print("Le joueur ouvre un coffre avec clé ou marteau")


class EndroitCreuser(AutreObjet):
    """Endroit ou le joueur peut creuser avec une pelle"""
    def __init__(self):
        AutreObjet.__init__(self, "Endroit a creuser", "Peut contenir des objets")

    def effet(self, joueur):
        print("Le joueur creuse a cet endroit")


class Casier(AutreObjet):
    """Casier du vestiaire contient parfois des objets"""
    def __init__(self):
        AutreObjet.__init__(self, "Casier", "Present dans le vestiaire peut contenir des objets.")

    def effet(self, joueur):
        print("Le joueur ouvre un casier une clé nécessaire")