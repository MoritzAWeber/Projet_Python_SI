# all the entities who will be populating the game
from abc import ABC, abstractmethod
import random


class Player:
    """Represents the player character with inventory, position, and resources.
    
    Manages player movement, resource tracking (steps, gold, gems, keys, dice),
    and interactions with rooms and objects in the manor.
    """

    opposite_direction = {"up": "down",
                          "down": "up",
                          "right": "left",
                          "left": "right"}

    def __init__(self, name, manor):
        """Initialize player with starting resources and position.
        
        Parameters:
        - name: str, player name
        - manor: Manor instance, reference to game world
        
        Starting resources:
        - 70 steps, 0 gold, 2 gems, 0 keys, 0 dice
        - Position at [2, 8] (starting room)
        """
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
        """Set callback function for displaying messages to player.
        
        Parameters:
        - callback: function that accepts a message string
        """
        self.message_callback = callback

    def add_message(self, message):
        """Utilise le callback pour ajouter un message au jeu."""
        if self.message_callback:
            self.message_callback(message)
        
        
    def a_des_pas(self):
        """Check if player has steps remaining.
        
        Returns:
        - bool: True if pas > 0, False otherwise
        """
        return self.pas > 0

    def perdre_pas(self, quantite=1, manor=None):
        """Reduce player steps, typically when moving.
        
        Parameters:
        - quantite: int, number of steps to lose (default 1)
        - manor: Manor instance, used to check for step-giving items in current room
        
        Side effects:
        - Sets is_alive to False if steps reach 0 and no step items available
        - Shows game over message or warning about available items
        """
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
        """Check if current room contains step-giving items.
        
        Parameters:
        - manor: Manor instance to query current room
        
        Returns:
        - bool: True if room contains food items (Pomme, Banane, Gateau, Sandwich, Repas)
        """
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
        """Add steps to player, typically from consuming food.
        
        Parameters:
        - quantite: int, number of steps to add
        
        Side effects:
        - Sets is_alive to True if player regains steps after reaching 0
        - Displays message with new total
        """
        self.pas += quantite
        if self.a_des_pas():
            self.is_alive = True  # Le joueur peut revivre s'il regagne des pas
        self.add_message(f"Vous gagnez {quantite} pas. Total: {self.pas}") 

    def can_move(self, direction, manor):
        """Check if movement in specified direction is valid.
        
        Parameters:
        - direction: str, one of "up", "down", "left", "right"
        - manor: Manor instance to check room connections
        
        Returns:
        - bool: True if movement allowed, checks door existence and room bounds
        """
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
        """Move player to adjacent room if doors are compatible.
        
        Parameters:
        - direction: str, movement direction ("up", "down", "left", "right")
        - manor: Manor instance to validate movement and get rooms
        
        Effects:
        - Consumes 1 step on successful movement
        - Updates player position
        - Applies room entry effects
        - Closes shop menu if leaving yellow room
        - Shows messages for invalid moves or successful transitions
        """
        
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
    """Manages player's consumable and permanent items.
    
    Separates items into two categories:
    - consumables: items used once
    - permanents: equipment and tools kept throughout game
    """
    def __init__(self):
        self.consumables = []
        self.permanents = []

    def add_item(self, item):
        """Add item to appropriate inventory category.
        
        Parameters:
        - item: Objet instance with type_ attribute
        """
        if item.type_ == "consommable":
            self.consumables.append(item)
        elif item.type_ == "permanent":
            self.permanents.append(item)

    
    def has_permanent(self, item_name):
        """Check if player has a specific permanent item.
        
        Parameters:
        - item_name: str, case-insensitive name of item
        
        Returns:
        - bool: True if item found in permanents
        """
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
    """Base class for consumable items with numeric values.
    
    Consumables are picked up and used immediately, typically granting
    resources like steps, gold, gems, keys, or dice.
    """
    def __init__(self, nom, description, valeur):
        """Initialize consumable with value.
        
        Parameters:
        - nom: str, item name
        - description: str, item description
        - valeur: int, magnitude of effect when consumed
        """
        super().__init__(nom, description, "consommable")
        self.valeur = valeur  # intensite de l’effet

    def pick_up(self, player):
        """Applique l'effet de l'objet sur le joueur"""
        pass

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return True


class Pas(ObjetConsommable):
    """Steps resource for player movement."""
    def __init__(self, valeur):
        super().__init__("Pas", "Permet de se deplacer", valeur)

    def pick_up(self, player):
        """Grant steps to player.
        
        Parameters:
        - player: Player instance to receive steps
        """
        player.gagner_pas(self.valeur)


