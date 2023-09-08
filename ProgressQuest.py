import random

# Define the Hero class
class Hero:
    XP_MULTIPLIER = 300  # Define a constant multiplier for XP required for next level


    DEFAULT_STR = 8
    DEFAULT_VIT = 0
    DEFAULT_ENDURANCE = 0
    DEFAULT_LUCK = 24
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
# Running the game loop
if __name__ == "__main__":
    game_actions_with_xp = game_loop(30000)

    for action in game_actions_with_xp[-100:]:
        print(action)

# Note:
#('今のHP/最大HP', Gold, スタミナ, 持ち物の数, 進捗(10を超えると+1%), クエスト進捗(%),
# W武器(耐久値), S防具(耐久値), [ログの中身]
#('38/176', 1, 32, 0, '+2', '44%', 'W(0)', 'S(0)', [])
