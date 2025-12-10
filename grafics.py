import tkinter as tk
from tkinter import messagebox
import os
import sys
# Импортируем Pillow для красивого ресайза картинок
from PIL import Image, ImageTk
import main

# --- ЦВЕТА ---
COLOR_UNKNOWN = "#2b2b2b"  # Темно-серый (Туман)
COLOR_VISITED = "#ffffff"  # Белый (Открыто)


class WumpusApp:
    """Главный класс приложения, управляет окнами"""

    def __init__(self, root):
        self.root = root
        self.root.title("Wumpus World AI")
        # Увеличил размер окна, чтобы влезало меню справа
        self.root.geometry("1100x800")

        # Контейнер для смены экранов
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.current_frame = None

        self.show_menu()

    def show_menu(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MainMenu(self.container, self.start_game)
        self.current_frame.pack(fill="both", expand=True)

    def start_game(self, rows, cols, prob):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = GameUI(
            self.container, rows, cols, prob, self.show_menu)
        self.current_frame.pack(fill="both", expand=True)


class MainMenu(tk.Frame):
    def __init__(self, parent, start_callback):
        super().__init__(parent, bg="#f0f0f0")
        self.start_callback = start_callback

        tk.Label(self, text="Wumpus World", font=(
            "Helvetica", 32, "bold"), bg="#f0f0f0").pack(pady=40)

        settings_frame = tk.Frame(self, bg="#f0f0f0")
        settings_frame.pack(pady=20)

        self.rows_entry = self.create_input(
            settings_frame, "Высота (Rows):", "5")
        self.cols_entry = self.create_input(
            settings_frame, "Ширина (Cols):", "5")
        self.prob_entry = self.create_input(
            settings_frame, "Шанс ямы (0.0 - 1.0):", "0.13")

        tk.Button(self, text="НАЧАТЬ ИГРУ", font=("Arial", 16), bg="#4CAF50", fg="white",
                  command=self.validate_and_start, width=20, height=2).pack(pady=40)

    def create_input(self, parent, text, default):
        frame = tk.Frame(parent, bg="#f0f0f0")
        frame.pack(pady=5)
        tk.Label(frame, text=text, width=20, anchor="e",
                 bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT)
        entry = tk.Entry(frame, font=("Arial", 12), width=10)
        entry.insert(0, default)
        entry.pack(side=tk.LEFT, padx=10)
        return entry

    def validate_and_start(self):
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.cols_entry.get())
            prob = float(self.prob_entry.get())

            if rows < 3 or cols < 3:
                messagebox.showerror("Ошибка", "Минимальный размер карты 3x3")
                return
            if not (0 <= prob <= 1.0):
                messagebox.showerror(
                    "Ошибка", "Вероятность должна быть от 0.0 до 1.0")
                return

            self.start_callback(rows, cols, prob)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа")


