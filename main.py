import random
import pygame as pg
from typing import Dict, List
from collections import deque
import os


class Genome:
    def __init__(self, app, square, bot, chain: Dict = None):
        self.app = app
        self.square = square
        self.bot = bot

        # creating dictionary of commands:
        self.commands: Dict = {
            23: 'Photosynthesis',
            25: 'Turn',
            33: 'How_many_energy',
            26: 'Move',
            40: 'Look',
            15: 'eat_coral',
            20: 'eat_bot',
            57: 'share_energy'
        }
        self.command_numbers: List = [23, 25, 33, 26, 40, 15, 20, 57]
        if chain is None:
            self.chain: Dict = {i: random.choice(self.command_numbers) for i in range(64)}
        else:
            self.chain: Dict = {key: value for key, value in chain.items()}
            self.chain[random.randint(0, 63)] = random.randint(0, 63)

        self.current_ptr = 0

    def is_relative(self, genome):
        count_of_match = 0
        for i in range(64):
            if genome.chain[i] == self.chain[i]:
                count_of_match += 1
        if count_of_match < 62:
            return False
        else:
            return True

    def choose_command(self, the_end):
        num = self.chain[self.current_ptr % 64]
        if num in self.command_numbers:
            comm = self.commands[num]
            if comm == 'Photosynthesis':
                the_end = self.bot.photosynthesis(the_end=the_end)
            elif comm == 'Turn':
                self.bot.turn()
            elif comm == 'How_many_energy':
                self.bot.how_many_energy()
            elif comm == 'Move':
                the_end = self.bot.move()
            elif comm == 'Look':
                self.bot.look()
            elif comm == 'eat_coral':
                the_end = self.bot.eat_corals(the_end=the_end)
            elif comm == 'eat_bot':
                the_end = self.bot.eat_bot(the_end=the_end)
            elif comm == 'share_energy':
                self.bot.share_energy()
                the_end = 1
        else:
            self.current_ptr += num
        return the_end


