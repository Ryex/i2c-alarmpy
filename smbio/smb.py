import smbus


def Bus(bus):
    return smbus.SMBus(bus)


class Peripheral:
    '''Create a SMB Peripheral interface'''

    DIRECTION = 0

    def __init__(self, pid, io, data=None):
        if not isinstance(io, IO):
            raise ValueError("io must be an IO instace")
        self.io = io
        self.pid = pid
        self.data = data
        self._state = 0
        self.init()

    def init(self):
        pass

    def get_state(self):
        return self._state


class Data:
    '''
    Create a data interface
    writing to address com
    with an number of bits offset and number of bits in size
    '''

    def __init__(self, bus, addr, com, offset=0, length=8):
        if not isinstance(bus, smbus.SMBus):
            raise ValueError("bus must be a SMBus instance")
        self.bus = bus
        self.addr = addr
        self.com = com
        self.offset = offset
        self.length = length

    def write(self, value):
        if not isinstance(value, int) or value.bit_length() > self.length:
            raise ValueError(
                "can only write ints with a bit length smaller than %s"
                % (self.length,)
            )


class IO():
    '''Define an interface to an 8 bit IO'''
    READ = 1
    WRITE = 0
    PINMIN = 0
    PINMAX = 7

    def __init__(self, bus, addr, iodir, gpio, olat):
        if not isinstance(bus, smbus.SMBus):
            raise ValueError("bus must be an SMBus instance")
        self.bus = bus
        self.addr = addr
        self.iodir = Data(bus, self.addr, iodir)
        self.olat = Data(bus, self.addr, olat)
        self.gpio = Data(bus, self.addr, gpio)

    def __check_value(self, value, pin=False):
        if not isinstance(value, int):
            raise ValueError("value must be an int")
        if value < 0x00 or value > 0xFF:
            raise ValueError("value must be between 0x00 and 0xff")
        if pin:
            if value.bit_length() > 1:
                raise ValueError("when setting a pin value must by 1 or 0")

    def __check_mode(self, mode):
        if not (mode == IO.READ or mode == IO.WRITE):
            raise ValueError("mode must be IO.READ or IO.WRITE")

    def __check_pin(self, pin):
        if pin > IO.PINMAX or pin < IO.PINMIN:
            raise ValueError(
                "pin must be between %s and %s"
                % (IO.PINMAX, IO.PINMIN)
            )

    def write_out(self, value):
        self.__check_value(value)
        self.olat.write(value)

    def write_out_pin(self, pin, value):
        self.__check_pin(pin)
        self.__check_value(value, True)
        cur = self.read_out()
        new = cur ^ ((-value ^ cur) & (1 << pin))
        self.write(new)

    def read_out(self):
        return self.olat.read()

    def read_out_pin(self, pin):
        self.__check_pin(pin)
        cur = self.read_out()
        return (cur >> pin) & 1

    def read_in(self):
        return self.gpio.read()

    def read_in_pin(self, pin):
        self.__check_pin(pin)
        cur = self.read_in()
        return (cur >> pin) & 1

    def set_mode(self, mode):
        self.__check_mode(mode)
        self.iodir.write(mode)

    def set_mode_pin(self, pin, mode):
        self.__check_pin(pin)
        self.__check_mode(mode)
        cur = self.get_mode()
        new = cur ^ ((-mode ^ cur) & (1 << pin))
        self.set_mode(new)

    def get_mode(self):
        return self.iodir.read()

    def get_mode_pin(self, slot, pin):
        self.__check_slot(slot)
        self.__check_pin(pin)
        cur = self.get_mode(slot)
        return (cur >> pin) & 1


class IOGroup:

    def __init__(self, name, bus, addr, ios):
        self.name = name
        if not isinstance(bus, smbus.SMBus):
            raise ValueError("bus must be a SMBus instance")
        self.bus = bus
        self.addr = addr
        self.ios = ios

    def __iter__(self):
        for io in self.ios:
            yield io

    def __getitem__(self, key):
        return self.ios[key]
