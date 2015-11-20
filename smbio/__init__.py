# SMBus Peripheral Wrapper lib

from . import detector
from . import indicator
from . import interface
from . import ioexpander
from . import smb

IOTYPES = {
    0: "MCP23008",
    1: "MCP23017"
}

INTERFACETYPES = {
    0: "Led",
    1: "LedBlink",
    2: "Switch",
    3: "Keypad4x4Matrix"
}

IOMAP = {
    "MCP23008": ioexpander.MCP23008,
    "MCP23018": ioexpander.MCP23017
}

INTERFACEMAP = {
    "Led": indicator.Led,
    "LedBlink": indicator.LedBlink,
    "Switch": detector.Switch,
    "Keypad4x4Matrix": interface.Keypad4x4Matrix
}

INTERFACEDATAMAP = {
    iface_type: INTERFACEMAP[INTERFACETYPES[iface_type]].DATAMAP
    for iface_type in INTERFACETYPES}
