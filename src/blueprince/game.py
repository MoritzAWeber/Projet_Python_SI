import pygame
import random
from .world import Manor, Antechamber
from .entities import Player, ObjetConsommable, ObjetPermanent, AutreObjet, KitCrochetage


class Game:

    opposite_direction = {"up": "down",
                          "down": "up",
                          "right": "left",
                          "left": "right"}

    def __init__(self):
        pygame.init()

        # === Dimensions ===
        self.COLS = 5
        self.ROWS = 9
        self.cell_size = 90
        self.margin = 5
        self.messages = []
        self.max_messages = 3

        self.game_width = self.COLS * self.cell_size
        self.hud_width = int(self.cell_size * 10)
        self.window_width = self.game_width + self.hud_width
        self.window_height = self.ROWS * self.cell_size

        # === Fenêtre ===
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Blue Prince – Interface avec HUD")

        # === Couleurs ===
        self.COLOR_BG = (10, 10, 20)
        self.COLOR_HUD = (240, 240, 240)
        self.COLOR_PLAYER = (255, 215, 0)
        self.COLOR_TEXT = (10, 10, 10)
        self.COLOR_WHITE = (255, 255, 255)

        # === Police ===
        self.font_title = pygame.font.SysFont("arial", 28, bold=True)
        self.font_text = pygame.font.SysFont("arial", 22)
        self.font_small = pygame.font.SysFont("arial", 20)
        
         # === SHOP MENU ===
        self.shop_menu_active = False
        self.shop_choices = []
        self.shop_index = 0
        self.current_shop_room = None

        # === Chargement des icônes d’inventaire ===
        def load_icon(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (32, 32))
            except:
                surf = pygame.Surface((32, 32))
                surf.fill((120, 120, 120))
                return surf

        
        self.icons = {
            "steps": load_icon("assets/icons/steps.png"),
            "coin": load_icon("assets/icons/coin.png"),
            "gem": load_icon("assets/icons/gem.png"),
            "key": load_icon("assets/icons/key.png"),
            "dice": load_icon("assets/icons/dice.png"),
        }

        # === Monde et joueur ===
        self.clock = pygame.time.Clock()
        self.manor = Manor()
        self.player = Player("Player", self.manor)
        self.player.game = self
        self.player.set_message_callback(self.add_message)
        self.running = True
        # HUD layout helpers
        self.hud_y_after_inventory = 0
        self.hud_y_after_room_menu = 0
        # HUD layout helper: records the Y after inventory/permanents
        self.hud_y_after_inventory = 0
        
        # === Tracking für gefundene Permanents (verhindert Respawn) ===
        self.found_permanents = set()
        # Referenz für Manor, damit Rooms darauf zugreifen können
        self.manor.found_permanents = self.found_permanents

        # === Sélecteur de porte + menu ===
        self.selected_door = "up"
        self.menu_active = False
        self.menu_choices = []
        self.menu_index = 0

        # === Ramasser des objets ===
        self.pickup_menu_active = False
        self.pickup_index = 0
        self.pickup_choices = []
        # === Game over state ===
        self.game_over = False
        self.game_over_message = ""
        # === Victory state ===
        self.victory = False
        self.victory_message = ""
        
        #demenade d'ouvrir la porte 
        self.confirm_door_active = False  # Nouvel état pour la confirmation
        self.confirm_door_details = {}    # Pour mémoriser quelle porte on ouvre
    
    
    def is_in_shop_room(self):
        """Check if the player is currently in a shop room (yellow room).

        Returns:
        - bool: True if current room color is yellow, False otherwise.
        """
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        return getattr(room, "color", None) == "yellow"

    # ====================== BOUCLE PRINCIPALE ======================
    def run(self):
        """Main game loop that handles events, updates game state, and renders.

        Runs at 30 FPS and continues until self.running is set to False.
        Checks end conditions only if game is not over.
        """
        while self.running:
            self.handle_events()
            if not self.game_over:
                self.check_end_conditions()
            self.render()
            self.clock.tick(30)
        pygame.quit()

    # ====================== GESTION DES TOUCHES ======================
    def handle_events(self):
        """Handle all keyboard and window events based on current game state.

        Processes different input modes:
        - Game over/victory: R to restart, ESC to quit
        - Door confirmation: O to confirm, A to cancel
        - Shop menu: UP/DOWN to navigate, SPACE to buy, M to close
        - Pickup menu: UP/DOWN to navigate, SPACE to pick up, E to close
        - Room draft menu: LEFT/RIGHT to navigate, SPACE to confirm, R to reroll
        - Normal navigation: Z/Q/S/D or arrows to select door, SPACE to open, M for opening shop, E for opening object pickup
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:

                # --- ESC pour quitter ---
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # --- Si game over / victoire ---
                if self.game_over or self.victory:
                    if event.key == pygame.K_r:
                        self.restart_game()
                    continue

                # --- Confirmation ouverture de porte ---
                if self.confirm_door_active:
                    if event.key == pygame.K_o:   # OUI
                        self._execute_door_opening()
                    elif event.key == pygame.K_a: # NON
                        self.confirm_door_active = False
                        self.confirm_door_details = {}
                        self.add_message("Action annulée.")
                    continue
                # ============================================================
                # MODE SHOP (menu actif)
                # ============================================================
                if self.shop_menu_active:
                    if event.key == pygame.K_UP:
                        self.shop_index = (self.shop_index - 1) % len(self.shop_items)
                    elif event.key == pygame.K_DOWN:
                        self.shop_index = (self.shop_index + 1) % len(self.shop_items)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_shop_choice()
                    elif event.key == pygame.K_m:
                        self.shop_menu_active = False
                    continue

                # ============================================================
                # MODE PICKUP (ramasser objets)
                # ============================================================
                if self.pickup_menu_active:
                    if event.key == pygame.K_UP:
                        self.pickup_index = (self.pickup_index - 1) % len(self.pickup_choices)
                    elif event.key == pygame.K_DOWN:
                        self.pickup_index = (self.pickup_index + 1) % len(self.pickup_choices)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_pickup_choice()
                    elif event.key == pygame.K_e:
                        self.pickup_menu_active = False
                    continue

                # ============================================================
                # MENU DE TIRAGE (3 pièces)
                # ============================================================
                if self.menu_active:
                    if event.key == pygame.K_LEFT:
                        self.menu_index = (self.menu_index - 1) % len(self.menu_choices)
                    elif event.key == pygame.K_RIGHT:
                        self.menu_index = (self.menu_index + 1) % len(self.menu_choices)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_room_choice()
                    elif event.key == pygame.K_r:
                        self.reroll_room_choices()
                    continue

                # ============================================================
                # NAVIGATION NORMALE
                # ============================================================
                # ============================================================
                # NAVIGATION / SELECTION & MENUS (PAS DE MOUVEMENT DIRECT)
                # ============================================================
                if not self.menu_active and not self.pickup_menu_active and not self.confirm_door_active:
                    if event.key == pygame.K_z or event.key == pygame.K_UP:
                        self.selected_door = "up"
                    elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                        self.selected_door = "down"
                    elif event.key == pygame.K_q or event.key == pygame.K_LEFT:
                        self.selected_door = "left"
                    elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                        self.selected_door = "right"
                    elif event.key == pygame.K_SPACE:
                        self.open_door_menu()
                    elif event.key == pygame.K_m:
                        if self.is_in_shop_room():
                            if self.shop_menu_active:
                                self.shop_menu_active = False
                            else:
                                self.open_shop_menu()
                                self.shop_menu_active = True
                        return
                    elif event.key == pygame.K_e:
                        if not self.is_in_shop_room():
                            self.open_object_pickup_menu()
                        return




    # la gestion des niveau des portes + gestion de la demande des cles
    def open_door_menu(self):
        """Handle door opening logic with lock levels and key requirements.

        Lock levels depend on Y position:
        - Y 8-6: Level 0 (free)
        - Y 5-4: Level 0 or 1 (random)
        - Y 3-2: Level 1 or 2 (random)
        - Y 1-0: Level 2

        If player has KitCrochetage, level 1 locks can be picked for free.
        Shows confirmation dialog if keys are required, otherwise opens directly.
        """
        
        if not self.player.can_move(self.selected_door, self.manor):
            self.add_message("Cette direction n'est pas accessible.")
            return

        x, y = self.player.position
        dx, dy = self.manor.get_direction_offset(self.selected_door)
        nx, ny = x + dx, y + dy

        # 1. Si la pièce existe déjà, on bouge
        if self.manor.get_room(nx, ny):
            self.player.move(self.selected_door, self.manor)
            return
        
        # 2. Calculer le coût de la porte
        lock_level = 0
        if ny in [8, 7, 6]:
            lock_level = 0
        elif ny in [5, 4]:
            lock_level = random.choice([0, 1])
        elif ny in [3, 2]:
            lock_level = random.choice([1, 2])
        elif ny in [1, 0]:
            lock_level = 2

        # 3. Vérifier les outils (Kit de crochetage)
        has_lockpick = any(isinstance(obj, KitCrochetage) for obj in self.player.inventory.permanents)

        required_keys = 0 if lock_level == 0 else 1
        pickaxe_msg = None

        if lock_level == 1 and has_lockpick:
            required_keys = 0
            pickaxe_msg = "Vous crochetez la serrure (Niv 1)."
        
        # 4. Vérifier si le joueur peut payer
        if self.player.cles < required_keys:
            self.add_message(f"Porte verrouillée ! (Niv {lock_level})")
            if required_keys > 0:
                self.add_message(f"Il vous faut {required_keys} clé(s).")
            return
        
        # 5. Stocker les détails pour la confirmation
        self.confirm_door_details = {
            'direction': self.selected_door,
            'keys': required_keys,
            'lock_level': lock_level,
            'pickaxe_msg': pickaxe_msg
        }

        # 6. Demander confirmation OU ouvrir directement si gratuit
        if required_keys > 0:
            # Demander confirmation
            self.confirm_door_active = True
            self.add_message(f"Porte Niv {lock_level} ({required_keys} clé). [O]=Ouvrir / [A]=Annuler")
        else:
            # C'est gratuit (porte Niv 0 ou crochetage)
            self._execute_door_opening()

    
    #
    def _execute_door_opening(self):
        """Execute the door opening after confirmation.

        Uses stored details from confirm_door_details to:
        - Deduct required keys from player inventory
        - Display lockpicking message if applicable
        - Draw 3 room choices and activate room draft menu
        - Refund keys if no rooms are available (error case)
        """
        # 1. Récupérer les détails stockés
        details = self.confirm_door_details
        required_keys = details['keys']
        direction = details['direction']
        pickaxe_msg = details['pickaxe_msg']

        # 2. Payer le coût et afficher le message
        if required_keys > 0:
            self.player.cles -= required_keys
            self.add_message(f"Vous utilisez {required_keys} clé(s).")
        elif pickaxe_msg:
            # Afficher le message de crochetage (si_execute_door_opening)
            self.add_message(pickaxe_msg)

        # 3. Ouvrir le menu de tirage des 3 pièces
        self.menu_choices = self.manor.draw_three_rooms(
            self.player.position, 
            direction, 
            self.manor.pioche
        )
        
        if not self.menu_choices:
             self.add_message("Erreur : Aucune pièce compatible trouvée !")
             # (On redonne les clés si elles ont été dépensées pour rien)
             if required_keys > 0:
                 self.player.cles += required_keys
             self.confirm_door_active = False
             self.confirm_door_details = {}
             return

        self.menu_index = 0
        self.menu_active = True # Activer le menu des pièces

        # 4. Réinitialiser l'état de confirmation
        self.confirm_door_active = False
        self.confirm_door_details = {}
    
    def reroll_room_choices(self):
        """Use a die to reroll the 3 current room options. Requires player to have at least 1 die

        Effects:
        - Consumes 1 die from player inventory
        - Generates new room choices for current door direction
        - Resets menu_index to 0
        """
        if self.player.des <= 0:
            self.add_message("Vous n'avez pas de dés pour relancer!")
            return

        self.player.des -= 1
        self.add_message(f"Vous utilisez un dé pour relancer. Dés restants: {self.player.des}")

        self.menu_choices = self.manor.draw_three_rooms(
            self.player.position, 
            self.selected_door, 
            self.manor.pioche
        )
        
        if not self.menu_choices:
            self.add_message("Erreur: Aucune pièce compatible trouvée après relance!")
            self.menu_active = False
            return

        self.menu_index = 0

    def confirm_room_choice(self):
        """Validate room choice and place it in the manor. Uses self.menu_index to identify chosen room from menu_choices

        Effects:
        - Deducts gem cost from player if room has gem_cost > 0
        - Places chosen room in manor at calculated position
        - Applies Nursery bonus if active and room is a bedroom type
        - Closes room draft menu
        """
        chosen = self.menu_choices[self.menu_index]
        cost = getattr(chosen, 'gem_cost', 0)
        if cost > 0:
            if self.player.gemmes < cost:
                self.add_message(f"Pas assez de gemmes (coût: {cost}).")
                return
            self.player.gemmes -= cost
            self.add_message(f"- {cost} gemme(s)")
        
        x, y = self.player.position
        dx, dy = self.manor.get_direction_offset(self.selected_door)

        nx, ny = x + dx, y + dy

        self.manor.place_room(nx, ny, chosen)
        self.menu_active = False
        self.add_message(f"Pièce ajoutée: {chosen.name}")


        # LE BONUS de la piece NURSERY
        if getattr(self.manor, "bonus_on_draft_bedroom", False):
            if chosen.name in ("Bedroom", "BunkRoom", "GuestBedroom"):
                self.player.gagner_pas(5)


    # choix de objet a echanger contre de l'or dans les pieces jaunes
    ####################################################################
    def open_shop_menu(self):
        """Initialize shop menu with available items.

        Effects:
        - Sets up shop_items list with name, cost, and effect lambda
        - Resets shop_index to 0
        - Does not activate menu automatically
        """
    # empêcher ouverture si un autre menu est actif
        if self.menu_active or self.pickup_menu_active or self.confirm_door_active:
            return

        # items du shop
        self.shop_items = [
            ("Pomme", 2, lambda player: player.gagner_pas(2)),
            ("Banane", 3, lambda player: player.gagner_pas(3)),
            ("Gâteau", 8, lambda player: player.gagner_pas(10)),
            ("Clé", 10, lambda player: setattr(player, "cles", player.cles + 1)),
            ("Gemme", 3, lambda player: setattr(player, "gemmes", player.gemmes + 1)),
        ]

        self.shop_index = 0


    def confirm_shop_choice(self):
            """Process shop purchase for currently selected item. Uses self.shop_index to identify selected item

            Effects:
            - Deducts gold from player if purchase successful
            - Applies item effect (adds steps, keys, gems, or permanent item)
            - Shows message about purchase or insufficient gold
            """
            name, cost, effect = self.shop_items[self.shop_index]

            if self.player.or_ < cost:
                self.add_message(f"Pas assez d'or pour acheter {name}.")
                return

            self.player.or_ -= cost
            effect(self.player)
            self.add_message(f"Achat : {name} pour {cost} or.")

    def open_object_pickup_menu(self):
        """Open pickup menu for objects in current room.

        Effects:
        - Sets pickup_choices to current room's objects list
        - Activates pickup menu if objects are available
        - Shows message if no objects present
        """
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        if not room or not room.objets:
            self.add_message("Il n'y a pas d'objets à ramasser ici.")
            return

        self.pickup_choices = room.objets
        self.pickup_index = 0
        self.pickup_menu_active = True

    def confirm_pickup_choice(self):
        """Validate and process object pickup from current room.

        Side effects:
        - Calls object's pick_up method to add to player inventory
        - Removes object from room (unless should_consume_on_pickup returns False)
        - Tracks permanent objects globally to prevent respawning
        - Updates pickup menu choices and index after removal
        - Closes menu if no objects remain
        """
        # Bounds check to prevent IndexError
        if not self.pickup_choices or self.pickup_index >= len(self.pickup_choices):
            self.pickup_menu_active = False
            return
        
        chosen = self.pickup_choices[self.pickup_index]
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        if not room:
            return
        
        # Track permanents global, um Respawn zu verhindern
        if chosen.type == "permanent":
            self.found_permanents.add(chosen.__class__.__name__)
        
        chosen.pick_up(self.player)
        # Ne retirer l'objet que s'il doit réellement être consommé.
        remove_after = True
        if hasattr(chosen, 'should_consume_on_pickup'):
            try:
                remove_after = chosen.should_consume_on_pickup()
            except Exception:
                remove_after = True
        if remove_after and chosen in room.objets:
            room.objets.remove(chosen)
        
        # Update pickup_choices to reflect current room state and reset index
        self.pickup_choices = room.objets
        if not self.pickup_choices:
            self.pickup_menu_active = False
            self.pickup_index = 0
        else:
            # Keep index valid after removal
            self.pickup_index = min(self.pickup_index, len(self.pickup_choices) - 1)

    def check_end_conditions(self):
        """Check and trigger game over or victory conditions.

        Loss conditions:
        - Player runs out of steps (not is_alive)
        - No more rooms can be placed (manor.can_advance returns False)

        Victory condition:
        - Player reaches the Antechamber room
        """
        # 1) Lose: plus de pas
        if not self.player.is_alive:
            self.end_game("Vous n'avez plus de pas...\nGame Over.")
        if not self.manor.can_advance():
            self.end_game("Il n'y a plus de pièces disponibles pour avancer.\nGame Over.")
            return

        # 2) Win: joueur dans l'Antechamber
        x, y = self.player.position
        current_room = self.manor.get_room(x, y)
        if isinstance(current_room, Antechamber):
            self.set_victory("Bravo ! Vous avez atteint l'Antechamber. Vous gagnez !")

    def end_game(self, message: str):
        """Trigger game over state.

        Parameters:
        - message: str, text to display on game over screen

        Side effects:
        - Sets game_over flag to True
        - Stores message for overlay display
        - Adds "GAME OVER" to message log
        """
        self.game_over = True
        self.game_over_message = message
        # Also push a concise last message into log
        self.add_message("GAME OVER")

    def set_victory(self, message: str):
        """Trigger victory state.

        Parameters:
        - message: str, text to display on victory screen

        Side effects:
        - Sets victory flag to True
        - Stores message for overlay display
        - Adds "VICTOIRE !" to message log
        """
        self.victory = True
        self.victory_message = message
        self.add_message("VICTOIRE !")

    def restart_game(self):
        """Reinitialize game state for a new run.

        Side effects:
        - Creates new Manor and Player instances
        - Resets all menu states and flags
        - Clears message log and found permanents tracking
        - Keeps window and pygame initialized
        """
        # Reinitialize dynamic game state (keep window & pygame)
        self.manor = Manor()
        self.player = Player("Player", self.manor)
        self.player.set_message_callback(self.add_message)
        # Reset tracking für permanente Objekte
        self.found_permanents = set()
        self.manor.found_permanents = self.found_permanents
        self.selected_door = "up"
        self.menu_active = False
        self.menu_choices = []
        self.menu_index = 0
        self.pickup_menu_active = False
        self.pickup_index = 0
        self.pickup_choices = []
        self.messages.clear()
        self.game_over = False
        self.game_over_message = ""
        self.victory = False
        self.victory_message = ""
        self.add_message("Nouvelle partie")

    # ====================== AFFICHAGE ======================
    def render(self):
        """Main rendering method called each frame.

        Draws in order:
        1. Manor grid with rooms and images
        2. HUD background
        3. White frame around current room
        4. Door selector indicators
        5. Player inventory (consumables + permanents)
        6. Room choice menu (if active)
        7. Message log
        8. Room objects panel (if not in menu or shop)
        9. Shop menu (passive display)
        10. Victory/Game over overlays (if triggered)

        Updates display with pygame.display.flip().
        """
        self.screen.fill(self.COLOR_BG, (0, 0, self.game_width, self.window_height))
        # reset dynamic layout markers each frame
        self.hud_y_after_room_menu = 0

        # --- 1. Dessiner le manoir ---
        self.draw_manor()

        # --- 2. HUD ---
        hud_rect = pygame.Rect(self.game_width, 0, self.hud_width, self.window_height)
        pygame.draw.rect(self.screen, self.COLOR_HUD, hud_rect)

        # --- 3. Cadre blanc autour de la pièce actuelle (sans cacher les portes) ---
        px, py = self.player.position
        outer_margin = 2  # cadre plus fin et plus éloigné des bords
        room_rect = pygame.Rect(
        px * self.cell_size + self.margin - outer_margin,
        py * self.cell_size + self.margin - outer_margin,
        self.cell_size - 2 * self.margin + outer_margin * 2,
        self.cell_size - 2 * self.margin + outer_margin * 2
        )
        pygame.draw.rect(self.screen, self.COLOR_WHITE, room_rect, 3)


        # --- 4. Sélecteur de porte ---
        self.draw_door_selector(px, py)

        # --- 5. Inventaire ---
        self.draw_inventory(self.player, hud_rect)

        # --- 6. Menu de choix de pièces ---
        if self.menu_active:
            self.draw_room_choice_menu(hud_rect)

        # --- 7. Messages ---
        self.draw_messages(hud_rect)

        # --- 8. Objets dans la pièce actuelle (toujours si pas menu de tirage et pas salle shop) ---
        if not self.menu_active and not self.is_in_shop_room():
            self.draw_room_objects(hud_rect)

        if self.victory:
            self.draw_victory_overlay()
        elif self.game_over:
            self.draw_game_over_overlay()
        # dessine toujours le shop (affichage passif possible)
        self.draw_shop_menu(hud_rect)
        pygame.display.flip()

    # ====================== DESSINS HUD ======================

    
    def draw_manor(self):
        """Draw manor grid with room images and door indicators.

        Renders:
        - Room background images from assets/rooms/
        - Locked door indicators (red lines with thickness based on lock level)
        - Open door gaps (black rectangles for visual clarity)
        - Player position indicator (blue circle)
        """
        # --- 1. Dessiner le manoir ---
        for y in range(self.ROWS):
            for x in range(self.COLS):
                room = self.manor.get_room(x, y)
                if room:
                    rect = pygame.Rect(
                        x * self.cell_size + self.margin,
                        y * self.cell_size + self.margin,
                        self.cell_size - 2 * self.margin,
                        self.cell_size - 2 * self.margin
                    )
                    if room.image:
                        scaled = pygame.transform.scale(room.image, (rect.width, rect.height))
                        self.screen.blit(scaled, rect)
                    else:
                        pygame.draw.rect(self.screen, (100, 100, 100), rect)

    def draw_door_selector(self, px, py):
        """Draw white indicator bar around currently selected door.

        Parameters:
        - px: int, player's x grid coordinate
        - py: int, player's y grid coordinate

        Renders:
        - White bar (8px thick) on the selected edge (up/down/left/right)
        - Positioned relative to room cell with 10px inset from corners
        """
        x = px * self.cell_size
        y = py * self.cell_size
        w = self.cell_size
        h = self.cell_size
        t = 8

        if self.selected_door == "up":
            rect = pygame.Rect(x + 10, y, w - 20, t)
        elif self.selected_door == "down":
            rect = pygame.Rect(x + 10, y + h - t, w - 20, t)
        elif self.selected_door == "left":
            rect = pygame.Rect(x, y + 10, t, h - 20)
        elif self.selected_door == "right":
            rect = pygame.Rect(x + w - t, y + 10, t, h - 20)
        else:
            return
        pygame.draw.rect(self.screen, self.COLOR_WHITE, rect)

    def draw_inventory(self, player, hud_rect):
        """Render player inventory in HUD.

        Parameters:
        - player: Player instance with stats and permanent objects
        - hud_rect: pygame.Rect defining HUD area

        Displays:
        - "Consumables" section: steps, coins, gems, keys, dice with icons
        - Horizontal divider line
        - "Objets permanents" section: list of permanent items or "(aucun)"
        
        Side effects:
        - Sets self.hud_y_after_inventory for layout tracking
        """
        margin_x = hud_rect.left + 40
        y = hud_rect.top + 40
        color = self.COLOR_TEXT

        title = self.font_title.render("Consumables:", True, color)
        self.screen.blit(title, (margin_x, y))
        y += 50

        stats = [
            ("steps", player.pas),
            ("coin", player.or_),
            ("gem", player.gemmes),
            ("key", player.cles),
            ("dice", player.des),
        ]

        for name, value in stats:
            icon = self.icons[name]
            self.screen.blit(icon, (margin_x, y))
            val_text = self.font_text.render(str(value), True, color)
            self.screen.blit(val_text, (margin_x + 45, y + 6))
            y += 45

        pygame.draw.line(self.screen, (180, 180, 180),
                         (margin_x, y + 10),
                         (margin_x + 200, y + 10), 1)
        y += 30
        # Permanent objects section (use same font family/size as consumables values)
        perm_title = self.font_title.render("Objets permanents:", True, color)
        self.screen.blit(perm_title, (margin_x, y))
        y += 40
        if self.player.inventory.permanents:
            for obj in self.player.inventory.permanents:
                line = self.font_text.render(f"- {obj.nom}", True, color)
                self.screen.blit(line, (margin_x + 8, y))
                y += 26
        else:
            none_line = self.font_text.render("(aucun)", True, color)
            self.screen.blit(none_line, (margin_x + 8, y))
            y += 26
        # Record end Y to position other HUD panes below
        self.hud_y_after_inventory = y

    def draw_room_choice_menu(self, hud_rect):
        """Render room drafting menu with 3 choices.

        Parameters:
        - hud_rect: pygame.Rect defining HUD area

        Displays:
        - Title "Choose a room to draft"
        - 3 room cards with images (90x90px), names, and gem costs
        - Blue frame around selected card (using menu_index)
        - Color-coded cost text (green for free, red if unaffordable, white otherwise)
        - Reroll prompt with available dice count

        Side effects:
        - Sets self.hud_y_after_room_menu for message layout
        - Dynamically positions below inventory with bounds clamping
        """
        color = self.COLOR_TEXT
        # Place below inventory/permanents if needed, with bounds clamp
        default_base_y = hud_rect.top + 400
        dyn_start = getattr(self, 'hud_y_after_inventory', default_base_y) + 30
        base_y = max(default_base_y, dyn_start)
        base_y = min(base_y, self.window_height - 260)
        base_x = hud_rect.left + 50

        title = self.font_text.render("Choose a room to draft", True, color)
        self.screen.blit(title, (base_x, base_y))

        card_size = 90
        spacing = 140
        y_img = base_y + 40

        for i, room in enumerate(self.menu_choices):
            x = base_x + i * spacing
            rect = pygame.Rect(x, y_img, card_size, card_size)
            img = pygame.transform.scale(room.image, (card_size, card_size))
            self.screen.blit(img, rect)
            if i == self.menu_index:
                color_frame = (0, 80, 200)  # bleu cyan lumineux
                pygame.draw.rect(self.screen, color_frame, rect, 4)


            name = self.font_small.render(room.name, True, color)
            self.screen.blit(name, (x + 10, y_img + card_size + 10))

            # Afficher le coût en gemmes
            cost = getattr(room, 'gem_cost', 0)
            cost_text = "Gratuit" if cost == 0 else f"Coût: {cost} gemme(s)"
            affordable = self.player.gemmes >= cost
            cost_color = (120, 180, 120) if cost == 0 else ((180, 60, 60) if not affordable else color)
            cost_surf = self.font_small.render(cost_text, True, cost_color)
            self.screen.blit(cost_surf, (x + 10, y_img + card_size + 28))
        
        # Reroll-Anzeige
        reroll_y = y_img + card_size + 50
        if self.player.des > 0:
            reroll_text = f"[R] Relancer ({self.player.des} dés disponibles)"
            reroll_color = (0, 150, 0)
        else:
            reroll_text = "[R] Relancer (pas de dés)"
            reroll_color = (150, 150, 150)
        
        reroll_surf = self.font_small.render(reroll_text, True, reroll_color)
        self.screen.blit(reroll_surf, (base_x, reroll_y))
        # record bottom of room menu to avoid overlap with messages
        bottom = reroll_y + reroll_surf.get_height()
        if bottom > getattr(self, 'hud_y_after_room_menu', 0):
            self.hud_y_after_room_menu = bottom

    def add_message(self, text: str):
        """Add a message to the log, maintaining max_messages limit.

        Parameters:
        - text: str, message text to append

        Effects:
        - Appends to self.messages list
        - Removes oldest message if list exceeds max_messages (10)
        """
        self.messages.append(text)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw_messages(self, hud_rect):
        """Render message log in HUD.

        Parameters:
        - hud_rect: pygame.Rect defining HUD area

        Displays:
        - "Messages:" title
        - List of recent messages (up to max_messages)

        Positioning:
        - Dynamically placed below inventory and room menu
        - Clamped to prevent overflow at bottom of HUD
        """
        x = hud_rect.left + 40
        # Place messages below inventory/permanents if needed, with bounds clamp
        default_y = hud_rect.top + 600
        dyn_inv = getattr(self, 'hud_y_after_inventory', default_y) + 40
        dyn_menu = getattr(self, 'hud_y_after_room_menu', 0) + 20
        y = max(default_y, dyn_inv, dyn_menu)
        y = min(y, self.window_height - 120)
        title = self.font_text.render("Messages:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 30

        for msg in self.messages:
            surf = self.font_small.render(msg, True, self.COLOR_TEXT)
            self.screen.blit(surf, (x, y))
            y += 22


    def draw_shop_menu(self, hud_rect):
        """Render shop interface when in yellow room.

        Parameters:
        - hud_rect: pygame.Rect defining HUD area

        Displays:
        - "Magasin :" title
        - List of shop items with names and gold costs
        - Highlights selected item (yellow) when shop_menu_active
        - Controls hint (M to open/close, UP/DOWN + SPACE to buy)

        Side effects:
        - Initializes shop_items if not already set
        - Only renders when is_in_shop_room() returns True
        """
        # afficher seulement dans une pièce jaune
        if not self.is_in_shop_room():
            return
        x = hud_rect.left + 500
        y = hud_rect.top + 40

        title = self.font_title.render("Magasin :", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 50

        # initialiser items si nécessaire (sans activation)
        if not hasattr(self, 'shop_items') or not self.shop_items:
            self.open_shop_menu()

        for i, (name, cost, _) in enumerate(self.shop_items):
            color = (255, 215, 0) if (self.shop_menu_active and i == self.shop_index) else self.COLOR_TEXT
            text = f"{i+1}. {name} - {cost} or"
            line = self.font_small.render(text, True, color)
            self.screen.blit(line, (x, y))
            y += 22

        y += 5
        if self.shop_menu_active:
            hint1 = self.font_small.render("M: fermer le menu", True, self.COLOR_TEXT)
            hint2 = self.font_small.render("UP/DOWN + SPACE : acheter", True, self.COLOR_TEXT)
            self.screen.blit(hint1, (x, y))
            self.screen.blit(hint2, (x, y + 22))
        else:
            hint_closed = self.font_small.render("M: ouvrir le menu", True, self.COLOR_TEXT)
            self.screen.blit(hint_closed, (x, y))




    def draw_room_objects(self, hud_rect):
        """Display objects available in current room.

        Parameters:
        - hud_rect: pygame.Rect defining HUD area

        Displays:
        - "Objets à ramasser:" title
        - List of objects with details:
          - Consumables show "x valeur"
          - Casier shows "[Clé requise]"
          - Coffre shows "[Marteau ou Clé requis]"
          - EndroitCreuser shows "[Pelle requise]"
        - Highlights selected object (yellow) when pickup_menu_active
        - Controls hint (E to open/close, UP/DOWN + SPACE to interact)
        """
        x = hud_rect.left + 500
        y = hud_rect.top + 40

        px, py = self.player.position
        room = self.manor.get_room(px, py)

        if not room or not room.objets:
            return
        title = self.font_title.render("Objets à ramasser:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 50

        if not self.pickup_menu_active:
            for i, obj in enumerate(room.objets, start=1):
                if isinstance(obj, ObjetConsommable):
                    line = self.font_small.render(f"{i}. {obj.nom} x {obj.valeur}", True, self.COLOR_TEXT)
                    self.screen.blit(line, (x, y))
                    y += 22
                else:
                    line = self.font_small.render(f"{i}. {obj.nom}", True, self.COLOR_TEXT)
                    self.screen.blit(line, (x, y))
                    y += 22
            hint = self.font_small.render("E: ouvrir le menu", True, self.COLOR_TEXT)
            self.screen.blit(hint, (x, y + 5))

        else:

            for i, obj in enumerate(room.objets, start=1):
                text_color = (255, 215, 0) if i - 1 == self.pickup_index else self.COLOR_TEXT

                # Construction du texte avec détails
                display_text = f"{i}. {obj.nom}"
                
                # Ajoute des infos spécifiques selon le type
                if isinstance(obj, ObjetConsommable):
                    display_text = display_text + f" x {obj.valeur}"
                # Ajoute le lock level pour les Casiers
                elif obj.__class__.__name__ == "Casier":
                    display_text += "[Clé requise]"
                # Ajoute l'état pour les Coffres
                elif obj.__class__.__name__ == "Coffre":
                    display_text += "[Marteau  ou Clé requis]"
                # Ajoute l'état pour EndroitCreuser
                elif obj.__class__.__name__ == "EndroitCreuser":
                    display_text += "[Pelle requise]"
                line = self.font_small.render(display_text, True, text_color)
                self.screen.blit(line, (x, y))
                y += 22
            
            y += 5
            hint = self.font_small.render("E: fermer le menu", True, self.COLOR_TEXT)
            self.screen.blit(hint, (x, y))
            hint2 = self.font_small.render("UP/DOWN + SPACE: interagir", True, self.COLOR_TEXT)
            y += 22
            self.screen.blit(hint2, (x, y))

    def draw_game_over_overlay(self):
        """
            Render game over screen overlay.
        """
        # Dark transparent overlay
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 520, 300
        panel_x = (self.window_width - panel_w) // 2
        panel_y = (self.window_height - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (245, 245, 245), panel_rect, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2, border_radius=12)

        title = self.font_title.render("GAME OVER", True, (180, 40, 40))
        self.screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 18))

        # Wrap message lines
        lines = [l for l in self.game_over_message.split('\n') if l.strip()] or ["Fin de la partie."]
        y = panel_y + 80
        for line in lines:
            surf = self.font_text.render(line, True, self.COLOR_TEXT)
            self.screen.blit(surf, (panel_x + 30, y))
            y += 32

        stats = f"Pas: {self.player.pas}  Or: {self.player.or_}  Gemmes: {self.player.gemmes}  Clés: {self.player.cles}"
        stats_surf = self.font_small.render(stats, True, (70, 70, 80))
        self.screen.blit(stats_surf, (panel_x + 30, panel_y + panel_h - 100))

        instr1 = self.font_small.render("R: recommencer", True, self.COLOR_TEXT)
        instr2 = self.font_small.render("ESC: quitter", True, self.COLOR_TEXT)
        self.screen.blit(instr1, (panel_x + 30, panel_y + panel_h - 60))
        self.screen.blit(instr2, (panel_x + 30, panel_y + panel_h - 30))

    def draw_victory_overlay(self):
        """
            Render victory screen overlay.
        """
        # Dark transparent overlay
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        panel_w, panel_h = 560, 320
        panel_x = (self.window_width - panel_w) // 2
        panel_y = (self.window_height - panel_h) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, (235, 245, 235), panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (120, 180, 120), panel_rect, 3, border_radius=14)

        title = self.font_title.render("VICTOIRE !", True, (30, 140, 30))
        self.screen.blit(title, (panel_x + (panel_w - title.get_width()) // 2, panel_y + 18))

        # Wrap message lines
        lines = [l for l in self.victory_message.split('\n') if l.strip()] or ["Partie gagnée !"]
        y = panel_y + 80
        for line in lines:
            surf = self.font_text.render(line, True, self.COLOR_TEXT)
            self.screen.blit(surf, (panel_x + 30, y))
            y += 32

        stats = f"Pas: {self.player.pas}  Or: {self.player.or_}  Gemmes: {self.player.gemmes}  Clés: {self.player.cles}"
        stats_surf = self.font_small.render(stats, True, (60, 90, 60))
        self.screen.blit(stats_surf, (panel_x + 30, panel_y + panel_h - 110))

        instr1 = self.font_small.render("R: recommencer", True, self.COLOR_TEXT)
        instr2 = self.font_small.render("ESC: quitter", True, self.COLOR_TEXT)
        self.screen.blit(instr1, (panel_x + 30, panel_y + panel_h - 70))
        self.screen.blit(instr2, (panel_x + 30, panel_y + panel_h - 40))




# ====================== MAIN ======================
if __name__ == "__main__":
    Game().run()