class Or(ObjetConsommable):
    """Gold coins used for shop purchases."""
    def __init__(self, valeur):
        super().__init__("Or", "Monnaie utilisée pour acheter des objets", valeur)

    def pick_up(self, player):
        """Add gold to player inventory.
        
        Parameters:
        - player: Player instance to receive gold
        """
        player.or_ += self.valeur
        player.add_message(f"Le joueur obtient {self.valeur} pieces d'or")


class Gemmes(ObjetConsommable):
    """Gems used to pay for special room drafts."""
    def __init__(self, valeur):
        super().__init__("Gemme", "Permet de choisir certaines pieces", valeur)

    def pick_up(self, player):
        """Add gems to player inventory.
        
        Parameters:
        - player: Player instance to receive gems
        """
        player.gemmes += self.valeur
        player.add_message(f"Le joueur obtient {self.valeur} gemmes.")


class Cles(ObjetConsommable):
    """Keys for opening locked doors and chests.
    
    Has higher base_find_chance (0.75) to ensure availability.
    """
    def __init__(self, valeur):
        super().__init__("Cle", "Permet d'ouvrir des portes verrouillées", valeur)
        # Augmenter la chance de base pour apparaître
        self.base_find_chance = 0.75

    def pick_up(self, player):
        """Add keys to player inventory.
        
        Parameters:
        - player: Player instance to receive keys
        """
        player.cles += self.valeur
        player.add_message(f"Le joueur obtient {self.valeur} clé")


class Des(ObjetConsommable):
    """Dice for rerolling room draft choices."""
    def __init__(self, valeur):
        super().__init__("Dés", "Permet de relancer un tirage de pieces", valeur)

    def pick_up(self, player):
        """Add dice to player inventory.
        
        Parameters:
        - player: Player instance to receive dice
        """
        player.des += self.valeur
        player.add_message("Le joueur obtient un dé")



class ObjetPermanent(Objet):
    """Base class for permanent equipment and tools.
    
    Permanent items remain in inventory after pickup and provide
    passive bonuses or enable special interactions.
    """
    def __init__(self, nom, description):
        super().__init__(nom, description, "permanent")

    def pick_up(self, player):
        """Add permanent item to inventory and apply its effect.
        
        Parameters:
        - player: Player instance receiving the item
        
        Side effects:
        - Adds item to permanents list
        - Calls appliquer_effet to activate item benefit
        """
        player.inventory.add_item(self)
        self.appliquer_effet(player)   # appelle l'effet spécifique
        player.add_message(f"Objet permanent obtenu : {self.nom}")

    def should_consume_on_pickup(self):
        """Boilerplate Method. Returns if permanent items are removed from room after pickup.
        
        Returns:
        - bool
        """
        return True

    def appliquer_effet(self, player):
        """Apply item-specific effect. Overridden by subclasses.
        
        Parameters:
        - player: Player instance to receive effect
        """
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
    """Metal detector that boosts find chance for metallic items.
    
    Increases discovery rate for gold, gems, and keys by 25%.
    Metallic item with base_find_chance 0.35.
    """
    def __init__(self):
        super().__init__("Détecteur de métaux", "Augmente les chances de trouver des clés et de l'or")
        self.is_metallic = True
        # Réduction de la probabilité de base pour équilibrer plus large distribution
        self.base_find_chance = 0.35

    def appliquer_effet(self, player):
        """Notify player of enhanced item discovery.
        
        Parameters:
        - player: Player instance
        """
        player.add_message("Le joueur augmente ses chances de trouver des objets utiles")


class PatteLapin(ObjetPermanent):
    """Rabbit's foot that increases luck for all item finds.
    
    Provides 15% multiplier to all discovery chances.
    Low base_find_chance (0.25) to maintain rarity.
    """
    def __init__(self):
        super().__init__("Patte de lapin", "Augmente la chance de trouver des objets rares")
        # Ajout d'une probabilité explicite plus faible (par défaut c'était ~0.5 implicite)
        self.base_find_chance = 0.25

    def appliquer_effet(self, player):
        """Notify player of increased luck.
        
        Parameters:
        - player: Player instance
        """
        player.add_message("Le joueur devient plus chanceux")


class AutreObjet(Objet):
    """Base class for special interactive objects.
    
    Includes food items, chests, digging spots, and lockers.
    These objects typically have custom interaction logic.
    """

    def __init__(self, nom, description):
        super().__init__(nom, description, "autre")

    def pick_up(self, player):
        pass

    def should_consume_on_pickup(self):
        """Détermine si l'objet doit être consommé immédiatement après la collecte."""
        return True



##### Autres Objets
class Pomme(AutreObjet):
    """Apple that restores 2 steps when consumed."""
    def __init__(self):
        super().__init__("Pomme", "Redonne 2 pas")

    def pick_up(self, player):
        """Grant 2 steps to player.
        
        Parameters:
        - player: Player instance
        """
        #player.add_message("Le joueur regagne 2 pas")
        player.gagner_pas(2) # Appelle la méthode du joueur