class Bot:
    def __init__(self, app, square, color, MAX_ENERGY=1000, genome=None):
        self.app = app
        self.color = color  # color of bot (green: often photosynthesis, blue: often corals, red: often eat other bots)
        self.square = square  # pointer on square where bot should to be
        # self.x, self.y = square.x, square.y

        self.max_energy = MAX_ENERGY
        self.energy = 50
        self.energy_to_next_division = 250
        self.count_of_children = 1

        self.photosynthesis_count = 0
        self.eat_corals_count = 0
        self.eat_bot_count = 0

        self.direction = deque([(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)])  # where bot is looking to (look at TURN and MOVE meth)
        if genome is None:
            self.genome: Genome = Genome(app=self.app, square=self.square, bot=self)
        else:
            self.genome: Genome = Genome(app=self.app, square=self.square, bot=self, chain=genome.chain)

    def turn(self):
        param = self.genome.chain[(self.genome.current_ptr + 1) % 64] % 8
        self.direction.rotate(param)
        self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 1) % 64]
        self.genome.current_ptr = self.genome.current_ptr % 64
        self.energy -= 25

    def move(self):
        # chose square to move
        x = (self.square.x + self.direction[0][0]) % self.app.COLS
        y = (self.square.y + self.direction[0][1]) % self.app.ROWS
        sq: Square = self.app.grid[y][x]            # target square

        if sq.is_wall:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 3) % 64]
            self.genome.current_ptr = self.genome.current_ptr % 64
            self.energy -= 25
        elif sq.is_bot:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 2) % 64]
            self.genome.current_ptr = self.genome.current_ptr % 64
            self.energy -= 25
        else:
            sq.bot_id = self.square.bot_id
            self.square.bot_id = 0
            self.square.is_bot = 0
            sq.is_bot = 1
            self.square = sq

            self.genome.current_ptr += 1 #self.genome.chain[(self.genome.current_ptr + 1) % 64]
            self.genome.current_ptr = self.genome.current_ptr % 64
            self.energy -= 50

    def photosynthesis(self, the_end):
        self.energy += self.square.sun * 0.65
        self.genome.current_ptr += 1
        self.genome.current_ptr = self.genome.current_ptr % 64
        if self.square.sun > 0:
            the_end = 1
            self.photosynthesis_count += 1
        else:
            the_end = 0
        return the_end

    def eat_corals(self, the_end):
        self.energy += self.square.corals * 0.65
        self.genome.current_ptr += 1
        self.genome.current_ptr = self.genome.current_ptr % 64
        if self.square.corals > 0:
            the_end = 1
            self.eat_corals_count += 1
        else:
            the_end = 0

        return the_end

    def eat_bot(self, the_end):
        x = (self.square.x + self.direction[0][0]) % self.app.COLS
        y = (self.square.y + self.direction[0][1]) % self.app.ROWS
        sq: Square = self.app.grid[y][x]            # target square

        if sq.is_wall:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 4) % 64]
            self.genome.current_ptr = self.genome.current_ptr % 64
            self.energy -= 25
        if sq.is_bot and sq.bot_id in self.app.bots_id_list:
            # TODO: fix keyerror (WHY?)
            # ТУТ ОШИБКА KEYERROR
            # os.system('pause')
            bot: Bot = self.app.bots_dict[sq.bot_id]
            # TODO is_relative (родственник (код-геном отличается меньше на 2 байта)) (done)
            if self.is_relative(bot=bot):
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+3) % 64]
            elif bot.energy-200 <= self.energy:            # если энергии меньше, то съедаем бота, иначе энергия минус
                # eat part
                sq.delete_bot()
                """
                sq.is_bot = 0
                del sq.app.bots_dict[sq.bot_id]
                sq.app.bots_id_list.remove(sq.bot_id)
                sq.bot_id = 0
                """
                self.energy += bot.energy

                # move part
                sq.bot_id = self.square.bot_id
                self.square.bot_id = 0
                self.square.is_bot = 0
                sq.is_bot = 1
                self.square = sq

                # color part
                self.color = pg.Color('red')

                # genome part
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+1) % 64]
                self.genome.current_ptr = self.genome.current_ptr % 64
                the_end = 1
            else:
                self.energy -= 50

                # genome part
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+2) % 64]
                self.genome.current_ptr = self.genome.current_ptr % 64
        elif (not sq.is_bot) and sq.bot_id in self.app.bots_id_list:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+4) % 64]
        self.eat_bot_count += 1
        return the_end

    def how_many_energy(self):
        """change genome ptr"""
        ptr = (self.genome.current_ptr + 1) % 64
        param = self.genome.chain[ptr] * 15
        if self.energy > param:
            self.genome.current_ptr += self.genome.chain[ptr]
        else:
            self.genome.current_ptr += self.genome.chain[(ptr+1) % 64]

        """delete and division"""
        if self.energy > self.max_energy or self.energy < 0:
            self.square.delete_bot()
        elif self.energy >= self.count_of_children * self.energy_to_next_division:
            self.division()

    def division(self):
        x = (self.square.x + self.direction[0][0]) % self.app.COLS
        y = (self.square.y + self.direction[0][1]) % self.app.ROWS
        sq: Square = self.app.grid[y][x]

        self.count_of_children += 1
        count_of_turns = 0
        while sq.is_wall or sq.is_bot:
            self.turn()
            count_of_turns += 1
            if count_of_turns >= 9:
                break
        if (not sq.is_bot) and (not sq.is_wall):
            sq.bot_id = self.app.new_bot(square=sq, bot=self)
            sq.is_bot = 1

    def is_relative(self, bot):
        return self.genome.is_relative(bot.genome) and self.color == bot.color

    def change_color(self):
        if self.photosynthesis_count >= self.eat_corals_count and self.photosynthesis_count >= self.eat_bot_count:
            self.color = pg.Color('green')
        elif self.eat_corals_count >= self.eat_bot_count and self.eat_corals_count > self.photosynthesis_count:
            self.color = pg.Color('blue')
        elif self.eat_bot_count > self.photosynthesis_count and self.eat_bot_count > self.eat_corals_count:
            self.color = pg.Color('red')

    def share_energy(self):
        x = (self.square.x + self.direction[0][0]) % self.app.COLS
        y = (self.square.y + self.direction[0][1]) % self.app.ROWS
        sq: Square = self.app.grid[y][x]  # target square

        if sq.is_bot and sq.bot_id in self.app.bots_id_list:
            bot: Bot = self.app.bots_dict[sq.bot_id]
            if self.is_relative(bot=bot):
                count = self.genome.chain[(self.genome.current_ptr + 1) % 64] * 2
                self.energy -= count
                bot.energy += count
                self.genome.current_ptr += 2        # тут всё правильно
            else:
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 2) % 64]       # тут всё правильно
        else:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 3) % 64]

    def look(self):
        x = (self.square.x + self.direction[0][0]) % self.app.COLS
        y = (self.square.y + self.direction[0][1]) % self.app.ROWS
        sq: Square = self.app.grid[y][x]

        if sq.is_wall:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr + 4) % 64]
        elif sq.is_bot and sq.bot_id in self.app.bots_id_list:
            bot: Bot = self.app.bots_dict[sq.bot_id]
            if self.is_relative(bot=bot):
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+3) % 64]
            else:
                self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+2) % 64]
        else:
            self.genome.current_ptr += self.genome.chain[(self.genome.current_ptr+1) % 64]

    def your_turn(self):
        the_end_of_turn = 0
        number_of_actions = 0
        while True:
            the_end_of_turn = self.genome.choose_command(the_end=the_end_of_turn)
            number_of_actions += 1
            if self.energy > self.max_energy or self.energy < 0:
                self.square.delete_bot()
            elif self.energy >= self.count_of_children * self.energy_to_next_division:
                self.division()
            if number_of_actions == 15 or the_end_of_turn == 1:
                break
        self.energy -= 50


