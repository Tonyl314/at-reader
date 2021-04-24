import os
import time


class ATLogger:
    VERSION = 1.2
    DATA_FOLDER_NAME = "Data"

    def __init__(self, logShort=False, filename="ATs.log"):
        self.logShort = logShort
        self.filepath = self.DATA_FOLDER_NAME + "/" + filename
        if not self.doesFileExist():
            self.makeDataFolder()
            self.makeNewFile()
        self.file = open(self.filepath, "a")

    def log(self, actionTest):
        self.writeToFile(actionTest.getLogLine(self.logShort) + "\n")

    def logNewSession(self, usedBbox):
        date = time.strftime("%d. %m. %Y %H:%M")
        pixelWidth = usedBbox[2] - usedBbox[0]
        line = f"---New Session (v{self.VERSION}) ({date}) ({pixelWidth} pixels wide)\n"
        self.writeToFile(line)

    def writeToFile(self, text):
        self.file.write(text)
        self.file.flush()

    def doesFileExist(self):
        return os.path.isfile(self.filepath)

    @classmethod  # other classes can also use the data folder
    def makeDataFolder(cls):
        if not os.path.exists(cls.DATA_FOLDER_NAME):
            os.mkdir(cls.DATA_FOLDER_NAME)

    def makeNewFile(self):
        open(self.filepath, "w").close()
