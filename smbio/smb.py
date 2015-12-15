import smbus
import warnings
import traceback


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
        self.message_q = []

    def message(self, message):
        self.message_q.append(message)

    def pull_messages(self):
        msgs = []
        while self.message_q:
            msgs.append(self.message_q.pop(0))
        return msgs

    def process_messages(self, messages):
        pass

    def init(self):
        pass

    def get_state(self):
        return self._state

    def update_state(self, state):
        pass

    def update(self):
        pass


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
                "can only write ints with a bit length "
                "smaller than {}".format(self.length))
        self.bus.write_byte_data(self.addr, self.com, value << self.offset)

    def read(self):
        value = self.bus.read_byte_data(self.addr, self.com) & 0xff
        return value >> self.offset


class IO:
    '''Define an interface to an 8 bit IO'''
    READ = 1
    WRITE = 0
    PINMIN = 0
    PINMAX = 7

    def __init__(self, bus, addr, iodir, gpio, olat, pullup):
        if not isinstance(bus, smbus.SMBus):
            raise ValueError("bus must be an SMBus instance")
        self.bus = bus
        self.addr = addr
        self.iodir = Data(bus, self.addr, iodir)
        self.olat = Data(bus, self.addr, olat)
        self.gpio = Data(bus, self.addr, gpio)
        self.pullup = Data(bus, self.addr, pullup)
        self.iodir_val = self.get_mode()
        self.gpio_val = self.read_in()
        self.olat_val = self.read_out()
        self.pullup_val = self.get_pullup()

    def __check_value(self, value, pin=False):
        if not isinstance(value, int):
            raise ValueError("value must be an int: {}".format(hex(value)))
        if value < 0x00 or value > 0xFF:
            raise ValueError(
                "value must be between 0x00 and 0xff: {}".format(hex(value)))
        if pin:
            if value.bit_length() > 1:
                raise ValueError(
                    "when setting a pin "
                    "value must by 1 or 0: {}".format(hex(value)))

    def __check_mode(self, mode):
        if not (mode == IO.READ or mode == IO.WRITE):
            raise ValueError(
                "mode must be IO.READ or IO.WRITE: {}".format(hex(mode)))

    def __check_pin(self, pin):
        if pin > IO.PINMAX or pin < IO.PINMIN:
            raise ValueError(
                "pin must be between {} and {}".format(IO.PINMAX, IO.PINMIN))

    def write_out(self, value):
        self.__check_value(value)
        self.olat.write(value)
        self.olat_val = value

    def write_out_pin(self, pin, value):
        self.__check_pin(pin)
        self.__check_value(value, True)
        cur = self.read_out()
        if cur != self.olat_val:
            self.warn(cur, self.olat_val, 'olat')
            cur = self.olat_val
        new = cur ^ ((-value ^ cur) & (1 << pin))
        self.write_out(new)

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
        self.__check_value(mode)
        self.iodir.write(mode)
        self.iodir_val = mode

    def set_mode_pin(self, pin, mode):
        self.__check_pin(pin)
        self.__check_mode(mode)
        cur = self.get_mode()
        if cur != self.iodir_val:
            self.warn(cur, self.iodir_val, 'iodir')
            cur = self.iodir_val
        new = cur ^ ((-mode ^ cur) & (1 << pin))
        self.set_mode(new)

    def get_mode(self):
        return self.iodir.read()

    def get_mode_pin(self, pin):
        self.__check_pin(pin)
        cur = self.get_mode()
        return (cur >> pin) & 1

    def set_pullup(self, mode):
        self.__check_value(mode)
        self.pullup.write(mode)
        self.pullup_val = mode

    def set_pullup_pin(self, pin, mode):
        self.__check_pin(pin)
        self.__check_mode(mode)
        cur = self.get_pullup()
        if cur != self.pullup_val:
            self.warn(cur, self.pullup_val, 'pullup')
            cur = self.pullup_val
        new = cur ^ ((-mode ^ cur) & (1 << pin))
        self.set_pullup(new)

    def get_pullup(self):
        return self.pullup.read()

    def get_pullup_pin(self, pin):
        self.__check_pin(pin)
        cur = self.get_pullup()
        return (cur >> pin) & 1

    def warn(self, got, expected, where):
            warnings.warn(
                "Unexpected state: "
                "got {} expected {} "
                "in {} bus: {} addr: {}".format(
                    hex(got),
                    hex(expected),
                    where,
                    int(self.bus),
                    hex(self.addr)),
                RuntimeWarning)


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
