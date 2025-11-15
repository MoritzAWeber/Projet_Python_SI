import pygame
import random
from .world import Manor, Antechamber
from .entities import Player, ObjetConsommable, ObjetPermanent, AutreObjet


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
        self.max_messages = 1

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
        self.player = Player("Raouf")
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

    # ====================== BOUCLE PRINCIPALE ======================
    def run(self):
        while self.running:
            self.handle_events()
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
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # ---- Navigation principale ----
                if not self.menu_active and not self.pickup_menu_active:
                    if event.key in (pygame.K_z, pygame.K_w):
                        self.player.move("up", self.manor)
                    elif event.key == pygame.K_s:
                        self.player.move("down", self.manor)
                    elif event.key == pygame.K_q:
                        self.player.move("left", self.manor)
                    elif event.key == pygame.K_d:
                        self.player.move("right", self.manor)
                    elif event.key == pygame.K_UP:
                        self.selected_door = "up"
                    elif event.key == pygame.K_DOWN:
                        self.selected_door = "down"
                    elif event.key == pygame.K_LEFT:
                        self.selected_door = "left"
                    elif event.key == pygame.K_RIGHT:
                        self.selected_door = "right"
                    elif event.key == pygame.K_SPACE:
                        self.open_door_menu()
                    elif event.key == pygame.K_e:
                        self.open_object_pickup_menu()

                # ---- Menu actif ----
                elif self.menu_active:
                    if event.key == pygame.K_LEFT:
                        self.menu_index = (self.menu_index - 1) % len(self.menu_choices)
                    elif event.key == pygame.K_RIGHT:
                        self.menu_index = (self.menu_index + 1) % len(self.menu_choices)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_room_choice()

                # ---- Ramasser des objets ----
                elif self.pickup_menu_active:
                    if event.key == pygame.K_UP:
                        self.pickup_index = (self.pickup_index - 1) % len(self.pickup_choices)
                    elif event.key == pygame.K_DOWN:
                        self.pickup_index = (self.pickup_index + 1) % len(self.pickup_choices)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_pickup_choice()
                    elif event.key == pygame.K_e:
                        self.pickup_menu_active = False

    # ====================== LOGIQUE DU JEU ======================
    def open_door_menu(self):
        
        if not self.player.can_move(self.selected_door, self.manor):
            self.add_message("Cette direction n'est pas accessible.")
            return

        x, y = self.player.position
        dx, dy = self.manor.get_direction_offset(self.selected_door)
        nx, ny = x + dx, y + dy

        if self.manor.get_room(nx, ny):
            self.player.move(self.selected_door, self.manor)
            return
        
        # Tirage aléatoire de 3 pièces disponibles
        self.menu_choices = self.manor.draw_three_rooms(self.player.position, self.selected_door, self.manor.pioche)
        self.menu_index = 0
        self.menu_active = True

    def confirm_room_choice(self):
        """Valide le choix de la pièce et la place dans le manoir."""
        chosen = self.menu_choices[self.menu_index]
        x, y = self.player.position
        dx, dy = self.manor.get_direction_offset(self.selected_door)

        nx, ny = x + dx, y + dy

        self.manor.place_room(nx, ny, chosen)
        self.menu_active = False
        print(f"Vous avez ajouté la pièce {chosen.name} en ({nx}, {ny})")

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

        if chosen.should_consume_on_pickup():
            room.objets.remove(chosen)
            self.add_message(f"Vous avez ramassé et utilisé: {chosen.nom}")
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
            self.end_game("Bravo ! Vous avez atteint l'Antechamber. Vous gagnez !")

    def end_game(self, message: str):
        print(message)
        self.running = False

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

        title = self.font_title.render("Inventory:", True, color)
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

    def draw_room_choice_menu(self, hud_rect):
        """Dessine le menu des 3 pièces tirées."""
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

    def draw_room_objects(self, hud_rect):
        """Shows the objects in the current Room"""
        x = hud_rect.left + 200
        y = hud_rect.top + 40

        px, py = self.player.position
        room = self.manor.get_room(px, py)

        if not room or not room.objets:
            return

        title = self.font_text.render("Objets dans la pièce:", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 30

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
                    display_text = display_text + f"x{obj.valeur}"
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




# ====================== MAIN ======================
if __name__ == "__main__":
    Game().run()
