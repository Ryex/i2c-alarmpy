import time
import re
from .smb import Peripheral


class Keypad4x4Matrix(Peripheral):

    DIRECTION = -1
    DATAMAP = {
        "upsidedown": "bool",
        "repeat": "int",
        "timeout": "int"}

    MATRIX = [['1', '2', '3', 'A'],
              ['4', '5', '6', 'B'],
              ['7', '8', '9', 'C'],
              ['*', '0', '#', 'D']]

    KEYCOL = [0b0111, 0b1011, 0b1101, 0b1110]
    DECODE = {
        0b0111: 0,
        0b1011: 1,
        0b1101: 2,
        0b1110: 3}

    CODE_RE = re.compile("^\*(.+?)#$")

    def __check_matrix(self, matrix):
        try:
            for x in range(4):
                for y in range(4):
                    matrix[x][y]
        except IndexError:
            raise ValueError("matrix must be 4x4")

    def init(self):
        if "upsidedown" in self.data:
            self.upsidedown = bool(int(self.data["upsidedown"]))
        else:
            self.upsidedown = False

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

        self.ensure_mode()

        self.last_t = time.time()
        self.last_s = ""
        self.in_string = ""

    def ensure_mode(self):
        self.io.set_mode(0xF0)  # upper 4 bits are inputs
        self.io.set_pullup(0xF0)  # enable upper 4 bits pullups

    def read(self):
        self.ensure_mode()
        for col in range(0, 4):
            time.sleep(0.01)
            self.io.write_out(self.KEYCOL[col])  # write 0 to lowest four bits
            key = self.io.read_in() >> 4
            if key in self.DECODE:
                row = self.DECODE[key]
                if self.upsidedown:
                    return self.matrix[row][col]  # keypad right side up
                else:
                    return self.matrix[3 - col][3 - row]  # keypad upside down
        return ""

    def update_input(self):
        s = self.read()
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
                print("INPUT:", s, self.in_string)
                self.message("buzz")
        else:
            if now - self.last_t > self.timeout:
                self.in_string = ""
                self.last_s = ""
                self.last_t = now

    def get_code(self, code):
        match = self.CODE_RE.match(code)
        if match:
            self.in_string = ""
            return match.group(1)
        return None

    def update(self):
        self.update_input()
        return {"input": self.get_code(self.in_string)}
