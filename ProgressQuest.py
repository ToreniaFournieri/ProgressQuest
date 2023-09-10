import random
import curses
import time

import json

# Load the master data from the JSON file
with open('master_data.json', 'r') as file:
    master_data = json.load(file)

# Extract individual data pieces
WEAPON_PREFIXES = master_data["WEAPON_PREFIXES"]
ZONE_TABLE = {int(key): value for key, value in master_data["ZONE_TABLE"].items()}
ZONE_MONSTERS = {int(key): value for key, value in master_data["ZONE_MONSTERS"].items()}
WEAPON_TYPES = master_data["WEAPON_TYPES"]
SHIELD_TYPES = master_data["SHIELD_TYPES"]






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
    EQUIPMENT_DURATION = 40
    current_turn = 1


    def __init__(self, STR=DEFAULT_STR, VIT=DEFAULT_VIT, ENDURANCE=DEFAULT_ENDURANCE, LUCK=DEFAULT_LUCK, DIRECTIONALSENSE=DEFAULT_DIRECTIONALSENSE, EQUIPMENT_DURATION=EQUIPMENT_DURATION):
        self.level = 1
        self.experience = 0
        self.STR = STR
        self.VIT = VIT
        self.ENDURANCE = ENDURANCE
        self.LUCK = LUCK
        self.DIRECTIONALSENSE = DIRECTIONALSENSE
        self.EQUIPMENT_DURATION = EQUIPMENT_DURATION
        self.max_health = int(100 + self.VIT / 4 * self.level)
        self.health = self.max_health
        self.stamina = 100
        self.gold = 0
        self.trophies = []
        self.distance_from_town = 0  # in kilometers
        self.zone = 1
        self.quest_progress = 0  # in percentage
        self.weapon = None
        self.shield = None
        self.monster_defeat_streak = 0  # Counter for the number of monsters defeated in a row
        self.magical_letters = set()  # Store the acquired magical letters
        self.latest_magical_letter = None  # New attribute
        self.magical_letters_collections = 0
        self.strong_weapon = None  # Initialize strong_weapon to None at the start

        self.special_logs = []  # New attribute for storing special logs


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
        # Determine the zone based on distance_from_town
        if self.distance_from_town < 3:
            zone = 1
        elif self.distance_from_town < 6:
            zone = 2
        elif self.distance_from_town < 9:
            zone = 3
        else:
            zone = 4

        monster_encounter = random.choice([True, False])
        return monster_encounter, zone
    
    def fight(self, monster):
        initial_monster_health = monster.health
        while self.health > 0 and monster.health > 0:
            damage_dealt = random.randint(self.STR // 3, self.STR)
            damage_taken = monster.attack()

            # Apply weapon modifier and take Endurance into account for durability
            if self.weapon and not self.weapon.is_broken():
                damage_dealt += self.weapon.use()
                if self.strong_weapon:
                    damage_dealt += self.strong_weapon.use()
                if random.random() < self.ENDURANCE / 40:
                    self.weapon.duration += 1  # Revert the duration decrement

            # Apply shield modifier and take Endurance into account for durability
            if self.shield and not self.shield.is_broken():
                damage_taken -= self.shield.use()
                if random.random() < self.ENDURANCE / 40:
                    self.shield.duration += 1  # Revert the duration decrement

            # Adjust damage dealt by monster's defense
            effective_damage_dealt = monster.defend(damage_dealt)
            monster.health -= max(effective_damage_dealt, 1)
            if monster.health > 0:  # Only subtract damage from hero if boss is still alive
                self.health -= max(damage_taken, 1)

        victory = self.health > 0
        # After the fight, if the hero won
        if victory:
            self.monster_defeat_streak += 1
            self.experience += initial_monster_health  # <-- Add this line
            if self.monster_defeat_streak == 3:
                self.acquire_magical_letter()
                self.monster_defeat_streak = 0  # Reset the counter
        else:
            self.monster_defeat_streak = 0  # Reset the counter if the hero was defeated

        return victory

    def boss_fight(self, boss):
        while self.health > 0 and boss.health > 0:
            damage_dealt = random.randint(self.STR // 3, self.STR)
            damage_taken = boss.attack()

            # Apply weapon and shield modifiers, similar to the monster fight
            if self.weapon and not self.weapon.is_broken():
                damage_dealt += self.weapon.use()
                if self.strong_weapon:
                    damage_dealt += self.strong_weapon.use()
                if random.random() < self.ENDURANCE / 40:
                    self.weapon.duration += 1

            if self.shield and not self.shield.is_broken():
                damage_taken -= self.shield.use()
                if random.random() < self.ENDURANCE / 40:
                    self.shield.duration += 1

            boss.health -= damage_dealt
            if boss.health > 0:  # Only subtract damage from hero if boss is still alive
                self.health -= max(damage_taken, 0)

        return self.health > 0  # Return True if hero won, otherwise False

    def reward_strong_weapon(self):
        modifiers = [1, 2, 3, 4, 5]
        probabilities = [0.7, 0.26, 0.03, 0.009, 0.001]  # Adjust these probabilities as needed
        chosen_modifier = random.choices(modifiers, probabilities)[0]

        # Only replace the strong weapon if the new one has a higher modifier
        if not self.strong_weapon or chosen_modifier > self.strong_weapon.modifier:
            self.strong_weapon = Equipment("Strong Weapon", chosen_modifier)
        
    def collect_trophy(self, monster):
        self.trophies.append((monster.trophy, monster.trophy_value))


    def acquire_magical_letter(self):
        letters = ["壱", "弐", "参", "肆", "伍", "陸", "漆", "捌", "玖"]
        acquired_letter = random.choice(letters)
        self.magical_letters.add(acquired_letter)
        # Update the latest_magical_letter attribute
        self.latest_magical_letter =acquired_letter
        # Check if the collection is complete
        if len(self.magical_letters) == 9:
            # Reward logic can go here...
            self.magical_letters_collections += 1
            self.health += int(self.max_health * 0.33)  # Heal 33% of max health
            # Check if a boss already exists and is not defeated, else create a new boss
            if hasattr(self, 'current_boss') and self.current_boss.health > 0:
                boss = self.current_boss
            else:
                boss = Boss(self)
                self.current_boss = boss  # Store the current boss

            victory = self.boss_fight(boss)
            if victory:  # Check if the opponent is a boss
                # Before rewarding the hero, store the current modifier of the strong_weapon (if it exists).
                previous_strong_weapon_modifier = None
                if self.strong_weapon:
                    previous_strong_weapon_modifier = self.strong_weapon.modifier
                self.reward_strong_weapon()

                # Check if a new weapon was acquired or the old one was retained
                if previous_strong_weapon_modifier == self.strong_weapon.modifier:
                    self.special_logs.append(f"主人公はボスを倒した！")
                else:
                    self.special_logs.append(f"主人公はボスを倒し、Strong Weapon +{self.strong_weapon.modifier} を獲得!")
                        
                if len(self.special_logs) > 5:
                    self.special_logs.pop(0)  # Remove the oldest log if there are more than 5
                # Handle rewards or other actions here
                delattr(self, 'current_boss')  # Remove the boss after defeating
            else:
                self.special_logs.append(f"主人公はボスに挑んだ。ボスの残り体力{self.current_boss.health}/{self.current_boss.max_health}。")
            self.magical_letters.clear()  # Reset the collection

    def return_to_town(self, town):
        self.distance_from_town = 0  # Reset the distance when returning to town
        self.discard_broken_equipment()
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
            
            if chosen_equipment.equipment_type == "Weapon":
                # Only replace the weapon if it's of a higher grade
                if not self.weapon or chosen_equipment.modifier > self.weapon.modifier:
                    self.weapon = chosen_equipment
                    self.gold -= equipment_cost
                    
            elif chosen_equipment.equipment_type == "Shield":
                # Only replace the shield if it's of a higher grade
                if not self.shield or chosen_equipment.modifier > self.shield.modifier:
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
        
        # Randomly select a status to increase
        statuses = ['STR', 'VIT', 'ENDURANCE', 'LUCK', 'DIRECTIONALSENSE']
        selected_status = random.choice(statuses)
        setattr(self, selected_status, getattr(self, selected_status) + 1)
        

    def experience_percentage(self):
        required_for_next_level = self.level * Hero.XP_MULTIPLIER
        return (self.experience / required_for_next_level) * 100

    def discard_broken_equipment(self):
        if self.weapon and self.weapon.duration == 0:
            self.weapon = None
        if self.shield and self.shield.duration == 0:
            self.shield = None



class Equipment:
    def __init__(self, equipment_type, modifier, duration=None, prefix=""):
        self.modifier = modifier
        self.duration = duration
        self.equipment_type = equipment_type
        self.prefix = prefix
        if equipment_type == "Weapon":
            self.name = random.choice(WEAPON_TYPES)
            self.prefix = random.choice(WEAPON_PREFIXES) if random.random() < 0.01 else ""
        else:
            self.name = random.choice(SHIELD_TYPES)
            self.prefix = ""

    def use(self):
        if self.duration is not None and self.duration > 0:
            self.duration -= 1
            return self.modifier
        elif self.duration is None:
            return self.modifier
        return 0

    def is_broken(self):
        if self.duration is not None:
            return self.duration <= 0
        return False

    def __str__(self):  # Overriding the default string representation
        if self.is_broken():
            if self.prefix:
                return f"{self.prefix} {self.name} +{self.modifier} (破損)"
            else:
                return f"{self.name} +{self.modifier} (破損)"

        else:
            if self.prefix:
                return f"{self.prefix} {self.name} +{self.modifier} ({self.duration})"
            else:
                return f"{self.name} +{self.modifier} ({self.duration})"

def display_hero_status(stdscr, hero, previous_health, previous_stamina):

    # Display hero status
    health_change = int(hero.health - previous_health)
    health_sign = "+" if health_change >= 0 else ""
    stamina_change = int(hero.stamina - previous_stamina)
    stamina_sign = "+" if stamina_change >= 0 else ""

    stdscr.addstr(0, 0, f"主人公  ターン: {hero.current_turn} ")
    stdscr.addstr(1, 0, f"力:{hero.STR}, 体力:{hero.VIT}, 運:{hero.LUCK}, 熟練:{hero.ENDURANCE}, 方向感覚:{hero.DIRECTIONALSENSE}  ")
    stdscr.addstr(2, 0, f"体力:   {hero.health}/{hero.max_health}   ({health_sign}{health_change})")
    stdscr.addstr(3, 0, f"スタミナ:  {hero.stamina}/100 ({stamina_sign}{stamina_change})")
    stdscr.addstr(4, 0, f"お金:  {hero.gold}")
    
    zone_name = ZONE_TABLE.get(hero.zone, "Unknown Zone")

    stdscr.addstr(5, 0, f"エリア:{zone_name} ({hero.distance_from_town} km) ")
    stdscr.addstr(2, 40, f"Level: {hero.level} ")
    stdscr.addstr(2, 60, f"経験値: {hero.experience} ({hero.experience_percentage():.1f}%)")
    stdscr.addstr(3, 40, f"武器: {hero.weapon}  {hero.strong_weapon}")
    stdscr.addstr(4, 40, f"防具: {hero.shield} ")
    stdscr.addstr(5, 40, f"クエスト進捗: {hero.quest_progress}% ")
    stdscr.addstr(6, 0, f"所持品: {[trophy_name for trophy_name, _ in hero.trophies]} ")
    # List of all possible magical letters in order
    magical_letters_pool = ["壱", "弐", "参", "肆", "伍", "陸", "漆", "捌", "玖"]

    # Display location
    x_pos = 40
    y_pos = 7

    # Display the magical letters
    stdscr.addstr(7, 0, f"連勝記録: {hero.monster_defeat_streak} コンプリート回数:{hero.magical_letters_collections}")

    # Loop through the magical letters pool
    for letter in magical_letters_pool:
        if letter in hero.magical_letters:
            if letter == hero.latest_magical_letter:
                stdscr.attron(curses.A_BOLD)
                stdscr.addstr(y_pos, x_pos, letter)
                stdscr.attroff(curses.A_BOLD)
            else:
                stdscr.addstr(y_pos, x_pos, letter)
        else:
            stdscr.addstr(y_pos, x_pos, '・')
        
        # Move to the next position (considering width of each character and the comma)
        x_pos += len(letter.encode('utf-8')) + 2
        stdscr.addstr(y_pos, x_pos - 2, ', ')

    # Check if the hero is currently challenging a boss
    if hasattr(hero, 'current_boss') and hero.current_boss.health > 0:
        stdscr.addstr(8, 0, f"ボスの体力: {hero.current_boss.health}/{hero.current_boss.max_health}")

    # Display special logs
    special_log_row = 9  # start at row 15, for example
    stdscr.addstr(special_log_row, 60, "特別なログ:")
    if len(hero.special_logs) > 5:
        hero.special_logs = hero.special_logs[-5:]  # Keep only the latest 5 logs
    
    special_log_row += 1
    for log in reversed(hero.special_logs):
        stdscr.addstr(special_log_row, 60, log)
        special_log_row += 1

    return hero.health, hero.stamina  # Return current health for next comparison

# Define the Monster class
class Monster:
    def __init__(self, zone=1):
        monster_type, self.health, self.attack_power, self.defense, self.trophy, self.trophy_value = random.choice(ZONE_MONSTERS[zone])
        self.name = monster_type

    def attack(self):
        return random.randint(self.attack_power // 2, self.attack_power)

    def defend(self, damage):
        return max(damage - self.defense, 1)

# Define the Boss class
class Boss:
    def __init__(self, hero):
        self.max_health = random.randint(hero.max_health * 2, hero.max_health * 4)
        self.health = self.max_health

    def attack(self):
        return random.randint(15, 25)  # Example attack range

# Define the Town class
class Town:
    def sell_trophies(self, trophies):
        return sum(value for name, value in trophies)
    def buy_equipment(self, gold):
        available_equipments = [
            Equipment("Weapon", i, Hero.EQUIPMENT_DURATION * i)
            for i in range(1, 6)
            if gold >= i * i * Hero.EQUIPMENT_COST_MULTIPLIER
        ] + [
            Equipment("Shield", i, Hero.EQUIPMENT_DURATION * i)
            for i in range(1, 6)
            if gold >= i * i * Hero.EQUIPMENT_COST_MULTIPLIER
        ]
        
        # Sort available equipment by modifier in descending order
        available_equipments.sort(key=lambda equipment: equipment.modifier, reverse=True)
    
        
        return available_equipments if available_equipments else None

        

# Game Loop
def game_loop(hero, turns=10):
    town = Town()
    log = []

    for _ in range(turns):
        action_log = []

        if hero.stamina > 20:
            monster_encounter, zone = hero.explore()
            hero.zone = zone
            if monster_encounter:
                monster = Monster(zone)
                initial_monster_health = monster.health  # Store the initial health
                action_log.append(f"{monster.name}に遭遇 (体力: {initial_monster_health}).")
                if hero.fight(monster):
                    # Incorporate LUCK for collecting trophies
                    if random.random() < hero.LUCK / 40:
                        hero.collect_trophy(monster)
                        action_log.append(f"{monster.name}を倒し、{monster.trophy}を獲得した。")
                    action_log.append(f"経験値{initial_monster_health}を獲得。")
                else:
                    action_log.append(f"主人公は{monster.name}にやられてしまった。")
            if hero.health <= 0.2 * hero.max_health:
                health_before = hero.health
                hero.rest_on_street()
                health_restored = hero.health - health_before
                action_log.append(f"主人公は休んで体力を{health_restored} 回復した。")
        else:
            action_log.append("主人公は街に帰った。")
            gold_from_trophies = town.sell_trophies(hero.trophies)
            action_log.append(f"持ち物を売り、{gold_from_trophies}ゴールド獲得した。")
            hero.return_to_town(town)
            
            # Handling the equipment purchase
            hero.buy_equipment(town)
            if hero.weapon:
                weapon_cost = hero.weapon.modifier * hero.weapon.modifier * Hero.EQUIPMENT_COST_MULTIPLIER
                action_log.append(f"武器 Weapon +{hero.weapon.modifier} を{weapon_cost}ゴールドで買った。")
            if hero.shield:
                shield_cost = hero.shield.modifier * hero.shield.modifier * Hero.EQUIPMENT_COST_MULTIPLIER
                action_log.append(f"防具 Shield +{hero.shield.modifier}を{shield_cost}ゴールドで買った.")

        
        while hero.experience >= hero.level * Hero.XP_MULTIPLIER:
            hero.experience -= hero.level * Hero.XP_MULTIPLIER
            hero.level_up()
            action_log.append(f"主人公はレベルアップして　レベル {hero.level}になった!")
        
        # Display distance from town with + or - sign
        distance_display = f"+{hero.distance_from_town}" if hero.distance_from_town >= 0 else str(hero.distance_from_town)

        # Display equipment status
        weapon_status = f"W+{hero.weapon.modifier}({hero.weapon.duration})" if hero.weapon and not hero.weapon.is_broken() else "W(0)"
        shield_status = f"S+{hero.shield.modifier}({hero.shield.duration})" if hero.shield and not hero.shield.is_broken() else "S(0)"

        log.append((f"{hero.health}/{hero.max_health}", hero.gold, hero.stamina, len(hero.trophies), distance_display, f"{hero.quest_progress}%", weapon_status, shield_status, action_log))

    return log


def main(stdscr):
    # Set up the terminal
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    stdscr.nodelay(0)  # Wait for user input
    stdscr.keypad(True)
    
    max_turns = 90000
    LOG_DISPLAY_COUNT = 5

    stdscr.addstr(0, 0, "Welcome to Text-Based Progress Quest!", curses.color_pair(1))

    stdscr.nodelay(1)  # Don't wait for user input
    stdscr.addstr(2, 0, "The game progresses automatically. Press 'q' to quit at any time.")

    
    
    
    # Initialize game
    hero = Hero()
    town = Town()
    log = []
    
    # Initialize previous health for comparison
    previous_health = hero.health
    previous_stamina = hero.stamina
    
    row = 9  # Starting row for game logs
    while True:
        stdscr.clear()  # Clear the screen
        display_hero_status(stdscr, hero, previous_health, previous_stamina)
        stdscr.addstr(row, 0, "----------------------------------------------")
        row +=1

        # Update previous_health and previous_stamina for the next iteration
        previous_health = hero.health
        previous_stamina = hero.stamina


        # When a magical letter is acquired:
        if hero.monster_defeat_streak == 3:
            hero.monster_defeat_streak = 0
            acquired_letter = random.choice(MAGICAL_LETTERS)
            hero.magical_letters.add(acquired_letter)
            hero.latest_magical_letter = acquired_letter  # Store the latest acquired letter

        # Advance one turn and append the results to log
        hero.current_turn += 1

        turn_actions = game_loop(hero, 1)
        log.append(turn_actions[0])

        # Display the last n logs
        for action_log in reversed(log[-LOG_DISPLAY_COUNT:]):
            for line in action_log[-1]:
                stdscr.addstr(row, 0, line)
                row += 1
            stdscr.addstr(row, 0, "--------------------------------")
            row += 1
        row += 1

        # Check for 'q' key to quit the game
        k = stdscr.getch()
        if k == ord('q'):
            break

        if k == ord('a'):
            time.sleep(5.01)


        if len(log) >= max_turns:
            stdscr.addstr(row, 0, "Game Over. Press 'q' to quit.")
            stdscr.getch()  # Wait for a key press
            break
        
        # Insert a delay so the game progresses at a reasonable pace
        time.sleep(0.01)

        row = 9  # Reset row for next iteration
    
    stdscr.addstr(row, 0, "Thanks for playing!", curses.color_pair(1))
    time.sleep(5.0)

    stdscr.getch()  # Wait for one more key press before exiting


curses.wrapper(main)
