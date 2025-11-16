# all the entities who will be populating the game
from abc import ABC, abstractmethod
import random


class Player:

    opposite_direction = {"up": "down",
                          "down": "up",
                          "right": "left",
                          "left": "right"}

    def __init__(self, name, manor):
        self.name = name
        self.inventory = Inventory()
        self.position = [2, 8]  # Starting position
        
        self.pas = 70       # Le joueur commence avec 70 pas    
        self.or_ = 0         
        self.gemmes = 2         # Commence avec 2
        self.cles = 0          # Commence avec 0 
        self.des = 0        # Commence avec 0 

        self.manor = manor
        
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
        
        # === FIX SHOP : fermer le shop si on quitte une pièce jaune ===
        if hasattr(self, "game") and self.game.shop_menu_active:
            old_color = getattr(current_room, "color", None)
            new_color = getattr(next_room, "color", None)
            if old_color == "yellow" and new_color != "yellow":
                self.game.shop_menu_active = False


        # Appliquer l'effet du nouveau salon
        next_room.apply_effect_on_enter(self)

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
        # Alias pour compatibilité (certains endroits utilisent .type)
        self.type = type_objet
        # Métadonnées par défaut pour la génération de butin
        # Les sous-classes peuvent les surcharger en tant qu'attributs de classe
        if not hasattr(self, "is_metallic"):
            self.is_metallic = False
        if not hasattr(self, "base_find_chance"):
            self.base_find_chance = 0.5
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
        # Augmenter la chance de base pour apparaître
        self.base_find_chance = 0.75

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
    def __init__(self, nom, description):
        super().__init__(nom, description, "permanent")

    def pick_up(self, player):
        """Ajoute l'objet permanent à l'inventaire et applique son effet."""
        player.inventory.add_item(self)
        self.appliquer_effet(player)   # ← appelle l'effet spécifique
        player.add_message(f"Objet permanent obtenu : {self.nom}")

    def should_consume_on_pickup(self):
        """Retirer l'objet de la liste après ramassage (reste en inventaire)."""
        return True

    def appliquer_effet(self, player):
        """Chaque sous-classe définit son propre effet."""
        pass



class Pelle(ObjetPermanent):
    """Permet de creuser certains endroits"""
    def __init__(self):
        super().__init__("Pelle", "Permet de creuser à certains endroits.")
        self.is_metallic = True
        self.base_find_chance = 0.35

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut maintenant creuser des trous")


class Marteau(ObjetPermanent):
    """Permet d’ouvrir les coffres sans clé"""
    def __init__(self):
        super().__init__("Marteau", "Permet d’ouvrir des coffres sans clé")
        self.is_metallic = True
        self.base_find_chance = 0.6

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut ouvrir les coffres sans clé")


class KitCrochetage(ObjetPermanent):
    """Permet d’ouvrir les portes de niveau 1 sans clé"""
    def __init__(self):
        super().__init__("Kit de crochetage", "Permet d’ouvrir les portes de niveau 1 sans clé")
        self.is_metallic = True
        self.base_find_chance = 0.8

    def appliquer_effet(self, player):
        player.add_message("Le joueur peut crocheter les portes de niveau 1")


class DetecteurMetaux(ObjetPermanent):
    """Augmente les chances de trouver des clés et des pieces"""
    def __init__(self):
        super().__init__("Détecteur de métaux", "Augmente les chances de trouver des clés et de l'or")
        self.is_metallic = True
        # Réduction de la probabilité de base pour équilibrer plus large distribution
        self.base_find_chance = 0.35

    def appliquer_effet(self, player):
        player.add_message("Le joueur augmente ses chances de trouver des objets utiles")


