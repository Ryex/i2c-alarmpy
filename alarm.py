#!/usr/bin/python
import os
import time
import threading
import traceback
import json
import bcrypt
from contextlib import closing
import smbio
import database
from config import Config


class AlarmManager:

    def __init__(self):
        self.alarm = Alarm()
        self._running = False
        self.COMMANDS = {
            "start": self.start_alarm,
            "stop": self.stop_alarm,
            "restart": self.restart_alarm,
            "action": self.action_alarm
        }

    def start_alarm(self, reason):
        self.alarm.start()
        self.log("Alarm thread start command sent: " + reason)

    def stop_alarm(self, reason):
        self.alarm.stop()
        self.log("Alarm thread stop command sent: " + reason)

    def restart_alarm(self, reason):
        self.alarm.restart()
        self.log("Alarm thread restart command sent: " + reason)

    def action_alarm(self, data):
        self.alarm.process_action(data["action"], data["reason"])
        self.log("Alarm thread action command sent")

    def log(self, message, error=None):
        timestamp = time.strftime("%Z %Y-%m-%d %H:%M:%S", time.localtime())
        if error:
            trace = traceback.format_exc(error)
            message += "\n" + trace
        message = timestamp + " " + message
        database.write_log(message, error=(error is not None))

    def main(self):
        self._running = True
        while self._running():
            try:
                with closing(database.get_db()) as db:
                    c = db.cursor()
                    c.execute("select cmd_id, data from cmdq;")
                    cmds = c.fetchall()
                    if cmds:
                        for cmd in cmds:
                            cmd_id, data_s = cmd
                            data = json.loads(data_s)
                            self.process_cmd(cmd_id, data)
                self.log_state()
                time.sleep(Config["manager_sleep"])
            except Exception as err:
                self.log("Error in manager Main loop", err)

    def process_cmd(self, cmd_id, data):
        self.clear_cmd(cmd_id)
        if isinstance(data, dict):
            for key in data:
                if key in self.COMMANDS:
                    func = self.COMMANDS[key]
                    func(data[key])
        else:
            raise ValueError("Bad manager cmd data '%r'" % (data,))

    def clear_cmd(self, cmd_id):
        with closing(database.get_db()) as db:
            c = db.cursor()
            c.execute("delete from cmdq where cmd_id = %s" % (cmd_id,))
            db.commit()

    def log_state(self):
        with closing(database.get_db()) as db:
            c = db.cursor()
            c.execute(
                "insert into manager_state "
                "(state, state_time) "
                "values (%d, %d);"
                % (self.alarm._running, time.time()))
            db.commit()


