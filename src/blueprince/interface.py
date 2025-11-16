import pygame
from .world import Manor
from .entities import Player


class Game:
    def __init__(self):
        pygame.init()

        # === Dimensions fixes du manoir ===
        self.COLS = 5
        self.ROWS = 9
        self.cell_size = 90
        self.margin = 5

        # === Dimensions de la fenêtre ===
        self.game_width = self.COLS * self.cell_size
        self.hud_width = int(self.cell_size * 6)
        self.window_width = self.game_width + self.hud_width
        self.window_height = self.ROWS * self.cell_size

        # === Création de la fenêtre ===
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Blue Prince - Interface avec HUD")

        # === Couleurs ===
        self.COLOR_BG = (10, 10, 20)
        self.COLOR_HUD = (240, 240, 240)
        self.COLOR_PLAYER = (255, 215, 0)
        self.COLOR_TEXT = (10, 10, 10)

        # === Police d’écriture ===
        self.font_title = pygame.font.SysFont("arial", 28, bold=True)
        self.font_text = pygame.font.SysFont("arial", 22)
        self.font_small = pygame.font.SysFont("arial", 20)

        # === SHOP MENU (pour les pièces jaunes) ===
        self.shop_menu_active = False
        self.shop_index = 0
        self.shop_items = [
            ("Pomme", 2, lambda player: player.gagner_pas(2)),
            ("Banane", 3, lambda player: player.gagner_pas(3)),
            ("Gâteau", 8, lambda player: player.gagner_pas(10)),
            ("Sandwich", 12, lambda player: player.gagner_pas(15)),
            ("Repas", 20, lambda player: player.gagner_pas(25)),
            ("Clé", 10, lambda player: setattr(player, "cles", player.cles + 1)),
            ("Gemme", 3, lambda player: setattr(player, "gemmes", player.gemmes + 1)),
        ]

        # === Chargement et redimensionnement des icônes ===
        def load_icon(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.scale(img, (32, 32))
            except:
                # Fallback carré gris si image manquante
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

        # === Horloge et entités ===
        self.clock = pygame.time.Clock()
        self.manor = Manor()
        self.player = Player("Player")
        self.running = True

    # ====================== BOUCLE PRINCIPALE ======================
    def run(self):
        while self.running:
            self.handle_events()
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

                # ======================
                # 1) NAVIGATION NORMALE
                # ======================
                elif not self.shop_menu_active:
                    if event.key in (pygame.K_z, pygame.K_UP):
                        self.player.move("up", self.manor)
                    elif event.key in (pygame.K_s, pygame.K_DOWN):
                        self.player.move("down", self.manor)
                    elif event.key in (pygame.K_q, pygame.K_LEFT):
                        self.player.move("left", self.manor)
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        self.player.move("right", self.manor)

                    # Touche E = ouvrir menu shop si pièce jaune
                    elif event.key == pygame.K_e:
                        self.try_open_shop()

                # ======================
                # 2) MENU DU SHOP
                # ======================
                elif self.shop_menu_active:
                    if event.key == pygame.K_UP:
                        self.shop_index = (self.shop_index - 1) % len(self.shop_items)
                    elif event.key == pygame.K_DOWN:
                        self.shop_index = (self.shop_index + 1) % len(self.shop_items)
                    elif event.key == pygame.K_SPACE:
                        self.confirm_shop_purchase()
                    elif event.key == pygame.K_e:
                        self.shop_menu_active = False

    # ========================= SHOP LOGIC =========================

    def try_open_shop(self):
        """Ouvre le shop si on est dans une pièce jaune."""
        rx, ry = self.player.position
        room = self.manor.get_room(rx, ry)
        if not room:
            return

        if getattr(room, "color", None) == "yellow":
            self.shop_menu_active = True
            self.shop_index = 0

    def confirm_shop_purchase(self):
        """Achète l'objet sélectionné."""
        name, cost, effect = self.shop_items[self.shop_index]

        if self.player.or_ < cost:
            return  # pas assez d'or

        self.player.or_ -= cost
        effect(self.player)

    # ====================== AFFICHAGE ======================
    def render(self):
        # --- 1. Zone du manoir ---
        self.screen.fill(self.COLOR_BG, (0, 0, self.game_width, self.window_height))

        # --- 2. Dessiner les pièces ---
        for y in range(self.ROWS):
            for x in range(self.COLS):
                room = self.manor.get_room(x, y)
                if room is not None:
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

        # --- 3. HUD ---
        hud_rect = pygame.Rect(self.game_width, 0, self.hud_width, self.window_height)
        pygame.draw.rect(self.screen, self.COLOR_HUD, hud_rect)

        # --- 4. Joueur ---
        px, py = self.player.position
        player_rect = pygame.Rect(
            px * self.cell_size + self.margin + 20,
            py * self.cell_size + self.margin + 20,
            self.cell_size - 40,
            self.cell_size - 40
        )
        pygame.draw.rect(self.screen, self.COLOR_PLAYER, player_rect)

        # --- 5. Inventaire ---
        self.draw_inventory(self.player, hud_rect)

        # --- 6. Menu du shop ---
        if self.shop_menu_active:
            self.draw_shop_menu(hud_rect)

        pygame.display.flip()

    # ====================== HUD SHOP ======================
    def draw_shop_menu(self, hud_rect):
        x = hud_rect.left + 40
        y = hud_rect.top + 350

        title = self.font_title.render("Magasin :", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 60

        for i, (name, cost, _) in enumerate(self.shop_items):
            color = (255, 200, 0) if i == self.shop_index else self.COLOR_TEXT
            line = self.font_small.render(f"{name} - {cost} or", True, color)
            self.screen.blit(line, (x, y))
            y += 30

        hint = self.font_small.render("UP/DOWN choisir  |  SPACE acheter  |  E fermer", True, self.COLOR_TEXT)
        self.screen.blit(hint, (x, y + 20))

    # ====================== INVENTAIRE ======================
    def draw_inventory(self, player, hud_rect):
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

        current_room = self.manor.get_room(*player.position)
        if current_room:
            y += 40
            label = self.font_text.render("Pièce actuelle :", True, color)
            self.screen.blit(label, (margin_x, y))
            room_name = self.font_small.render(current_room.name, True, color)
            self.screen.blit(room_name, (margin_x + 15, y + 25))
