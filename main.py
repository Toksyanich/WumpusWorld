import sympy as sp
import random
import time
from collections import deque  # Нужна для очереди BFS


class WampusWorld:
    def __init__(self, x, y, probability_of_pit=0.0, custom_grid=None):
        # Если передан custom_grid — используем его, иначе генерируем рандом
        self.x = x
        self.y = y
        self.probability_of_pit = probability_of_pit

        if custom_grid:
            self.world = custom_grid
            self.recalculate_signals()  # Убеждаемся, что ветра/вони расставлены верно
        else:
            self.world = self.generation_world(x, y, probability_of_pit)

    def get_world(self):
        return self.world

    # --- НОВЫЙ МЕТОД: СОЗДАНИЕ ПУСТОГО МИРА ---
    @classmethod
    def create_empty(cls, x, y):
        # Создаем объект, но с пустой сеткой
        instance = cls(x, y)
        instance.world = [[[] for _ in range(y)] for _ in range(x)]
        # Агент всегда на старте
        instance.world[0][0].append("agent")
        return instance

    # --- НОВЫЙ МЕТОД: ПЕРЕСЧЕТ СИГНАЛОВ (ДЛЯ РЕДАКТОРА) ---
    def recalculate_signals(self):
        """
        Полностью очищает ветер/вонь и расставляет их заново 
        на основе положения Ям и Вантуса.
        """
        rows = len(self.world)
        cols = len(self.world[0])

        # 1. Очистка старых сигналов
        for i in range(rows):
            for j in range(cols):
                if "wind" in self.world[i][j]:
                    self.world[i][j].remove("wind")
                if "stink" in self.world[i][j]:
                    self.world[i][j].remove("stink")

        # 2. Расстановка новых
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for x in range(rows):
            for y in range(cols):
                cell = self.world[x][y]

                # Если нашли ЯМУ -> ставим ВЕТЕР соседям
                if "pit" in cell:
                    for dx, dy in deltas:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols:
                            if "wind" not in self.world[nx][ny]:
                                self.world[nx][ny].append("wind")

                # Если нашли ВАНТУСА -> ставим ВОНЬ соседям
                if "vantus" in cell:
                    for dx, dy in deltas:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < rows and 0 <= ny < cols:
                            if "stink" not in self.world[nx][ny]:
                                self.world[nx][ny].append("stink")

    def generation_world(self, x, y, probability_of_pit):
        max_attempts = 1000
        attempt = 0
        final_world = []

        while attempt < max_attempts:
            attempt += 1
            gen_x = self.x + 1
            gen_y = self.y + 1
            temp_world = [[[] for _ in range(gen_x + 1)]
                          for _ in range(gen_y + 1)]

            # Генерация ЯМ
            for i in range(1, gen_x):
                for j in range(1, gen_y):
                    if (i != 1 or j != 1) and (random.random() < self.probability_of_pit):
                        if "pit" not in temp_world[i][j]:
                            temp_world[i][j].append("pit")
                        if "wind" not in temp_world[i][j+1]:
                            temp_world[i][j+1].append("wind")
                        if "wind" not in temp_world[i][j-1]:
                            temp_world[i][j-1].append("wind")
                        if "wind" not in temp_world[i+1][j]:
                            temp_world[i+1][j].append("wind")
                        if "wind" not in temp_world[i-1][j]:
                            temp_world[i-1][j].append("wind")

            # Генерация ВАНТУСА
            temp_mass = []
            for i in range(1, gen_x):
                for j in range(1, gen_y):
                    if ("pit" not in temp_world[i][j]) and (i != 1 or j != 1):
                        temp_mass.append((j*3+i*2, i, j))

            if not temp_mass:
                temp_mass.append((0, 2, 2))

            target = random.randint(
                min(x[0] for x in temp_mass), max(x[0] for x in temp_mass))
            indexs = min(temp_mass, key=lambda x: (abs(x[0] - target), -x[0]))

            temp_world[indexs[1]][indexs[2]].append("vantus")

            if "stink" not in temp_world[indexs[1]][indexs[2]+1]:
                temp_world[indexs[1]][indexs[2]+1].append("stink")
            if "stink" not in temp_world[indexs[1]][indexs[2]-1]:
                temp_world[indexs[1]][indexs[2]-1].append("stink")
            if "stink" not in temp_world[indexs[1]+1][indexs[2]]:
                temp_world[indexs[1]+1][indexs[2]].append("stink")
            if "stink" not in temp_world[indexs[1]-1][indexs[2]]:
                temp_world[indexs[1]-1][indexs[2]].append("stink")

            temp_world[1][1].append("agent")

            # Золото
            temp_mass = []
            for i in range(1, gen_x):
                for j in range(1, gen_y):
                    if ("pit" not in temp_world[i][j]) and \
                        (i != 1 or j != 1) and \
                            ("vantus" not in temp_world[i][j]):
                        temp_mass.append((j*3+i*2, i, j))

            if not temp_mass:
                temp_mass.append((0, 2, 2))

            target = random.randint(
                min(x[0] for x in temp_mass), max(x[0] for x in temp_mass))
            indexs = min(temp_mass, key=lambda x: (abs(x[0] - target), -x[0]))

            temp_world[indexs[1]][indexs[2]].append("gold")
            temp_world[indexs[1]][indexs[2]].append("shine")

            # Обрезка
            cropped_world = [[[]
                              for _ in range(self.x)] for _ in range(self.y)]
            for i in range(0, self.x):
                for j in range(0, self.y):
                    cropped_world[i][j] = temp_world[i+1][j+1]

            if self.check_solvability(cropped_world, 0, 0):
                print('\nСгенерированный мир:')
                for row in cropped_world:
                    print(row)
                return cropped_world
            final_world = cropped_world

        print("\nНе удалось создать гарантированно проходимый мир.")
        return final_world

    def get_percepts(self, x, y):
        real_cell = self.world[x][y]
        percepts = []
        if "wind" in real_cell:
            percepts.append("wind")
        if "stink" in real_cell:
            percepts.append("stink")
        if "shine" in real_cell:
            percepts.append("shine")
        return percepts

    def check_solvability(self, grid, start_x, start_y):
        rows = len(grid)
        cols = len(grid[0])
        queue = [(start_x, start_y)]
        visited = set()
        visited.add((start_x, start_y))

        while queue:
            cx, cy = queue.pop(0)
            cell = grid[cx][cy]
            if "gold" in cell:
                return True

            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in deltas:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    if (nx, ny) not in visited:
                        neighbor_cell = grid[nx][ny]
                        if "pit" not in neighbor_cell and "vantus" not in neighbor_cell:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
        return False


