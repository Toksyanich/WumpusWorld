import tkinter as tk
from tkinter import messagebox
import os
import sys
import main  # Твой файл логики

# --- НАСТРОЙКИ ---
CELL_SIZE = 100  # Размер клетки
COLOR_UNKNOWN = "#2b2b2b"  # Темно-серый (Туман)
COLOR_VISITED = "#ffffff"  # Белый (Открыто)


class WumpusGUI:
    def __init__(self, master, rows, cols, prob):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.prob = prob  # Сохраняем вероятность для рестарта

        # Начальная скорость (задержка в мс): 500мс = 0.5 сек
        self.speed_delay = 500

        self.master.title("Wumpus World AI")

        # Загрузка иконок
        self.icons = {}
        self.load_assets()

        # Интерфейс: Канвас слева, Панель справа
        canvas_width = cols * CELL_SIZE
        canvas_height = rows * CELL_SIZE
        self.canvas = tk.Canvas(
            master, width=canvas_width, height=canvas_height, bg="gray")
        self.canvas.pack(side=tk.LEFT)

        self.panel = tk.Frame(master, bg="#e0e0e0")
        self.panel.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

        # --- КНОПКИ УПРАВЛЕНИЯ ---
        tk.Label(self.panel, text="Меню", bg="#e0e0e0", font=(
            "Arial", 14, "bold")).pack(pady=10, padx=20)

        self.btn_step = tk.Button(
            self.panel, text="Сделать Шаг", command=self.do_step, width=15, height=2)
        self.btn_step.pack(pady=5)

        self.btn_run = tk.Button(self.panel, text="Авто-игра",
                                 command=self.auto_play, width=15, height=2, bg="lightgreen")
        self.btn_run.pack(pady=5)

        self.btn_pause = tk.Button(
            self.panel, text="Пауза", command=self.toggle_pause, width=15, height=2, bg="#FFD700")
        self.btn_pause.pack(pady=5)

        # --- БЛОК СКОРОСТИ ---
        tk.Label(self.panel, text="Скорость (мс)", bg="#e0e0e0",
                 font=("Arial", 10)).pack(pady=(15, 0))

        speed_frame = tk.Frame(self.panel, bg="#e0e0e0")
        speed_frame.pack(pady=5)

        # Кнопка Медленнее
        self.btn_slow = tk.Button(
            speed_frame, text="<<", command=self.decrease_speed, width=5)
        self.btn_slow.pack(side=tk.LEFT, padx=2)

        # Отображение текущей задержки
        self.lbl_speed = tk.Label(
            speed_frame, text=f"{self.speed_delay}", bg="white", width=6, relief="sunken")
        self.lbl_speed.pack(side=tk.LEFT, padx=2)

        # Кнопка Быстрее
        self.btn_fast = tk.Button(
            speed_frame, text=">>", command=self.increase_speed, width=5)
        self.btn_fast.pack(side=tk.LEFT, padx=2)
        # ---------------------

        self.btn_restart = tk.Button(
            self.panel, text="Рестарт", command=self.reset_game, width=15, height=2, bg="salmon")
        self.btn_restart.pack(pady=20)

        self.status_var = tk.StringVar()
        self.status_var.set("Нажмите старт")
        tk.Label(self.panel, textvariable=self.status_var,
                 bg="#e0e0e0", wraplength=150, justify="left").pack(pady=10)

        # Инициализация первой игры
        self.start_new_game()

    def start_new_game(self):
        """Создает объекты мира и агента заново"""
        self.world = main.WampusWorld(self.rows, self.cols, self.prob)
        self.agent = main.Agent(self.world, 0, 0, self.rows, self.cols)
        self.is_running = False
        self.game_over = False
        self.suicide_pos = None
        self.status_var.set("Новая игра началась.")

        self.btn_pause.config(text="Пауза", bg="#FFD700", state=tk.NORMAL)
        self.draw_grid()

    def reset_game(self):
        """Функция для кнопки Рестарт"""
        self.is_running = False
        self.start_new_game()

    # --- УПРАВЛЕНИЕ СКОРОСТЬЮ ---
    def decrease_speed(self):
        """Увеличиваем задержку (медленнее)"""
        if self.speed_delay < 2000:
            self.speed_delay += 100
            self.lbl_speed.config(text=f"{self.speed_delay}")

    def increase_speed(self):
        """Уменьшаем задержку (быстрее)"""
        if self.speed_delay > 50:  # Минимум 50мс
            self.speed_delay -= 100
            if self.speed_delay < 50:
                self.speed_delay = 50
            self.lbl_speed.config(text=f"{self.speed_delay}")
    # ----------------------------

    def load_assets(self):
        """Загрузка картинок (С поддержкой EXE)"""
        # Проверяем, запущены ли мы как EXE или как скрипт
        if getattr(sys, 'frozen', False):
            # Если EXE — берем путь к временной папке
            base_dir = sys._MEIPASS
        else:
            # Если скрипт — берем путь к файлу
            base_dir = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_dir, "icons")

        image_files = {
            "agent": "agent.png",
            "vantus": "wumpus.png",
            "pit": "pit.png",
            "gold": "gold.png",
            "wind": "wind.png",
            "stink": "stench.png",
            "victory": "victory.png"
        }

        for key, filename in image_files.items():
            full_path = os.path.join(icons_dir, filename)
            if os.path.exists(full_path):
                try:
                    img = tk.PhotoImage(file=full_path)
                    self.icons[key] = img
                except Exception:
                    self.icons[key] = None
            else:
                self.icons[key] = None

    def draw_grid(self):
        self.canvas.delete("all")
        real_map = self.world.get_world()

        for x in range(self.rows):
            for y in range(self.cols):
                x1 = y * CELL_SIZE
                y1 = x * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE
                cx = x1 + CELL_SIZE // 2
                cy = y1 + CELL_SIZE // 2

                is_visible = ((x, y) in self.agent.visited) or self.game_over

                if (x, y) == self.suicide_pos:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill="#ff4d4d", outline="black")
                elif is_visible:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=COLOR_VISITED, outline="#ccc")
                else:
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=COLOR_UNKNOWN, outline="black")

                if is_visible:
                    cell = real_map[x][y]

                    if "pit" in cell:
                        if self.icons["pit"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["pit"])
                        else:
                            self.canvas.create_oval(
                                x1+10, y1+10, x2-10, y2-10, fill="black")

                    if "gold" in cell:
                        if self.icons["gold"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["gold"])
                        else:
                            self.canvas.create_oval(
                                x1+20, y1+20, x2-20, y2-20, fill="gold")

                    if "vantus" in cell:
                        if self.icons["vantus"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["vantus"])
                        else:
                            self.canvas.create_rectangle(
                                x1+15, y1+15, x2-15, y2-15, fill="red")

                    if "wind" in cell:
                        if self.icons["wind"]:
                            self.canvas.create_image(
                                x1+20, y1+20, image=self.icons["wind"])
                        else:
                            self.canvas.create_text(
                                x1+20, y1+20, text="~~", fill="blue")

                    if "stink" in cell:
                        if self.icons["stink"]:
                            self.canvas.create_image(
                                x2-20, y1+20, image=self.icons["stink"])
                        else:
                            self.canvas.create_text(
                                x2-20, y1+20, text="SS", fill="green")

                if self.agent.x == x and self.agent.y == y:
                    cell_content = real_map[x][y]
                    found_gold = "gold" in cell_content and "shine" in cell_content

                    if found_gold and self.icons["victory"]:
                        self.canvas.create_image(
                            cx, cy, image=self.icons["victory"])
                    else:
                        if self.icons["agent"]:
                            self.canvas.create_image(
                                cx, cy, image=self.icons["agent"])
                        else:
                            self.canvas.create_oval(
                                x1+30, y1+30, x2-30, y2-30, fill="blue", width=2)

    def do_step(self):
        if self.game_over:
            return

        try:
            result = self.agent.step()
        except Exception as e:
            print(f"Ошибка: {e}")
            result = False

        self.status_var.set(
            f"Позиция: [{self.agent.x}, {self.agent.y}]\nОщущения: {self.world.get_percepts(self.agent.x, self.agent.y)}")

        if result is False:
            self.game_over = True
            self.is_running = False
            self.btn_pause.config(state=tk.DISABLED)

            cell = self.world.get_world()[self.agent.x][self.agent.y]
            is_death = "pit" in cell or "vantus" in cell
            is_win = "gold" in cell and "shine" in cell

            if not is_death and not is_win:
                self.suicide_pos = (self.agent.x, self.agent.y)

            self.draw_grid()
            self.show_end_message()
        else:
            self.draw_grid()

    def show_end_message(self):
        cell = self.world.get_world()[self.agent.x][self.agent.y]
        if "gold" in cell and "shine" in cell:
            messagebox.showinfo("Победа!", "Золото найдено! Вы богаты!")
        elif "pit" in cell:
            messagebox.showerror("Game Over", "Агент упал в яму.")
        elif "vantus" in cell:
            messagebox.showerror("Game Over", "Агента съел Вантус.")
        else:
            messagebox.showwarning(
                "Стоп", "Агент зашел в тупик и сделал харакири.")

    def auto_play(self):
        if self.game_over:
            return
        self.is_running = True
        self.btn_pause.config(text="Пауза", bg="#FFD700")
        self.run_loop()

    def toggle_pause(self):
        if self.game_over:
            return
        if self.is_running:
            self.is_running = False
            self.btn_pause.config(text="Продолжить", bg="lightgreen")
        else:
            self.is_running = True
            self.btn_pause.config(text="Пауза", bg="#FFD700")
            self.run_loop()

    def run_loop(self):
        if self.is_running and not self.game_over:
            self.do_step()
            # ТЕПЕРЬ ЗАДЕРЖКА БЕРЕТСЯ ИЗ ПЕРЕМЕННОЙ
            self.master.after(self.speed_delay, self.run_loop)


def main_gui():
    root = tk.Tk()
    ROWS = 10
    COLS = 10
    PROB = 0.2
    app = WumpusGUI(root, ROWS, COLS, PROB)
    root.mainloop()


if __name__ == "__main__":
    main_gui()
