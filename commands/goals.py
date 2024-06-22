import json

class Goals:
  def __init__(self, channel:str):
    self.channel = channel
    self.progress = 0
    self.goals = []

  def save_goals(self):
    json_str = json.dumps(
        self,
        default=lambda o: o.__dict__,
        indent=2
      )
    with open(f'./commands/resources/channels/{self.channel}/goals.json', 'w', encoding="utf-8") as json_file:
      json_file.write(json_str)

  def load_goals(self):
    try:
      with open(f'./commands/resources/channels/{self.channel}/goals.json', 'r', encoding="utf-8") as json_file:
        try:
          data = json.load(json_file)
          self.progress = data["progress"]
          self.goals = data["goals"]
        except json.decoder.JSONDecodeError:
          print("[ERROR] Failed to load goals from JSON")
    except:
      print(f"Goals do not exist for {self.channel}")

  def add_goal(self, sub_count:int, desc:str):
    self.goals.append({
      "value": sub_count * 300, # treat a tier 1 sub as $3
      "goal": desc
    })
    self.goals.sort(key=lambda x: x["value"])
    self.save_goals()

  def add_tier1(self):
    self.progress += 300
    self.save_goals()

  def add_tier2(self):
    self.progress += 500
    self.save_goals()

  def add_tier3(self):
    self.progress += 1250
    self.save_goals()

  def add_bits(self, bits):
    self.progress += bits
    self.save_goals()

  def get_next_goal(self) -> str:
    for goal in self.goals:
      if goal["value"] < self.progress:
        return f"Next sub / bit goal is \"{goal['goal']}\" at {int(goal['value'] / 300)} subs or equivalent bits!"
    return "Currently no new sub goals, everything has been hit!"

  def get_all_goals(self) -> str:
    if len(self.goals) > 0:
      goal_list = ""
      for goal in self.goals:
        goal_info = f"• {int(goal['value'] / 300)} Subs: {goal['goal']}"
        if goal["value"] <= self.progress:
          goal_info += " - COMPLETED"
        goal_list += f"{goal_info}\n"
      return goal_list
    return "Currently no goals have been created"