class GameUI(tk.Frame):
    def __init__(self, parent, rows, cols, prob, back_callback):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.prob = prob
        self.back_callback = back_callback

        self.speed_delay = 500

        # --- ДИНАМИЧЕСКИЙ РАСЧЕТ РАЗМЕРА КЛЕТКИ ---
        # Максимальное место под поле: 800x750 пикселей (примерно)
        max_w = 800
        max_h = 750

        # Считаем, сколько пикселей может быть клетка
        cell_w = max_w // cols
        cell_h = max_h // rows

        # Берем минимум, чтобы клетки были квадратными
        # Ограничиваем: не больше 120 (слишком огромные), не меньше 20 (микроскопические)
        self.cell_size = min(cell_w, cell_h)
        self.cell_size = min(120, max(30, self.cell_size))

        print(f"Размер клетки: {self.cell_size}px")  # Для отладки

        self.icons = {}
        self.load_assets()

        self.setup_ui()
        self.start_new_game()

    def setup_ui(self):
        # Левая часть (Поле)
        self.canvas_frame = tk.Frame(self, bg="#333")
        self.canvas_frame.pack(side=tk.LEFT, fill="both", expand=True)

        # Центрируем канвас внутри фрейма
        self.canvas = tk.Canvas(
            self.canvas_frame, bg="gray", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        # Правая часть (Меню)
        self.panel = tk.Frame(self, bg="#e0e0e0", width=280)
        self.panel.pack(side=tk.RIGHT, fill="y")
        self.panel.pack_propagate(False)

        tk.Label(self.panel, text="Меню Игры", bg="#e0e0e0",
                 font=("Arial", 14, "bold")).pack(pady=15)

        tk.Button(self.panel, text="Сделать Шаг",
                  command=self.do_step, width=20, height=2).pack(pady=5)
        self.btn_run = tk.Button(self.panel, text="Авто-игра",
                                 command=self.auto_play, width=20, height=2, bg="lightgreen")
        self.btn_run.pack(pady=5)
        self.btn_pause = tk.Button(
            self.panel, text="Пауза", command=self.toggle_pause, width=20, height=2, bg="#FFD700")
        self.btn_pause.pack(pady=5)

        # Скорость
        tk.Label(self.panel, text="Скорость (мс):",
                 bg="#e0e0e0").pack(pady=(10, 0))
        speed_frame = tk.Frame(self.panel, bg="#e0e0e0")
        speed_frame.pack(pady=5)
        tk.Button(speed_frame, text="<<", command=self.decrease_speed,
                  width=3).pack(side=tk.LEFT)
        self.lbl_speed = tk.Label(
            speed_frame, text=f"{self.speed_delay}", width=5)
        self.lbl_speed.pack(side=tk.LEFT, padx=5)
        tk.Button(speed_frame, text=">>", command=self.increase_speed,
                  width=3).pack(side=tk.LEFT)

        tk.Button(self.panel, text="Рестарт (R)", command=self.reset_game,
                  width=20, height=2, bg="salmon").pack(pady=15)
        tk.Button(self.panel, text="🏠 В Меню", command=self.go_back,
                  width=20, height=2).pack(pady=5)

        self.status_var = tk.StringVar(value="Старт")
        tk.Label(self.panel, textvariable=self.status_var, bg="#e0e0e0", wraplength=260,
                 justify="left", font=("Consolas", 10)).pack(side=tk.BOTTOM, pady=20)

    def go_back(self):
        self.is_running = False
        self.back_callback()

    def start_new_game(self):
        self.world = main.WampusWorld(self.rows, self.cols, self.prob)
        self.agent = main.Agent(self.world, 0, 0, self.rows, self.cols)
        self.is_running = False
        self.game_over = False
        self.suicide_pos = None
        self.status_var.set("Новая игра.")
        self.btn_pause.config(text="Пауза", bg="#FFD700", state=tk.NORMAL)

        # Устанавливаем размер канваса ровно под клетки
        w = self.cols * self.cell_size
        h = self.rows * self.cell_size
        self.canvas.config(width=w, height=h)

        self.draw_grid()

    def reset_game(self):
        self.is_running = False
        self.start_new_game()

    def load_assets(self):
        """Загрузка с ресайзом через Pillow"""
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")

        # Размер иконок чуть меньше клетки, чтобы был отступ
        icon_size = int(self.cell_size * 0.8)
        # Для сенсоров (ветер/вонь) иконки поменьше
        sensor_size = int(self.cell_size * 0.4)

        # Имя файла -> (Ключ, Целевой размер)
        assets_config = {
            "agent.png": ("agent", icon_size),
            "wumpus.png": ("vantus", icon_size),
            "pit.png": ("pit", icon_size),
            "gold.png": ("gold", icon_size),
            "victory.png": ("victory", self.cell_size),  # Победа на всю клетку
            "wind.png": ("wind", sensor_size),
            "stench.png": ("stink", sensor_size)
        }

        for filename, (key, size) in assets_config.items():
            path = os.path.join(icons_dir, filename)
            if os.path.exists(path):
                try:
                    # Используем PIL для открытия и ресайза
                    pil_img = Image.open(path)
                    # Resize с сглаживанием (LANCZOS)
                    pil_img = pil_img.resize(
                        (size, size), Image.Resampling.LANCZOS)
                    # Конвертируем обратно в Tkinter
                    self.icons[key] = ImageTk.PhotoImage(pil_img)
                except Exception as e:
                    print(f"Ошибка загрузки {filename}: {e}")
                    self.icons[key] = None
            else:
                self.icons[key] = None

    def draw_grid(self):
        self.canvas.delete("all")
        real_map = self.world.get_world()

        # Динамический размер шрифта для текста
        font_size = max(8, int(self.cell_size / 4))
        sensor_font = ("Arial", font_size, "bold")

        for x in range(self.rows):
            for y in range(self.cols):
                # Координаты с учетом self.cell_size
                x1, y1 = y * self.cell_size, x * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                cx, cy = x1 + self.cell_size//2, y1 + self.cell_size//2

                is_visible = ((x, y) in self.agent.visited) or self.game_over

                # Фон
                bg = COLOR_UNKNOWN
                if (x, y) == self.suicide_pos:
                    bg = "#ff4d4d"
                elif is_visible:
                    bg = COLOR_VISITED

                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=bg, outline="black")

                if is_visible:
                    cell = real_map[x][y]

                    # --- ОБЪЕКТЫ ---
                    if "pit" in cell:
                        if self.icons["pit"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["pit"])
                        else:
                            self.canvas.create_oval(
                                x1+5, y1+5, x2-5, y2-5, fill="black")

                    if "gold" in cell:
                        if self.icons["gold"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["gold"])
                        else:
                            self.canvas.create_oval(
                                x1+10, y1+10, x2-10, y2-10, fill="gold")

                    if "vantus" in cell:
                        if self.icons["vantus"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["vantus"])
                        else:
                            self.canvas.create_rectangle(
                                x1+10, y1+10, x2-10, y2-10, fill="red")

                    # --- СЕНСОРЫ ---
                    # Смещения для иконок сенсоров (в углы)
                    offset = self.cell_size // 4

                    if "wind" in cell:
                        if self.icons["wind"]:
                            self.canvas.create_image(
                                x1 + offset, y1 + offset, image=self.icons["wind"])
                        else:
                            self.canvas.create_text(
                                x1 + offset, y1 + offset, text="~", fill="blue", font=sensor_font)

                    if "stink" in cell:
                        if self.icons["stink"]:
                            self.canvas.create_image(
                                x2 - offset, y1 + offset, image=self.icons["stink"])
                        else:
                            self.canvas.create_text(
                                x2 - offset, y1 + offset, text="S", fill="green", font=sensor_font)

                # --- АГЕНТ ---
                if self.agent.x == x and self.agent.y == y:
                    victory = (
                        "gold" in real_map[x][y] and "shine" in real_map[x][y])
                    icon = self.icons["victory"] if victory else self.icons["agent"]

                    if icon:
                        self.canvas.create_image(cx, cy, image=icon)
                    else:
                        pad = self.cell_size // 5
                        self.canvas.create_oval(
                            x1+pad, y1+pad, x2-pad, y2-pad, fill="blue", width=2, outline="white")

    def do_step(self):
        if self.game_over:
            return
        try:
            res = self.agent.step()
        except Exception as e:
            print(e)
            res = False

        self.status_var.set(
            f"Pos: {self.agent.x},{self.agent.y} | Sens: {self.world.get_percepts(self.agent.x, self.agent.y)}")

        if res is False:
            self.game_over = True
            self.is_running = False
            self.btn_pause.config(state=tk.DISABLED)

            cell = self.world.get_world()[self.agent.x][self.agent.y]
            death = "pit" in cell or "vantus" in cell
            win = "gold" in cell and "shine" in cell
            if not death and not win:
                self.suicide_pos = (self.agent.x, self.agent.y)

            self.draw_grid()
            self.show_message(win, death)
        else:
            self.draw_grid()

    def show_message(self, win, death):
        if win:
            messagebox.showinfo("Win", "Золото найдено!")
        elif death:
            messagebox.showerror("Game Over", "Агент погиб.")
        else:
            messagebox.showwarning("Stop", "Агент сдался.")

    def auto_play(self):
        if self.game_over:
            return
        self.is_running = True
        self.btn_pause.config(text="Пауза", bg="#FFD700")
        self.run_loop()

    def toggle_pause(self):
        if self.game_over:
            return
        self.is_running = not self.is_running
        txt = "Пауза" if self.is_running else "Продолжить"
        col = "#FFD700" if self.is_running else "lightgreen"
        self.btn_pause.config(text=txt, bg=col)
        if self.is_running:
            self.run_loop()

    def run_loop(self):
        if self.is_running and not self.game_over:
            self.do_step()
            self.after(self.speed_delay, self.run_loop)

    def decrease_speed(self):
        if self.speed_delay < 2000:
            self.speed_delay += 100
            self.lbl_speed.config(text=str(self.speed_delay))

    def increase_speed(self):
        if self.speed_delay > 50:
            self.speed_delay -= 100
            if self.speed_delay < 50:
                self.speed_delay = 50
            self.lbl_speed.config(text=str(self.speed_delay))


def main_gui():
    root = tk.Tk()
    app = WumpusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main_gui()
