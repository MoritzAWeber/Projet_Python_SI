# all the entities who will be populating the game
from abc import ABC, abstractmethod
import random


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
        self.cles = 10           # Commence avec 0 
        self.des = 0            # Commence avec 0 
        
        self.is_alive = True    # Utile pour la boucle de jeu principale
        
        self.message_callback = None  # Callback function for messages

    def set_message_callback(self, callback):
        self.message_callback = callback

    def add_message(self, message):
        """Utilise le callback pour ajouter un message au jeu."""
        if self.message_callback:
            self.message_callback(message)
        
        
    def a_des_pas(self):
        """Vérifie s'il reste des pas."""
        return self.pas > 0

    def perdre_pas(self, quantite=1, manor=None):
        """Appelée quand le joueur bouge."""
        self.pas -= quantite
        if not self.a_des_pas():
            self.pas = 0
            
            # Check if there are step-giving items in current room
            if manor and self.has_step_items_in_room(manor):
                self.add_message("Attention! Plus de pas, mais des objets peuvent vous aider!")
            else:
                self.is_alive = False  # Le joueur perd s'il n'a plus de pas !
                self.add_message("Vous n'avez plus de pas! Game Over.")
    
    def has_step_items_in_room(self, manor):
        """Vérifie s'il y a des objets qui donnent des pas dans la pièce actuelle."""
        x, y = self.position
        room = manor.get_room(x, y)
        
        if not room or not room.objets:
            return False
        
        # Check for food items (Pomme, Banane, Gateau, Sandwich, Repas) or Pas objects
        step_giving_items = ["Pomme", "Banane", "Gâteau", "Sandwich", "Repas", "Pas"]
        
        for obj in room.objets:
            if obj.nom in step_giving_items:
                return True

        return False

    def gagner_pas(self, quantite):
        """Appelée quand le joueur mange une pomme, par exemple."""
        self.pas += quantite
        if self.a_des_pas():
            self.is_alive = True  # Le joueur peut revivre s'il regagne des pas
        self.add_message(f"Vous gagnez {quantite} pas. Total: {self.pas}") 

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
            self.add_message("Vous n'avez plus de pas pour vous déplacer.")
            return

        x, y = self.position
        current_room = manor.get_room(x, y)

        if not current_room:
            self.add_message("Vous n’êtes dans aucune pièce.")
            return

        # 1️⃣ Vérifier qu'il y a une porte dans cette direction depuis la pièce actuelle
        if direction not in current_room.doors:
            self.add_message(f"Pas de porte vers {direction} dans {current_room.name}.")
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
            self.add_message("Il n'y a pas encore de pièce dans cette direction.")
            return

        # 3- Vérifier la porte opposée dans la pièce d'arrivée
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
        if opposite[direction] not in next_room.doors:
            self.add_message(f"{next_room.name} n’a pas de porte vers {opposite[direction]}.")
            return

        # 4️-  Déplacement autorisé
        self.position = [nx, ny]
        self.perdre_pas(1, manor)  # Perdre un pas à chaque déplacement
        self.add_message(f"Vous êtes maintenant dans {next_room.name}. ({self.pas} pas restants)")
        
        # Appliquer l'effet du nouveau salon
        next_room.apply_effect_on_enter(self, manor)

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

        player.add_message(f"{item_name} not found in inventory.")
    
    def has_permanent(self, item_name):
        """Check if player has a specific permanent item"""
        for item in self.permanents:
            if item.nom.lower() == item_name.lower():
                return True
        return False


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

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return True


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
        player.add_message(f"Le joueur obtient {self.valeur} pieces d'or")


class Gemmes(ObjetConsommable):
    """Gemmes pour tirer des pieces speciales"""
    def __init__(self, valeur):
        super().__init__("Gemme", "Permet de choisir certaines pieces", valeur)

    def pick_up(self, player):
        player.gemmes += self.valeur
        player.add_message(f"Le joueur obtient {self.valeur} gemmes.")


