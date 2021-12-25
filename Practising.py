import os
from ATReading import *
from ATLogging import ATLogger
from Preferences import PreferencesManager


class Practise:
    def __init__(self):
        self.bbox, self.log_short, self.log_filename = None, None, None
        self.load_preferences()
        self.reader = ATReader(self.bbox)
        self.logger = ATLogger(self.log_short, self.log_filename)
        self.all_time = AllTimeStats()
        self.session = Session()
        self.info_text = InfoTextManager(self)
        self.info_text.update()

    def load_preferences(self):
        prefs = PreferencesManager.get_instance()
        self.load_bbox_from_prefs(prefs)
        self.load_batch_from_prefs(prefs)
        self.load_log_from_prefs(prefs)

    def load_bbox_from_prefs(self, prefs):
        x_left = prefs.get_value_by_key_name("xLeft")
        x_right = prefs.get_value_by_key_name("xRight")
        y_top = prefs.get_value_by_key_name("yTop")
        self.bbox = ATReader.construct_bbox(x_left, x_right, y_top)

    def load_batch_from_prefs(self, prefs):
        Session.BATCH_SIZE = prefs.get_value_by_key_name("batchSize")
        InfoTextManager.BATCHES_TO_SHOW = prefs.get_value_by_key_name("batchesToShow")

    def load_log_from_prefs(self, prefs):
        log_short_yn = prefs.get_value_by_key_name("logShort")
        if log_short_yn == "y":
            self.log_short = True
        elif log_short_yn == "n":
            self.log_short = False
        else:
            print("---Preference error: unknown answer for y/n.")
            self.log_short = True  # default
        self.log_filename = prefs.get_value_by_key_name("logFilename")

    def start(self):
        print("Session started.")
        self.logger.log_new_session(self.reader.bbox)
        while True:
            action_test = self.reader.read_at()
            self.process_action_test(action_test)
            time.sleep(.1)  # a tiny bit for the result to settle down

    def process_action_test(self, action_test):
        self.logger.log_at(action_test)
        self.session.add_action_test(action_test)
        self.all_time.add_action_test(action_test, self.session.chain)
        self.info_text.update()


class AllTimeStats:
    DATA_FOLDER_NAME = ATLogger.DATA_FOLDER_NAME

    def __init__(self, filename="allTimeData.txt"):
        self.filepath = self.DATA_FOLDER_NAME + "/" + filename
        if not self.does_file_exist():
            ATLogger.make_data_folder()
            self.make_new_file()
        self.greens, self.total_ats, self.best_chain = self.read_saved_data()

    def does_file_exist(self):
        return os.path.isfile(self.filepath)

    def make_new_file(self):
        default_text = "0;0;0"
        self.override_file(default_text)

    def read_saved_data(self):
        line = self.read_file()
        return map(int, line.split(";"))

    def add_action_test(self, action_test, chain=0):
        self.total_ats += 1
        if action_test.result == ATResult.GREEN:
            self.greens += 1
        if chain > self.best_chain:
            self.best_chain = chain
        self.save()

    def save(self):
        data = map(str, [self.greens, self.total_ats, self.best_chain])
        to_write = ";".join(list(data))
        self.override_file(to_write)

    def read_file(self):
        file = open(self.filepath, "r")
        text = file.read()
        file.close()
        return text

    def override_file(self, to_write):
        try:
            file = open(self.filepath, "w")
        except PermissionError:
            print(f"---Permission error to {self.filepath}!")
            return
        file.write(to_write)
        file.close()


class Session:
    BATCH_SIZE = 10
    # indexes in a batch ([green, total])
    BATCH_GREENS = 0
    BATCH_TOTAL = 1

    def __init__(self):
        self.total_ats = 0
        self.greens = 0
        self.chain = 0
        self.best_chain = 0
        self.batches = []

    def add_action_test(self, action_test):
        if self.total_ats % self.BATCH_SIZE == 0:
            self.add_new_batch()
        self.increment_total_ats()
        if action_test.result == ATResult.GREEN:
            self.increment_greens()
        else:
            self.chain = 0  # non-green ruins chain

    def add_new_batch(self):
        self.batches.append([0, 0])

    def increment_total_ats(self):
        self.total_ats += 1
        self.batches[-1][self.BATCH_TOTAL] += 1

    def increment_greens(self):
        self.greens += 1
        self.batches[-1][self.BATCH_GREENS] += 1
        self.chain += 1
        self.best_chain = max(self.chain, self.best_chain)


class InfoTextManager:
    INFO_FILENAME = "sessionInfo.txt"
    BATCHES_TO_SHOW = 5

    def __init__(self, practise_object):
        self.practise = practise_object

    def update(self):
        sections = [self.get_all_time_section(), self.get_session_section(), self.get_batches_section()]
        to_write = "\n\n".join(sections)
        self.override_info_file(to_write)

    def get_all_time_section(self):
        greens = self.practise.all_time.greens
        ATs = self.practise.all_time.total_ats
        percentage = in_percent(greens, ATs, 1)
        best_chain = self.practise.all_time.best_chain
        section = f"""---ALL TIME---
Action tests: {ATs}
Greens: {greens} ({percentage}%)
Best streak: {best_chain}"""
        return section

    def get_session_section(self):
        greens = self.practise.session.greens
        ATs = self.practise.session.total_ats
        percentage = in_percent(greens, ATs, 1)
        current_chain = self.practise.session.chain
        best_chain = self.practise.session.best_chain
        section = f"""---SESSION---
Action tests: {ATs}
Greens: {greens} ({percentage}%)
Best streak: {best_chain}
Current streak: {current_chain}"""
        return section

    def get_batches_section(self):
        batch_amount = len(self.practise.session.batches)
        start_batch_index = max(0, batch_amount - self.BATCHES_TO_SHOW)
        batch_texts = ["---BATCHES---"]
        for batch_index in range(start_batch_index, batch_amount):
            text = self.get_batch_text_with_index(batch_index)
            batch_texts.append(text)
        return "\n".join(batch_texts)

    def get_batch_text_with_index(self, index):
        batch = self.practise.session.batches[index]
        greens = batch[Session.BATCH_GREENS]
        total_ats = batch[Session.BATCH_TOTAL]
        percentage = in_percent(greens, total_ats, 0)
        return f"{index+1}) {greens}/{total_ats} ({percentage}%)"

    def override_info_file(self, to_write):
        try:
            with open(self.INFO_FILENAME, "w") as file:
                file.write(to_write)
        except PermissionError:
            print(f"---Permission error to {self.INFO_FILENAME}!")


def in_percent(portion, total, decimal_places=1):
    if total == 0:
        return "None"
    percentage = (portion / total) * 100
    if decimal_places == 0:
        return int(round(percentage, 0))  # no decimal point
    return round(percentage, decimal_places)


if __name__ == "__main__":
    practise = Practise()
    practise.start()
