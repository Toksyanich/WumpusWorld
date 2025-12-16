import tkinter as tk
from tkinter import messagebox
import os
import sys
from PIL import Image, ImageTk
import main

# --- ЦВЕТА ---
COLOR_UNKNOWN = "#2b2b2b"
COLOR_VISITED = "#ffffff"
COLOR_EDITOR_BG = "#e6f7ff"  # Светло-голубой фон для редактора


class WumpusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wumpus World AI")
        self.root.geometry("1100x850")

        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)
        self.current_frame = None
        self.show_menu()

    def show_menu(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = MainMenu(
            self.container, self.start_game, self.open_editor)
        self.current_frame.pack(fill="both", expand=True)

    def open_editor(self, rows, cols):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = EditorUI(
            self.container, rows, cols, self.start_game_from_editor, self.show_menu)
        self.current_frame.pack(fill="both", expand=True)

    def start_game(self, rows, cols, prob):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = GameUI(
            self.container, rows, cols, prob, None, self.show_menu)
        self.current_frame.pack(fill="both", expand=True)

    def start_game_from_editor(self, world_instance):
        if self.current_frame:
            self.current_frame.destroy()
        # Запускаем игру с уже готовым миром (prob=0, так как мир уже есть)
        self.current_frame = GameUI(
            self.container, world_instance.x, world_instance.y, 0, world_instance, self.show_menu)
        self.current_frame.pack(fill="both", expand=True)


class MainMenu(tk.Frame):
    def __init__(self, parent, start_callback, editor_callback):
        super().__init__(parent, bg="#f0f0f0")
        self.start_callback = start_callback
        self.editor_callback = editor_callback

        tk.Label(self, text="Wumpus World", font=(
            "Helvetica", 32, "bold"), bg="#f0f0f0").pack(pady=30)

        settings_frame = tk.Frame(self, bg="#f0f0f0")
        settings_frame.pack(pady=10)

        self.rows_entry = self.create_input(
            settings_frame, "Высота (Rows):", "5")
        self.cols_entry = self.create_input(
            settings_frame, "Ширина (Cols):", "5")
        self.prob_entry = self.create_input(
            settings_frame, "Шанс ямы (0.0-1.0):", "0.2")

        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack(pady=30)

        # Кнопка обычной игры
        tk.Button(btn_frame, text="🎲 СЛУЧАЙНАЯ ИГРА", font=("Arial", 14), bg="#4CAF50", fg="white",
                  command=self.validate_and_start, width=20, height=2).pack(side=tk.LEFT, padx=10)

        # Кнопка редактора
        tk.Button(btn_frame, text="✏️ РЕДАКТОР КАРТ", font=("Arial", 14), bg="#2196F3", fg="white",
                  command=self.validate_and_edit, width=20, height=2).pack(side=tk.LEFT, padx=10)

    def create_input(self, parent, text, default):
        frame = tk.Frame(parent, bg="#f0f0f0")
        frame.pack(pady=5)
        tk.Label(frame, text=text, width=20, anchor="e",
                 bg="#f0f0f0", font=("Arial", 12)).pack(side=tk.LEFT)
        entry = tk.Entry(frame, font=("Arial", 12), width=10)
        entry.insert(0, default)
        entry.pack(side=tk.LEFT, padx=10)
        return entry

    def get_params(self):
        try:
            rows = int(self.rows_entry.get())
            cols = int(self.cols_entry.get())
            prob = float(self.prob_entry.get())
            if rows < 3 or cols < 3 or rows > 30 or cols > 30:
                messagebox.showerror("Ошибка", "Размер карты от 3x3 до 30x30")
                return None
            if not (0 <= prob <= 1.0):
                messagebox.showerror("Ошибка", "Вероятность 0.0 - 1.0")
                return None
            return rows, cols, prob
        except ValueError:
            messagebox.showerror("Ошибка", "Введите числа")
            return None

    def validate_and_start(self):
        params = self.get_params()
        if params:
            self.start_callback(*params)

    def validate_and_edit(self):
        params = self.get_params()
        if params:
            # Передаем только размеры
            self.editor_callback(params[0], params[1])


class EditorUI(tk.Frame):
    def __init__(self, parent, rows, cols, play_callback, back_callback):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.play_callback = play_callback
        self.back_callback = back_callback

        # Создаем пустой мир
        self.world = main.WampusWorld.create_empty(rows, cols)

        self.selected_tool = "pit"  # Инструмент по умолчанию

        # Расчет размера клетки
        max_w, max_h = 800, 750
        self.cell_size = min(120, max(30, min(max_w // cols, max_h // rows)))

        self.icons = {}
        self.load_assets()
        self.setup_ui()
        self.draw_grid()

    def setup_ui(self):
        # Левая часть (Канвас)
        self.canvas_frame = tk.Frame(self, bg="#333")
        self.canvas_frame.pack(side=tk.LEFT, fill="both", expand=True)

        w, h = self.cols * self.cell_size, self.rows * self.cell_size
        self.canvas = tk.Canvas(
            self.canvas_frame, bg="gray", width=w, height=h, highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        # Биндим клик мыши
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Правая часть (Палитра)
        self.panel = tk.Frame(self, bg=COLOR_EDITOR_BG, width=280)
        self.panel.pack(side=tk.RIGHT, fill="y")
        self.panel.pack_propagate(False)

        tk.Label(self.panel, text="РЕДАКТОР", bg=COLOR_EDITOR_BG,
                 font=("Arial", 16, "bold")).pack(pady=20)

        # Инструменты
        self.create_tool_btn("🕳 Яма (Pit)", "pit", "#444")
        self.create_tool_btn("😈 Вантус", "vantus", "#d9534f")
        self.create_tool_btn("💰 Золото", "gold", "#f0ad4e")
        self.create_tool_btn("🧹 Ластик", "eraser", "#5bc0de")

        self.lbl_tool = tk.Label(
            self.panel, text=f"Выбрано: {self.selected_tool}", bg=COLOR_EDITOR_BG, font=("Arial", 12))
        self.lbl_tool.pack(pady=20)

        tk.Button(self.panel, text="▶ ИГРАТЬ", command=self.start_game,
                  bg="#5cb85c", fg="white", font=("Arial", 14, "bold"), height=2, width=15).pack(side=tk.BOTTOM, pady=20)

        tk.Button(self.panel, text="🏠 Назад", command=self.back_callback,
                  width=15).pack(side=tk.BOTTOM, pady=5)

    def create_tool_btn(self, text, tool_name, color):
        btn = tk.Button(self.panel, text=text, bg=color, fg="white", font=("Arial", 11),
                        width=20, height=2, command=lambda: self.select_tool(tool_name))
        btn.pack(pady=5)

    def select_tool(self, tool):
        self.selected_tool = tool
        self.lbl_tool.config(text=f"Выбрано: {tool.upper()}")

    def on_canvas_click(self, event):
        # Определяем клетку по координатам клика
        y = event.x // self.cell_size
        x = event.y // self.cell_size

        if 0 <= x < self.rows and 0 <= y < self.cols:
            self.apply_tool(x, y)
            self.draw_grid()

    def apply_tool(self, x, y):
        cell = self.world.get_world()[x][y]

        # Нельзя трогать (0,0) - там старт агента
        if x == 0 and y == 0:
            messagebox.showwarning("Ой", "Нельзя ставить ловушки на старте!")
            return

        if self.selected_tool == "eraser":
            # Удаляем всё опасное и ценное
            for item in ["pit", "vantus", "gold", "shine"]:
                if item in cell:
                    cell.remove(item)
        else:
            # Логика уникальности: Вантус и Золото обычно одни, но можно разрешить много
            # Давайте разрешим много для веселья, но уберем дубликаты в одной клетке
            if self.selected_tool not in cell:
                cell.append(self.selected_tool)
                if self.selected_tool == "gold":
                    cell.append("shine")

        # МАГИЯ: Автоматический пересчет ветра и вони
        self.world.recalculate_signals()

    def start_game(self):
        # Проверка на наличие золота
        has_gold = False
        for row in self.world.get_world():
            for cell in row:
                if "gold" in cell:
                    has_gold = True
                    break

        if not has_gold:
            if not messagebox.askyesno("Нет золота", "Вы не поставили золото. Играть будет бессмысленно. Всё равно начать?"):
                return

        self.play_callback(self.world)

    def draw_grid(self):
        # Этот метод почти копия из GameUI, но показывает ВСЁ (без тумана)
        self.canvas.delete("all")
        real_map = self.world.get_world()
        font_size = max(8, int(self.cell_size / 4))
        sensor_font = ("Arial", font_size, "bold")

        for x in range(self.rows):
            for y in range(self.cols):
                x1, y1 = y * self.cell_size, x * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                cx, cy = x1 + self.cell_size//2, y1 + self.cell_size//2

                # Фон всегда белый (мы видим всё)
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill="white", outline="gray")

                cell = real_map[x][y]
                offset = self.cell_size // 4

                # Рисуем объекты
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
                if "agent" in cell:
                    if self.icons["agent"]:
                        self.canvas.create_image(
                            cx, cy, image=self.icons["agent"])
                    else:
                        self.canvas.create_oval(
                            x1+30, y1+30, x2-30, y2-30, fill="blue")

                # Сенсоры (Ветер/Вонь)
                if "wind" in cell:
                    if self.icons["wind"]:
                        self.canvas.create_image(
                            x1 + offset, y1 + offset, image=self.icons["wind"])
                    else:
                        self.canvas.create_text(
                            x1+offset, y1+offset, text="~", fill="blue", font=sensor_font)
                if "stink" in cell:
                    if self.icons["stink"]:
                        self.canvas.create_image(
                            x2 - offset, y1 + offset, image=self.icons["stink"])
                    else:
                        self.canvas.create_text(
                            x2-offset, y1+offset, text="S", fill="green", font=sensor_font)

    def load_assets(self):
        # (Копипаст метода load_assets из GameUI, т.к. нам нужны те же иконки)
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")
        icon_size = int(self.cell_size * 0.8)
        sensor_size = int(self.cell_size * 0.4)

        assets_config = {
            "agent.png": ("agent", icon_size), "wumpus.png": ("vantus", icon_size),
            "pit.png": ("pit", icon_size), "gold.png": ("gold", icon_size),
            "wind.png": ("wind", sensor_size), "stench.png": ("stink", sensor_size)
        }
        for filename, (key, size) in assets_config.items():
            path = os.path.join(icons_dir, filename)
            if os.path.exists(path):
                try:
                    self.icons[key] = ImageTk.PhotoImage(Image.open(
                        path).resize((size, size), Image.Resampling.LANCZOS))
                except:
                    self.icons[key] = None
            else:
                self.icons[key] = None


class GameUI(tk.Frame):
    def __init__(self, parent, rows, cols, prob, custom_world=None, back_callback=None):
        super().__init__(parent)
        self.rows = rows
        self.cols = cols
        self.prob = prob
        self.custom_world = custom_world  # Если передан, используем его
        self.back_callback = back_callback

        self.speed_delay = 500

        max_w, max_h = 800, 750
        cell_w, cell_h = max_w // cols, max_h // rows
        self.cell_size = min(120, max(30, min(cell_w, cell_h)))

        self.icons = {}
        self.load_assets()
        self.setup_ui()
        self.start_new_game()

    def setup_ui(self):
        self.canvas_frame = tk.Frame(self, bg="#333")
        self.canvas_frame.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas = tk.Canvas(
            self.canvas_frame, bg="gray", highlightthickness=0)
        self.canvas.place(relx=0.5, rely=0.5, anchor="center")

        self.panel = tk.Frame(self, bg="#e0e0e0", width=280)
        self.panel.pack(side=tk.RIGHT, fill="y")
        self.panel.pack_propagate(False)

        tk.Label(self.panel, text="ИГРА", bg="#e0e0e0",
                 font=("Arial", 14, "bold")).pack(pady=15)

        tk.Button(self.panel, text="Сделать Шаг",
                  command=self.do_step, width=20, height=2).pack(pady=5)
        self.btn_run = tk.Button(self.panel, text="Авто-игра",
                                 command=self.auto_play, width=20, height=2, bg="lightgreen")
        self.btn_run.pack(pady=5)
        self.btn_pause = tk.Button(
            self.panel, text="Пауза", command=self.toggle_pause, width=20, height=2, bg="#FFD700")
        self.btn_pause.pack(pady=5)

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
        tk.Label(self.panel, textvariable=self.status_var, bg="#e0e0e0",
                 wraplength=260, justify="left").pack(side=tk.BOTTOM, pady=20)

    def go_back(self):
        self.is_running = False
        if self.back_callback:
            self.back_callback()

    def start_new_game(self):
        if self.custom_world:
            # Если пришли из редактора - используем переданный мир
            # Важно: нужно создать копию логики агента для этого мира
            self.world = self.custom_world
        else:
            # Иначе генерируем новый
            self.world = main.WampusWorld(self.rows, self.cols, self.prob)

        self.agent = main.Agent(self.world, 0, 0, self.rows, self.cols)
        self.is_running = False
        self.game_over = False
        self.suicide_pos = None
        self.status_var.set("Игра началась.")
        self.btn_pause.config(text="Пауза", bg="#FFD700", state=tk.NORMAL)

        w, h = self.cols * self.cell_size, self.rows * self.cell_size
        self.canvas.config(width=w, height=h)
        self.draw_grid()

    def reset_game(self):
        # Если играем на кастомной карте, рестарт просто сбрасывает агента в начало
        self.is_running = False
        self.start_new_game()

    # ... (Остальные методы load_assets, draw_grid, do_step и т.д. такие же как были,
    # просто убедись что они внутри класса GameUI. Я их не дублирую, чтобы код влез)
    # СКОПИРУЙ ИХ ИЗ СТАРОГО grafics.py ИЛИ ПРОСТО ОСТАВЬ КАК ЕСТЬ В GameUI

    # ВАЖНО: В методе draw_grid в GameUI нужно убедиться, что он использует self.world
    # который теперь может быть custom_world.

    # Вот методы, которые нужно вернуть (они такие же):
    def load_assets(self):
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")
        icon_size = int(self.cell_size * 0.8)
        sensor_size = int(self.cell_size * 0.4)
        assets_config = {
            "agent.png": ("agent", icon_size), "wumpus.png": ("vantus", icon_size),
            "pit.png": ("pit", icon_size), "gold.png": ("gold", icon_size),
            "victory.png": ("victory", self.cell_size), "wind.png": ("wind", sensor_size),
            "stench.png": ("stink", sensor_size)
        }
        for filename, (key, size) in assets_config.items():
            path = os.path.join(icons_dir, filename)
            if os.path.exists(path):
                try:
                    self.icons[key] = ImageTk.PhotoImage(Image.open(
                        path).resize((size, size), Image.Resampling.LANCZOS))
                except:
                    self.icons[key] = None
            else:
                self.icons[key] = None

    def draw_grid(self):
        self.canvas.delete("all")
        real_map = self.world.get_world()
        sensor_font = ("Arial", max(8, int(self.cell_size/4)), "bold")
        for x in range(self.rows):
            for y in range(self.cols):
                x1, y1 = y * self.cell_size, x * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                cx, cy = x1 + self.cell_size//2, y1 + self.cell_size//2
                is_visible = ((x, y) in self.agent.visited) or self.game_over
                bg = COLOR_UNKNOWN
                if (x, y) == self.suicide_pos:
                    bg = "#ff4d4d"
                elif is_visible:
                    bg = COLOR_VISITED
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=bg, outline="black")
                if is_visible:
                    cell = real_map[x][y]
                    if "pit" in cell:
                        self.canvas.create_image(cx, cy, image=self.icons["pit"]) if self.icons["pit"] else self.canvas.create_oval(
                            x1+5, y1+5, x2-5, y2-5, fill="black")
                    if "gold" in cell:
                        self.canvas.create_image(cx, cy, image=self.icons["gold"]) if self.icons["gold"] else self.canvas.create_oval(
                            x1+10, y1+10, x2-10, y2-10, fill="gold")
                    if "vantus" in cell:
                        self.canvas.create_image(cx, cy, image=self.icons["vantus"]) if self.icons["vantus"] else self.canvas.create_rectangle(
                            x1+10, y1+10, x2-10, y2-10, fill="red")

                    off = self.cell_size//4
                    if "wind" in cell:
                        self.canvas.create_image(x1+off, y1+off, image=self.icons["wind"]) if self.icons["wind"] else self.canvas.create_text(
                            x1+off, y1+off, text="~", fill="blue", font=sensor_font)
                    if "stink" in cell:
                        self.canvas.create_image(x2-off, y1+off, image=self.icons["stink"]) if self.icons["stink"] else self.canvas.create_text(
                            x2-off, y1+off, text="S", fill="green", font=sensor_font)

                if self.agent.x == x and self.agent.y == y:
                    vic = "gold" in cell and "shine" in cell
                    ic = self.icons["victory"] if vic else self.icons["agent"]
                    if ic:
                        self.canvas.create_image(cx, cy, image=ic)
                    else:
                        self.canvas.create_oval(
                            x1+30, y1+30, x2-30, y2-30, fill="blue")

    def do_step(self):
        if self.game_over:
            return
        try:
            res = self.agent.step()
        except:
            res = False
        self.status_var.set(f"Pos: {self.agent.x},{self.agent.y}")
        if res is False:
            self.game_over = True
            self.is_running = False
            self.btn_pause.config(state=tk.DISABLED)
            cell = self.world.get_world()[self.agent.x][self.agent.y]
            if not ("pit" in cell or "vantus" in cell or ("gold" in cell and "shine" in cell)):
                self.suicide_pos = (self.agent.x, self.agent.y)
            self.draw_grid()
            self.show_message("gold" in cell and "shine" in cell,
                              "pit" in cell or "vantus" in cell)
        else:
            self.draw_grid()

    def show_message(self, w, d):
        if w:
            messagebox.showinfo("Win", "Победа!")
        elif d:
            messagebox.showerror("Die", "Смерть")
        else:
            messagebox.showwarning("Stop", "Сдался")

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
        self.btn_pause.config(text="Пауза" if self.is_running else "Продолжить",
                              bg="#FFD700" if self.is_running else "lightgreen")
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
