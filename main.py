import sympy as sp
import random
import time

description_cells = {
    "empty_cell": 0,
    "pit": -1,
    "vantus": -10,
    "wind": -2,
    "stink": -11,
    "agent": 100,
    "shine": 9999,
    "gold": 9999
}


class WampusWorld:
    def __init__(self, x, y, probability_of_pit):
        print(
            f"Размеры карты: x={x}, y={y}, вероятность_появление_ямы={probability_of_pit}")
        self.x = x
        self.y = y
        self.probability_of_pit = probability_of_pit
        self.description_cells = description_cells
        self.world = self.generation_world(x, y, probability_of_pit)

    def get_world(self):
        return self.world

    def generation_world(self, x, y, probability_of_pit):
        self.world = [[[] for _ in range(self.x+2)] for _ in range(self.y+2)]

        self.y = self.y + 1
        self.x = self.x + 1

        # Генерация ЯМ (Pits)
        for i in range(1, self.x):
            for j in range(1, self.y):
                if (i != 1 or j != 1) and (random.random() < self.probability_of_pit):
                    if "pit" not in self.world[i][j]:
                        self.world[i][j].append("pit")

                    if "wind" not in self.world[i][j+1]:
                        self.world[i][j+1].append("wind")

                    if "wind" not in self.world[i][j-1]:
                        self.world[i][j-1].append("wind")

                    if "wind" not in self.world[i+1][j]:
                        self.world[i+1][j].append("wind")

                    if "wind" not in self.world[i-1][j]:
                        self.world[i-1][j].append("wind")

        # Генерация ВАНТУСА (Vantus)
        temp_mass = []
        for i in range(1, self.x):
            for j in range(1, self.y):
                if ("pit" not in self.world[i][j]) and (i != 1 or j != 1):
                    temp_mass.append((j*3+i*2, i, j))

        target = random.randint(
            min(x[0] for x in temp_mass), max(x[0] for x in temp_mass))
        indexs = min(temp_mass, key=lambda x: (abs(x[0] - target), -x[0]))

        # Ставим Вантуса
        self.world[indexs[1]][indexs[2]].append("vantus")

        # Добавляем вонь (stink) соседям

        if "stink" not in self.world[indexs[1]][indexs[2]+1]:
            self.world[indexs[1]][indexs[2]+1].append("stink")

        if "stink" not in self.world[indexs[1]][indexs[2]-1]:
            self.world[indexs[1]][indexs[2]-1].append("stink")

        if "stink" not in self.world[indexs[1]+1][indexs[2]]:
            self.world[indexs[1]+1][indexs[2]].append("stink")

        if "stink" not in self.world[indexs[1]-1][indexs[2]]:
            self.world[indexs[1]-1][indexs[2]].append("stink")

        # Генерация ИГРОКА (agent)
        self.world[1][1].append("agent")

        # Генерация ЗОЛОТА (Gold)
        temp_mass = []
        for i in range(1, self.x):
            for j in range(1, self.y):
                if ("pit" not in self.world[i][j]) and \
                    (i != 1 or j != 1) and \
                        ("vantus" not in self.world[i][j]):
                    temp_mass.append((j*3+i*2, i, j))

        target = random.randint(
            min(x[0] for x in temp_mass), max(x[0] for x in temp_mass))
        indexs = min(temp_mass, key=lambda x: (abs(x[0] - target), -x[0]))

        # Ставим золото
        self.world[indexs[1]][indexs[2]].append("gold")
        self.world[indexs[1]][indexs[2]].append("shine")

        print('\n')
        for row in self.world:
            print(row)
        self.world_replication = [
            [[] for _ in range(self.x-1)] for _ in range(self.y-1)]
        print('\n')
        for i in range(0, self.x-1):
            for j in range(0, self.y-1):
                self.world_replication[i][j] = self.world[i+1][j+1]
        for row in self.world_replication:
            print(row)
        self.world = self.world_replication

        return self.world

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
        # Сам не додумался, но формула и теории задач о блуждании интересная( не зря в Т-банк пробовал решить её)
        # Но это тоже мусор, так как у нас игра, а не теор вер
        self.max_stuck_count = 3*(x*y)**0.5
        self.kb_processed_cells = set()  # Все клетки, которые посетили

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

        print("Думаю...")
        safe_moves = []
        for i, j in neighbors:  # спрашиваем, нас не убьет?)
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
            if self.stuck_count >= self.max_stuck_count:
                print("Я застрял в безопасном круге! ПРИДЕТСЯ РИСКОВАТЬ!")
            if random.random() < 0.01:
                print("Нервы сдали. Агент сделал харакири!")
                return False
            else:
                print("Безопасных нет! Придется рисковать...")
                risky_unvisited = [
                    n for n in neighbors if n not in self.visited]
                if risky_unvisited:
                    next_move = random.choice(risky_unvisited)
                    print(
                        f"!!!Кто не рисукет, тот не открывает сезон в Шерегеше с Егермейстером!!! Иду в неизвестность: {next_move}")
                else:
                    next_move = random.choice(neighbors)
                    print(f"!!! РИСКУЮ !!! Иду наугад по соседям: {next_move}")
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
