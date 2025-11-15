# all the entities who will be populating the game
from abc import ABC, abstractmethod


class Player:

    opposite_direction = {"up": "down",
                          "down": "up",
                          "right": "left",
                          "left": "right"}

    def __init__(self, name):
        self.name = name
        self.inventory = Inventory()
        self.position = [2, 8]  # Starting position
        
        self.pas = 70       # Le joueur commence avec 70 pas    
        self.or_ = 0            
        self.gemmes = 2         # Commence avec 2
        self.cles = 0           # Commence avec 0 
        self.des = 0            # Commence avec 0 
        
        self.is_alive = True    # Utile pour la boucle de jeu principale
        
        
    def a_des_pas(self):
        """Vérifie s'il reste des pas."""
        return self.pas > 0

    def perdre_pas(self, quantite=1):
        """Appelée quand le joueur bouge."""
        self.pas -= quantite
        if not self.a_des_pas():
            self.pas = 0
            self.is_alive = False # Le joueur perd s'il n'a plus de pas !
            print("Vous n'avez plus de pas! Game Over.")

    def gagner_pas(self, quantite):
        """Appelée quand le joueur mange une pomme, par exemple."""
        self.pas += quantite
        if self.a_des_pas():
            self.is_alive = True  # Le joueur peut revivre s'il regagne des pas
        print(f"Vous gagnez {quantite} pas. Total: {self.pas}") 

    def can_move(self, direction, manor):
        """Checks if movement in direction is possible."""
        current_room = manor.get_room(*self.position)
        if not current_room or direction not in current_room.doors:
            return False
            
        x, y = self.position
        dx, dy = manor.get_direction_offset(direction)
        nx, ny = x + dx, y + dy
        
        if not manor.in_bounds(nx, ny):
            return False
            
        next_room = manor.get_room(nx, ny)
        if next_room and self.opposite_direction[direction] not in next_room.doors:
            return False
        return True   
    

    def move(self, direction, manor):
        """Déplace le joueur si les portes sont compatibles entre les deux salles."""
        
        if not self.a_des_pas():
            print("Vous n'avez plus de pas pour vous déplacer.")
            return

        x, y = self.position
        current_room = manor.get_room(x, y)

        if not current_room:
            print("Vous n’êtes dans aucune pièce.")
            return

        # 1️⃣ Vérifier qu'il y a une porte dans cette direction depuis la pièce actuelle
        if direction not in current_room.doors:
            print(f"Pas de porte vers {direction} dans {current_room.name}.")
            return

        # 2️⃣ Calculer la position de la pièce voisine
        dx, dy = 0, 0
        if direction == "up":
            dy = -1
        elif direction == "down":
            dy = 1
        elif direction == "left":
            dx = -1
        elif direction == "right":
            dx = 1

        nx, ny = x + dx, y + dy

        next_room = manor.get_room(nx, ny)
        if not next_room:
            print("Il n’y a pas encore de pièce dans cette direction.")
            return

        # 3️⃣ Vérifier la porte opposée dans la pièce d'arrivée
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
        if opposite[direction] not in next_room.doors:
            print(f"{next_room.name} n’a pas de porte vers {opposite[direction]}.")
            return

        # 4️⃣ Déplacement autorisé
        self.position = [nx, ny]
        self.perdre_pas(1)  # Perdre un pas à chaque déplacement
        print(f"Vous êtes maintenant dans {next_room.name}. ({self.pas} pas restants)")

    def use_item(self, item_name, player):
        for item in self.inventory.consumables:
            if item.nom.lower() == item_name.lower():
                item.utiliser(player) # L'objet applique son effet
                
                # --- MON AJOUT ---
                self.inventory.consumables.remove(item) # On détruit l'objet consommé
                break


class Inventory:
    def __init__(self):
        self.consumables = []
        self.permanents = []

    def add_item(self, item):
        if item.type_ == "consommable":
            self.consumables.append(item)
        elif item.type_ == "permanent":
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
        self.type_ = type_objet
        super().__init__()

    @abstractmethod
    def pick_up(self, player):
        """Chaque sous class definit comment l'objet est utilisé"""
        pass

##### Objets Consommables
class ObjetConsommable(Objet):
    def __init__(self, nom, description, valeur):
        super().__init__(nom, description, "consommable")
        self.valeur = valeur  # intensite de l’effet

    def pick_up(self, player):
        """Applique l'effet de l'objet sur le joueur"""
        pass


class Pas(ObjetConsommable):
    """Représente le nombre de pas disponibles"""
    def __init__(self, valeur):
        super().__init__("Pas", "Permet de se deplacer", valeur)

    def pick_up(self, player):
        player.gagner_pas(self.valeur)


class Or(ObjetConsommable):
    """Pieces d'or utilisées dans les magasins"""
    def __init__(self, valeur):
        super().__init__("Or", "Monnaie utilisée pour acheter des objets", valeur)

    def pick_up(self, player):
        player.or_ += self.valeur
        print(f"Le joueur obtient {self.valeur} pieces d'or")


class Gemmes(ObjetConsommable):
    """Gemmes pour tirer des pieces speciales"""
    def __init__(self, valeur):
        super().__init__("Gemme", "Permet de choisir certaines pieces", valeur)

    def pick_up(self, player):
        player.gemmes += self.valeur
        print(f"Le joueur obtient {self.valeur} gemmes.")


