import json
import os
import random
import threading
from copy import deepcopy
from datetime import datetime
from utils.utils import debugPrint

class CustomCommands:
    def __init__(self):
        self.access_lock = threading.RLock()
        self.file_lock = threading.RLock()
        self.command_set = {}

    def load_commands(self):
        self.file_lock.acquire()
        root = './commands/resources/channels/'
        for folder in os.listdir(root):
            channel_folder = os.path.join(root, folder)
            if os.path.isdir(channel_folder):
                commands_file = os.path.join(channel_folder, "custom_commands.json")
                if os.path.isfile(commands_file):
                    with open(commands_file, 'r', encoding="utf-8") as json_file:
                        try:
                            data = json.load(json_file)
                            self.command_set[folder] = deepcopy(data)
                            print(f"Custom Commands [{folder}]: {len(self.command_set[folder])}")
                        except json.decoder.JSONDecodeError:
                            print("[ERROR] Failed to load commands from JSON")
        self.file_lock.release()

    def save_commands(self, channel: str):
        channel = channel.lower()
        self.file_lock.acquire()
        with open(f'./commands/resources/channels/{channel}/custom_commands.json', 'w', encoding="utf-8") as json_file:
            json_str = json.dumps(self.command_set[channel], indent=2)
            json_file.write(json_str)
        self.file_lock.release()

    '''
    Check if a command already exists.
    '''
    def command_exists(self, command: str, channel: str) -> bool:
        channel = channel.lower()
        self.file_lock.acquire()
        exists = channel in self.command_set and command.lower() in self.command_set[channel]
        self.file_lock.release()
        return exists

    '''
    Get the response string for a given command. Automatically replaces variables that can only be determined at this point.
    '''
    def get_command(self, command: str, channel: str) -> str:
        channel = channel.lower()
        command_lower = command.lower()
        com = None
        self.file_lock.acquire()
        if self.command_exists(command_lower, channel):
            com = self.command_set[channel][command_lower]["response"]

            # replace command specific vars
            if "$count" in com:
                if "count" in self.command_set[channel][command_lower]:
                    self.command_set[channel][command_lower]["count"] = self.command_set[channel][command_lower]["count"] + 1
                else:
                    self.command_set[channel][command_lower]["count"] = 1
                self.save_commands(channel) # need to save because data has been updated
                com = com.replace("$count", str(self.command_set[channel][command_lower]["count"]))
        self.file_lock.release()
        return com
    
    '''
    Get the full list of all commands.
    '''
    def get_command_list(self, channel: str) -> list:
        channel = channel.lower()
        command_list = []
        self.file_lock.acquire()
        for key in self.command_set[channel].keys():
            command_list.append(key)
        self.file_lock.release()
        return command_list

    '''
    Add a new command if one does not already exist.
    '''
    def add_command(self, command: str, response: str, cooldown: int, channel: str) -> bool:
        channel = channel.lower()
        command_lower = command.lower()
        self.file_lock.acquire()
        if not self.command_exists(command_lower, channel):
            debugPrint(f"Adding [{command_lower}] -> {response}")
            self.command_set[channel][command_lower] = {
                "response": response,
                "cooldown": cooldown,
                "last_use": 0
            }
            self.file_lock.release()
            self.save_commands(channel)
            return True
        self.file_lock.release()
        return False
    
    '''
    Set the cooldown for a specific command.
    '''
    def set_cooldown(self, command: str, cooldown: int, channel: str) -> bool:
        channel = channel.lower()
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower, channel):
            self.command_set[channel][command_lower]["cooldown"] = cooldown
            self.file_lock.release()
            self.save_commands(channel)
            return True
        self.file_lock.release()
        return False

    '''
    Set a random response chance in the range [1,100]
    '''
    def set_rng_response(self, command: str, rng: int, channel: str) -> bool:
        channel = channel.lower()
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower, channel):
            self.command_set[channel][command_lower]["rng"] = rng
            self.file_lock.release()
            self.save_commands(channel)
            return True
        self.file_lock.release()
        return False

    '''
    Edit the response for a given command.
    '''
    def edit_command(self, command: str, response: str, cooldown: int, channel: str) -> bool:
        channel = channel.lower()
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower, channel):
            debugPrint(f"Editing [{command_lower}] -> {response}")
            self.command_set[channel][command_lower]["response"] = response
            self.command_set[channel][command_lower]["cooldown"] = cooldown
            self.command_set[channel][command_lower]["last_use"] = 0
            self.file_lock.release()
            self.save_commands(channel)
            return True
        self.file_lock.release()
        return False

    '''
    Delete an existing command.
    '''
    def remove_command(self, command: str, channel: str) -> bool:
        channel = channel.lower()
        command_lower = command.lower()
        self.file_lock.acquire()
        if self.command_exists(command_lower, channel):
            debugPrint(f"Deleting [{command_lower}]")
            del self.command_set[channel][command_lower]
            self.file_lock.release()
            self.save_commands(channel)
            return True
        self.file_lock.release()
        return False

    '''
    Return a response based on if the input string provided matches a command that is not on cooldown.
    '''
    def parse_custom_command(self, message: str, channel: str) -> str:
        channel = channel.lower()
        lower_message = message.lower()
        if self.command_exists(lower_message, channel):
            response = None
            self.file_lock.acquire()
            # check if command has been used, and if it has, if it is past the cooldown period
            current_seconds = (datetime.now() - datetime(1970,1,1)).total_seconds()
            unused_command = self.command_set[channel][lower_message]["last_use"] == 0
            cooldown_passed = current_seconds - self.command_set[channel][lower_message]["last_use"] > self.command_set[channel][lower_message]["cooldown"]
            try:
                response_chance = self.command_set[channel][lower_message]["rng"]
            except:
                response_chance = 100
            can_respond = random.randint(0, 100) < response_chance
            if (unused_command or cooldown_passed) and can_respond:
                self.command_set[channel][lower_message]["last_use"] = current_seconds
                response = self.get_command(lower_message, channel)
            self.file_lock.release()
            return response
        return None