class Banane(AutreObjet):
    """Banana that restores 3 steps when consumed."""
    def __init__(self):
        super().__init__("Banane", "Redonne 3 pas")

    def pick_up(self, player):
        """Grant 3 steps to player.
        
        Parameters:
        - player: Player instance
        """
        #player.add_message("Le joueur regagne 3 pas")
        player.gagner_pas(3) #


class Gateau(AutreObjet):
    """Cake that restores 10 steps when consumed."""
    def __init__(self):
        super().__init__("Gâteau", "Redonne 10 pas")

    def pick_up(self, player):
        """Grant 10 steps to player.
        
        Parameters:
        - player: Player instance
        """
        #player.add_message("Le joueur regagne 10 pas")
        player.gagner_pas(10)


class Sandwich(AutreObjet):
    """Sandwich that restores 15 steps when consumed."""
    def __init__(self):
        super().__init__("Sandwich", "Redonne 15 pas")

    def pick_up(self, player):
        """Grant 15 steps to player.
        
        Parameters:
        - player: Player instance
        """
        #player.add_message("Le joueur regagne 15 pas")
        player.gagner_pas(15)


class Repas(AutreObjet):
    """Full meal that restores 25 steps when consumed."""
    def __init__(self):
        super().__init__("Repas", "Redonne 25 pas")

    def pick_up(self, player):
        """Grant 25 steps to player.
        
        Parameters:
        - player: Player instance
        """
        #player.add_message("Le joueur regagne 25 pas")
        player.gagner_pas(25)



#### Autres Objets liée a l'environement et vont etre appelés dans world
class Coffre(AutreObjet):
    """Chest containing random loot, opened with key or hammer.
    
    Contents determined by luck modifiers (metal detector, rabbit's foot).
    Can only be opened once.
    """
    def __init__(self):
        super().__init__( "Coffre", "Peut être ouvert avec une clé ou un marteau")
        self.already_opened = False

    def pick_up(self, player):
        """Attempt to open chest with hammer or key.
        
        Parameters:
        - player: Player instance with inventory and resources
        
        Effects:
        - Consumes 1 key if no hammer available
        - Generates random loot based on luck modifiers
        - Marks chest as opened
        """
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
        """Generate and grant random loot from chest.
        
        Parameters:
        - player: Player instance to receive rewards
        
        Loot probabilities (base * luck_multiplier):
        - Or: 80% (metallic, +25% with detector)
        - Gemmes: 70% (metallic, +25% with detector)
        - Cles: 60% (metallic, +25% with detector)
        - Des: 50%
        - Pas: 70%
        
        Rabbit's foot provides 15% luck multiplier for all rolls.
        """
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
    """Digging spot that yields loot when excavated with shovel.
    
    Requires Pelle in inventory. Contents determined by luck modifiers.
    Can only be dug once.
    """
    def __init__(self):
        super().__init__("Endroit a creuser", "Peut contenir des objets")
        self.already_dug = False

    def pick_up(self, player):
        """Attempt to dig with shovel.
        
        Parameters:
        - player: Player instance with inventory
        
        Loot probabilities (base * luck_multiplier):
        - Or: 50% (metallic, +25% with detector)
        - Gemmes: 40% (metallic, +25% with detector)
        - Cles: 35% (metallic, +25% with detector)
        - Pas: 60%
        - Pomme: 30%
        - Banane: 30%
        
        Side effects:
        - Marks spot as dug
        - Generates and grants random loot
        """
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
    """Locker in locker room, may contain items.
    
    Requires key to open (unless unlocked). 30% chance of being empty.
    Contents determined by luck modifiers.
    """
    def __init__(self, locked = True):
        super().__init__("Casier", "Present dans le vestiaire peut contenir des objets.")
        self.locked = locked
        self.already_opened = False

    def pick_up(self, player):
        """Attempt to open locker with key.
        
        Parameters:
        - player: Player instance with key resources
        
        Effects:
        - Consumes 1 key if locked
        - Marks locker as opened
        - Generates random loot (or empty)
        """
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
        """Generate and grant random loot from locker.
        
        Parameters:
        - player: Player instance to receive rewards
        
        Empty chance: 30% (reduced by luck multiplier)
        
        Loot probabilities (base * luck_multiplier):
        - Or: 60% (metallic, +25% with detector)
        - Gemmes: 50% (metallic, +25% with detector)
        - Cles: 40% (metallic, +25% with detector)
        - Pas: 60%
        - Pomme: 40%
        - Banane: 40%
        - Des: 30%
        """
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
    