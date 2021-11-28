import json
from copy import deepcopy
from datetime import datetime
from utils.utils import debugPrint

class CustomCommands:
    async def load_commands(self):
        with open('./commands/resources/custom_commands.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.command_set = deepcopy(data)
                print(f"Custom Commands: {self.command_set}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load commands from JSON")
                return

    async def save_commands(self):
        with open('./commands/resources/custom_commands.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.command_set)
            json_file.write(json_str)

    def command_exists(self, command: str) -> bool:
        return command.lower() in self.command_set

    def get_command(self, command: str) -> str:
        command_lower = command.lower()
        if self.command_exists(command_lower):
            return self.command_set[command_lower]["response"]
        return None
    
    def get_command_list(self) -> list:
        command_list = []
        for key in self.command_set.keys():
            command_list.append(key)
        return command_list

    async def add_command(self, command: str, response: str, cooldown: int) -> bool:
        command_lower = command.lower()
        if command_lower not in self.command_set:
            debugPrint(f"Adding [{command_lower}] -> {response}")
            self.command_set[command_lower] = {
                "response": response,
                "cooldown": cooldown,
                "last_use": 0
            }
            await self.save_commands()
            return True
        return False
    
    async def set_cooldown(self, command: str, cooldown: int) -> bool:
        command_lower = command.lower()
        if command_lower in self.command_set:
            self.command_set[command_lower]["cooldown"] = cooldown
            await self.save_commands()
            return True
        return False

    async def edit_command(self, command: str, response: str, cooldown: int) -> bool:
        command_lower = command.lower()
        if command_lower in self.command_set:
            debugPrint(f"Editing [{command_lower}] -> {response}")
            self.command_set[command_lower]["response"] = response
            self.command_set[command_lower]["cooldown"] = cooldown
            self.command_set[command_lower]["last_use"] = 0
            await self.save_commands()
            return True
        return False

    async def remove_command(self, command: str) -> bool:
        command_lower = command.lower()
        if command_lower in self.command_set:
            debugPrint(f"Deleting [{command_lower}]")
            del self.command_set[command_lower]
            await self.save_commands()
            return True
        return False

    async def parse_custom_command(self, message: str) -> str:
        lower_message = message.lower()
        if lower_message in self.command_set:
            # check if command has been used, and if it has, if it is past the cooldown period
            if self.command_set[lower_message]["last_use"] == 0 or (datetime.now() - self.command_set[lower_message]["last_use"]).total_seconds() > self.command_set[lower_message]["cooldown"]:
                self.command_set[lower_message]["last_use"] = datetime.now()
                return self.command_set[lower_message]["response"]
            return None
        return None
