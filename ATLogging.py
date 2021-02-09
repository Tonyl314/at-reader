import os, time

class ATLogger:
    VERSION = 1.0
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
        line = "---New Session (v{}) ({}) ({} pixels wide)\n"
        line = line.format(self.VERSION, date, pixelWidth)
        self.writeToFile(line)

    def writeToFile(self, text):
        self.file.write(line)
        self.file.flush()

    def doesFileExist(self):
        return os.path.isfile(self.filepath)

    @classmethod # other classes can also use the data folder
    def makeDataFolder(thisClass):
        if os.path.exists(thisClass.DATA_FOLDER_NAME): return
        os.mkdir(thisClass.DATA_FOLDER_NAME)

    def makeNewFile(self):
        open(self.filepath, "w").close()
