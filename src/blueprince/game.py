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
        self.hud_width = int(self.cell_size * 6)
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
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        return getattr(room, "color", None) == "yellow"

    # ====================== BOUCLE PRINCIPALE ======================
    def run(self):
        while self.running:
            self.handle_events()
            if not self.game_over:
                self.check_end_conditions()
            self.render()
            self.clock.tick(30)
        pygame.quit()

    # ====================== GESTION DES TOUCHES ======================
    def handle_events(self):
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
                # MODE SHOP (magasin jaune)
                # ============================================================
                if self.shop_menu_active:
                    if event.key == pygame.K_UP:
                        self.shop_index = (self.shop_index - 1) % len(self.shop_items)
                    elif event.key == pygame.K_DOWN:
                        self.shop_index = (self.shop_index + 1) % len(self.shop_items)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_shop_choice()
                    elif event.key == pygame.K_e:
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
                # NAVIGATION NORMALE (aucun menu actif)
                # ============================================================
                if event.key in (pygame.K_z, pygame.K_w):
                    self.player.move("up", self.manor)
                elif event.key == pygame.K_s:
                    self.player.move("down", self.manor)
                elif event.key == pygame.K_q:
                    self.player.move("left", self.manor)
                elif event.key == pygame.K_d:
                    self.player.move("right", self.manor)

                # Sélection de la porte
                elif event.key == pygame.K_UP:
                    self.selected_door = "up"
                elif event.key == pygame.K_DOWN:
                    self.selected_door = "down"
                elif event.key == pygame.K_LEFT:
                    self.selected_door = "left"
                elif event.key == pygame.K_RIGHT:
                    self.selected_door = "right"

                # Ouvrir porte
                elif event.key == pygame.K_SPACE:
                    self.open_door_menu()

                # ============================================================
                # TOUCHE E — Ouvrir soit SHOP
                # ============================================================
                elif event.key == pygame.K_e:
                    if self.is_in_shop_room():
                        self.open_shop_menu(None)
                    else:
                        self.open_object_pickup_menu()


    # la gestion des niveau des portes + gestion de la demande des cles
    def open_door_menu(self):
        
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

        required_keys = lock_level
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
        """Benutzt einen Würfel um die 3 Raumoptionen neu zu würfeln."""
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
        """Valide le choix de la pièce et la place dans le manoir."""
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
                print("Nursery : +5 pas (draft Bedroom).")


    # choix de objet a echanger contre de l'or dans les pieces jaunes
    def open_shop_menu(self, shop_room):
            # --- empêcher ouverture si un autre menu est actif ---
            if self.menu_active or self.pickup_menu_active or self.confirm_door_active:
                return

            # --- items du shop ---
            self.shop_items = [
            ("Pomme", 2, lambda player: player.gagner_pas(2)),
            ("Banane", 3, lambda player: player.gagner_pas(3)),
            ("Gâteau", 8, lambda player: player.gagner_pas(10)),
            ("Clé", 10, lambda player: setattr(player, "cles", player.cles + 1)),
            ("Gemme", 3, lambda player: setattr(player, "gemmes", player.gemmes + 1)),
        ]

            self.shop_index = 0
            self.shop_menu_active = True
            self.current_shop_room = shop_room
            self.add_message("Magasin")

    def confirm_shop_choice(self):
            name, cost, effect = self.shop_items[self.shop_index]

            if self.player.or_ < cost:
                self.add_message(f"Pas assez d'or pour acheter {name}.")
                return

            self.player.or_ -= cost
            effect(self.player)
            self.add_message(f"Achat : {name} pour {cost} or.")

    def open_object_pickup_menu(self):
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        if not room or not room.objets:
            self.add_message("Il n'y a pas d'objets à ramasser ici.")
            return

        self.pickup_choices = room.objets
        self.pickup_index = 0
        self.pickup_menu_active = True

    def confirm_pickup_choice(self):
        """Valide le choix de l'objet à ramasser."""
        chosen = self.pickup_choices[self.pickup_index]
        x, y = self.player.position
        room = self.manor.get_room(x, y)
        if not room:
            return
        
        chosen.pick_up(self.player)

        if chosen in room.objets:
            room.objets.remove(chosen)
        if not room.objets:
            self.pickup_menu_active = False

    def check_end_conditions(self):
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
        self.game_over = True
        self.game_over_message = message
        # Also push a concise last message into log
        self.add_message("GAME OVER")

    def set_victory(self, message: str):
        self.victory = True
        self.victory_message = message
        self.add_message("VICTOIRE !")

    def restart_game(self):
        # Reinitialize dynamic game state (keep window & pygame)
        self.manor = Manor()
        self.player = Player("Player", self.manor)
        self.player.set_message_callback(self.add_message)
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
        self.screen.fill(self.COLOR_BG, (0, 0, self.game_width, self.window_height))

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

        # --- 6. Messages ---
        self.draw_messages(hud_rect)

        # --- 7. Menu de choix de pièces ---
        if self.menu_active:
            self.draw_room_choice_menu(hud_rect)

        # --- 8. Objets dans la pièce actuelle ---
        if not self.menu_active:
            self.draw_room_objects(hud_rect)

        if self.victory:
            self.draw_victory_overlay()
        elif self.game_over:
            self.draw_game_over_overlay()
        if self.shop_menu_active:
            self.draw_shop_menu(hud_rect)
        pygame.display.flip()

    # ====================== DESSINS HUD ======================

    
    def draw_manor(self):
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
        """Dessine la barre blanche autour de la porte sélectionnée."""
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
        """Affiche l'inventaire."""
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
        # Permanent objects section
        perm_title = self.font_small.render("Objets permanents:", True, color)
        self.screen.blit(perm_title, (margin_x, y))
        y += 26
        if self.player.inventory.permanents:
            for obj in self.player.inventory.permanents:
                line = self.font_small.render(f"- {obj.nom}", True, color)
                self.screen.blit(line, (margin_x + 8, y))
                y += 22
        else:
            none_line = self.font_small.render("(aucun)", True, color)
            self.screen.blit(none_line, (margin_x + 8, y))
            y += 22

    def draw_room_choice_menu(self, hud_rect):
        color = self.COLOR_TEXT
        base_y = hud_rect.top + 400
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

    def add_message(self, text: str):
        self.messages.append(text)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def draw_messages(self, hud_rect):
        x = hud_rect.left + 40
        y = hud_rect.top + 600
        title = self.font_text.render("Messages:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 30

        for msg in self.messages:
            surf = self.font_small.render(msg, True, self.COLOR_TEXT)
            self.screen.blit(surf, (x, y))
            y += 22

    def draw_shop_menu(self, hud_rect):
        x = hud_rect.left + 280
        y = hud_rect.top + 40

        title = self.font_title.render("Magasin:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 40

        if not self.shop_menu_active:
            # MODE PASSIF : comme les objets
            hint = self.font_small.render("E: ouvrir le menu", True, self.COLOR_TEXT)
            self.screen.blit(hint, (x, y))
            return

        # MODE ACTIF (menu ouvert)
        for i, (name, cost, _) in enumerate(self.shop_items):
            color = (255, 215, 0) if i == self.shop_index else self.COLOR_TEXT
            line = self.font_small.render(f"{i+1}. {name} - {cost} or", True, color)
            self.screen.blit(line, (x, y))
            y += 22

        y += 5
        hint = self.font_small.render("E: fermer le menu", True, self.COLOR_TEXT)
        self.screen.blit(hint, (x, y))

        hint2 = self.font_small.render("UP/DOWN + SPACE: acheter", True, self.COLOR_TEXT)
        self.screen.blit(hint2, (x, y + 22))



    def draw_room_objects(self, hud_rect):
        """Shows the objects in the current Room"""
        x = hud_rect.left + 280
        y = hud_rect.top + 40

        px, py = self.player.position
        room = self.manor.get_room(px, py)

        if not room or not room.objets:
            return
        title = self.font_title.render("Objets:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 40

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
                    if hasattr(obj, 'already_opened') and obj.already_opened:
                        display_text += "[Ouvert]"
                    elif hasattr(obj, 'lock_level'):
                        if obj.lock_level == 1:
                            display_text += "[Kit requis]"
                        elif obj.lock_level == 2:
                            display_text += "[Clé requise]"
                # Ajoute l'état pour les Coffres
                elif obj.__class__.__name__ == "Coffre":
                    if hasattr(obj, 'already_opened') and obj.already_opened:
                        display_text += "[Vide]"
                    else:
                        display_text += "[Marteau requis]"
                # Ajoute l'état pour EndroitCreuser
                elif obj.__class__.__name__ == "EndroitCreuser":
                    if hasattr(obj, 'already_dug') and obj.already_dug:
                        display_text += "[Creusé]"
                    else:
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
