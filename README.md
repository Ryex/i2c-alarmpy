# i2c-alarmpy
A home alarm system written in python using i2c addressable sensors and indicators

This system is designed to run on a raspi but it should work on any system
that can run python with an i2c SMBus interface.

run `alarm.py` to monitor sensors and update indicators

run `web.py` to have a web interface to configure and monitor system

The system makes user of `smbus` the python interface released with lm-sensors,
`flask` the python micro web framework,
`sqlite` for a database for storing logs and configuration,
and `bcrypt` to keep user passwords and alarm cods secure.

system also uses local copies of bootstrap and jquery to make web
interface visualy apealing.
