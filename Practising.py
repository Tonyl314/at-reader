import os
from ATReading import *
from ATLogging import ATLogger
from Preferences import PreferencesManager


class Practise:
    def __init__(self):
        self.bbox, self.logShort, self.logFilename = None, None, None
        self.loadPreferences()
        self.reader = ATReader(self.bbox)
        self.logger = ATLogger(self.logShort, self.logFilename)
        self.allTime = AllTimeStats()
        self.session = Session()
        self.infoText = InfoTextManager(self)
        self.infoText.update()

    def loadPreferences(self):
        prefs = PreferencesManager.getInstance()
        self.loadBboxFromPrefs(prefs)
        self.loadBatchFromPrefs(prefs)
        self.loadLogFromPrefs(prefs)

    def loadBboxFromPrefs(self, prefs):
        xLeft = prefs.getValueByKeyName("xLeft")
        xRight = prefs.getValueByKeyName("xRight")
        yTop = prefs.getValueByKeyName("yTop")
        self.bbox = ATReader.constructBbox(xLeft, xRight, yTop)

    def loadBatchFromPrefs(self, prefs):
        Session.BATCH_SIZE = prefs.getValueByKeyName("batchSize")
        InfoTextManager.BATCHES_TO_SHOW = prefs.getValueByKeyName("batchesToShow")

    def loadLogFromPrefs(self, prefs):
        logShortYN = prefs.getValueByKeyName("logShort")
        if logShortYN == "y":
            self.logShort = True
        elif logShortYN == "n":
            self.logShort = False
        else:
            print("---Preference error: unknown answer for y/n.")
            self.logShort = True  # default
        self.logFilename = prefs.getValueByKeyName("logFilename")

    def start(self):
        print("Session started.")
        self.logger.logNewSession(self.reader.bbox)
        while True:
            actionTest = self.reader.readAT()
            self.processActionTest(actionTest)
            time.sleep(.1)  # a tiny bit for the result to settle down

    def processActionTest(self, actionTest):
        self.logger.log(actionTest)
        self.session.addActionTest(actionTest)
        self.allTime.addActionTest(actionTest, self.session.chain)
        self.infoText.update()


class AllTimeStats:
    DATA_FOLDER_NAME = ATLogger.DATA_FOLDER_NAME

    def __init__(self, filename="allTimeData.txt"):
        self.filepath = self.DATA_FOLDER_NAME + "/" + filename
        if not self.doesFileExist():
            ATLogger.makeDataFolder()
            self.makeNewFile()
        self.greens, self.totalATs, self.bestChain = self.readSavedData()

    def doesFileExist(self):
        return os.path.isfile(self.filepath)

    def makeNewFile(self):
        defaultText = "0;0;0"
        self.overrideFile(defaultText)

    def readSavedData(self):
        line = self.readFile()
        return map(int, line.split(";"))

    def addActionTest(self, actionTest, chain=0):
        self.totalATs += 1
        if actionTest.result == ATResult.GREEN:
            self.greens += 1
        if chain > self.bestChain:
            self.bestChain = chain
        self.save()

    def save(self):
        data = map(str, [self.greens, self.totalATs, self.bestChain])
        toWrite = ";".join(list(data))
        self.overrideFile(toWrite)

    def readFile(self):
        file = open(self.filepath, "r")
        text = file.read()
        file.close()
        return text

    def overrideFile(self, toWrite):
        try:
            file = open(self.filepath, "w")
        except PermissionError:
            print(f"---Permission error to {self.filepath}!")
            return
        file.write(toWrite)
        file.close()


class Session:
    BATCH_SIZE = 10
    # indexes in a batch ([green, total])
    BATCH_GREENS = 0
    BATCH_TOTAL = 1

    def __init__(self):
        self.totalATs = 0
        self.greens = 0
        self.chain = 0
        self.bestChain = 0
        self.batches = []

    def addActionTest(self, actionTest):
        if self.totalATs % self.BATCH_SIZE == 0:
            self.addNewBatch()
        self.incrementTotalATs()
        if actionTest.result == ATResult.GREEN:
            self.incrementGreens()
        else:
            self.chain = 0  # non-green ruins chain

    def addNewBatch(self):
        self.batches.append([0, 0])

    def incrementTotalATs(self):
        self.totalATs += 1
        self.batches[-1][self.BATCH_TOTAL] += 1

    def incrementGreens(self):
        self.greens += 1
        self.batches[-1][self.BATCH_GREENS] += 1
        self.chain += 1
        self.bestChain = max(self.chain, self.bestChain)


class InfoTextManager:
    INFO_FILENAME = "sessionInfo.txt"
    BATCHES_TO_SHOW = 5

    def __init__(self, practiseObject):
        self.practise = practiseObject

    def update(self):
        sections = [self.getAllTimeSection(), self.getSessionSection(), self.getBatchesSection()]
        toWrite = "\n\n".join(sections)
        self.overrideInfoFile(toWrite)

    def getAllTimeSection(self):
        greens = self.practise.allTime.greens
        ATs = self.practise.allTime.totalATs
        percentage = inPercent(greens, ATs, 1)
        bestChain = self.practise.allTime.bestChain
        section = f"""---ALL TIME---
Action tests: {ATs}
Greens: {greens} ({percentage}%)
Best streak: {bestChain}"""
        return section

    def getSessionSection(self):
        greens = self.practise.session.greens
        ATs = self.practise.session.totalATs
        percentage = inPercent(greens, ATs, 1)
        currentChain = self.practise.session.chain
        bestChain = self.practise.session.bestChain
        section = f"""---SESSION---
Action tests: {ATs}
Greens: {greens} ({percentage}%)
Best streak: {bestChain}
Current streak: {currentChain}"""
        return section

    def getBatchesSection(self):
        batchAmount = len(self.practise.session.batches)
        startBatchIndex = max(0, batchAmount - self.BATCHES_TO_SHOW)
        batchTexts = ["---BATCHES---"]
        for batchIndex in range(startBatchIndex, batchAmount):
            text = self.getBatchTextWithIndex(batchIndex)
            batchTexts.append(text)
        return "\n".join(batchTexts)

    def getBatchTextWithIndex(self, index):
        batch = self.practise.session.batches[index]
        greens = batch[Session.BATCH_GREENS]
        totalATs = batch[Session.BATCH_TOTAL]
        percentage = inPercent(greens, totalATs, 0)
        return f"{index+1}) {greens}/{totalATs} ({percentage}%)"

    def overrideInfoFile(self, toWrite):
        try:
            with open(self.INFO_FILENAME, "w") as file:
                file.write(toWrite)
        except PermissionError:
            print(f"---Permission error to {self.INFO_FILENAME}!")


def inPercent(portion, total, decimalPlaces=1):
    if total == 0:
        return "None"
    percentage = (portion / total) * 100
    if decimalPlaces == 0:
        return int(round(percentage, 0))  # no decimal point
    return round(percentage, decimalPlaces)


if __name__ == "__main__":
    practise = Practise()
    practise.start()
