import sympy as sp
import random
import time


class WampusWorld:
    def __init__(self, x, y, probability_of_pit):
        print(
            f"Размеры карты: x={x}, y={y}, вероятность_появление_ямы={probability_of_pit}")
        self.x = x
        self.y = y
        self.probability_of_pit = probability_of_pit
        self.world = self.generation_world(x, y, probability_of_pit)

    def get_world(self):
        return self.world

    def generation_world(self, x, y, probability_of_pit):
        max_attempts = 1000  # Защита от зависания
        attempt = 0
        final_world = []

        while attempt < max_attempts:
            attempt += 1

            gen_x = self.x + 1
            gen_y = self.y + 1

            temp_world = [[[] for _ in range(gen_x + 1)]
                          for _ in range(gen_y + 1)]

            # Генерация ЯМ (Pits)
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

            # Генерация ВАНТУСА (Vantus)
            temp_mass = []
            for i in range(1, gen_x):
                for j in range(1, gen_y):
                    if ("pit" not in temp_world[i][j]) and (i != 1 or j != 1):
                        temp_mass.append((j*3+i*2, i, j))

            target = random.randint(
                min(x[0] for x in temp_mass), max(x[0] for x in temp_mass))
            indexs = min(temp_mass, key=lambda x: (abs(x[0] - target), -x[0]))

            # Ставим Вантуса
            temp_world[indexs[1]][indexs[2]].append("vantus")

            # Добавляем вонь (stink) соседям
            if "stink" not in temp_world[indexs[1]][indexs[2]+1]:
                temp_world[indexs[1]][indexs[2]+1].append("stink")

            if "stink" not in temp_world[indexs[1]][indexs[2]-1]:
                temp_world[indexs[1]][indexs[2]-1].append("stink")

            if "stink" not in temp_world[indexs[1]+1][indexs[2]]:
                temp_world[indexs[1]+1][indexs[2]].append("stink")

            if "stink" not in temp_world[indexs[1]-1][indexs[2]]:
                temp_world[indexs[1]-1][indexs[2]].append("stink")

            # Генерация ИГРОКА (agent)
            temp_world[1][1].append("agent")

            # Генерация ЗОЛОТА (Gold)
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

            # Ставим золото
            temp_world[indexs[1]][indexs[2]].append("gold")
            temp_world[indexs[1]][indexs[2]].append("shine")

            # Обрезка мира
            cropped_world = [[[]
                              for _ in range(self.x)] for _ in range(self.y)]
            for i in range(0, self.x):
                for j in range(0, self.y):
                    cropped_world[i][j] = temp_world[i+1][j+1]

            # Проверка на проходимость
            if self.check_solvability(cropped_world, 0, 0):
                print('\nСгенерированный мир:')
                for row in cropped_world:
                    print(row)
                return cropped_world
            final_world = cropped_world

        print("\nНе удалось создать гарантированно проходимый мир. Возвращаем последний вариант.")
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
        """
        Проверяет, есть ли безопасный путь от (start_x, start_y) до Золота.
        Использует BFS.
        """
        rows = len(grid)
        cols = len(grid[0])

        queue = [(start_x, start_y)]
        visited = set()
        visited.add((start_x, start_y))

        while queue:
            cx, cy = queue.pop(0)
            cell = grid[cx][cy]

            # Если нашли золото - карта проходима!
            if "gold" in cell:
                return True

            # Проверяем соседей
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dx, dy in deltas:
                nx, ny = cx + dx, cy + dy

                # Проверка границ
                if 0 <= nx < rows and 0 <= ny < cols:
                    if (nx, ny) not in visited:
                        neighbor_cell = grid[nx][ny]

                        # Путь существует, только если в клетке НЕТ Ямы и НЕТ Вантуса
                        if "pit" not in neighbor_cell and "vantus" not in neighbor_cell:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
        return False  # Пути нет


