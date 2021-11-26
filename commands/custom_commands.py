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
        return command in self.command_set

    def get_command(self, command: str) -> str:
        if self.command_exists(command):
            return self.command_set[command]["response"]
        return None

    async def add_command(self, command: str, response: str, cooldown: int) -> bool:
        if command not in self.command_set:
            debugPrint(f"Adding [{command}] -> {response}")
            self.command_set[command] = {
                "response": response,
                "cooldown": cooldown,
                "last_use": 0
            }
            await self.save_commands()
            return True
        return False
    
    async def set_cooldown(self, command: str, cooldown: int) -> bool:
        if command in self.command_set:
            self.command_set[command]["cooldown"] = cooldown
            await self.save_commands()
            return True
        return False

    async def edit_command(self, command: str, response: str, cooldown: int) -> bool:
        if command in self.command_set:
            debugPrint(f"Editing [{command}] -> {response}")
            self.command_set[command]["response"] = response
            self.command_set[command]["cooldown"] = cooldown
            self.command_set[command]["last_use"] = 0
            await self.save_commands()
            return True
        return False

    async def remove_command(self, command: str) -> bool:
        if command in self.command_set:
            debugPrint(f"Deleting [{command}]")
            del self.command_set[command]
            await self.save_commands()
            return True
        return False

    def replace_vars(self, message, ctx) -> str:
        out_str = message

        out_str = out_str.replace("$user", ctx.message.author.mention)

        return out_str

    async def parse_custom_command(self, message: str, ctx) -> str:
        if message in self.command_set:
            # check if command has been used, and if it has, if it is past the cooldown period
            if self.command_set[message]["last_use"] == 0 or (datetime.now() - self.command_set[message]["last_use"]).total_seconds() > self.command_set[message]["cooldown"]:
                self.command_set[message]["last_use"] = datetime.now()
                return self.replace_vars(self.command_set[message]["response"], ctx)
            return None
        return None
