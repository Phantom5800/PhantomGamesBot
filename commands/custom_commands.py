import json
import threading
from copy import deepcopy
from datetime import datetime
from utils.utils import debugPrint

class CustomCommands:
    def __init__(self):
        self.access_lock = threading.RLock()
        self.file_lock = threading.RLock()

    def load_commands(self):
        self.file_lock.acquire()
        with open('./commands/resources/custom_commands.json', 'r', encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                self.command_set = deepcopy(data)
                print(f"Custom Commands: {self.command_set}")
            except json.decoder.JSONDecodeError:
                print("[ERROR] Failed to load commands from JSON")
        self.file_lock.release()

    def save_commands(self):
        self.file_lock.acquire()
        with open('./commands/resources/custom_commands.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.command_set)
            json_file.write(json_str)
        self.file_lock.release()

    def command_exists(self, command: str) -> bool:
        self.file_lock.acquire()
        exists = command.lower() in self.command_set
        self.file_lock.release()
        return exists

    def get_command(self, command: str) -> str:
        command_lower = command.lower()
        com = None
        self.file_lock.acquire()
        if self.command_exists(command_lower):
            com = self.command_set[command_lower]["response"]

            # replace command specific vars
            if "$count" in com:
                if "count" in self.command_set[command_lower]:
                    self.command_set[command_lower]["count"] = self.command_set[command_lower]["count"] + 1
                else:
                    self.command_set[command_lower]["count"] = 1
                self.save_commands() # need to save because data has been updated
                com = com.replace("$count", str(self.command_set[command_lower]["count"]))
        self.file_lock.release()
        return com
    
    def get_command_list(self) -> list:
        command_list = []
        self.file_lock.acquire()
        for key in self.command_set.keys():
            command_list.append(key)
        self.file_lock.release()
        return command_list

    def add_command(self, command: str, response: str, cooldown: int) -> bool:
        command_lower = command.lower()
        self.file_lock.acquire()
        if not self.command_exists(command_lower):
            debugPrint(f"Adding [{command_lower}] -> {response}")
            self.command_set[command_lower] = {
                "response": response,
                "cooldown": cooldown,
                "last_use": 0
            }
            self.file_lock.release()
            self.save_commands()
            return True
        self.file_lock.release()
        return False
    
    def set_cooldown(self, command: str, cooldown: int) -> bool:
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower):
            self.command_set[command_lower]["cooldown"] = cooldown
            self.file_lock.release()
            self.save_commands()
            return True
        self.file_lock.release()
        return False

    def edit_command(self, command: str, response: str, cooldown: int) -> bool:
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower):
            debugPrint(f"Editing [{command_lower}] -> {response}")
            self.command_set[command_lower]["response"] = response
            self.command_set[command_lower]["cooldown"] = cooldown
            self.command_set[command_lower]["last_use"] = 0
            self.file_lock.release()
            self.save_commands()
            return True
        self.file_lock.release()
        return False

    def remove_command(self, command: str) -> bool:
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower):
            debugPrint(f"Deleting [{command_lower}]")
            del self.command_set[command_lower]
            self.file_lock.release()
            self.save_commands()
            return True
        self.file_lock.release()
        return False

    def parse_custom_command(self, message: str) -> str:
        lower_message = message.lower()
        if self.command_exists(lower_message):
            response = None
            self.file_lock.acquire()
            # check if command has been used, and if it has, if it is past the cooldown period
            current_seconds = (datetime.now() - datetime(1970,1,1)).total_seconds()
            if self.command_set[lower_message]["last_use"] == 0 or current_seconds - self.command_set[lower_message]["last_use"] > self.command_set[lower_message]["cooldown"]:
                self.command_set[lower_message]["last_use"] = current_seconds
                response = self.get_command(lower_message)
            self.file_lock.release()
            return response
        return None
