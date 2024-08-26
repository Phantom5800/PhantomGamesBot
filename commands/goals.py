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
    self.update_progress_file()

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

  def update_progress_file(self):
    with open(f'./commands/resources/channels/{self.channel}/goal_progress.txt', 'w', encoding="utf-8") as txt:
      txt.write(f"Goal: ${self.progress / 100} / ${self.goals[-1]['value'] / 100}")

  def reset_progress(self):
    self.progress = 0
    self.save_goals()

  def reset_goals(self):
    self.progress = 0
    self.goals = []
    self.save_goals()

  def add_goal(self, sub_count:int, desc:str):
    value = sub_count * 300 # treat a tier 1 sub as $3

    exists = False
    # override existing value if already entered
    for goal in self.goals:
      if goal["value"] == value:
        goal["goal"] = desc
        goal["complete"] = False
        exists = True

    # enter new goal
    if not exists:
      self.goals.append({
        "value": value,
        "goal": desc,
        "complete": False
      })
      self.goals.sort(key=lambda x: x["value"])
    self.save_goals()

  def add_prime(self):
    self.progress += 225 # prime value if coming from a US account
    self.save_goals()

  def add_sub(self, tier: int):
    if tier == 1:
      self.progress += 300
    elif tier == 2:
      self.progress += 500
    elif tier == 3:
      self.progress += 1250
    self.save_goals()

  def add_bits(self, bits):
    self.progress += bits
    self.save_goals()

  def get_next_goal(self) -> str:
    for goal in self.goals:
      if goal["value"] > self.progress:
        return f"Next sub / bit goal is \"{goal['goal']}\" at {int(self.progress / 300)}/{int(goal['value'] / 300)} subs or equivalent bits!"
    return "Currently no new sub goals, everything has been hit!"

  def get_all_goals(self) -> str:
    if len(self.goals) > 0:
      goal_list = f"Current Progress = {int(self.progress / 300)}\n"
      for goal in self.goals:
        goal_info = ""
        if goal["complete"]:
          goal_info += "~~"
        goal_info += f"• {int(goal['value'] / 300)} Subs: {goal['goal']}"
        if goal["value"] <= self.progress:
          goal_info += " - COMPLETED"
        if goal["complete"]:
          goal_info += "~~"
        goal_list += f"{goal_info}\n"
      return goal_list
    return "Currently no goals have been created"