class Cles(ObjetConsommable):
    """Clés permettant d'ouvrir portes et coffres."""
    def __init__(self, valeur):
        super().__init__("Cle", "Permet d'ouvrir des portes verrouillées", valeur)

    def pick_up(self, player):
        player.cles += self.valeur
        player.add_message(f"Le joueur obtient {self.valeur} clé")


class Des(ObjetConsommable):
    """Dés pour relancer le tirage de pieces"""
    def __init__(self, valeur):
        super().__init__("Dés", "Permet de relancer un tirage de pieces", valeur)

    def pick_up(self, player):
        player.des += self.valeur
        player.add_message("Le joueur obtient un dé")



class ObjetPermanent(Objet):
    """Classe mère pour les objets permanents"""

    def __init__(self, nom, description):
        super().__init__(nom, description, "permanent")

    def pick_up(self, player):
        player.inventory.add_item(self)
        player.add_message("Le joueur peut maintenant creuser des trous")

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return True



class Pelle(ObjetPermanent):
    """Permet de creuser certains endroits"""
    def __init__(self):
        super().__init__("Pelle", "Permet de creuser à certains endroits.")

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut maintenant creuser des trous")


class Marteau(ObjetPermanent):
    """Permet d’ouvrir les coffres sans clé"""
    def __init__(self):
        super().__init__("Marteau", "Permet d’ouvrir des coffres sans clé")

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut ouvrir les coffres sans clé")


class KitCrochetage(ObjetPermanent):
    """Permet d’ouvrir les portes de niveau 1 sans clé"""
    def __init__(self):
        super().__init__("Kit de crochetage", "Permet d’ouvrir les portes de niveau 1 sans clé")

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut crocheter les portes de niveau 1")


class DetecteurMetaux(ObjetPermanent):
    """Augmente les chances de trouver des clés et des pieces"""
    def __init__(self):
        super().__init__("Détecteur de métaux", "Augmente les chances de trouver des clés et de l'or")

    def appliquer_effet(self, player):
        player.add_message("Le joueur augmente ses chances de trouver des objets utiles")


class PatteLapin(ObjetPermanent):
    """Augmente la probabilité de trouver des objets rares"""
    def __init__(self):
        super().__init__("Patte de lapin", "Augmente la chance de trouver des objets rares")

    def appliquer_effet(self, player):
        player.add_message("Le joueur devient plus chanceux")


class AutreObjet(Objet):
    """Class mere pour les objets speciaux"""

    def __init__(self, nom, description):
        super().__init__(nom, description, "autre")

    def pick_up(self, player):
        pass

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return True



##### Autres Objets
class Pomme(AutreObjet):
    """Redonne 2 pas"""
    def __init__(self):
        super().__init__("Pomme", "Redonne 2 pas")

    def pick_up(self, player):
        #player.add_message("Le joueur regagne 2 pas")
        player.gagner_pas(2) # Appelle la méthode du joueur


class Banane(AutreObjet):
    """Redonne 3 pas"""
    def __init__(self):
        super().__init__("Banane", "Redonne 3 pas")

    def pick_up(self, player):
        #player.add_message("Le joueur regagne 3 pas")
        player.gagner_pas(3) #


class Gateau(AutreObjet):
    """Redonne 10 pas"""
    def __init__(self):
        super().__init__("Gâteau", "Redonne 10 pas")

    def pick_up(self, player):
        #player.add_message("Le joueur regagne 10 pas")
        player.gagner_pas(10)


class Sandwich(AutreObjet):
    """Redonne 15 pas"""
    def __init__(self):
        super().__init__("Sandwich", "Redonne 15 pas")

    def pick_up(self, player):
        #player.add_message("Le joueur regagne 15 pas")
        player.gagner_pas(15)


class Repas(AutreObjet):
    """Redonne 25 pas"""
    def __init__(self):
        super().__init__("Repas", "Redonne 25 pas")

    def pick_up(self, player):
        #player.add_message("Le joueur regagne 25 pas")
        player.gagner_pas(25)



