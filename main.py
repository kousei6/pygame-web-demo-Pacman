from enum import Enum, auto
import heapq
import os
import random
import sys
import time
import pygame as pg
import math


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 640  # ゲームウィンドウの高さ
GRID_SIZE = 20
PLAYER_SPEED = 3
PLAYER_SIZE = 20
ENEMY_SIZE = 30

# 色の定義
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def fade_in_image(image: pg.Surface, screen: pg.Surface, duration: float = 2.0) -> None:
    """
    渡されたSurfaceをフェードイン表示する簡易関数。
    引数:
        image (pg.Surface): フェードイン表示する画像
        screen (pg.Surface): メイン画面
        duration (float): フェードインにかける秒数
    """
    clock = pg.time.Clock()
    start_time = time.time()

    # フェードイン用に、imageをコピーし alpha=0 から 255 へ少しずつ上げる
    alpha_surf = image.copy()
    alpha_surf.set_alpha(0)

    while True:
        elapsed = time.time() - start_time
        alpha = min(255, int((elapsed / duration) * 255))
        alpha_surf.set_alpha(alpha)

        screen.fill(BLACK)
        screen.blit(alpha_surf, (0, 0))
        pg.display.update()

        if alpha >= 255:
            break

        clock.tick(60)


def run_difficulty_menu_with_title(screen: pg.Surface) -> int:
    """
    タイトル画面の描画と、EASY / NORMAL / HARD を横に並べたカーソル操作を行う。
    戻り値として 1=EASY, 2=NORMAL, 3=HARD を返す。
    
    引数:
        screen (pg.Surface): メイン画面
    戻り値:
        int: 選択した難易度(1,2,3)
    """
    clock = pg.time.Clock()
    font_title = pg.font.Font(None, 100)
    font_menu  = pg.font.Font(None, 60)

    menu_items = ["EASY", "NORMAL", "HARD"]
    current_index = 0  # 0=EASY, 1=NORMAL, 2=HARD

    while True:
        # ---------- イベント処理 ------------
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LEFT:
                    current_index = (current_index - 1) % len(menu_items)
                elif event.key == pg.K_RIGHT:
                    current_index = (current_index + 1) % len(menu_items)
                elif event.key == pg.K_RETURN:
                    return current_index + 1  # 1,2,3

        # ---------- 画面描画 ------------
        screen.fill((0,0,0))

        # 1) タイトル文字を描画
        title_text = font_title.render("PacmanGame", True, (255, 255, 0))
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

        # 2) パックマンのイラスト（背景の一部として毎フレーム描画）
        pacman_center = (WIDTH // 2, HEIGHT // 2 - 50)
        pacman_radius = 100
        pacman_color = (255, 255, 0)
        pacman_mouth_angle = 30

        points = [pacman_center]
        for angle in range(pacman_mouth_angle, 360 - pacman_mouth_angle + 1):
            x = pacman_center[0] + pacman_radius * math.cos(math.radians(angle))
            y = pacman_center[1] - pacman_radius * math.sin(math.radians(angle))
            points.append((x, y))
        pg.draw.polygon(screen, pacman_color, points)

        # 目
        eye_position = (pacman_center[0] + pacman_radius // 4, pacman_center[1] - pacman_radius // 2)
        eye_radius = 10
        pg.draw.circle(screen, (0, 0, 0), eye_position, eye_radius)

        # 3) カーソル付き難易度メニュー(横並び)
        offset = 50  # 項目の間隔
        y_base = HEIGHT // 2 + 100

        # テキストを赤/白で切り替え
        easy_surf   = font_menu.render("EASY",   True, (  0,   0, 255) if current_index==0 else (255, 255, 255))
        normal_surf = font_menu.render("NORMAL", True, (  0, 255,   0) if current_index==1 else (255, 255, 255))
        hard_surf   = font_menu.render("HARD",   True, (255,   0,   0) if current_index==2 else (255, 255, 255))

        total_width = easy_surf.get_width() + normal_surf.get_width() + hard_surf.get_width() + offset*2
        start_x = WIDTH // 2 - total_width // 2

        x = start_x
        screen.blit(easy_surf,   (x, y_base))
        x += easy_surf.get_width() + offset
        screen.blit(normal_surf, (x, y_base))
        x += normal_surf.get_width() + offset
        screen.blit(hard_surf,   (x, y_base))

        font_copyright = pg.font.Font(None, 30)
        copyright_text = font_copyright.render("(c) 2025 Group15", True, (255, 255, 255))
        screen.blit(
            copyright_text,
            (WIDTH - copyright_text.get_width() - 10, HEIGHT - copyright_text.get_height() - 10)
        )

        # 4) 画面更新
        pg.display.update()
        clock.tick(60)


def get_grid_pos(pixel_x: int, pixel_y: int) -> tuple[int, int]:
    """
    ピクセル座標から、対応するグリッド座標を返す。
    
    引数:
        pixel_x (int): ピクセル座標(x)
        pixel_y (int): ピクセル座標(y)
    戻り値:
        tuple[int, int]: グリッド座標
    """
    return pixel_x // GRID_SIZE, pixel_y // GRID_SIZE


def get_pixel_pos(grid_x: int, grid_y: int) -> tuple[int, int]:
    """
    グリッド座標から、中心座標をピクセル単位で計算し返す。
    
    引数:
        grid_x (int): グリッド座標(x)
        grid_y (int): グリッド座標(y)
    戻り値:
        tuple[int, int]: ピクセル座標
    """
    pixel_x = grid_x * GRID_SIZE + GRID_SIZE // 2
    pixel_y = grid_y * GRID_SIZE + GRID_SIZE // 2
    return pixel_x, pixel_y


class Map:
    """
    マップの管理を行うクラス。
    テキストファイルから読み込んだマップデータ(map_file)を保持し、描画や
    マップ上の位置情報を提供する。
    """
    def __init__(self, map_file: str) -> None:
        self.dots_remaining = 0
        self.dots_eaten = 0

        # マップデータの読み込み
        self.map_data = []
        with open(map_file, 'r') as f:
            for line in f:
                row = [int(cell) for cell in line.strip().split()]
                self.map_data.append(row)
        self.height = len(self.map_data)
        self.width = len(self.map_data[0])
        
        # パワーエサとワープトンネルの位置を特定
        power_pellets = []
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == 3:
                    power_pellets.append({'x': x, 'y': y})
        self.power_pellets = power_pellets
        
        tunnels = []
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == 5:
                    tunnels.append({'x': x, 'y': y})
        self.tunnels = tunnels
        
        # プレイフィールドの作成
        playfield = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                cell = {
                    'path': self.map_data[y][x] in [0, 2, 3, 4, 5],
                    'dot': 1 if self.map_data[y][x] == 2 else 2 if self.map_data[y][x] == 3 else 0,
                    'intersection': False,
                    'tunnel': self.map_data[y][x] == 5
                }
                if cell['dot'] > 0:
                    self.dots_remaining += 1
                row.append(cell)
            playfield.append(row)
        
        # 交差点の判定
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if playfield[y][x]['path']:
                    paths = 0
                    if playfield[y-1][x]['path']: paths += 1
                    if playfield[y+1][x]['path']: paths += 1
                    if playfield[y][x-1]['path']: paths += 1
                    if playfield[y][x+1]['path']: paths += 1
                    playfield[y][x]['intersection'] = (paths > 2)
        self.playfield = playfield

        # 敵の初期位置を特定
        self.enemy_start_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y][x] == 4:
                    self.enemy_start_positions.append((x, y))
    
    def draw(self, screen: pg.Surface, field_start: tuple[int, int]) -> None:
        """
        マップを描画する。
        
        引数:
            screen (pg.Surface): メイン画面
            field_start (tuple[int, int]): マップを描画開始するピクセル座標
        """
        colors = {
            0: (0, 0, 0),       # 通路: 黒
            1: (54, 67, 100),   # 壁: 青
            4: (255, 192, 203), # ゴーストの家の入り口: ピンク
            5: (0, 255, 0)      # ワープトンネル: 緑
        }
        
        for y, row in enumerate(self.map_data):
            for x, cell in enumerate(row):
                rect_x = field_start[0] + (x * GRID_SIZE)
                rect_y = field_start[1] + (y * GRID_SIZE)
                if cell in colors:
                    pg.draw.rect(screen, colors[cell], (rect_x, rect_y, GRID_SIZE, GRID_SIZE))


class Player(pg.sprite.Sprite):
    """
    プレイヤー(パックマン)を管理するクラス。
    移動、アニメーション、残機管理、死亡処理などの機能を持つ。
    """
    def __init__(self, grid_pos: tuple[int, int], map_data: 'Map'):
        super().__init__()
        self.grid_pos = grid_pos
        self.map_data = map_data
        self.lives = 3  # 残機の初期値
        self.font = pg.font.Font(None, 30)

        # --- パックマン本体画像 (アニメ用) ---
        self.original_images = [
            pg.transform.scale(pg.image.load("fig/pacman_open.png").convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE)),
            pg.transform.scale(pg.image.load("fig/pacman_circle.png").convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE))
        ]
        self.current_frame = 0
        self.animation_counter = 0
        self.animation_speed = 5
        self.image = self.original_images[0]
        self.rect = self.image.get_rect()

        # --- 残機アイコン (小さめパックマン画像) ---
        self.life_icon = pg.transform.scale(
            pg.image.load("fig/pacman_circle.png").convert_alpha(),
            (int(PLAYER_SIZE * 0.8), int(PLAYER_SIZE * 0.8))
        )

        # 位置関連
        self.rect.center = get_pixel_pos(*grid_pos)
        self.target_pos = self.rect.center
        self.moving = False

        # 移動関連
        self.current_direction = None
        self.queued_direction = None

        # 回転関連
        self.angle = 0
        self.target_angle = 0
        self.rotation_speed = 45

        # ワープ関連
        self.can_warp = True
        self.last_warp_pos = None
        self.warp_cells = [tuple(cell.values()) for cell in map_data.tunnels]

        # 死亡アニメーション関連
        self.is_dying = False
        self.death_images = [
            pg.transform.scale(pg.image.load(f"fig/pacman_death/pacman_open_{i:02d}.png").convert_alpha(), 
                                (PLAYER_SIZE, PLAYER_SIZE))
            for i in range(20)
        ]
        self.death_frame = 0
        self.death_timer = 0
        self.death_duration = 4
        self.death_start_time = 0
        self.game_over = False

    def reset_position(self):
        """プレイヤーを初期位置にリセットする。"""
        self.rect.center = get_pixel_pos(*self.grid_pos)
        self.current_direction = None
        self.queued_direction = None
        self.moving = False
        self.angle = 0
        self.target_angle = 0
    
    def handle_input(self, keys: pg.key.ScancodeWrapper) -> None:
        """
        プレイヤーの入力を受け取り、移動方向を更新する。
        
        引数:
            keys (pg.key.ScancodeWrapper): 押下されているキー情報
        """
        if self.is_dying or self.game_over:
            return
        
        new_direction = None
        if keys[pg.K_LEFT]:
            new_direction = (-1, 0)
        elif keys[pg.K_RIGHT]:
            new_direction = (1, 0)
        elif keys[pg.K_UP]:
            new_direction = (0, -1)
        elif keys[pg.K_DOWN]:
            new_direction = (0, 1)
        
        if new_direction:
            self.queued_direction = new_direction
            if not self.moving:
                self.try_move(new_direction)
    
    def try_move(self, direction: tuple[int, int]) -> bool:
        """
        指定した方向へ移動可能か判定し、可能なら移動処理を開始する。
        
        引数:
            direction (tuple[int, int]): 移動方向 (x方向, y方向)
        戻り値:
            bool: 移動成功なら True、失敗なら False
        """
        current_pos = self.get_grid_pos()
        next_pos = (current_pos[0] + direction[0], current_pos[1] + direction[1])

        # 移動可能かどうかチェック
        if not self.is_valid_move(next_pos):
            return False

        # ワープトンネルの処理
        if self.map_data.playfield[next_pos[1]][next_pos[0]]['tunnel'] and self.can_warp:
            warp_pos = self.get_warp_destination(next_pos)
            if warp_pos:
                self.rect.center = get_pixel_pos(*warp_pos)
                self.target_pos = self.rect.center
                self.last_warp_pos = warp_pos
                self.can_warp = False
                # ワープ後の次ポジションも同様にチェック
                next_pos = (warp_pos[0] + direction[0], warp_pos[1] + direction[1])
                if not self.is_valid_move(next_pos):
                    return False

        self.current_direction = direction
        self.target_pos = get_pixel_pos(*next_pos)
        self.moving = True
        self.update_rotation(direction)
        return True

    def update_rotation(self, direction: tuple[int, int]) -> None:
        """
        プレイヤーが進もうとしている方向に応じて画像の回転角度を設定する。
        
        引数:
            direction (tuple[int, int]): 移動方向
        """
        new_angle = 0
        if direction[0] > 0:
            new_angle = 0   # 右
        elif direction[0] < 0:
            new_angle = 180 # 左
        elif direction[1] > 0:
            new_angle = 90  # 下
        elif direction[1] < 0:
            new_angle = 270 # 上
        
        angle_diff = (new_angle - self.angle) % 360
        if abs(angle_diff) == 180:
            self.angle = new_angle
            self.target_angle = new_angle
        else:
            if angle_diff > 180:
                angle_diff -= 360
            self.target_angle = self.angle + angle_diff

    def is_valid_move(self, grid_pos: tuple[int, int]) -> bool:
        """
        マップ上の指定した座標が移動可能かどうかを返す。
        
        引数:
            grid_pos (tuple[int, int]): グリッド座標
        戻り値:
            bool: 移動可能なら True
        """
        grid_x, grid_y = grid_pos
        return self.map_data.playfield[grid_y][grid_x]['path']
    
    def get_warp_destination(self, current_pos: tuple[int, int]) -> tuple[int, int] | None:
        """
        ワープトンネル通過後の座標を取得する。
        同じトンネルセルでの連続ワープは防ぐ。

        引数:
            current_pos (tuple[int, int]): 現在のグリッド座標
        戻り値:
            tuple[int, int] or None: ワープ先のグリッド座標(存在すれば)
        """
        if self.last_warp_pos == current_pos:
            return None
        for cell in self.warp_cells:
            if cell != current_pos and cell != self.last_warp_pos:
                return cell
        return None

    def update(self) -> None:
        """
        プレイヤーの状態を更新する。移動や回転アニメーション、死亡アニメーションを処理。
        """
        if self.is_dying:
            self.update_death_animation()
            return
        
        if self.moving:
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            
            if abs(dx) <= PLAYER_SPEED and abs(dy) <= PLAYER_SPEED:
                self.rect.center = self.target_pos
                self.moving = False
                if self.queued_direction:
                    if not self.try_move(self.queued_direction):
                        if self.current_direction:
                            self.try_move(self.current_direction)
                elif self.current_direction:
                    self.try_move(self.current_direction)

                current_pos = self.get_grid_pos()
                if not self.is_tunnel_position(current_pos):
                    self.can_warp = True
                    self.last_warp_pos = None
            else:
                move_x = PLAYER_SPEED * (1 if dx > 0 else -1 if dx < 0 else 0)
                move_y = PLAYER_SPEED * (1 if dy > 0 else -1 if dy < 0 else 0)
                self.rect.centerx += move_x
                self.rect.centery += move_y
        
        # 回転
        if self.angle != self.target_angle:
            angle_diff = self.target_angle - self.angle
            if abs(angle_diff) <= self.rotation_speed:
                self.angle = self.target_angle
            else:
                self.angle += self.rotation_speed if angle_diff > 0 else -self.rotation_speed
        
        # アニメーション
        self.update_animation()
        
        # 角度に基づいて画像を回転
        self.image = pg.transform.rotate(self.original_images[self.current_frame], -self.angle)
    
    def update_animation(self) -> None:
        """
        通常移動時のパックマンのアニメーションを更新する。
        """
        if self.moving:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % 2
        else:
            self.current_frame = 0
            self.animation_counter = 0
    
    def draw(self, screen: pg.Surface) -> None:
        """
        プレイヤーをメイン画面に描画する。残機数の描画も行う。

        引数:
            screen (pg.Surface): メイン画面
        """
        # 1) プレイヤー本体を描画
        screen.blit(self.image, self.rect)

        # 2) "LIFE" の文字を描画
        label_text = self.font.render("LIFE", True, (255, 255, 255))
        screen.blit(label_text, (WIDTH - 180, 10)) 

        # 3) 残機アイコンを右上に横並びで描画
        offset = 30
        x_base = (WIDTH - 50)
        y_base = 10
        for i in range(self.lives):
            icon_x = x_base - i * offset
            icon_y = y_base
            screen.blit(self.life_icon, (icon_x, icon_y))

    def get_grid_pos(self) -> tuple[int, int]:
        """プレイヤーの現在グリッド座標を返す。"""
        return (self.rect.centerx // GRID_SIZE, self.rect.centery // GRID_SIZE)
    
    def is_tunnel_position(self, pos: tuple[int, int]) -> bool:
        """マップ上の指定座標がワープトンネルかどうか判定する。"""
        x, y = pos
        return self.map_data.playfield[y][x]['tunnel']
    
    def start_death_animation(self) -> None:
        """
        プレイヤーの死亡アニメーションを開始する。
        残機を一つ減らし、死亡アニメーション後にリセットを行う。
        """
        self.is_dying = True
        self.lives -= 1
        self.death_frame = 0
        self.death_timer = 0
        self.death_start_time = time.time()
        self.image = self.death_images[0]
    
    def update_death_animation(self) -> None:
        """
        死亡アニメーションの進行を管理。アニメ終了後は残機を確認し、ゲームオーバーか
        リスポーンかを判定する。
        """
        current_time = time.time()
        time_elapsed = current_time - self.death_start_time
        
        frame_index = int((time_elapsed / self.death_duration) * len(self.death_images))
        if frame_index < len(self.death_images):
            self.image = self.death_images[frame_index]
        else:
            self.is_dying = False
            if self.lives <= 0:
                self.game_over = True
                return
            
            self.death_frame = 0
            self.image = self.original_images[0]
            self.reset_position()
            if Enemy.enemies_group:
                for enemy in Enemy.enemies_group:
                    enemy.reset(enemy.enemy_id)


class EnemyMode(Enum):
    """
    敵の行動モードを管理するための Enum。
    """
    CHASE = auto()
    TERRITORY = auto()
    WEAK = auto()


class Enemy(pg.sprite.Sprite):
    """
    敵キャラクター（ゴースト）を管理するクラス。
    追跡やテリトリーモード、弱体化モードなど、モードごとに行動を変化させる。
    """
    enemies_group: list['Enemy'] = []

    def __init__(self, enemy_id: int, player: 'Player', map_data: 'Map') -> None:
        super().__init__()
        self.enemy_id = enemy_id
        self.player = player
        self.map_data = map_data
        Enemy.enemies_group.append(self)

        image_idex = [0, 4, 5, 7]
        
        self.normal_image_base = pg.transform.scale(
            pg.image.load(f"fig/{image_idex[enemy_id-1]}.png").convert_alpha(), 
            (ENEMY_SIZE, ENEMY_SIZE)
        )
        self.normal_image_lst = {
            (-1, 0): self.normal_image_base,
            (1, 0): pg.transform.flip(self.normal_image_base, True, False),
            (0, -1): self.normal_image_base,
            (0, 1): pg.transform.rotozoom(self.normal_image_base, 90, 1)
        }
        self.initial_direction = (1, 0)
        self.normal_image = self.normal_image_lst[self.initial_direction]

        self.weak_images = [
            pg.transform.scale(pg.image.load("fig/chicken.png").convert_alpha(), (ENEMY_SIZE, ENEMY_SIZE)),
            pg.transform.scale(pg.image.load("fig/food_christmas_chicken.png").convert_alpha(), (ENEMY_SIZE, ENEMY_SIZE)),
            pg.transform.scale(pg.image.load("fig/chicken_honetsuki.png").convert_alpha(), (ENEMY_SIZE, ENEMY_SIZE)),
        ]
        self.current_weak_image = None

        self.eaten_image = pg.transform.scale(
            pg.image.load("fig/pet_hone.png").convert_alpha(), 
            (ENEMY_SIZE, ENEMY_SIZE)
        )
        
        self.image = self.normal_image
        self.rect = self.image.get_rect()
        
        # 初期位置の設定
        self.start_pos = map_data.enemy_start_positions[enemy_id-1]
        self.rect.center = get_pixel_pos(*self.start_pos)
        
        # 移動関連
        self.default_speed = 2
        self.speed = self.default_speed
        self.current_path = []
        self.moving = False
        self.direction = self.initial_direction
        
        # スタート時の遅延
        self.start_delay = enemy_id * 1
        self.game_start_time = time.time()
        self.can_move = False
        
        # モード関連
        self.mode = EnemyMode.CHASE
        self.mode_timer = time.time()
        self.chase_duration = 15
        self.territory_duration = 4
        self.weak_duration = 10
        self.weak_start_time = 0
        self.is_eaten = False
        
        self.territory_corners = [
            (1, 1), 
            (1, map_data.height-2),
            (map_data.width-2, 1),
            (map_data.width-2, map_data.height-2)
        ]
        self.current_corner = self.enemy_id - 1
        self.revive_delay = 3
        self.revive_start_time = 0
        self.is_reviving = False
        self.restart_delay = 0
        self.restart_start_time = 0
        self.is_restarting = False

        self.eaten_after = False

    def update(self) -> None:
        """
        敵の状態を更新する。モードの切り替え、A*経路探索、プレイヤー衝突判定など。
        """
        current_time = time.time()
        if self.is_reviving:
            if current_time - self.revive_start_time >= self.revive_delay:
                self.is_reviving = False
                self.can_move = True
            else:
                return

        if self.is_restarting:
            if current_time - self.restart_start_time >= self.restart_delay:
                self.is_restarting = False
                self.can_move = True
            else:
                return
        
        if self.eaten_after:
            # 敵が食べられたあとの一時停止
            time.sleep(1)
            self.eaten_after = False
        
        # スタート時の遅延
        if not self.can_move and not self.is_reviving and not self.is_restarting:
            if current_time - self.game_start_time >= self.start_delay:
                self.can_move = True
            else:
                return
        
        # 食べられた状態
        if self.is_eaten:
            if not self.moving:
                self.current_path = self.find_path(self.get_grid_pos(), self.start_pos)
                if self.current_path:
                    self.moving = True
            self.move()
            if self.get_grid_pos() == self.start_pos:
                self.revive()
            return
        
        # 通常モード(CHASE or TERRITORY)
        if self.mode != EnemyMode.WEAK:
            if self.mode == EnemyMode.CHASE and current_time - self.mode_timer > self.chase_duration:
                self.mode = EnemyMode.TERRITORY
                self.mode_timer = current_time
            elif self.mode == EnemyMode.TERRITORY and current_time - self.mode_timer > self.territory_duration:
                self.mode = EnemyMode.CHASE
                self.mode_timer = current_time
        else:
            # WEAKモード
            if current_time - self.weak_start_time > self.weak_duration:
                self.mode = EnemyMode.CHASE
                self.image = self.normal_image_lst[self.initial_direction]
                self.speed = self.default_speed
        
        # 経路探索
        if not self.moving and self.can_move:
            target = self.get_target_position()
            self.current_path = self.find_path(self.get_grid_pos(), target)
            if self.current_path:
                self.moving = True
        
        # 移動
        self.move()
        
        # プレイヤー衝突判定
        if pg.sprite.collide_rect(self, self.player):
            if self.mode == EnemyMode.WEAK and not self.is_eaten:
                self.get_eaten()
            elif self.mode != EnemyMode.WEAK and not self.is_eaten:
                self.player.start_death_animation()

    def get_target_position(self) -> tuple[int, int]:
        """
        敵が次に向かうターゲット座標を決定する。
        通常モード(CHASE/TERRITORY)の場合とWEAKモードの場合で処理が異なる。
        """
        if self.mode == EnemyMode.WEAK:
            return self.get_random_position()
        
        if self.mode == EnemyMode.TERRITORY:
            return self.territory_corners[self.current_corner]
        
        # CHASEモード時の行動パターンはenemy_idにより変化
        player_pos = self.player.get_grid_pos()
        if self.enemy_id == 1:
            return player_pos
        elif self.enemy_id == 2:
            return self.get_position_ahead(player_pos, 4)
        elif self.enemy_id == 3:
            return self.get_pincer_position()
        else:  # enemy_id == 4
            distance = self.calculate_distance(self.get_grid_pos(), player_pos)
            return player_pos if distance > 8 else self.get_random_position()

    def find_path(self, start: tuple[int, int], goal: tuple[int, int]) -> list:
        """
        A* アルゴリズムを用いて、start から goal までの最短経路を求める。
        
        引数:
            start (tuple[int, int]): 開始座標
            goal (tuple[int, int]): 目標座標
        戻り値:
            list: 最短経路を構成する座標のリスト
        """
        def heuristic(a: tuple[int, int], b: tuple[int, int]) -> int:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while frontier:
            current = heapq.heappop(frontier)[1]
            if current == goal:
                break
            
            for next_pos in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(next_pos, goal)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current
        
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path if len(path) > 1 else []

    def move(self) -> None:
        """
        経路に沿って移動する。next_pos に到達したらリストから削除して、次の座標へ進む。
        """
        if not self.moving or not self.current_path:
            return
        
        next_pos = self.current_path[0]
        target = get_pixel_pos(*next_pos)
        current_pos = pg.math.Vector2(self.rect.center)
        target_pos = pg.math.Vector2(target)
        
        move_vector = target_pos - current_pos
        distance = move_vector.length()
        
        if distance <= self.speed:
            self.rect.center = target
            self.current_path.pop(0)
            if not self.current_path:
                self.moving = False
                if self.mode == EnemyMode.TERRITORY:
                    self.current_corner = (self.current_corner + 1) % 4
        else:
            if move_vector.length() > 0:
                move_vector = move_vector.normalize() * self.speed
                self.rect.center = tuple(current_pos + move_vector)

                # 移動方向
                if abs(move_vector.x) > abs(move_vector.y):
                    self.direction = (1 if move_vector.x > 0 else -1, 0)
                else:
                    self.direction = (0, 1 if move_vector.y > 0 else -1)

                # 画像の向き
                if self.direction in self.normal_image_lst and not self.is_eaten and self.mode != EnemyMode.WEAK:
                    self.image = self.normal_image_lst[self.direction]

    def make_weak(self) -> None:
        """
        敵を弱体化(WEAK)モードにする。ランダムで選ばれた弱体化画像に切り替えて動きを遅くする。
        """
        if not self.is_eaten:
            self.mode = EnemyMode.WEAK
            self.weak_start_time = time.time()
            if self.current_weak_image is None:
                self.current_weak_image = random.choice(self.weak_images)
            self.image = self.current_weak_image
            self.speed = self.default_speed * 0.8

    def get_eaten(self) -> None:
        """
        プレイヤーに食べられた時の処理。
        画像を食べられた用の画像に変え、リスポーン位置へ移動するまで速度を上げる。
        """
        self.is_eaten = True
        self.image = self.eaten_image
        self.speed = self.default_speed * 2
        self.current_path = []
        self.moving = False
        self.eaten_after = True
    
    def revive(self) -> None:
        """
        敵をリスポーンさせる。位置や状態を初期化し、少し待ってから追跡行動を再開する。
        """
        self.reset()
        self.mode = EnemyMode.CHASE
        self.mode_timer = time.time()
        self.weak_start_time = 0
        self.is_eaten = False
        self.is_reviving = True
        self.revive_start_time = time.time()
        self.can_move = False
    
    def reset(self, delay=0.0) -> None:
        """
        敵を初期位置に戻し、初期設定にリセットする。開始までの遅延時間を指定可能。
        
        引数:
            delay (float): 再スタートまでの遅延秒数
        """
        self.rect.center = get_pixel_pos(*self.start_pos)
        self.speed = self.default_speed
        self.current_path = []
        self.moving = False
        self.direction = self.initial_direction
        self.image = self.normal_image_lst[self.initial_direction]
        self.mode = EnemyMode.CHASE
        self.mode_timer = time.time()
        self.current_weak_image = None
        self.can_move = False
        self.is_restarting = True
        self.restart_delay = delay
        self.restart_start_time = time.time()

    def get_grid_pos(self) -> tuple[int, int]:
        """敵の現在グリッド座標を返す。"""
        return self.rect.centerx // GRID_SIZE, self.rect.centery // GRID_SIZE

    def get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """
        A*用の近傍ノードを返す。壁ではなくpathがTrueになっているセルが隣接セルとなる。
        """
        x, y = pos
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < self.map_data.width and 
                0 <= ny < self.map_data.height and 
                self.map_data.playfield[ny][nx]['path']):
                neighbors.append((nx, ny))
        return neighbors

    def calculate_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> int:
        """マップ上の2点間のマンハッタン距離を返す。"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_position_ahead(self, pos: tuple[int, int], distance: int) -> tuple[int, int]:
        """
        指定した距離だけ先の座標を返す。
        主にプレイヤーの正面に移動するゴーストの行動を実装するために使用。
        """
        dx = pos[0] - self.get_grid_pos()[0]
        dy = pos[1] - self.get_grid_pos()[1]
        
        if abs(dx) > abs(dy):
            for d in range(distance, 0, -1):
                new_x = pos[0] + (d if dx > 0 else -d)
                if (0 <= new_x < self.map_data.width and 
                    self.map_data.playfield[pos[1]][new_x]['path']):
                    return (new_x, pos[1])
        else:
            for d in range(distance, 0, -1):
                new_y = pos[1] + (d if dy > 0 else -d)
                if (0 <= new_y < self.map_data.height and 
                    self.map_data.playfield[new_y][pos[0]]['path']):
                    return (pos[0], new_y)
        return pos

    def get_pincer_position(self) -> tuple[int, int]:
        """
        「挟み撃ち」ゴースト用のターゲット座標を計算する。
        他のゴーストの位置を参照し、プレイヤーと他ゴーストの座標から2倍先の位置を狙う。
        """
        if not Enemy.enemies_group or len(Enemy.enemies_group) < 1:
            return self.get_grid_pos()
        enemy1 = Enemy.enemies_group[0]
        if not enemy1:
            return self.get_grid_pos()
        enemy1_pos = enemy1.get_grid_pos()
        player_pos = self.player.get_grid_pos()
        dx = player_pos[0] - enemy1_pos[0]
        dy = player_pos[1] - enemy1_pos[1]
        
        target_x = enemy1_pos[0] + dx * 2
        target_y = enemy1_pos[1] + dy * 2
        
        if (0 <= target_x < self.map_data.width and 
            0 <= target_y < self.map_data.height and 
            self.map_data.playfield[target_y][target_x]['path']):
            return (target_x, target_y)
        
        min_distance = float('inf')
        best_pos = enemy1_pos
        
        for y in range(max(0, target_y-2), min(self.map_data.height, target_y+3)):
            for x in range(max(0, target_x-2), min(self.map_data.width, target_x+3)):
                if self.map_data.playfield[y][x]['path']:
                    dist = abs(x - target_x) + abs(y - target_y)
                    if dist < min_distance:
                        min_distance = dist
                        best_pos = (x, y)
        
        return best_pos

    def get_random_position(self) -> tuple[int, int]:
        """
        マップ内の通行可能セルからランダムに1つ選んで返す。
        WEAKモードなど、ランダム移動に使用。
        """
        valid_positions = []
        for y in range(self.map_data.height):
            for x in range(self.map_data.width):
                if self.map_data.playfield[y][x]['path']:
                    valid_positions.append((x, y))
        return random.choice(valid_positions) if valid_positions else self.get_grid_pos()


class Item(pg.sprite.Sprite):
    """
    アイテム（エサ）を管理するクラス。衝突判定によりスコアを加算し自身を消滅する。
    """
    def __init__(self, grid_pos: tuple[int, int], item_type: int, score: 'Score') -> None:
        super().__init__()
        self.image = pg.Surface((GRID_SIZE, GRID_SIZE), pg.SRCALPHA)
        self.grid_pos = grid_pos
        self.item_type = item_type
        self.score = score
        self.eat_count = 0
        
        center_x = GRID_SIZE // 2
        center_y = GRID_SIZE // 2

        if self.item_type == 1: # 通常エサ
            self.color = (255, 105, 180)
            self.radius = 3
            pg.draw.circle(self.image, self.color, (center_x, center_y), self.radius)
        elif self.item_type == 2: # パワーエサ
            self.color = (255, 105, 180)
            self.radius = 6
            pg.draw.circle(self.image, self.color, (center_x, center_y), self.radius)
        
        self.rect = self.image.get_rect(center=get_pixel_pos(*grid_pos))
    
    def update(self, player: 'Player'):
        """
        プレイヤーとの衝突を検知し、衝突した場合はスコアを加算して自身を削除する。
        
        引数:
            player (Player): プレイヤーオブジェクト
        """
        if pg.sprite.collide_rect(self, player):
            self.score.value += 20
            self.kill()
            self.eat_count += 1


class Score:
    """
    スコアを管理・表示するクラス。
    """
    def __init__(self):
        self.font = pg.font.Font(None, 40)
        self.color = (255, 255, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH - 110, HEIGHT - 50

    def draw(self, screen: pg.Surface):
        """
        スコアを画面右下に描画する。
        
        引数:
            screen (pg.Surface): メイン画面
        """
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class DebugInfo:
    """
    デバッグ情報を表示するクラス。
    プレイヤーや敵の位置、所要時間、アイテム状態などを描画する。
    """
    def __init__(self, player: 'Player', enemies: pg.sprite.Group, baits: pg.sprite.Group) -> None:
        self.player = player
        self.enemies = enemies
        self.baits = baits
        self.font = pg.font.Font(None, 30)
        self.item_count = len(baits)
        self.items_eaten = 0
        self.enemy_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

    def update(self):
        """フレームごとにデバッグ情報の更新を行う。"""
        self.items_eaten = self.item_count - len(self.baits)

    def draw(self, screen: pg.Surface):
        """
        画面右側に各種デバッグ情報を描画する。
        
        引数:
            screen (pg.Surface): メイン画面
        """
        # プレイヤー情報
        player_pos_text = self.font.render(f"Player Pos: {self.player.get_grid_pos()}", True, WHITE)
        screen.blit(player_pos_text, (WIDTH - 500, 20))
        player_moving_text = self.font.render(f"Moving: {self.player.moving}", True, WHITE)
        screen.blit(player_moving_text, (WIDTH - 500, 50))
        player_direction_text = self.font.render(f"Direction: {self.player.current_direction}", True, WHITE)
        screen.blit(player_direction_text, (WIDTH - 500, 80))

        # 起動からの経過秒表示
        elapsed_ms = pg.time.get_ticks()  
        elapsed_sec = elapsed_ms / 1000
        current_time_text = self.font.render(f"Time: {elapsed_sec:.2f}", True, WHITE)
        screen.blit(current_time_text, (WIDTH - 500, 110))

        # 敵の情報
        for i, enemy in enumerate(self.enemies):
            color_rect = pg.Surface((20, 20))
            color_rect.fill(self.enemy_colors[i])
            screen.blit(color_rect, (WIDTH - 500, 180 + i * 50))

            enemy_info_text = self.font.render(
                f"Enemy {enemy.enemy_id}: {enemy.mode.name}, Moving: {enemy.moving}, Target: {enemy.get_target_position()}",
                True, WHITE
            )
            screen.blit(enemy_info_text, (WIDTH - 480, 180 + i * 50))

            target_pos = enemy.get_target_position()
            target_rect = pg.Rect(get_pixel_pos(*target_pos), (10, 10))
            pg.draw.rect(screen, self.enemy_colors[i], target_rect)
            if enemy.current_path and len(enemy.current_path) >= 2:
                points = [get_pixel_pos(*pos) for pos in enemy.current_path]
                pg.draw.lines(screen, self.enemy_colors[i], False, points, 3)

        # アイテム情報
        item_count_text = self.font.render(f"Total Items: {self.item_count}", True, WHITE)
        screen.blit(item_count_text, (WIDTH - 500, 450))
        items_eaten_text = self.font.render(f"Items Eaten: {self.items_eaten}", True, WHITE)
        screen.blit(items_eaten_text, (WIDTH - 500, 480))


def draw_start_screen(screen):
    """
    スタート画面を描画する関数。
    タイトルテキストとパックマンのイラスト、ENTERキー待ちのメッセージを表示する。
    
    引数:
        screen (pg.Surface): メイン画面
    """
    screen.fill((0, 0, 0))

    font_title = pg.font.Font(None, 100)
    title_text = font_title.render("PacmanGame", True, (255, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
     
    # パックマンのイラスト
    pacman_center = (WIDTH // 2, HEIGHT // 2 - 50)
    pacman_radius = 100
    pacman_color = (255, 255, 0)
    pacman_mouth_angle = 30

    points = [pacman_center]
    for angle in range(pacman_mouth_angle, 360 - pacman_mouth_angle + 1):
        x = pacman_center[0] + pacman_radius * math.cos(math.radians(angle))
        y = pacman_center[1] - pacman_radius * math.sin(math.radians(angle))
        points.append((x, y))
    pg.draw.polygon(screen, pacman_color, points)

    eye_position = (pacman_center[0] + pacman_radius // 4, pacman_center[1] - pacman_radius // 2)
    eye_radius = 10
    pg.draw.circle(screen, (0, 0, 0), eye_position, eye_radius)

    font_subtitle = pg.font.Font(None, 50)
    select_diff_text = font_subtitle.render("PRESS ENTER KEY", True, (255, 255, 255))

    select_diff_x = WIDTH // 2 - select_diff_text.get_width() // 2
    select_diff_y = HEIGHT // 2 + 50 + 50

    screen.blit(select_diff_text, (select_diff_x, select_diff_y))

    font_copyright = pg.font.Font(None, 30)
    copyright_text = font_copyright.render("(c) 2025 Group15", True, (255, 255, 255))
    screen.blit(
        copyright_text,
        (WIDTH - copyright_text.get_width() - 10, HEIGHT - copyright_text.get_height() - 10)
    )


def draw_game_over(screen):
    """
    ゲームオーバー画面を描画する関数。
    暗めのオーバーレイを敷き、その上に「GAME OVER」テキストなどを表示する。
    
    引数:
        screen (pg.Surface): メイン画面
    """
    # --- 薄暗いオーバーレイを全画面に敷く ---
    overlay = pg.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(64)
    screen.blit(overlay, (0, 0))

    font = pg.font.Font(None, 74)
    game_text = font.render("GAME", True, WHITE)
    over_text = font.render("OVER", True, WHITE)

    screen_center_x = WIDTH // 2
    screen_center_y = HEIGHT // 2

    game_rect = game_text.get_rect(centerx=screen_center_x, centery=screen_center_y - 50)
    over_rect = over_text.get_rect(centerx=screen_center_x, centery=screen_center_y + 50)
    
    screen.blit(game_text, game_rect)
    screen.blit(over_text, over_rect)
    
    # パックマン画像
    pacman_image = pg.transform.scale(pg.image.load("fig/pac-man1.png").convert_alpha(), (50, 50))
    pacman_rect = pacman_image.get_rect(center=(screen_center_x, screen_center_y))
    screen.blit(pacman_image, pacman_rect)

    font_instruction = pg.font.Font(None, 40)
    instruction_text = font_instruction.render("Press SPACE to return to Start Screen", True, (255, 255, 255))
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT * 2 // 3 - instruction_text.get_height() // 2))


def draw_game_clear(screen: pg.Surface, score: 'Score'):
    """
    ゲームクリア画面を描画する関数。
    クリアの文言と最終スコアを表示する。
    
    引数:
        screen (pg.Surface): メイン画面
        score (Score): スコア管理クラス
    """
    screen.fill((0, 0, 0))
    font_title = pg.font.Font(None, 100)
    title_text = font_title.render("GAME CLEAR!", True, (0, 255, 0))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 3 - title_text.get_height() // 2))

    font_score = pg.font.Font(None, 60)
    score_text = font_score.render(f"Final Score: {score.value}", True, (255, 255, 255))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - score_text.get_height() // 2))

    font_instruction = pg.font.Font(None, 40)
    instruction_text = font_instruction.render("Press SPACE to return to Start Screen", True, (255, 255, 255))
    screen.blit(instruction_text, (WIDTH // 2 - instruction_text.get_width() // 2, HEIGHT * 2 // 3 - instruction_text.get_height() // 2))


def input_map_data(map_n):
    """
    難易度(マップ番号)に応じて、マップやプレイヤー、スコア、エサ、敵等を初期化して返す。
    
    引数:
        map_n (int): 選択した難易度に応じたマップ番号(1,2,3)
    戻り値:
        tuple[Map, Player, Score, pg.sprite.Group, pg.sprite.Group, DebugInfo]:
            (map_data, player, score, baits, enemies, debug_info)
    """
    map_dic = {1: "map2.txt", 2: "map3.txt", 3: "map1.txt"}
    map_data = Map(map_dic[map_n])
    player = Player((1, 1), map_data)
    score = Score()
    baits = pg.sprite.Group()
    for x in range(map_data.height):
        for y in range(map_data.width):
            if map_data.playfield[x][y]["dot"] in [1, 2]:
                baits.add(Item((y, x), map_data.playfield[x][y]["dot"], score))

    Enemy.enemies_group = []
    enemies = pg.sprite.Group()
    for i in range(4):
        enemies.add(Enemy(i+1, player, map_data))
    
    debug_info = DebugInfo(player, enemies, baits)
    return map_data, player, score, baits, enemies, debug_info


def main():
    """
    メイン関数。
    ゲームループを管理し、スタート画面・ゲーム画面・ゲームオーバー画面・クリア画面の表示切り替えを行う。
    """
    pg.display.set_caption("Pacman")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    start = True
    game_clear = False
    tmr = 0
    clock = pg.time.Clock()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0

        if start:
            # 1) スタート画面用Surfaceを作り、描画
            start_screen = pg.Surface((WIDTH, HEIGHT))
            draw_start_screen(start_screen)  # スタート画面を描画

            # 2) まずは描画した内容を一度画面に反映
            screen.blit(start_screen, (0, 0))
            pg.display.update()

            # 3) Enter キーが押されるまで待機する
            waiting_for_enter = True
            while waiting_for_enter:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        pg.quit()
                        sys.exit()
                    elif event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                        waiting_for_enter = False

            # 4) カーソル付きメニューで難易度選択（Enterで抜ける）
            difficulty = run_difficulty_menu_with_title(screen)  # 1,2,3 を返す
            tmr = 0  # タイマーをリセット

            # 5) map_data等を読み込み
            map_data, player, score, baits, enemies, debug_info = input_map_data(difficulty)

            start = False  # スタート画面フラグOFF

        elif player and player.game_over:
            # プレイヤーが死亡してゲームオーバーになった場合
            draw_game_over(screen)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    start = True

        elif game_clear:
            # 全エサを食べきってクリアした場合
            draw_game_clear(screen, score)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                    start = True
                    game_clear = False
                    player.game_over = False

        else:
            # ゲームメイン画面
            screen.fill(BLACK)
            map_data.draw(screen, (0, 0))

            baits.draw(screen)
            baits.update(player)

            keys = pg.key.get_pressed()
            player.handle_input(keys)
            player.update()
            player.draw(screen)

            if not player.is_dying:
                enemies.update()
            enemies.draw(screen)

            debug_info.update()
            debug_info.draw(screen)

            score.draw(screen)

            # パワーエサの処理
            for bait in baits:
                if bait.item_type == 2 and pg.sprite.collide_rect(player, bait):
                    for enemy in enemies:
                        enemy.make_weak()

            # ゲームクリア判定
            if not baits:
                if not game_clear:
                    game_clear = True

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