class Square:
    def __init__(self, _app, pos, is_bot, sun, corals, is_wall):
        self.app = _app                 # pointer on class app
        self.is_bot = is_bot            # bot here or not
        self.sun = sun                  # how many energy bot may get from this square
        self.corals = corals            # just coral here or not, bot may eat coral and get energy
        self.is_wall = is_wall
        self.x, self.y = pos

        self.rect = self.x * self.app.CELL_SIZE, self.y * self.app.CELL_SIZE, \
                    self.app.CELL_SIZE - 1, self.app.CELL_SIZE - 1

        if is_wall:
            self.is_bot = 0
        if self.is_bot:
            self.bot_id = self.app.new_bot(square=self)
        else:
            self.bot_id = 0

    def draw_rect(self):
        if self.bot_id == 0:            # костыль, иногда в клетке bot_id = 0, a is_bot = 1
            self.is_bot = 0
        if self.is_bot and self.bot_id in self.app.bots_id_list:
            bot: Bot = self.app.bots_dict[self.bot_id]
            # os.system('pause')
            # TODO: fix keyerror (WHY?)

            bot.change_color()

            color = bot.color
            pg.draw.rect(self.app.screen, color, self.rect)
        else:
            pg.draw.rect(self.app.screen, pg.Color('white'), self.rect)

    def delete_bot(self):
        if self.is_bot and self.bot_id in self.app.bots_id_list:
            del self.app.bots_dict[self.bot_id]
            self.app.bots_id_list.remove(self.bot_id)
            self.is_bot = 0
            self.bot_id = 0


class App:
    def __init__(self, WIDTH=1920, HEIGHT=1080, CELL_SIZE=12, FPS=300):
        self.bots_eated = 0
        pg.init()
        self.screen = pg.display.set_mode([WIDTH, HEIGHT])
        self.clock = pg.time.Clock()
        self.FPS = FPS
        self.CELL_SIZE = CELL_SIZE
        self.ROWS, self.COLS = int(HEIGHT // CELL_SIZE), int(WIDTH // CELL_SIZE)
        # self.grid = [[0 for col in range(self.COLS)] for j in range(self.ROWS)]

        self.colors: Dict = {
            0: 'green',         # to make random color from this dictionary
            1: 'blue',
            2: 'red'
        }
        self.bots_id_list: List = []  # чтобы в функции new bot айди не повторялось
        self.bots_dict: Dict = {}
        self.grid = [[Square(_app=self, pos=[col, row], is_bot=random.randint(0, 1),
                             sun=self.resource_sun_allocation(y=row), corals=self.resource_coral_allocation(y=row),
                             is_wall=1 if row == 0 or row == self.ROWS - 1 else 0)
                      for col in range(self.COLS)] for row in range(self.ROWS)]

########################################################################################################################

    def run(self):
        while True:
            for row in self.grid:
                for square in row:
                    if square.is_bot and square.bot_id in self.bots_id_list:
                        bot: Bot = self.bots_dict[square.bot_id]
                        bot.your_turn()
                        """
                        rand_command = random.randint(0, 6)
                        if rand_command == 0:
                            bot.how_many_energy()
                        if rand_command == 1:
                            bot.photosynthesis()
                        if rand_command == 2:
                            bot.eat_corals()
                        if rand_command == 3:
                            bot.eat_bot()
                        if rand_command == 4:
                            bot.move()
                        if rand_command == 5:
                            bot.turn()
                        if rand_command == 6:
                            bot.share_energy()
                        # bot.turn()
                        # bot.move()
                        """

            for row in self.grid:
                for square in row:
                    square.draw_rect()

            [exit() for i in pg.event.get() if type == pg.QUIT]
            pg.display.flip()
            self.clock.tick(self.FPS)

            """
            for row in self.grid:
                for square in row:
                    square.draw_rect()
            """

    def new_bot(self, square, bot: Bot = None):
        squares_count = self.ROWS * self.COLS
        _id = random.randrange(1, squares_count * 5)
        while _id in self.bots_id_list:  # уникальный id, чтобы не повторялся с уже сгенерированными
            _id = random.randrange(1, squares_count * 5)
        self.bots_id_list.append(_id)

        if bot is None:
            self.bots_dict[_id] = Bot(app=self, square=square, color=pg.Color('grey'))   # pg.Color(self.colors[random.randint(0, 2)]))
        else:
            self.bots_dict[_id] = Bot(app=self, square=square, color=bot.color, genome=bot.genome)
        return _id

    def resource_sun_allocation(self, y):       # or Y?
        if y <= int(self.ROWS / 2):
            sun = 100-(y-1)*(100/self.ROWS/2)
        else:
            sun = 0
        return sun

    def resource_coral_allocation(self, y):
        if y > int(self.ROWS / 2):
            coral = 100-(self.ROWS-(y-1))*(100/self.ROWS/2)        # (y-int(self.ROWS*(2/3)))*int(100/(self.ROWS-int(self.ROWS*(2/3))))
        else:
            coral = 0
        return coral   # int(y/(3*self.ROWS) * 100) if y > int(self.ROWS * 2 / 3) else 0


if __name__ == '__main__':
    main_app = App()
    main_app.run()
