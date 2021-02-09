import os
from ATLogging import ATLogger

class Preferences:
    DATA_FOLDER_NAME = ATLogger.DATA_FOLDER_NAME
    FILENAME = "prefs.txt"
    DEFAULTS = [("batch size",100),
                ("batches to show",5),
                ("AT top left X",835),
                ("AT top right X",1084),
                ("AT top Y",895),
                ("short logs (y/n)","y"),
                ("log filename","ATs.log")]
    KEY_NAMES = ["batchSize","batchesToShow","xLeft","xRight","yTop","logShort","logFilename"]
    _instance = None # singleton

    def __init__(self):
        self.filepath = self.DATA_FOLDER_NAME + "/" + self.FILENAME
        self.loadValues()

    @classmethod
    def getInstance(thisClass):
        if thisClass._instance is None:
            thisClass._instance = thisClass()
        return thisClass._instance

    def getValueByKeyName(self, keyName):
        if keyName not in self.KEY_NAMES:
            raise Exception("Wrong preference key name: " + keyName)
        index = self.KEY_NAMES.index(keyName)
        return self.chosenValues[index]

    def loadValues(self):
        if not self.doesFileExist():
            ATLogger.makeDataFolder()
            self.makeNewFile()
        lines = self.readFileLines()
        if len(lines) < len(self.DEFAULTS):
            input("-Prefs file uncomplete. Press enter to revert to defaults:")
            self.repairFileAndReload()
            return

        self.repairFileLater = False
        userChosenValues = []
        for index in range(len(self.DEFAULTS)):
            value = self.getValueViaLinesAndIndex(lines, index)
            userChosenValues.append(value)
        self.chosenValues = userChosenValues
        if self.repairFileLater:
            self.offerFileRepair()

    def getValueViaLinesAndIndex(self, lines, index):
        line = lines[index]
        try:
            name, value = line.split(":")
            value = value.strip()
        except ValueError:
            return self.getDefaultAndRepairLater(index, "no separator")
        if name != self.DEFAULTS[index][0]:
            return self.getDefaultAndRepairLater(index, "wrong name")
        return self.handleValueDataType(value, index)

    def getDefaultAndRepairLater(self, index, message):
        self.repairFileLater = True
        lineName = self.DEFAULTS[index][0]
        print("---Prefs file error ({}): {}".format(lineName, message))
        return self.DEFAULTS[index][1]

    def handleValueDataType(self, value, index):
        if type(self.DEFAULTS[index][1]) == int:
            try:
                value = int(value)
            except:
                return self.getDefaultAndRepairLater(index, "expected integer")
        return value

    def offerFileRepair(self):
        answer = input("Prefs file broken, do you want to revert to defaults? (y/n)")
        while answer not in "yn":
            answer = input("Choose y or n:")
        if answer == "y":
            self.repairFileAndReload()

    def repairFileAndReload(self):
        self.makeNewFile()
        print("Preference file repaired.")
        self.loadValues()

    def makeNewFile(self):
        lines = []
        for default in self.DEFAULTS:
            lines.append(default[0] + ": " + str(default[1]))
        self.overrideFile("\n".join(lines))

    def doesFileExist(self):
        return os.path.isfile(self.filepath)

    def overrideFile(self, toWrite):
        file = open(self.filepath, "w")
        file.write(toWrite)
        file.close()

    def readFileLines(self):
        file = open(self.filepath, "r")
        lines = file.readlines()
        file.close()
        return lines
