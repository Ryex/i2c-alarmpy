import time
import re
from .smb import Peripheral


class Keypad4x4Matrix(Peripheral):

    DIRECTION = -1
    DATAMAP = {
        "order": "bool",
        "repeat": "int",
        "timeout": "int"
    }

    MATRIX = [
        ["1", "2", "3", "A"],
        ["4", "5", "6", "B"],
        ["7", "8", "9", "C"],
        ["*", "0", "#", "D"]
    ]

    ROW_MASKS = {
        0b00010000: 0,
        0b00100000: 1,
        0b01000000: 2,
        0b10000000: 3,
        0b00001000: 0,
        0b00000100: 1,
        0b00000010: 2,
        0b00000001: 3
    }

    BLANK = 0b00000000

    CODE_RE = re.compile("^\*(.+?)#$")

    def __check_matrix(self, matrix):
        try:
            for x in range(4):
                for y in range(4):
                    matrix[x][y]
        except IndexError:
            raise ValueError("matrix must be 4x4")

    def __check_row(self, row):
        if row in self.ROW_MASKS:
            return self.ROW_MASKS[row]
        else:
            return -1

    def init(self):
        if "order" in self.data:
            self.order = int(self.data["order"])
        else:
            self.order = 1

        if "repeat" in self.data:
            self.repeat = int(self.data["repeat"])
        else:
            self.repeat = 100

        if "timeout" in self.data:
            self.timeout = int(self.data["timeout"])
        else:
            self.timeout = 30

        self.matrix = Keypad4x4Matrix.MATRIX
        self.__check_matrix(self.matrix)

        if self.order >= 0:
            self.io.set_mode(0b00001111)
        else:
            self.io.set_mode(0b11110000)
        self.last_t = time.time()
        self.last_s = ""
        self.in_string = ""

    def read(self):
        self.init()
        if self.order >= 0:
            columns = [
                0b00001000,
                0b00000100,
                0b00000010,
                0b00000001
            ]
        else:
            columns = [
                0b00010000,
                0b00100000,
                0b01000000,
                0b10000000
            ]
        rows = self.scan(columns)
        for y in range(4):
            x = self.__check_row(rows[y])
            if x >= 0:
                return self.matrix[x][y]
        return ""

    def scan(self, columns):
        rows = []
        for i in range(4):
            self.io.write_out(columns[i])
            time.sleep(0.001)
            rows.append(self.io.read_in())
            self.io.write_out(self.BLANK)
            time.sleep(0.001)
            time.sleep()
        return rows

    def update_input(self):
        s = self.read()
        if s:
            print("INPUT:", s)
        now = time.time()
        if s:
            flag = False
            if self.last_s:
                if s == self.last_s:
                    if (now - self.last_t) * 1000 > self.repeat:
                        flag = True
                else:
                    flag = True
            else:
                flag = True
            if flag:
                self.last_s = s
                self.last_t = now
                self.in_string += s
                self.message("buzz")
        else:
            if now - self.last_t > self.timeout:
                self.in_string = ""
                self.last_s = ""
                self.last_t = now

    def get_code(self, code):
        match = self.CODE_RE.match(code)
        if match:
            return match.group(0)
        return None

    def update(self):
        self.update_input()
        return {"input": self.get_code(self.in_string)}
