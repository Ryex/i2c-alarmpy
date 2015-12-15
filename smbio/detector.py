from .smb import Peripheral


class Switch(Peripheral):

    DIRECTION = -1
    DATAMAP = {
        "pin": "pin"}

    def init(self):
        if "pin" in self.data:
            self.pin = int(self.data["pin"])
        else:
            self.pin = 0
        self._state = 0
        self.io.set_mode_pin(self.pin, self.io.READ)

    def read(self):
        self.init()
        self._state = self.io.read_in_pin(self.pin)
        return self._state

    def update(self):
        state = self.read()
        return {"switch": state}
