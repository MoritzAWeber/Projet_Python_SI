import pygame
from world import Manor
from entities import Player


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
        pygame.display.set_caption("Blue Prince – Interface avec HUD")

        # === Couleurs ===
        self.COLOR_BG = (10, 10, 20)
        self.COLOR_HUD = (240, 240, 240)
        self.COLOR_PLAYER = (255, 215, 0)
        self.COLOR_TEXT = (10, 10, 10)

        # === Police d’écriture ===
        self.font_title = pygame.font.SysFont("arial", 28, bold=True)
        self.font_text = pygame.font.SysFont("arial", 22)
        self.font_small = pygame.font.SysFont("arial", 20)

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
        self.player = Player("Raouf")
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
                elif event.key in (pygame.K_z, pygame.K_UP):
                    self.player.move("up", self.manor)
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.player.move("down", self.manor)
                elif event.key in (pygame.K_q, pygame.K_LEFT):
                    self.player.move("left", self.manor)
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.player.move("right", self.manor)

    # ====================== AFFICHAGE ======================
    def render(self):
        # --- 1. Zone du manoir ---
        self.screen.fill(self.COLOR_BG, (0, 0, self.game_width, self.window_height))

        # --- 2. Dessiner les pièces découvertes ---
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

        # --- 3. Panneau HUD ---
        hud_rect = pygame.Rect(self.game_width, 0, self.hud_width, self.window_height)
        pygame.draw.rect(self.screen, self.COLOR_HUD, hud_rect)

        # --- 4. Dessiner le joueur ---
        px, py = self.player.position
        player_rect = pygame.Rect(
            px * self.cell_size + self.margin + 20,
            py * self.cell_size + self.margin + 20,
            self.cell_size - 40,
            self.cell_size - 40
        )
        pygame.draw.rect(self.screen, self.COLOR_PLAYER, player_rect)

        # --- 5. Inventaire dynamique ---
        self.draw_inventory(self.player, hud_rect)

        # --- 6. Rafraîchissement ---
        pygame.display.flip()

    # ====================== INVENTAIRE ======================
    def draw_inventory(self, player, hud_rect):
        """Affiche l'inventaire du joueur (HUD à droite)."""
        margin_x = hud_rect.left + 40
        y = hud_rect.top + 40
        color = self.COLOR_TEXT

        # === Titre ===
        title = self.font_title.render("Inventory:", True, color)
        self.screen.blit(title, (margin_x, y))
        y += 50

        # === Liste des stats ===
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
            y += 45  # espacement régulier

        # === Ligne de séparation ===
        pygame.draw.line(self.screen, (180, 180, 180),
                         (margin_x, y + 10),
                         (margin_x + 200, y + 10), 1)

        # === Objets permanents ===
        y += 30
        if player.inventory.permanents:
            label = self.font_text.render("Objets permanents :", True, color)
            self.screen.blit(label, (margin_x, y))
            y += 30
            for obj in player.inventory.permanents:
                text = self.font_small.render(f"- {obj.nom}", True, color)
                self.screen.blit(text, (margin_x + 15, y))
                y += 25

        # === Nom de la pièce actuelle ===
        current_room = self.manor.get_room(*player.position)
        if current_room:
            y += 40
            label = self.font_text.render("Pièce actuelle :", True, color)
            self.screen.blit(label, (margin_x, y))
            room_name = self.font_small.render(current_room.name, True, color)
            self.screen.blit(room_name, (margin_x + 15, y + 25))