class Alarm:

    DISARMED = 0
    ARMED = 1
    TRIPPED = 2
    ALARMED = 3
    FALT = 4

    ALARM_STATES = {
        DISARMED: "Disarmed",
        ARMED: "Armed",
        TRIPPED: "Triped",
        ALARMED: "Alarmed",
        FALT: "Falt"
    }

    ACTIONS = {
        "arm": None,
        "disarm": None,
        "trip": None,
        "alarm": None
    }

    def __init__(self):
        self.thread = None
        self._running = False
        self._configured = False
        self.ios = None
        self.interfaces = None
        self.MESSAGES = {
            "input": self.process_imput,
            "switch": self.process_switch
        }

        self.ACTIONS["arm"] = self.arm
        self.ACTIONS["disarm"] = self.disarm
        self.ACTIONS["trip"] = self.trip
        self.ACTIONS["alarm"] = self.alarm

        self.state = 0
        self.last = time.time()

    def arm(self, reason):
        if self.state == self.DISARMED:
            self.state = self.ARMED
        self.log("ARM " + reason)

    def disarm(self, reason):
        self.state = self.DISARMED
        self.log("DISARM " + reason)

    def trip(self, reason):
        if self.state == Alarm.ARMED:
            self.state = Alarm.TRIPPED
            self.last = time.time()
            self.log("TRIPPED " + reason)
        elif self.state == Alarm.DISARMED:
            self.state = Alarm.FALT
            self.last = time.time()

    def alarm(self, reason):
        self.state = Alarm.ALARMED
        self.log("ALARM " + reason, alarm=True)

    def update_state(self):
        for key in self.indicators:
            indicator = self.indicators[key]
            self.interfaces[indicator["interface"]].update_state(
                indicator["state"] == self.state)

    def update_triped(self):
        now = time.time()
        if now - self.last > Config["tripped_timeout"]:
            self.alarm("Tripped timeout")

    def update_falted(self):
        now = time.time()
        if now - self.last > Config["falted_timeout"]:
            self.state = Alarm.DISARMED

    def configure(self):
        with closing(database.get_db()) as db:
            c = db.cursor()

            c.execute("select io_id, type, bus, addr from io;")
            ios = c.fetchall()
            if ios:
                self.ios = {}
                for io in ios:
                    io_id, t, bus, addr, = io
                    if t not in smbio.IOTYPES:
                        raise ValueError("invaid io type for io %s" % (io_id,))
                    klass = smbio.IOMAP[smbio.IOTYPES[t]]
                    self.ios[io_id] = klass(smbio.Bus(bus), addr)

            c.execute("select interface_id, type, io_id, data from interface;")
            interfaces = c.fetchall()
            if interfaces:
                self.interfaces = {}
                for interface in interfaces:
                    interface_id, t, io_id, data_s = interface
                    if t not in smbio.INTERFACETYPES:
                        raise ValueError(
                            "invalid interface type for interface %s"
                            % (interface_id,))
                    data = json.loads(data_s)
                    klass = smbio.SMBINTERFACEMAP[
                        smbio.INTERFACETYPES[t]
                    ]
                    self.interfaces[interface_id] = klass(
                        interface_id, self.ios[io_id], data)

            c.execute(
                "select action_id, code_hash, command, reason"
                "from action;")
            actions = c.fetchall()
            if actions:
                self.actions = {}
                for action in actions:
                    action_id, code_hash, command, reason = action
                    self.actions[action_id] = {
                        "code_hash": code_hash,
                        "command": command,
                        "reason": reason
                    }

            c.execute(
                "select indicator_id, interface_id, state from indicator;")
            indicators = c.fetchall()
            if indicators:
                self.indicators = []
                for indicator in indicators:
                    indicator_id, interface_id, state = indicator
                    self.indicators[indicator_id] = {
                        "interface": interface_id,
                        "state": state
                    }

        self._configured = True

    def log(self, message, error=None, alarm=False):
        timestamp = time.strftime("%Z %Y-%m-%d %H:%M:%S", time.localtime())
        if error:
            trace = traceback.format_exc(error)
            message += "\n" + trace
        message = timestamp + " " + message
        database.write_log(message, error=(error is not None), alarm=alarm)

    def log_state(self, states):
        with closing(database.get_db()) as db:
            c = db.cursor()
            c.execute(
                "insert into state "
                "(state, data, state_time) "
                "values (%d, '%s', %d);"
                % (self.state, json.dumps(states), time.time()))
            db.commit()

    def stop(self):
        if self._running:
            if self.thread is not None:
                self._running = False
                self.thread.join()
            del self.thread
            del self.ios
            del self.interfaces
            self.thread = None
            self._configured = False
            self.ios = None
            self.interfaces = None

    def start(self):
        if not self._running:
            if self.thread is not None:
                self.thread = threading.Thread(target=self.run)
                self._running = True
                self.configure()
                self.thread.start()

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        try:
            if not self._configured:
                raise RuntimeError("Alarm system has no configuration")
            if self.ios is None:
                raise RuntimeError("No ios configured")
            if self.interfaces is None:
                raise RuntimeError("No interfaces configured")
            self.main()
        except Exception as err:
            self.log("Error running alarm main thread", error=err)
        self._running = False

    def update(self):
        self.update_commands()
        if self.state == Alarm.TRIPPED:
            self.update_tripped()
        elif self.state == Alarm.DISARMED:
            self.update_falted()
        self.update_state()
        states = {}
        for key in self.interfaces:
            interface = self.inerfaces[key]
            self.process_interface(interface, interface.update())
            states[key] = interface.get_state()
        self.log_state(states)

    def main(self):
        self.log("Alarm main loop starting")
        while self._running:
            self.update()
            time.sleep(Config["alarm_sleep"])
        self.log("Alarm main loop stoped")

    def process_interface(self, interface, message):
        for key in message:
            if key in self.MESSAGES:
                func = self.MESSAGES[key]
                func(message[key], interface)

    def process_action(self, action, reason):
        cmd = action["command"]
        res = action["reason"]
        if cmd in self.ACTIONS:
            func = self.ACTIONS[cmd]
            func(res + " " + reason)

    def process_imput(self, data):
        for key in self.actions:
            action = self.actions[key]
            if bcrypt.hashpw(data, action["code_hash"]) == action["code_hash"]:
                self.process_action(action["data"])
                break

    def process_switch(self, state, interface):
        self.trip("Switch on interface %s tripped" % (interface.pid,))


def write_pid():
    with open(Config["pidfile"], "w") as f:
        f.write(str(os.getpid()))


if __name__ == "__main__":
    database.init_db()
    a = AlarmManager()
    write_pid()
    a.main()
