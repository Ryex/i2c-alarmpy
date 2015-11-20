import time
from .smb import Peripheral


class Led(Peripheral):

    DIRECTION = 1
    DATAMAP = {
        "pin": "pin"
    }

    def init(self):
        if "pin" in self.data:
            self.pin = int(self.data["pin"])
        else:
            self.pin = 0
        self._state = 0
        self.io.set_mode_pin(self.pin, self.io.WRITE)

    def on(self):
        self.init()
        self.io.write_out_pin(self.pin, 1)
        self._state = 1

    def off(self):
        self.init()
        self.io.write_out_pin(self.pin, 0)
        self._state = 0

    def update_state(self, state):
        if state:
            self.on()
        else:
            self.off()

    def update(self):
        return {"led": self._state}


class LedBlink(Peripheral):

    DIRECTION = 1
    DATAMAP = {
        "pin": "pin",
        "interval": "int"
    }

    def init(self):
        if "pin" in self.data:
            self.pin = int(self.data["pin"])
        else:
            self.pin = 0
        if "interval" in self.data:
            self.interval = int(self.data["interval"])
        else:
            self.interval = 500
        self.last = time.time()
        self._state = 0
        self._running = False
        self.io.set_mode_pin(self.pin, self.io.WRITE)

    def on(self):
        self.init()
        self.io.write_out_pin(self.pin, 1)
        self._state = 1

    def off(self):
        self.init()
        self.io.write_out_pin(self.pin, 0)
        self._state = 0

    def flip(self):
        if self._state:
            self.off()
        else:
            self.on()

    def update_state(self, state):
        if state:
            self._running = True
        else:
            self._running = False

    def update(self):
        if self._running:
            now = time.time()
            if (now - self.last) * 1000 > self.interval:
                self.flip()
                self.last = now
        else:
            self.off()
        return {"ledblink": self._state}


class Siren(Peripheral):

    DIRECTION = 1
    DATAMAP = {
        "pin": "pin"
    }

    def init(self):
        if "pin" in self.data:
            self.pin = int(self.data["pin"])
        else:
            self.pin = 0
        self._state = 0
        self.io.set_mode_pin(self.pin, self.io.WRITE)

    def on(self):
        self.init()
        self.io.write_out_pin(self.pin, 1)
        self._state = 1

    def off(self):
        self.init()
        self.io.write_out_pin(self.pin, 0)
        self._state = 0

    def get_state(self):
        return self._state

    def update_state(self, state):
        if state:
            self.on()
        else:
            self.off()

    def update(self):
        return {"led": self._state}
