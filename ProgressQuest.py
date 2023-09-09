import random
import curses

# Define the Hero class
class Hero:

#ここあたりのパラメータをいじると楽しい。
    XP_MULTIPLIER = 300  # Define a constant multiplier for XP required for next level
    DEFAULT_STR = 8
    DEFAULT_VIT = 8
    DEFAULT_ENDURANCE = 8
    DEFAULT_LUCK = 8
    DEFAULT_DIRECTIONALSENSE = 8
    
    EQUIPMENT_COST_MULTIPLIER = 3  # New constant for equipment pricing formula


    def __init__(self, STR=DEFAULT_STR, VIT=DEFAULT_VIT, ENDURANCE=DEFAULT_ENDURANCE, LUCK=DEFAULT_LUCK, DIRECTIONALSENSE=DEFAULT_DIRECTIONALSENSE):
        self.level = 1
        self.experience = 0
        self.STR = STR
        self.VIT = VIT
        self.ENDURANCE = ENDURANCE
        self.LUCK = LUCK
        self.DIRECTIONALSENSE = DIRECTIONALSENSE
        self.max_health = int(100 + self.VIT / 4 * self.level)
        self.health = self.max_health
        self.stamina = 100
        self.gold = 0
        self.trophies = []
        self.distance_from_town = 0  # in kilometers
        self.quest_progress = 0  # in percentage
        self.weapon = None
        self.shield = None
        
    def explore(self):
        self.stamina -= 1
        # Use DirectionalSense to determine if the hero moves forward or backward
        if random.random() < (80 + self.DIRECTIONALSENSE) / 160:
            self.distance_from_town += 1
        else:
            self.distance_from_town -= 1
        # If 10km away from town, gain 1% of quest progress
        if self.distance_from_town == 10:
            self.quest_progress += 1
            self.distance_from_town = 0  # Reset the distance after gaining progress
        return random.choice([True, False])

    def fight(self, monster):
        initial_monster_health = monster.health
        while self.health > 0 and monster.health > 0:
            damage_dealt = random.randint(self.STR // 3, self.STR)
            damage_taken = monster.attack()

            # Apply weapon modifier and take Endurance into account for durability
            if self.weapon and not self.weapon.is_broken():
                damage_dealt += self.weapon.use()
                if random.random() < self.ENDURANCE / 40:
                    self.weapon.duration += 1  # Revert the duration decrement

            # Apply shield modifier and take Endurance into account for durability
            if self.shield and not self.shield.is_broken():
                damage_taken -= self.shield.use()
                if random.random() < self.ENDURANCE / 40:
                    self.shield.duration += 1  # Revert the duration decrement

            self.health -= max(damage_taken, 0)
            monster.health -= damage_dealt

        victory = self.health > 0
        if victory:
            self.experience += initial_monster_health
            self.check_level_up()
        return victory

    def collect_trophy(self, monster):
        self.trophies.append(monster.trophy)

    def return_to_town(self, town):
        self.distance_from_town = 0  # Reset the distance when returning to town

        self.gold += town.sell_trophies(self.trophies)
        self.trophies = []
        self.eat(town)
        self.sleep(town)
        self.stamina = 100  # Restore stamina to max

    def buy_equipment(self, town):
        # Check gold and see what equipment is affordable
        affordable_equipments = town.buy_equipment(self.gold)
        if affordable_equipments:
            chosen_equipment = random.choice(affordable_equipments)
            equipment_cost = chosen_equipment.modifier * chosen_equipment.modifier * Hero.EQUIPMENT_COST_MULTIPLIER
            if chosen_equipment.name == "Weapon":
                self.weapon = chosen_equipment
            elif chosen_equipment.name == "Shield":
                self.shield = chosen_equipment
            self.gold -= equipment_cost

    def eat(self, town):
        food_cost = 10
        if self.gold >= food_cost:
            self.gold -= food_cost
            self.stamina += 50

    def sleep(self, town):
        self.health = self.max_health

    def rest_on_street(self):
        health_before = self.health
        self.stamina -= 10
        self.health += int(self.max_health * 0.2)
        if self.health > self.max_health:
            self.health = self.max_health

    def check_level_up(self):
        while self.experience >= self.level * Hero.XP_MULTIPLIER:
            self.experience -= self.level * Hero.XP_MULTIPLIER
            self.level_up()

    def level_up(self):
        self.level += 1
        # Adjust the max health based on VIT
        self.max_health = int(100 + self.VIT / 4 * self.level)
        self.health = self.max_health
        self.stamina += 1
        
class Equipment:
    def __init__(self, name, modifier, duration):
        self.name = name
        self.modifier = modifier
        self.duration = duration

    def use(self):
        if self.duration > 0:
            self.duration -= 1
            return self.modifier
        return 0

    def is_broken(self):
        return self.duration <= 0

def display_hero_status(stdscr, hero, previous_health, previous_stamina):
    # Clear the top portion of the screen for the status
    for i in range(5):
        stdscr.addstr(i, 0, " " * 80)

    # Display hero status
    health_change = int(hero.health - previous_health)
    health_sign = "+" if health_change >= 0 else ""
    stamina_change = int(hero.stamina - previous_stamina)
    stamina_sign = "+" if stamina_change >= 0 else ""

    stdscr.addstr(0, 0, "HERO")
    stdscr.addstr(1, 0, f"Health:   {hero.health}/{hero.max_health}   ({health_sign}{health_change})")
    stdscr.addstr(2, 0, f"Stamina:  {hero.stamina}/100 ({stamina_sign}{stamina_change})")
    stdscr.addstr(3, 0, f"Gold:     {hero.gold}")
    stdscr.addstr(4, 0, f"Distance: {hero.distance_from_town} km from town")

    return hero.health, hero.stamina  # Return current health for next comparison

# Define the Monster class
class Monster:
    def __init__(self):
        self.health = random.randint(20, 60)
        self.trophy = random.choice(['Claw', 'Fang', 'Hide', 'Bone'])

    def attack(self):
        return random.randint(5, 10)

# Define the Town class
class Town:
    def sell_trophies(self, trophies):
        prices = {'Claw': 5, 'Fang': 7, 'Hide': 10, 'Bone': 3}
        return sum(prices[trophy] for trophy in trophies)
    def buy_equipment(self, gold):
        available_equipments = [
            Equipment("Weapon", i, 10 * i) for i in range(1, 6) if gold >= i * i * Hero.EQUIPMENT_COST_MULTIPLIER
        ] + [
            Equipment("Shield", i, 10 * i) for i in range(1, 6) if gold >= i * i * Hero.EQUIPMENT_COST_MULTIPLIER
        ]
        return available_equipments if available_equipments else None

        
        return available_equipments if available_equipments else None

# Game Loop
def game_loop(turns=10):
    hero = Hero()
    town = Town()
    log = []

    for _ in range(turns):
        action_log = []

        if hero.stamina > 20:
            if hero.explore():
                monster = Monster()
                initial_monster_health = monster.health  # Store the initial health
                action_log.append(f"Encountered a monster (Health: {initial_monster_health}).")
                if hero.fight(monster):
                    action_log.append(f"Defeated the monster and collected a {monster.trophy} trophy. Gained {initial_monster_health} XP.")
            # Incorporate LUCK for collecting trophies
                if random.random() < hero.LUCK / 40:
                    hero.collect_trophy(monster)
            if hero.health <= 0.2 * hero.max_health:
                health_before = hero.health
                hero.rest_on_street()
                health_restored = hero.health - health_before
                action_log.append(f"Hero rested on the street and restored {health_restored} health.")
        else:
            action_log.append("Hero returned to town.")
            gold_from_trophies = town.sell_trophies(hero.trophies)
            action_log.append(f"Sold trophies and earned {gold_from_trophies} gold.")
            hero.return_to_town(town)
            
            # Handling the equipment purchase
            hero.buy_equipment(town)
            if hero.weapon:
                weapon_cost = hero.weapon.modifier * hero.weapon.modifier * Hero.EQUIPMENT_COST_MULTIPLIER
                action_log.append(f"Bought a Weapon +{hero.weapon.modifier} for {weapon_cost} gold.")
            if hero.shield:
                shield_cost = hero.shield.modifier * hero.shield.modifier * Hero.EQUIPMENT_COST_MULTIPLIER
                action_log.append(f"Bought a Shield +{hero.shield.modifier} for {shield_cost} gold.")

        
        while hero.experience >= hero.level * Hero.XP_MULTIPLIER:
            hero.experience -= hero.level * Hero.XP_MULTIPLIER
            hero.level_up()
            action_log.append(f"Hero leveled up to level {hero.level}!")
        
        # Display distance from town with + or - sign
        distance_display = f"+{hero.distance_from_town}" if hero.distance_from_town >= 0 else str(hero.distance_from_town)
        
        # Display equipment status
        weapon_status = f"W+{hero.weapon.modifier}({hero.weapon.duration})" if hero.weapon and not hero.weapon.is_broken() else "W(0)"
        shield_status = f"S+{hero.shield.modifier}({hero.shield.duration})" if hero.shield and not hero.shield.is_broken() else "S(0)"
        
        log.append((f"{hero.health}/{hero.max_health}", hero.gold, hero.stamina, len(hero.trophies), distance_display, f"{hero.quest_progress}%", weapon_status, shield_status, action_log))

    return log

'''
# Running the game loop on terminal
if __name__ == "__main__":

    #ゲームの試行回数。数が多ければ多いほど進捗
    game_actions_with_xp = game_loop(30000)

    #ログとして見る分の内容。マイナスがついているのは、最後から何番目までのログを見るかを指定。全部見るとなると大変なため、最後の部分だけ表示させている
    for action in game_actions_with_xp[-100:]:
        print(action)
'''

# Note:
#('今のHP/最大HP', Gold, スタミナ, 持ち物の数, 進捗(10を超えると+1%), クエスト進捗(%),
# W武器(耐久値), S防具(耐久値), [ログの中身]
#('38/176', 1, 32, 0, '+2', '44%', 'W(0)', 'S(0)', [])


def main(stdscr):
    # Set up the terminal
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.nodelay(0)  # Wait for user input
    stdscr.keypad(True)
    
    max_turns = 10000
    
    stdscr.addstr(0, 0, "Welcome to Text-Based Progress Quest!", curses.color_pair(1))
    stdscr.addstr(2, 0, "Press any key to progress one turn or 'q' to quit.")
    
    
    
    # Initialize game
    hero = Hero()
    town = Town()
    log = []
    
    # Initialize previous health for comparison
    previous_health = hero.health
    previous_stamina = hero.stamina
    
    row = 5  # Starting row for game logs
    while True:
        stdscr.clear()  # Clear the screen
        display_hero_status(stdscr, hero, previous_health, previous_stamina)
        
        # Advance one turn and append the results to log
        turn_actions = game_loop(1)
        log.append(turn_actions[0])

        # Display the last action
        for line in log[-1][-1]:  # Taking the last element which is the action_log
            stdscr.addstr(row, 0, line)
            row += 1
        row += 1

        stdscr.addstr(row, 0, "-------------------------------------------------------------------------------")
        row += 1

        # Update previous_health and previous_stamina for the next iteration
        previous_health = hero.health
        previous_stamina = hero.stamina
        
        # Check for 'q' key to quit the game
        k = stdscr.getch()
        if k == ord('q'):
            break

        if len(log) >= max_turns:
            stdscr.addstr(row, 0, "Game Over. Press 'q' to quit.")
            stdscr.getch()  # Wait for a key press
            break
        
        row = 5  # Reset row for next iteration
    
    stdscr.addstr(row, 0, "Thanks for playing!", curses.color_pair(1))
    stdscr.getch()  # Wait for one more key press before exiting


curses.wrapper(main)
