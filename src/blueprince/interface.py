import pygame
from world import Manor
from entities import Player


class Game:
    def __init__(self):
        pygame.init()

        # Dimensions fixes du manoir
        self.COLS = 5   # nombre de colonnes
        self.ROWS = 9   # nombre de lignes
        self.cell_size = 90
        self.margin = 5

        # Dimensions de la fenêtre
        self.game_width = self.COLS * self.cell_size
        self.hud_width = int(self.cell_size * 6)   # panneau inventaire large
        self.window_width = self.game_width + self.hud_width
        self.window_height = self.ROWS * self.cell_size

        # Création de la fenêtre
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Blue Prince – Interface avec HUD")

        # Couleurs
        self.COLOR_BG = (10, 10, 20)          # Couleur manoir
        self.COLOR_HUD = (240, 240, 240)      # Inventaire
        self.COLOR_PLAYER = (255, 200, 0)     # Jaune doré
        self.COLOR_TEXT = (0, 0, 0)           # Texte noir

        # Police d’écriture
        self.font_title = pygame.font.Font(None, 38)
        self.font_text = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)

        # Horloge et entités
        self.clock = pygame.time.Clock()
        self.manor = Manor()
        self.player = Player("Raouf")
        self.running = True


    ######## BOUCLE PRINCIPALE
    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(30)
        pygame.quit()


    ######### GESTION DES TOUCHES
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


    ###### AFFICHAGE
    ###### AFFICHAGE
    def render(self):
        # --- 1. Zone du manoir (fond noir) ---
        self.screen.fill(self.COLOR_BG, (0, 0, self.game_width, self.window_height))

        # --- 2. AJOUT : DESSINER LES PIÈCES DÉCOUVERTES ---
        # On parcourt toute la grille du manoir
        for y in range(self.ROWS):
            for x in range(self.COLS):
                room = self.manor.get_room(x, y) # On récupère la pièce à (x, y)
                
                # S'il y a une pièce ici (elle n'est pas "None")
                if room is not None:
                    # On définit le rectangle où dessiner
                    rect = pygame.Rect(
                        x * self.cell_size + self.margin,
                        y * self.cell_size + self.margin,
                        self.cell_size - 2 * self.margin,
                        self.cell_size - 2 * self.margin
                    )

                    # On vérifie si la pièce a une image
                    if room.image:
                        # On redimensionne l'image pour qu'elle rentre pile dans la case
                        scaled_image = pygame.transform.scale(room.image, (rect.width, rect.height))
                        self.screen.blit(scaled_image, rect)
                    else:
                        # Si l'image est None (comme notre Antechamber), on dessine un carré gris
                        pygame.draw.rect(self.screen, (100, 100, 100), rect)

        # --- 3. Panneau HUD (inventaire) ---
        pygame.draw.rect(
            self.screen,
            self.COLOR_HUD,
            (self.game_width, 0, self.hud_width, self.window_height)
        )

        # --- 4. Dessiner le joueur (PAR-DESSUS les pièces) ---
        px, py = self.player.position
        player_rect = pygame.Rect(
            px * self.cell_size + self.margin,
            py * self.cell_size + self.margin,
            self.cell_size - 2 * self.margin,
            self.cell_size - 2 * self.margin
        )
        pygame.draw.rect(self.screen, self.COLOR_PLAYER, player_rect) # Dessine un carré jaune vif

        # --- 5. Texte inventaire (Inchangé) ---
        title = self.font_title.render("Inventory:", True, self.COLOR_TEXT)
        self.screen.blit(title, (self.game_width + 40, 40))

        room_label = self.font_text.render("Entrée du manoir", True, self.COLOR_TEXT)
        self.screen.blit(room_label, (self.game_width + 40, 150))

        hint = self.font_small.render("(Inventaire à venir)", True, (80, 80, 80))
        self.screen.blit(hint, (self.game_width + 40, 100))

        # --- 6. Mettre à jour l'écran ---
        pygame.display.flip()

###### POINT D’ENTRÉE
if __name__ == "__main__":
    Game().run()