class Cles(ObjetConsommable):
    """Clés permettant d'ouvrir portes et coffres."""
    def __init__(self, valeur):
        super().__init__("Cle", "Permet d'ouvrir des portes verrouillées", valeur)

    def pick_up(self, player):
        player.cles += self.valeur
        print(f"Le joueur obtient {self.valeur} clé")


class Des(ObjetConsommable):
    """Dés pour relancer le tirage de pieces"""
    def __init__(self):
        super().__init__("Dés", "Permet de relancer un tirage de pieces", 0)

    def pick_up(self, player):
        player.des += 1
        print("Le joueur obtient un dé")



class ObjetPermanent(Objet):
    """Classe mère pour les objets permanents"""

    def __init__(self, nom, description):
        super().__init__(nom, description, "permanent")

    def pick_up(self, player):
        player.inventory.add_item(self)
        print("Le joueur peut maintenant creuser des trous")



class Pelle(ObjetPermanent):
    """Permet de creuser certains endroits"""
    def __init__(self):
        super().__init__("Pelle", "Permet de creuser à certains endroits.")

    def appliquer_effet(self, player):
        print("Le joueur peut maintenant creuser des trous")


class Marteau(ObjetPermanent):
    """Permet d’ouvrir les coffres sans clé"""
    def __init__(self):
        super().__init__("Marteau", "Permet d’ouvrir des coffres sans clé")

    def appliquer_effet(self, player):
        print("Le joueur peut ouvrir les coffres sans clé")


class KitCrochetage(ObjetPermanent):
    """Permet d’ouvrir les portes de niveau 1 sans clé"""
    def __init__(self):
        super().__init__("Kit de crochetage", "Permet d’ouvrir les portes de niveau 1 sans clé")

    def appliquer_effet(self, player):
        print("Le joueur peut crocheter les portes de niveau 1")


class DetecteurMetaux(ObjetPermanent):
    """Augmente les chances de trouver des clés et des pieces"""
    def __init__(self):
        super().__init__("Détecteur de métaux", "Augmente les chances de trouver des clés et de l'or")

    def appliquer_effet(self, player):
        print("Le joueur augmente ses chances de trouver des objets utiles")


class PatteLapin(ObjetPermanent):
    """Augmente la probabilité de trouver des objets rares"""
    def __init__(self):
        super().__init__("Patte de lapin", "Augmente la chance de trouver des objets rares")

    def appliquer_effet(self, player):
        print("Le joueur devient plus chanceux")


class AutreObjet(Objet):
    """Class mere pour les objets speciaux"""

    def __init__(self, nom, description):
        super().__init__(nom, description, "autre")

    def pick_up(self, player):
        pass



##### Autres Objets
class Pomme(AutreObjet):
    """Redonne 2 pas"""
    def __init__(self):
        super().__init__("Pomme", "Redonne 2 pas")

    def pick_up(self, player):
        #print("Le joueur regagne 2 pas")
        player.gagner_pas(2) # Appelle la méthode du joueur


class Banane(AutreObjet):
    """Redonne 3 pas"""
    def __init__(self):
        super().__init__("Banane", "Redonne 3 pas")

    def pick_up(self, player):
        #print("Le joueur regagne 3 pas")
        player.gagner_pas(3) #


class Gateau(AutreObjet):
    """Redonne 10 pas"""
    def __init__(self):
        super().__init__("Gâteau", "Redonne 10 pas")

    def pick_up(self, player):
        #print("Le joueur regagne 10 pas")
        player.gagner_pas(10)


class Sandwich(AutreObjet):
    """Redonne 15 pas"""
    def __init__(self):
        super().__init__("Sandwich", "Redonne 15 pas")

    def pick_up(self, player):
        #print("Le joueur regagne 15 pas")
        player.gagner_pas(15)


class Repas(AutreObjet):
    """Redonne 25 pas"""
    def __init__(self):
        super().__init__("Repas", "Redonne 25 pas")

    def pick_up(self, player):
        #print("Le joueur regagne 25 pas")
        player.gagner_pas(25)



#### Autres Objets liée a l'environement et vont etre appelés dans world
class Coffre(AutreObjet):
    """Contient des objets peut etre ouvert avec une clé ou un marteau"""
    def __init__(self):
        super().__init__( "Coffre", "Peut contenir des objets aléatoires")

    def pick_up(self, player):
        # TODO: Implémenter la logique d'ouverture (clé/marteau) et de loot
        print("Le joueur ouvre un coffre avec clé ou marteau")


class EndroitCreuser(AutreObjet):
    """Endroit ou le joueur peut creuser avec une pelle"""
    def __init__(self):
        super().__init__("Endroit a creuser", "Peut contenir des objets")

    def pick_up(self, player):
        # TODO: Implémenter la logique (vérifier si le joueur a la pelle)
        print("Le joueur creuse a cet endroit")


class Casier(AutreObjet):
    """Casier du vestiaire contient parfois des objets"""
    def __init__(self):
        super().__init__("Casier", "Present dans le vestiaire peut contenir des objets.")

    def pick_up(self, player):
        # TODO: Implémenter la logique (vérifier si le joueur a une clé)
        print("Le joueur ouvre un casier une clé nécessaire")