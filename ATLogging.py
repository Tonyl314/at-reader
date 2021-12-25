import os
import time


class ATLogger:
    VERSION = 1.2
    DATA_FOLDER_NAME = "Data"

    def __init__(self, log_short=False, filename="ATs.log"):
        self.log_short = log_short
        self.filepath = self.DATA_FOLDER_NAME + "/" + filename
        if not self.does_file_exist():
            self.make_data_folder()
            self.make_new_file()
        self.file = open(self.filepath, "a")

    def log_at(self, action_test):
        self.write_to_file(action_test.get_log_line(self.log_short) + "\n")

    def log_new_session(self, used_bbox):
        date = time.strftime("%d. %m. %Y %H:%M")
        pixel_width = used_bbox[2] - used_bbox[0]
        line = f"---New Session (v{self.VERSION}) ({date}) ({pixel_width} pixels wide)\n"
        self.write_to_file(line)

    def write_to_file(self, text):
        self.file.write(text)
        self.file.flush()

    def does_file_exist(self):
        return os.path.isfile(self.filepath)

    @classmethod  # other classes can also use the data folder
    def make_data_folder(cls):
        if not os.path.exists(cls.DATA_FOLDER_NAME):
            os.mkdir(cls.DATA_FOLDER_NAME)

    def make_new_file(self):
        open(self.filepath, "w").close()