class Agent:
    def __init__(self, world_object, start_x, start_y, x, y):
        self.world = world_object
        self.x = start_x
        self.y = start_y
        self.map_x = x
        self.map_y = y
        self.knowledge_base = []
        self.visited = set()  # Где был
        self.visited.add((start_x, start_y))
        self.stuck_count = 0
        self.kb_processed_cells = set()  # Все клетки, которые посетили
        # Для расчета точного ям и вантуса
        self.confirmed_pits = set()
        self.confirmed_wumpus = set()

    def get_symbol(self, name, x, y):
        return sp.Symbol(f"{name}_{x}_{y}")

    def tell_kb(self, formula):
        # Добавить знание в базу
        self.knowledge_base.append(formula)

    def ask_kb_is_safe(self, target_x, target_y):
        # Проверка на яму
        pit_sym = self.get_symbol("pit", target_x, target_y)
        full_kb = sp.And(*self.knowledge_base)
        # satisfiable ищет мир где наша гипотеза + правила - правда, если да, то True
        if sp.satisfiable(full_kb & pit_sym):
            return False

        # Проверка на вантуса
        vantus_sym = self.get_symbol("vantus", target_x, target_y)
        if sp.satisfiable(full_kb & vantus_sym):
            return False

        return True

    def ask_kb_is_confirmed(self, target_x, target_y, danger_type):
        """
        Проверяет, гарантировано ли наличие угрозы (pit/vantus) в клетке.
        """
        # Берем символ (pit_x_y или vantus_x_y)
        danger_sym = self.get_symbol(danger_type, target_x, target_y)

        full_kb = sp.And(*self.knowledge_base)

        # Делаем предположение, что угрозы НЕТ (Not danger)
        assumption = full_kb & sp.Not(danger_sym)

        if not sp.satisfiable(assumption):
            return True

        return False  # Иначе угрозы нет.

    def get_neighbors(self, x, y):

        max_x, max_y = self.map_x, self.map_y
        neighbors = []
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            if 0 <= nx < max_x and 0 <= ny < max_y:
                neighbors.append((nx, ny))
        return neighbors

    def step(self):
        print(f"---Я в {self.x}, {self.y}---")
        real_cell = self.world.get_world()[self.x][self.y]

        # Проверки на смерть
        if "pit" in real_cell:
            print("АААА! Агент упал в ЯМУ! Смерть.")
            return False  # Игра окончена

        if "vantus" in real_cell:
            print("НЯМ-НЯМ! Агента съел ВАНТУС! Смерть.")
            return False

        current_feelings = self.world.get_percepts(self.x, self.y)
        print(f"Чувствую: {current_feelings}")

        if "shine" in current_feelings:
            print("Победа, ЗОЛОТО НАЙДЕНО!")
            return False

        neighbors = self.get_neighbors(self.x, self.y)
        pit_neighbors = [self.get_symbol("pit", i, j) for i, j in neighbors]

        # Факты + правила только в новых клетках, убрали дубли
        if (self.x, self.y) not in self.kb_processed_cells:
            self.tell_kb(sp.Not(self.get_symbol("pit", self.x, self.y)))
            self.tell_kb(sp.Not(self.get_symbol("vantus", self.x, self.y)))

            # wind <=> (p_n1|p_n2 ...)
            wind_rule = sp.Equivalent(
                self.get_symbol("wind", self.x, self.y),
                sp.Or(*pit_neighbors)
            )
            self.tell_kb(wind_rule)

            if "wind" in current_feelings:
                print("-> Тут дует ветер! Добавляю факт")
                self.tell_kb(self.get_symbol("wind", self.x, self.y))
            else:
                self.tell_kb(sp.Not(self.get_symbol("wind", self.x, self.y)))

            # stink
            vantus_neighbors = [self.get_symbol(
                "vantus", i, j) for i, j in neighbors]
            stink_rule = sp.Equivalent(
                self.get_symbol("stink", self.x, self.y),
                sp.Or(*vantus_neighbors)
            )
            self.tell_kb(stink_rule)

            if "stink" in current_feelings:
                print("-> Тут воняет! Добавляю факт")
                self.tell_kb(self.get_symbol("stink", self.x, self.y))
            else:
                self.tell_kb(sp.Not(self.get_symbol("stink", self.x, self.y)))
            self.kb_processed_cells.add((self.x, self.y))

        # Поиск точных угроз
        for nx, ny in neighbors:
            # 1. Проверка ЯМЫ
            if (nx, ny) not in self.confirmed_pits and (nx, ny) not in self.visited:
                if self.ask_kb_is_confirmed(nx, ny, "pit"):
                    print(f"!!! ЭВРИКА! В ({nx}, {ny}) 100% ЯМА! Запоминаю...")
                    self.confirmed_pits.add((nx, ny))
                    self.tell_kb(self.get_symbol("pit", nx, ny))

            # 2. Проверка ВАНТУСА
            if (nx, ny) not in self.confirmed_wumpus and (nx, ny) not in self.visited:
                if self.ask_kb_is_confirmed(nx, ny, "vantus"):
                    print(
                        f"!!! ЭВРИКА! В ({nx}, {ny}) 100% ВАНТУС! Запоминаю...")
                    self.confirmed_wumpus.add((nx, ny))
                    self.tell_kb(self.get_symbol("vantus", nx, ny))

        print("Думаю...")
        safe_moves = []
        for i, j in neighbors:
            # Сначала проверяем: не является ли эта клетка уже доказанной смертью?
            if (i, j) in self.confirmed_pits or (i, j) in self.confirmed_wumpus:
                continue  # пропускаем
            # 2. Безопасно ли там?
            if self.ask_kb_is_safe(i, j):
                safe_moves.append((i, j))

        print("Безопасные соседи:", safe_moves)

        self.max_stuck_count = max(5, len(self.visited)*2)
        # Выбираем приоритет Непосещенные > Посещенные
        unvisited_safe = [m for m in safe_moves if m not in self.visited]

        if unvisited_safe:
            # Если есть новые безопасные клетки - идем в первую
            next_move = unvisited_safe[0]
            self.stuck_count = 0  # понятие скуки, агент устал ходить туда сюда
            print(f"Иду в новую клетку: {next_move}")
        elif safe_moves and self.stuck_count < self.max_stuck_count:
            # Если новых нет идем назад в любую безопасную
            # сделал рандом, чтобы не уходить в цикл при 1 безопасной клетке
            next_move = random.choice(safe_moves)
            self.stuck_count += 1  # ммм новые возможности
            print(
                f"Новых безопасных нет, иду назад ({self.stuck_count}/{self.max_stuck_count}): {next_move}")
        else:
            print("Безопасных нет! Придется рисковать...")
            valid_risk_neighbors = [
                n for n in neighbors
                if n not in self.confirmed_pits and n not in self.confirmed_wumpus
            ]
            risky_unvisited = [
                n for n in valid_risk_neighbors if n not in self.visited]
            if risky_unvisited:
                next_move = random.choice(risky_unvisited)
                print(f"!!!Кто не рисукет... Иду в неизвестность: {next_move}")
            elif valid_risk_neighbors:  # Если есть хоть куда пойти (не в яму)
                next_move = random.choice(valid_risk_neighbors)
                print(
                    f"!!! РИСКУЮ !!! Иду наугад по соседям (но не в яму): {next_move}")
            else:
                print("Я окружен доказанными смертями! Выхода нет.")
                return False  # Вот тут реальный конец игры без шансов
        # логика сборса поумнее:
        # если мы шагнули в клетку, где еще не были — агент успокаивается.
        print(self.knowledge_base)
        if next_move not in self.visited:
            self.stuck_count = 0
        # Делаем ход
        self.x, self.y = next_move
        self.visited.add((self.x, self.y))
        return True  # Продолжаем игру

    def run(self):
        print("Начинаю игру...")
        steps_limit = 20
        steps = 0
        while steps < steps_limit:
            steps += 1
            result = self.step()
            # print("\n")
            # print(f"база знаний: {self.knowledge_base}")
            # print("\n")

            if result is False:
                print("Игра окончена!")
                break
            time.sleep(1)
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
