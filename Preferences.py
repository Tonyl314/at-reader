import os
from ATLogging import ATLogger


class PreferencesManager:
    DATA_FOLDER_NAME = ATLogger.DATA_FOLDER_NAME
    FILENAME = "prefs.txt"
    DEFAULTS = [("batch size", 100),  # not dict because order matters
                ("batches to show", 5),
                ("AT top left X", 835),
                ("AT top right X", 1084),
                ("AT top Y", 895),
                ("short logs (y/n)", "y"),
                ("log filename", "ATs.log")]
    KEY_NAMES = ["batchSize", "batchesToShow", "xLeft", "xRight", "yTop", "logShort", "logFilename"]
    _instance = None  # singleton

    def __init__(self):
        self.filepath = self.DATA_FOLDER_NAME + "/" + self.FILENAME
        self.repair_file_later = False
        self.chosen_values = None
        self.load_values()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_value_by_key_name(self, key_name):
        if key_name not in self.KEY_NAMES:
            raise Exception("Wrong preference key name: " + key_name)
        index = self.KEY_NAMES.index(key_name)
        return self.chosen_values[index]

    def load_values(self):
        if not self.does_file_exist():
            ATLogger.make_data_folder()
            self.make_new_file()
        lines = self.read_file_lines()
        if len(lines) < len(self.DEFAULTS):
            input("-Prefs file incomplete. Press enter to revert to defaults:")
            self.repair_file_and_reload()
            return

        self.repair_file_later = False
        user_chosen_values = []
        for index in range(len(self.DEFAULTS)):
            value = self.get_value_via_lines_and_index(lines, index)
            user_chosen_values.append(value)
        self.chosen_values = user_chosen_values

        if self.repair_file_later:
            self.offer_file_repair()

    def get_value_via_lines_and_index(self, lines, index):
        line = lines[index]
        try:
            name, value = line.split(":")
            value = value.strip()
        except ValueError:
            return self.get_default_and_repair_later(index, "no separator")
        if name != self.DEFAULTS[index][0]:
            return self.get_default_and_repair_later(index, "wrong name")
        return self.handle_value_data_type(value, index)

    def get_default_and_repair_later(self, index, message):
        self.repair_file_later = True
        line_name = self.DEFAULTS[index][0]
        print(f"---Prefs file error ({line_name}): {message}")
        return self.DEFAULTS[index][1]

    def handle_value_data_type(self, value, index):
        if type(self.DEFAULTS[index][1]) == int:
            try:
                value = int(value)
            except ValueError:
                return self.get_default_and_repair_later(index, "expected integer")
        return value

    def offer_file_repair(self):
        prompt = "Prefs file broken, do you want to revert to defaults? (y/n)"
        answer = input(prompt).strip().lower()
        while answer not in "yn":
            answer = input("Choose y or n:")
        if answer == "y":
            self.repair_file_and_reload()

    def repair_file_and_reload(self):
        self.make_new_file()
        print("Preference file repaired.")
        self.load_values()

    def make_new_file(self):
        lines = []
        for default in self.DEFAULTS:
            lines.append(default[0] + ": " + str(default[1]))
        self.override_file("\n".join(lines))

    def does_file_exist(self):
        return os.path.isfile(self.filepath)

    def override_file(self, to_write):
        with open(self.filepath, "w") as file:
            file.write(to_write)

    def read_file_lines(self):
        with open(self.filepath, "r") as file:
            lines = file.readlines()
        return lines
