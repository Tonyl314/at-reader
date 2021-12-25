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
    def construct_bbox(x_left, x_right, y_top):
        return (x_left, y_top - 2, x_right + 1, y_top + 1)

    def __init__(self, bbox):
        self.bbox = bbox
        self.current_at = None

    def read_at(self):
        self.setup_new_at()
        self.wait_to_load_up()
        self.locate_sections()
        self.watch_bar()
        self.evaluate_result()
        self.current_at.print()
        return self.current_at

    def setup_new_at(self):
        self.current_at = ActionTest()

    def wait_to_load_up(self):
        attempts = 0
        with mss() as sct:
            while True:
                img = sct.grab(self.bbox)
                if self.contains_at(img):
                    time.sleep(.0275)  # a tiny bit for the green to settle
                    return attempts
                attempts += 1

    def contains_at(self, img):
        x_right = img.size.width - 1
        # check the pixels NEXT to the border (border can be darker)
        is_left_red = Colour.is_colour_red(img.pixel(1, 2))
        is_right_red = Colour.is_colour_red(img.pixel(x_right - 1, 2))
        is_top_row_dark = self.is_top_row_dark(img)
        return (is_left_red or is_right_red) and is_top_row_dark

    def locate_sections(self):  # would use refactoring
        img = mss().grab(self.bbox)
        greenPos = None
        white_pos = [None, None]  # start and end
        for x in range(img.size.width):
            section = self.determine_section_in_column(img, x)
            if section == ATResult.GREEN:
                if white_pos[1] is not None:
                    self.inform_user_about_problem("whiteEndsBeforeGreen", img)
                if greenPos is None:
                    greenPos = x
            elif section == ATResult.WHITE:
                if white_pos[1] is not None:
                    self.inform_user_about_problem("whiteStartsAfterEnding", img)
                if white_pos[0] is None:
                    white_pos[0] = x
            elif section == ATResult.RED:
                # is it the end of the white section?
                if white_pos[0] is not None and white_pos[1] is None:
                    white_pos[1] = x - 1
        # cover the edge case where the end of an AT is white
        if white_pos[1] is None and white_pos[0] is not None:
            white_pos[1] = img.size.width - 1
        self.current_at.green_position = greenPos
        self.current_at.white_positions = white_pos
        self.informUserIfLocatingFailed(img)

    def determine_section_in_column(self, img, x):
        rgb_middle = img.pixel(x, 1)
        if Colour.is_quite_green(rgb_middle) and Colour.has_pure_green(rgb_middle):
            return self.check_further_for_green(img, x)
        rgb_bottom = img.pixel(x, 2)
        if Colour.is_mostly_red(rgb_bottom):
            return ATResult.RED
        return self.check_furhter_for_white(img, x)

    def check_further_for_green(self, img, x):
        # green section! but check just in case
        rgb_top = img.pixel(x, 0)
        if not Colour.is_quite_dark(rgb_top):
            # false alarm?
            self.inform_user_about_problem("lightPixelAboveGreen", img)
            return ATResult.WHITE
        return ATResult.GREEN

    def check_furhter_for_white(self, img, x):
        # looks white – but it could be the bar
        rgb_top = img.pixel(x, 0)
        if Colour.is_quite_dark(rgb_top):
            return ATResult.WHITE
        return ATResult.RED

    def informUserIfLocatingFailed(self, img):
        if self.current_at.green_position is None:
            self.inform_user_about_problem("greenNotFound", img)
        if None in self.current_at.white_positions:
            self.inform_user_about_problem("whiteNotFound", img)

    def inform_user_about_problem(self, image_name, img):
        print("---Problem: " + image_name + ".png")
        mss_tools.to_png(img.rgb, img.size, output=(image_name + ".png"))

    def watch_bar(self):
        last_x = 0
        still_frames = 0
        bar_positions = []
        start_time = time.time()
        with mss() as sct:
            while True:
                img = sct.grab(self.bbox)
                new_x = self.find_bar(img, last_x)
                if new_x is False:
                    # couldn't find – done!
                    break
                if new_x == last_x:
                    # same frame
                    still_frames += 1
                    continue
                last_x = new_x
                bar_positions.append(last_x)
        time_took = time.time() - start_time
        captures = len(bar_positions) + still_frames + 1  # +1 for when not found
        self.current_at.bar_positions = bar_positions
        self.current_at.still_frames = still_frames
        self.current_at.captures_per_second = round(captures / time_took, 2)

    def find_bar(self, img, minimum_x):
        width = img.size.width
        for x in range(minimum_x, width):
            rgb = img.pixel(x, 0)
            if Colour.has_pure_green(rgb):
                return x
        return False

    def evaluate_result(self):
        time.sleep(.02)  # wait a tiny bit for the colour to be clear
        img = mss().grab(self.bbox)
        mss_tools.to_png(img.rgb, img.size, output="lastResult.png")

        is_red = self.is_result_red(img)
        is_green = self.is_result_green(img)
        self.apply_result_with_red_green(is_red, is_green)

    def is_top_row_dark(self, img):
        right_x = img.size.width - 1
        is_left_dark = Colour.is_dark(img.pixel(0, 0))
        is_right_dark = Colour.is_dark(img.pixel(right_x, 0))
        return is_left_dark and is_right_dark

    def is_result_red(self, img):
        right_x = img.size.width - 1
        is_left_red = Colour.is_very_red(img.pixel(0, 2))
        is_right_red = Colour.is_very_red(img.pixel(right_x, 2))
        return is_left_red and is_right_red

    def is_result_green(self, img):
        right_x = img.size.width - 1
        is_left_green = Colour.is_colour_green(img.pixel(0, 2))
        is_right_green = Colour.is_colour_green(img.pixel(right_x, 2))
        return is_left_green and is_right_green

    def apply_result_with_red_green(self, is_red, is_green):
        if is_red and is_green:
            raise Exception("Red and green at the same time?!")
        elif is_red:
            self.current_at.result = ATResult.RED
        elif is_green:
            self.current_at.result = ATResult.GREEN
        else:
            self.current_at.result = ATResult.WHITE