#### Autres Objets liée a l'environement et vont etre appelés dans world
class Coffre(AutreObjet):
    """Contient des objets peut etre ouvert avec une clé ou un marteau"""
    def __init__(self):
        super().__init__( "Coffre", "Peut contenir des objets aléatoires")
        self.already_opened = False

    def pick_up(self, player):
        """Open chest if player has Marteau"""
        if player.inventory.has_permanent("Marteau"):
            self.open_chest(player)
            player.add_message("Vous utilisez le marteau pour ouvrir le coffre.")
        elif player.cles > 0:
            player.add_message("Vous utilisez une clé pour ouvrir le coffre.")
            self.open_chest(player)
            player.cles -= 1
        else:
            player.add_message("Vous avez besoin d'un marteau ou un clé pour ouvrir ce coffre.")
    
    def open_chest(self, player):
        self.already_opened = True
        # Random reward
        rewards = [
            Or(random.randint(3, 8)),
            Gemmes(random.randint(1, 3)),
            Cles(1),
            Des(random.randint(1, 2))
        ]
        reward = random.choice(rewards)
        reward.pick_up(player)


    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return self.already_opened


class EndroitCreuser(AutreObjet):
    """Endroit ou le joueur peut creuser avec une pelle"""
    def __init__(self):
        super().__init__("Endroit a creuser", "Peut contenir des objets")
        self.already_dug = False

    def pick_up(self, player):
        if self.already_dug:
            player.add_message("Vous avez déjà creusé ici.")
            return
        
        if player.inventory.has_permanent("Pelle"):
            player.add_message("Vous creusez avec la pelle...")
            self.already_dug = True
            
            # Chance-based rewards
            chance = random.random()
            
            # DetecteurMetaux improves chances
            if player.inventory.has_permanent("Détecteur de métaux"):
                chance += 0.2  # +20% better luck
                player.add_message("Le détecteur de métaux augmente vos chances!")
            
            if chance < 0.3:
                player.add_message("Vous ne trouvez rien...")
            elif chance < 0.6:
                # Small reward
                reward = random.choice([Or(2), Pas(5)])
                reward.pick_up(player)
                player.add_message(f"Vous avez trouvé: {reward.nom}!")
            else:
                # Big reward
                reward = random.choice([Gemmes(2), Cles(1), Or(5)])
                reward.pick_up(player)
                player.add_message(f"Vous avez trouvé: {reward.nom}!")
        else:
            player.add_message("Vous avez besoin d'une pelle pour creuser ici.")

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return self.already_dug



class Casier(AutreObjet):
    """Casier du vestiaire contient parfois des objets"""
    def __init__(self, locked = True, lock_level = 1):
        super().__init__("Casier", "Present dans le vestiaire peut contenir des objets.")
        self.locked = locked
        self.lock_level = lock_level
        self.already_opened = False

    def pick_up(self, player):
        if self.already_opened:
            player.add_message("Le casier est déjà vide.")
            return
        
        if not self.locked:
            self.open_locker(player)
            return
        
        # Level 1 lock: needs Kit de crochetage
        if self.lock_level == 1:
            if player.inventory.has_permanent("Kit de crochetage"):
                player.add_message("Vous crochetez le casier avec le kit!")
                self.open_locker(player)
            elif player.cles > 0:
                player.cles -= 1
                player.add_message(f"Vous utilisez une clé! (Reste: {player.cles})")
                self.open_locker(player)
            else:
                player.add_message("Ce casier nécessite une clé ou un kit de crochetage.")
        
        # Level 2 lock: needs Key
        elif self.lock_level == 2:
            if player.cles > 0:
                player.cles -= 1
                player.add_message(f"Vous utilisez une clé! (Reste: {player.cles})")
                self.open_locker(player)
            else:
                player.add_message("Ce casier nécessite une clé.")

    def open_locker(self, player):
        self.already_opened = True
        # Random reward
        rewards = [
            Or(random.randint(1, 5)),
            Gemmes(random.randint(1, 2)),
            Pas(random.randint(5, 15))
        ]
        reward = random.sample(rewards, random.randint(1, 3))
        for item in reward:
            item.pick_up(player)
            player.add_message(f"Vous avez trouvé: {item.nom} dans le casier!")

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return self.already_opened
    