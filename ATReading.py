from mss import mss
import mss.tools as mss_tools
import time

# KNOWN ISSUES:
# - canceled ATs get read as white
# - difficult prints are broken
# - redding very early is broken
# - ATs *right* after each other might not get registered


class ATReader:
    @staticmethod
    def constructBbox(xLeft, xRight, yTop):
        return (xLeft, yTop - 2, xRight + 1, yTop + 1)

    def __init__(self, bbox):
        self.bbox = bbox
        self.currentAT = None

    def readAT(self):
        self.setupNewAT()
        self.waitToLoadUp()
        self.locateSections()
        self.watchBar()
        self.evaluateResult()
        self.currentAT.print()
        return self.currentAT

    def setupNewAT(self):
        self.currentAT = ActionTest()

    def waitToLoadUp(self):
        attempts = 0
        with mss() as sct:
            while True:
                img = sct.grab(self.bbox)
                if self.containsAT(img):
                    time.sleep(.0275)  # a tiny bit for the green to settle
                    return attempts
                attempts += 1

    def containsAT(self, img):
        xRight = img.size.width - 1
        # check the pixels NEXT to the border (border can be darker)
        isLeftRed = Colour.isColourRed(img.pixel(1, 2))
        isRightRed = Colour.isColourRed(img.pixel(xRight - 1, 2))
        isTopRowDark = self.isTopRowDark(img)
        return (isLeftRed or isRightRed) and isTopRowDark

    def locateSections(self):  # would use refactoring
        img = mss().grab(self.bbox)
        greenPos = None
        whitePos = [None, None]  # start and end
        for x in range(img.size.width):
            section = self.determineSectionInColumn(img, x)
            if section == ATResult.GREEN:
                if whitePos[1] is not None:
                    self.informUserAboutProblem("whiteEndsBeforeGreen", img)
                if greenPos is None:
                    greenPos = x
            elif section == ATResult.WHITE:
                if whitePos[1] is not None:
                    self.informUserAboutProblem("whiteStartsAfterEnding", img)
                if whitePos[0] is None:
                    whitePos[0] = x
            elif section == ATResult.RED:
                # is it the end of the white section?
                if whitePos[0] is not None and whitePos[1] is None:
                    whitePos[1] = x - 1
        # cover the edge case where the end of an AT is white
        if whitePos[1] is None and whitePos[0] is not None:
            whitePos[1] = img.size.width - 1
        self.currentAT.greenPosition = greenPos
        self.currentAT.whitePositions = whitePos
        self.informUserIfLocatingFailed(img)

    def determineSectionInColumn(self, img, x):
        rgbMiddle = img.pixel(x, 1)
        if Colour.isQuiteGreen(rgbMiddle) and Colour.hasPureGreen(rgbMiddle):
            return self.checkFurtherForGreen(img, x)
        rgbBottom = img.pixel(x, 2)
        if Colour.isMostlyRed(rgbBottom):
            return ATResult.RED
        return self.checkFurtherForWhite(img, x)

    def checkFurtherForGreen(self, img, x):
        # green section! but check just in case
        rgbTop = img.pixel(x, 0)
        if not Colour.isQuiteDark(rgbTop):
            # false alarm?
            self.informUserAboutProblem("lightPixelAboveGreen", img)
            return ATResult.WHITE
        return ATResult.GREEN

    def checkFurtherForWhite(self, img, x):
        # looks white – but it could be the bar
        rgbTop = img.pixel(x, 0)
        if Colour.isQuiteDark(rgbTop):
            return ATResult.WHITE
        return ATResult.RED

    def informUserIfLocatingFailed(self, img):
        if self.currentAT.greenPosition is None:
            self.informUserAboutProblem("greenNotFound", img)
        if None in self.currentAT.whitePositions:
            self.informUserAboutProblem("whiteNotFound", img)

    def informUserAboutProblem(self, imageName, img):
        print("---Problem: " + imageName + ".png")
        mss_tools.to_png(img.rgb, img.size, output=(imageName + ".png"))

    def watchBar(self):
        lastX = 0
        stillFrames = 0
        barPositions = []
        startTime = time.time()
        with mss() as sct:
            while True:
                img = sct.grab(self.bbox)
                newX = self.findBar(img, lastX)
                if newX is False:
                    # couldn't find – done!
                    break
                if newX == lastX:
                    # same frame
                    stillFrames += 1
                    continue
                lastX = newX
                barPositions.append(lastX)
        timeTook = time.time() - startTime
        captures = len(barPositions) + stillFrames + 1  # +1 for when not found
        self.currentAT.barPositions = barPositions
        self.currentAT.stillFrames = stillFrames
        self.currentAT.capturesPerSecond = round(captures / timeTook, 2)

    def findBar(self, img, minimumX):
        width = img.size.width
        for x in range(minimumX, width):
            rgb = img.pixel(x, 0)
            if Colour.hasPureGreen(rgb):
                return x
        return False

    def evaluateResult(self):
        time.sleep(.02)  # wait a tiny bit for the colour to be clear
        img = mss().grab(self.bbox)
        mss_tools.to_png(img.rgb, img.size, output="lastResult.png")

        isRed = self.isResultRed(img)
        isGreen = self.isResultGreen(img)
        self.applyResultWithRedGreen(isRed, isGreen)

    def isTopRowDark(self, img):
        rightX = img.size.width - 1
        isLeftDark = Colour.isDark(img.pixel(0, 0))
        isRightDark = Colour.isDark(img.pixel(rightX, 0))
        return isLeftDark and isRightDark

    def isResultRed(self, img):
        rightX = img.size.width - 1
        isLeftRed = Colour.isVeryRed(img.pixel(0, 2))
        isRightRed = Colour.isVeryRed(img.pixel(rightX, 2))
        return isLeftRed and isRightRed

    def isResultGreen(self, img):
        rightX = img.size.width - 1
        isLeftGreen = Colour.isColourGreen(img.pixel(0, 2))
        isRightGreen = Colour.isColourGreen(img.pixel(rightX, 2))
        return isLeftGreen and isRightGreen

    def applyResultWithRedGreen(self, isRed, isGreen):
        if isRed and isGreen:
            raise Exception("Red and green at the same time?!")
        elif isRed:
            self.currentAT.result = ATResult.RED
        elif isGreen:
            self.currentAT.result = ATResult.GREEN
        else:
            self.currentAT.result = ATResult.WHITE