class PatteLapin(ObjetPermanent):
    """Augmente la probabilité de trouver des objets rares"""
    def __init__(self):
        super().__init__("Patte de lapin", "Augmente la chance de trouver des objets rares")
        # Ajout d'une probabilité explicite plus faible (par défaut c'était ~0.5 implicite)
        self.base_find_chance = 0.25

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
        super().__init__( "Coffre", "Peut être ouvert avec une clé ou un marteau")
        self.already_opened = False

    def pick_up(self, player):
        """Open chest if player has Marteau"""
        if self.already_opened:
            player.add_message("Ce coffre est déjà vide.")
            return
            
        if player.inventory.has_permanent("Marteau"):
            player.add_message("Vous utilisez le marteau pour ouvrir le coffre.")
            self.already_opened = True
            self.open_chest(player)
        elif player.cles > 0:
            player.cles -= 1
            player.add_message("Vous utilisez une clé pour ouvrir le coffre.")
            self.already_opened = True
            self.open_chest(player)
        else:
            player.add_message("Vous avez besoin d'un marteau ou d'une clé pour ouvrir ce coffre.")
    
    def open_chest(self, player):
        # Check for luck modifiers
        has_rabbits_foot = player.inventory.has_permanent("Patte de lapin")
        has_metal_detector = player.inventory.has_permanent("Détecteur de métaux")
        
        luck_multiplier = 1.15 if has_rabbits_foot else 1.0
        
        # Build weighted list based on luck modifiers
        possible_rewards = []
        
        # Or and Gemmes are metallic (benefit from detector)
        or_chance = 0.8 * luck_multiplier
        if has_metal_detector:
            or_chance *= 1.25
        if random.random() < or_chance:
            possible_rewards.append(Or(random.randint(5, 12)))
        
        gemmes_chance = 0.7 * luck_multiplier
        if has_metal_detector:
            gemmes_chance *= 1.25
        if random.random() < gemmes_chance:
            possible_rewards.append(Gemmes(random.randint(2, 4)))
        
        # Cles are metallic
        cles_chance = 0.6 * luck_multiplier
        if has_metal_detector:
            cles_chance *= 1.25
        if random.random() < cles_chance:
            possible_rewards.append(Cles(random.randint(1, 2)))
        
        # Des and Pas are not metallic
        des_chance = 0.5 * luck_multiplier
        if random.random() < des_chance:
            possible_rewards.append(Des(random.randint(1, 3)))
        
        pas_chance = 0.7 * luck_multiplier
        if random.random() < pas_chance:
            possible_rewards.append(Pas(random.randint(10, 20)))
        
        if not possible_rewards:
            player.add_message("Le coffre était vide...")
        else:
            player.add_message(f"Le coffre contenait {len(possible_rewards)} objet(s):")
            for reward in possible_rewards:
                reward.pick_up(player)
                player.add_message(f"  • {reward.nom}")


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
            
            # Check for luck modifiers
            has_rabbits_foot = player.inventory.has_permanent("Patte de lapin")
            has_metal_detector = player.inventory.has_permanent("Détecteur de métaux")
            
            luck_multiplier = 1.15 if has_rabbits_foot else 1.0
            
            if has_metal_detector:
                player.add_message("Le détecteur de métaux augmente vos chances!")
            
            # Build weighted list based on luck modifiers
            possible_rewards = []
            
            # Or and Gemmes are metallic (benefit from detector)
            or_chance = 0.5 * luck_multiplier
            if has_metal_detector:
                or_chance *= 1.25
            if random.random() < or_chance:
                possible_rewards.append(Or(random.randint(3, 8)))
            
            gemmes_chance = 0.4 * luck_multiplier
            if has_metal_detector:
                gemmes_chance *= 1.25
            if random.random() < gemmes_chance:
                possible_rewards.append(Gemmes(random.randint(1, 2)))
            
            # Cles are metallic
            cles_chance = 0.35 * luck_multiplier
            if has_metal_detector:
                cles_chance *= 1.25
            if random.random() < cles_chance:
                possible_rewards.append(Cles(1))
            
            # Non-metallic items
            pas_chance = 0.6 * luck_multiplier
            if random.random() < pas_chance:
                possible_rewards.append(Pas(random.randint(5, 15)))
            
            pomme_chance = 0.3 * luck_multiplier
            if random.random() < pomme_chance:
                possible_rewards.append(Pomme())
            
            banane_chance = 0.3 * luck_multiplier
            if random.random() < banane_chance:
                possible_rewards.append(Banane())
            
            if not possible_rewards:
                player.add_message("Vous ne trouvez rien...")
            else:
                player.add_message(f"Vous avez trouvé {len(possible_rewards)} objet(s):")
                for reward in possible_rewards:
                    reward.pick_up(player)
                    player.add_message(f"  • {reward.nom}")
        else:
            player.add_message("Vous avez besoin d'une pelle pour creuser ici.")

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return self.already_dug



class Casier(AutreObjet):
    """Casier du vestiaire contient parfois des objets"""
    def __init__(self, locked = True):
        super().__init__("Casier", "Present dans le vestiaire peut contenir des objets.")
        self.locked = locked
        self.already_opened = False

    def pick_up(self, player):
        if self.already_opened:
            player.add_message("Le casier est déjà vide.")
            return
        
        if not self.locked:
            self.already_opened = True
            self.open_locker(player)
            return
        
        # Casiers can only be opened with keys
        if player.cles > 0:
            player.cles -= 1
            player.add_message(f"Vous utilisez une clé pour ouvrir le casier! (Reste: {player.cles})")
            self.already_opened = True
            self.open_locker(player)
        else:
            player.add_message("Ce casier nécessite une clé.")

    def open_locker(self, player):
        # Check for luck modifiers
        has_rabbits_foot = player.inventory.has_permanent("Patte de lapin")
        has_metal_detector = player.inventory.has_permanent("Détecteur de métaux")
        
        luck_multiplier = 1.15 if has_rabbits_foot else 1.0
        
        # Empty chance reduced by luck
        empty_chance = 0.3 / luck_multiplier
        if random.random() < empty_chance:
            player.add_message("Le casier est vide...")
            return
        
        # Build weighted list based on luck modifiers
        possible_rewards = []
        
        # Or and Gemmes are metallic (benefit from detector)
        or_chance = 0.6 * luck_multiplier
        if has_metal_detector:
            or_chance *= 1.25
        if random.random() < or_chance:
            possible_rewards.append(Or(random.randint(2, 6)))
        
        gemmes_chance = 0.5 * luck_multiplier
        if has_metal_detector:
            gemmes_chance *= 1.25
        if random.random() < gemmes_chance:
            possible_rewards.append(Gemmes(random.randint(1, 2)))
        
        # Cles are metallic
        cles_chance = 0.4 * luck_multiplier
        if has_metal_detector:
            cles_chance *= 1.25
        if random.random() < cles_chance:
            possible_rewards.append(Cles(1))
        
        # Non-metallic items
        pas_chance = 0.6 * luck_multiplier
        if random.random() < pas_chance:
            possible_rewards.append(Pas(random.randint(5, 10)))
        
        pomme_chance = 0.4 * luck_multiplier
        if random.random() < pomme_chance:
            possible_rewards.append(Pomme())
        
        banane_chance = 0.4 * luck_multiplier
        if random.random() < banane_chance:
            possible_rewards.append(Banane())
        
        des_chance = 0.3 * luck_multiplier
        if random.random() < des_chance:
            possible_rewards.append(Des(random.randint(1, 2)))
        
        if not possible_rewards:
            player.add_message("Le casier est finalement vide...")
        else:
            player.add_message(f"Trouvé {len(possible_rewards)} objet(s) dans le casier:")
            for item in possible_rewards:
                item.pick_up(player)
                player.add_message(f"  • {item.nom}")

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return self.already_opened
    