class Agent:
    def __init__(self, world_object, start_x, start_y, x, y):
        self.world = world_object
        self.x = start_x
        self.y = start_y
        self.map_x = x
        self.map_y = y
        self.knowledge_base = []

        self.visited = set()
        self.visited.add((start_x, start_y))

        self.kb_processed_cells = set()
        self.confirmed_pits = set()
        self.confirmed_wumpus = set()

        # УДАЛИЛИ stuck_count и max_stuck_count - они больше не нужны!

    def get_symbol(self, name, x, y):
        return sp.Symbol(f"{name}_{x}_{y}")

    def tell_kb(self, formula):
        self.knowledge_base.append(formula)

    def ask_kb_is_safe(self, target_x, target_y):
        full_kb = sp.And(*self.knowledge_base)
        pit_sym = self.get_symbol("pit", target_x, target_y)
        if sp.satisfiable(full_kb & pit_sym):
            return False
        vantus_sym = self.get_symbol("vantus", target_x, target_y)
        if sp.satisfiable(full_kb & vantus_sym):
            return False
        return True

    def ask_kb_is_confirmed(self, target_x, target_y, danger_type):
        danger_sym = self.get_symbol(danger_type, target_x, target_y)
        full_kb = sp.And(*self.knowledge_base)
        assumption = full_kb & sp.Not(danger_sym)
        if not sp.satisfiable(assumption):
            return True
        return False

    def get_neighbors(self, x, y):
        neighbors = []
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.map_x and 0 <= ny < self.map_y:
                neighbors.append((nx, ny))
        return neighbors

    # --- ГЛАВНОЕ НОВОВВЕДЕНИЕ: BFS ---
    def get_best_move_bfs(self):
        """
        Ищет путь к БЛИЖАЙШЕЙ безопасной, но не посещенной клетке.
        Возвращает координаты первой клетки, в которую надо шагнуть.
        """
        # Очередь хранит: (координаты_x, координаты_y, первый_шаг_чтобы_туда_попасть)
        queue = deque()
        visited_in_bfs = set()
        visited_in_bfs.add((self.x, self.y))

        # Добавляем соседей текущей клетки в очередь
        for nx, ny in self.get_neighbors(self.x, self.y):
            # Мы можем шагнуть в соседа, только если он безопасен
            # Но если там яма или монстр (доказанные) - туда идти нельзя
            if (nx, ny) in self.confirmed_pits or (nx, ny) in self.confirmed_wumpus:
                continue

            # Важный момент: BFS ходит ТОЛЬКО по безопасным клеткам
            # Мы проверяем is_safe только для первого шага? Нет, для всех.
            # Но чтобы не перегружать логику (ask_kb долго думает), мы делаем хитро:
            # Мы можем ходить по УЖЕ ПОСЕЩЕННЫМ клеткам (они точно безопасны)
            # И мы ищем такую клетку, которая БЕЗОПАСНА и НЕ ПОСЕЩЕНА.

            # Третий параметр - это First Move
            queue.append((nx, ny, (nx, ny)))
            visited_in_bfs.add((nx, ny))

        while queue:
            cx, cy, first_move = queue.popleft()

            # 1. Проверяем, является ли эта клетка целью?
            # Цель = Безопасная И Непосещенная
            is_visited = (cx, cy) in self.visited

            # Если мы тут не были - надо проверить, безопасно ли тут?
            # Если мы тут были - мы знаем, что безопасно.
            if not is_visited:
                # Спрашиваем базу знаний (это тяжелая операция, но BFS гарантирует, что мы спросим ближайшие сначала)
                if self.ask_kb_is_safe(cx, cy):
                    # НАШЛИ! Идем в сторону этой клетки (делаем first_move)
                    return first_move
                else:
                    # Если клетка не безопасна, мы через неё пройти не можем, путь закрыт
                    continue

            # 2. Если мы тут уже были (или клетка безопасна), расширяем поиск дальше
            # Мы можем идти дальше только через те клетки, которые мы уже посетили
            # (потому что мы не можем телепортироваться через неисследованные безопасные клетки, мы должны дойти до них)
            if is_visited:
                for nx, ny in self.get_neighbors(cx, cy):
                    if (nx, ny) not in visited_in_bfs:
                        if (nx, ny) in self.confirmed_pits or (nx, ny) in self.confirmed_wumpus:
                            continue

                        visited_in_bfs.add((nx, ny))
                        # first_move тянется от самого начала цепочки
                        queue.append((nx, ny, first_move))

        return None  # Если ничего не нашли

    def step(self):
        print(f"\n---Я в {self.x}, {self.y}---")
        real_cell = self.world.get_world()[self.x][self.y]

        if "pit" in real_cell:
            print(">>> СМЕРТЬ В ЯМЕ! <<<")
            return False
        if "vantus" in real_cell:
            print(">>> СЪЕЛ ВАМПУС! <<<")
            return False

        current_feelings = self.world.get_percepts(self.x, self.y)
        print(f"Чувствую: {current_feelings}")

        if "shine" in current_feelings:
            print(">>> ЗОЛОТО! ПОБЕДА! <<<")
            return False

        neighbors = self.get_neighbors(self.x, self.y)

        # Обновление базы знаний
        if (self.x, self.y) not in self.kb_processed_cells:
            self.tell_kb(sp.Not(self.get_symbol("pit", self.x, self.y)))
            self.tell_kb(sp.Not(self.get_symbol("vantus", self.x, self.y)))

            pit_neighbors = [self.get_symbol("pit", i, j)
                             for i, j in neighbors]
            wind_rule = sp.Equivalent(self.get_symbol(
                "wind", self.x, self.y), sp.Or(*pit_neighbors))
            self.tell_kb(wind_rule)

            if "wind" in current_feelings:
                self.tell_kb(self.get_symbol("wind", self.x, self.y))
            else:
                self.tell_kb(sp.Not(self.get_symbol("wind", self.x, self.y)))

            vantus_neighbors = [self.get_symbol(
                "vantus", i, j) for i, j in neighbors]
            stink_rule = sp.Equivalent(self.get_symbol(
                "stink", self.x, self.y), sp.Or(*vantus_neighbors))
            self.tell_kb(stink_rule)

            if "stink" in current_feelings:
                self.tell_kb(self.get_symbol("stink", self.x, self.y))
            else:
                self.tell_kb(sp.Not(self.get_symbol("stink", self.x, self.y)))
            self.kb_processed_cells.add((self.x, self.y))

        # Поиск точных угроз (Эврика)
        for nx, ny in neighbors:
            if (nx, ny) not in self.confirmed_pits and (nx, ny) not in self.visited:
                if self.ask_kb_is_confirmed(nx, ny, "pit"):
                    print(f"!!! ЭВРИКА! В ({nx}, {ny}) 100% ЯМА! Запоминаю...")
                    self.confirmed_pits.add((nx, ny))
                    self.tell_kb(self.get_symbol("pit", nx, ny))

            if (nx, ny) not in self.confirmed_wumpus and (nx, ny) not in self.visited:
                if self.ask_kb_is_confirmed(nx, ny, "vantus"):
                    print(
                        f"!!! ЭВРИКА! В ({nx}, {ny}) 100% ВАНТУС! Запоминаю...")
                    self.confirmed_wumpus.add((nx, ny))
                    self.tell_kb(self.get_symbol("vantus", nx, ny))

        print("Думаю...")

        # --- НОВАЯ ЛОГИКА ВЫБОРА ХОДА (BFS) ---

        # 1. Пытаемся найти путь к ближайшей безопасной неизведанной клетке
        best_move = self.get_best_move_bfs()

        if best_move:
            print(f"Умный ход (BFS): {best_move}")
            next_move = best_move
        else:
            # 2. Если безопасных целей нет вообще -> РИСКУЕМ (Panic Mode)
            print(">>> БЕЗОПАСНЫХ ЦЕЛЕЙ НЕТ! РЕЖИМ РИСКА! <<<")

            # Фильтруем соседей, исключая явную смерть
            valid_risk_neighbors = [
                n for n in neighbors
                if n not in self.confirmed_pits and n not in self.confirmed_wumpus
            ]

            risky_unvisited = [
                n for n in valid_risk_neighbors if n not in self.visited]

            if risky_unvisited:
                next_move = random.choice(risky_unvisited)
                print(f"!!! РИСКУЮ (В неизвестность): {next_move}")
            elif valid_risk_neighbors:
                next_move = random.choice(valid_risk_neighbors)
                print(
                    f"!!! РИСКУЮ (Куда угодно, лишь бы не в стену): {next_move}")
            else:
                print("Я полностью окружен смертью. Выхода нет.")
                return False

        self.x, self.y = next_move
        self.visited.add((self.x, self.y))
        return True

    def run(self):
        print("Начинаю игру...")
        steps_limit = 50
        steps = 0
        while steps < steps_limit:
            steps += 1
            result = self.step()
            if result is False:
                print("Игра окончена!")
                break
            time.sleep(0.1)  # Быстрее для консоли
        if steps >= steps_limit:
            print("Превышен лимит шагов!")


def main():
    print("Hello from ВАНТУС!")
    x = 5
    y = 5
    probability_of_pit = 0.16
    world = WampusWorld(x,  y, probability_of_pit)
    agent = Agent(world, 0, 0, x, y)
    agent.run()


if __name__ == "__main__":
    main()