class ActionTest:
    barPositions = []
    greenPosition = None
    whitePositions = [None, None]  # start, end
    stillFrames = None
    result = None
    capturesPerSecond = None

    def print(self):
        resultName = ATResult.names[self.result]
        if self.result == ATResult.GREEN:
            timing = "ok"
        elif self.barPositions and self.greenPosition:
            lastPos = self.barPositions[-1]
            if lastPos > self.greenPosition:
                timing = "late"
            else:
                timing = "early"
        else:
            timing = "?"
        whiteStart, whiteEnd = self.whitePositions
        print(f"{resultName} ({timing}): {self.greenPosition} {whiteStart}-{whiteEnd} ...{self.barPositions[-4:]}")

    def getLogLine(self, logShort=False):
        resultName = ATResult.getResultName(self.result)
        whiteStart, whiteEnd = self.whitePositions
        barPositions = self.barPositions
        if logShort:
            if self.barPositions:
                barPositions = self.barPositions[-1]
            else:
                barPositions = "?"
        cps = self.capturesPerSecond
        return f"{resultName} {self.greenPosition} {whiteStart}-{whiteEnd} {barPositions} {self.stillFrames} {cps}"


class ATResult:
    WHITE = 0
    GREEN = 1
    RED = 2
    names = ["white", "green", "red"]

    @classmethod
    def getResultName(cls, index):
        return cls.names[index]


class Colour:
    @staticmethod
    def isColourRed(rgb):
        return rgb[0] >= 145 and rgb[1] <= 35 and rgb[2] <= 35

    @staticmethod
    def isVeryRed(rgb):
        return rgb[0] >= 225 and rgb[1] <= 15 and rgb[2] <= 15

    @staticmethod
    def isMostlyRed(rgb):
        return (rgb[0] - rgb[1]) >= 15

    @staticmethod
    def isColourGreen(rgb):
        return rgb[0] < 50 and rgb[1] > 200 and rgb[2] < 50

    @staticmethod
    def isQuiteGreen(rgb):
        return rgb[1] > 200 and (rgb[1] - rgb[0]) > 50

    @staticmethod
    def hasPureGreen(rgb):
        return rgb[1] == 255

    @staticmethod
    def isDark(rgb):
        return max(rgb) < 50

    @staticmethod
    def isQuiteDark(rgb):
        return sum(rgb) < 270
