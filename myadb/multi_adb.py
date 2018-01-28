#!/usr/bin/env python3
# coding: utf-8

from __future__ import print_function, unicode_literals

from distutils.spawn import find_executable
import asyncio
import os
import re
import subprocess
import sys
from threading import Thread


adb_path = find_executable("adb")

if not adb_path:
    print('adb path not found.')
    exit(-1)


def mkdir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def connect(device):
    process = subprocess.Popen([adb_path, 'connect', device], stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline().decode('utf-8').strip()
        if not line:
            break
        if line.strip() and line.startswith('connected to'):
            return True
    return False


def disconnect(device):
    process = subprocess.Popen([adb_path, 'disconnect', device], stdout=subprocess.PIPE)
    while True:
        line = process.stdout.readline().decode('utf-8').strip()
        if not line:
            break
        if line.strip() and line.startswith('disconnected'):
            return True
    return False


class Device:
    def __init__(self, name, usb):
        self.__name = name
        self.__loop = None
        self.__thread = None
        self.__running = False
        self.__connected = True
        self.__auto_connect = False
        if len(usb) != 0 or name.startswith("emulator"):
            self.__auto_connect = True

    def __del__(self):
        if self.__loop is not None:
            self.__loop.stop()
            self.__loop.close()
            self.__loop = None
        if self.__thread is not None:
            self.__thread.join()
            self.__thread = None

    def __run_forever(self):
        self.__loop.run_forever()
        # set exit point
        self.__running = False

    def start(self):
        if self.__loop is not None:
            return
        self.__running = True
        self.__loop = asyncio.new_event_loop()
        self.__thread = Thread(target=self.__run_forever)
        self.__thread.start()

    def stop(self):
        self.__loop.call_soon_threadsafe(self.__stop_in_loop_thread)

    def __get_name(self):
        return "[" + self.__name + "]"

    def execute(self, command):
        self.start()
        self.__loop.call_soon_threadsafe(self.__run_in_loop_thread, command)

    def __stop_in_loop_thread(self):
        self.__loop.stop()

    def wait_stop(self):
        while self.__running:
            pass

    def __run_in_loop_thread(self, command):
        if command.find("{device}") >= 0:
            command = command.format(device=self.__name)
        if command.find("{output_device}") >= 0:
            command = command.format(output_device="output/"+self.__name)
            mkdir("output/"+self.__name)
        print(self.__get_name() + " execute: " + command)
        cmd = command.split(" ")
        if cmd[0] == "connect":
            self.__run_connect()
            return
        if cmd[0] == "disconnect":
            self.__run_disconnect()
            return
        if cmd[0] == "root":
            self.__run_root()
            return
        self.__run_normal(command)

    def __run_connect(self):
        if self.__connected:
            return
        if connect(self.__name):
            self.__connected = True
            return
        print(self.__get_name() + " connect fail")
        exit(1)

    def __run_disconnect(self):
        if not self.__connected:
            return
        if self.__auto_connect:
            return
        if disconnect(self.__name):
            self.__connected = False
            return
        print(self.__get_name() + " disconnect fail")
        exit(1)

    def __run_root(self):
        process = subprocess.Popen([adb_path, '-s', self.__name, 'root'], stdout=subprocess.PIPE)
        while True:
            line = process.stdout.readline().decode('utf-8').strip()
            if not line:
                break
            line = line.strip()
            if line != 'adbd is already running as root':
                self.__connected = False

    def __run_normal(self, command):
        subprocess.run("\"" + adb_path + "\"" + " -s " + self.__name + " " + command, shell=True)


class Devices:
    def __init__(self):
        self.__devices = []

    def __str__(self):
        return self.__devices.__str__()

    def append(self, device):
        if not self.has_device(device['serial']):
            device['object'] = Device(device['serial'], device['usb'])
            self.__devices.append(device)

    def has_device(self, device_name):
        for device in self.__devices:
            if device['serial'] == device_name:
                return True
            if device['serial_short'] == device_name:
                return True
        return False

    def execute(self, command):
        for device in self.__devices:
            device['object'].execute(command)

    def stop(self):
        for device in self.__devices:
            device['object'].stop()

    def wait_stop(self):
        for device in self.__devices:
            device['object'].wait_stop()


class Adb:
    def __init__(self):
        self.__devices = Devices()
        self.read_devices()

    @staticmethod
    def get_key_value(var, key):
        if not var.startswith(key):
            print("key " + key + " not found in " + var)
            sys.exit(1)
        return var[len(key) + 1:]

    @staticmethod
    def get_serial_short(serial):
        pos = serial.find(':')
        if pos < 0:
            return serial
        short = serial[0: pos]
        short = short.strip()
        return short

    def read_devices(self):
        process = subprocess.Popen([adb_path, 'devices', '-l'], stdout=subprocess.PIPE)
        while True:
            line = process.stdout.readline().decode('utf-8').strip()
            if not line:
                break
            if line.strip() and not line.startswith('List of devices'):
                d = re.split(r'\s+', line.strip())
                if len(d) == 7:
                    # serial "device" usb product model device transport_id
                    self.__devices.append({
                        'serial': d[0],
                        'serial_short': Adb.get_serial_short(d[0]),
                        'usb': Adb.get_key_value(d[2], "usb"),
                        'product': Adb.get_key_value(d[3], "product"),
                        'model': Adb.get_key_value(d[4], "model"),
                        'device': Adb.get_key_value(d[5], "device"),
                        'transport_id': Adb.get_key_value(d[6], "transport_id")
                    })
                elif len(d) == 6:
                    # serial "device" product model device transport_id
                    self.__devices.append({
                        'serial': d[0],
                        'serial_short': Adb.get_serial_short(d[0]),
                        'usb': "",
                        'product': Adb.get_key_value(d[2], "product"),
                        'model': Adb.get_key_value(d[3], "model"),
                        'device': Adb.get_key_value(d[4], "device"),
                        'transport_id': Adb.get_key_value(d[5], "transport_id")
                    })
                elif len(d) == 5:
                    # serial "device" product model device
                    self.__devices.append({
                        'serial': d[0],
                        'serial_short': Adb.get_serial_short(d[0]),
                        'usb': "",
                        'product': Adb.get_key_value(d[2], "product"),
                        'model': Adb.get_key_value(d[3], "model"),
                        'device': Adb.get_key_value(d[4], "device"),
                        'transport_id': ""
                    })
                else:
                    if d[1] == "offline":
                        # only : serial "offline" transport_id
                        continue
                    print(line + " not support")
                    sys.exit(1)

    def connect_devices(self):
        if not os.path.exists("device.txt"):
            return
        with open("device.txt", "r") as f:
            for line in f:
                if line.startswith("#"):
                    # support minimum comment
                    continue
                line = line.strip("\n")
                line = line.strip("\r")
                if len(line) == 0:
                    continue
                if not self.__devices.has_device(line):
                    connect(line)
        # reset
        self.__devices = Devices()
        self.read_devices()
        print(self.__devices)

    def run(self):
        with open("command.txt", "r") as f:
            for line in f:
                if line.startswith("#"):
                    # support minimum comment
                    continue
                line = line.strip("\n")
                line = line.strip("\r")
                if len(line) == 0:
                    continue
                self.__devices.execute(line)
            self.__devices.stop()
        self.__devices.wait_stop()


if __name__ == '__main__':
    adb = Adb()
    adb.connect_devices()
    adb.run()