class ActionTest:
    bar_positions = []
    green_position = None
    white_positions = [None, None]  # start, end
    still_frames = None
    result = None
    captures_per_second = None

    def print(self):
        result_name = ATResult.names[self.result]
        if self.result == ATResult.GREEN:
            timing = "ok"
        elif self.bar_positions and self.green_position:
            last_pos = self.bar_positions[-1]
            if last_pos > self.green_position:
                timing = "late"
            else:
                timing = "early"
        else:
            timing = "?"
        white_start, white_end = self.white_positions
        print(f"{result_name} ({timing}): {self.green_position} {white_start}-{white_end} ...{self.bar_positions[-4:]}")

    def get_log_line(self, log_short=False):
        result_name = ATResult.get_result_name(self.result)
        white_start, white_end = self.white_positions
        bar_positions = self.bar_positions
        if log_short:
            if self.bar_positions:
                bar_positions = self.bar_positions[-1]
            else:
                bar_positions = "?"
        cps = self.captures_per_second
        return f"{result_name} {self.green_position} {white_start}-{white_end} {bar_positions} {self.still_frames} {cps}"


class ATResult:
    WHITE = 0
    GREEN = 1
    RED = 2
    names = ["white", "green", "red"]

    @classmethod
    def get_result_name(cls, index):
        return cls.names[index]


class Colour:
    @staticmethod
    def is_colour_red(rgb):
        return rgb[0] >= 145 and rgb[1] <= 35 and rgb[2] <= 35

    @staticmethod
    def is_very_red(rgb):
        return rgb[0] >= 225 and rgb[1] <= 15 and rgb[2] <= 15

    @staticmethod
    def is_mostly_red(rgb):
        return (rgb[0] - rgb[1]) >= 15

    @staticmethod
    def is_colour_green(rgb):
        return rgb[0] < 50 and rgb[1] > 200 and rgb[2] < 50

    @staticmethod
    def is_quite_green(rgb):
        return rgb[1] > 200 and (rgb[1] - rgb[0]) > 50

    @staticmethod
    def has_pure_green(rgb):
        return rgb[1] == 255

    @staticmethod
    def is_dark(rgb):
        return max(rgb) < 50

    @staticmethod
    def is_quite_dark(rgb):
        return sum(rgb) < 270
