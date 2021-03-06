#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2018  Matthias Kolja Miehl
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
DESCRIPTION: Python script for reading a line via UART and
             appending it to a CSV file along with a timestamp
UPDATES    : https://github.com/makomi/uart2csv
"""


# -----------------------------------------------------------------------------
# include libraries and set defaults
# -----------------------------------------------------------------------------

import os
import operator
import serial
import serial.tools.list_ports
from datetime import datetime

folder_output = "csv"
#file_cfg      = "settings.cfg"

# -----------------------------------------------------------------------------
# settings (change this as required)
# -----------------------------------------------------------------------------

serial_baud_rate     = 115200
serial_timeout_read  = 0.05        # number of seconds after which we consider the serial read operation to have failed
serial_timeout_msg   = "--READ-TIMEOUT--"
serial_too_short_msg = "--ADDR-TOO-SHORT: "
serial_cmd           = "\r"        # characters sent to request the device ID
length_device_id     = 16

# -----------------------------------------------------------------------------
# global variables
# -----------------------------------------------------------------------------

global selected_port       # serial port that will be used
global operator_initials   # used to identify the operator in the CSV file log
global uart                # serial port object
global file_csv            # file object for the CSV file
global serial_read_ok      # 'True' if we read what we expected

# -----------------------------------------------------------------------------
# helper functions
# -----------------------------------------------------------------------------

def mkdir(folder_name):
    """create a new folder"""
    if not os.path.isdir(folder_name):
        try:
            os.makedirs(folder_name)
        except OSError:
            if not os.path.isdir(folder_name):
                raise

def get_available_serial_ports():
    available_ports_all = list(serial.tools.list_ports.comports())               # get all available serial ports
    available_ports = [port for port in available_ports_all if port[2] != 'n/a'] # remove all unfit serial ports
    available_ports.sort(key=operator.itemgetter(1))                             # sort the list based on the port
    return available_ports

def select_a_serial_port(available_ports):                                       # TODO: check file_cfg for preselected serial port
    global selected_port
    if len(available_ports) == 0:       # list is empty -> exit
        print("[!] No suitable serial port found.")
        exit(-1)
    elif len(available_ports) == 1:     # only one port available
        (selected_port,_,_) = available_ports[0]
        print("[+] Using only available serial port: %s" % selected_port)
    else:                               # let user choose a port
        successful_selection = False
        while not successful_selection:
            print("[+] Select one of the available serial ports:")
            # port selection
            item=1
            for port,desc,_ in available_ports:
                print ("    (%d) %s \"%s\"" % (item,port,desc))
                item=item+1
            selected_item = int(raw_input(">>> "))                               # TODO: handle character input
            # check if a valid item was selected
            if (selected_item > 0) and (selected_item <= len(available_ports)):
                (selected_port,_,_) = available_ports[selected_item-1]
                successful_selection = True
            else:
                print("[!] Invalid serial port.\n")

def open_selected_serial_port():
    global uart
    try:
        uart = serial.Serial(
            selected_port,
            serial_baud_rate,
            timeout  = serial_timeout_read,
            bytesize = serial.EIGHTBITS,
            parity   = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
        )
        print("[+] Successfully connected.")
    except serial.SerialException:
        print("[!] Unable to open %s." % selected_port)
        exit(-1)

def set_operator_initials():
    global operator_initials
    # get operator's initials
    print("\n[+] Operator's initials:")
    operator_initials = raw_input(">>> ")

    # make it obvious that the operator did not provide initials
    if len(operator_initials) == 0:
        operator_initials = "n/a"

def create_csv_file():
    global file_csv              # file object for CSV file
    mkdir(folder_output)         # create the output folder for the CSV files if it does not already exist
    file_csv = open('%s/%s.csv' % (folder_output,datetime.now().strftime("%Y-%m-%d %H-%M-%S")), 'w+', -1)  # FIXME: make sure the file is continuously flushed

def print_usage_guide():
    print("\nPress ENTER to read a line from the serial port.")
    print("Press 'q' and ENTER to exit.")

def check_for_exit_condition():
    """exit program after releasing all resources"""
    global uart
    global file_csv
    if user_input == "q":
        successful_exit = False
        # close serial port
        try:
            uart.close()
            print("[+] Closed %s." % selected_port)
            successful_exit = True
        except serial.SerialException:
            print("[!] Unable to close %s." % selected_port)
        # close file
        try:
            file_csv.close()
            print("[+] Closed CSV file.")
            successful_exit = True
        except:
            print("[!] Unable to close CSV file.")
        # exit
        if successful_exit:
            exit(0)
        else:
            exit(-1)

def get_device_id():
    global uart
    global device_id
    global serial_read_ok
    # request the device's ID and read the response
    uart.write(serial_cmd)
    line = uart.readline().decode('ascii')

    # extract the device_id (expected: "<16 character device ID>\n")
    device_id = line[0:length_device_id]

    # make typical whitespace characters visible
    if device_id == '\n':
        device_id = "<LF>"
    elif device_id == '\r':
        device_id = "<CR>"
    elif device_id == "\n\r":
        device_id = "<LF><CR>"
    elif device_id == "\r\n":
        device_id = "<CR><LF>"

    # display read timeout message to notify the operator
    if len(device_id) == 0:
        device_id = serial_timeout_msg
    elif len(device_id) < length_device_id:
        device_id = serial_too_short_msg + "'" + device_id + "'"
    else:
        serial_read_ok = True

def handle_device_id_duplicates():
    pass                                                                         # TODO: check if the device_id is a duplicate

def output_data():
    global file_csv
    # create a timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # display the result
    print("%s  %s" % (timestamp, device_id))

    # append the result to the CSV
    if serial_read_ok:
        file_csv.write("%s,%s,%s\n" % (timestamp, device_id, operator_initials))

    # TODO: print the device_id on paper
    # Zebra S4M, v53.17.11Z

# -----------------------------------------------------------------------------
# main program
# -----------------------------------------------------------------------------

if __name__ == '__main__':

    select_a_serial_port(get_available_serial_ports())
    open_selected_serial_port()

    set_operator_initials()

    create_csv_file()

    print_usage_guide()

    while True:

        serial_read_ok = False

        # wait for enter
        user_input = raw_input("")

        # avoid empty line between results                                       # FIXME: this only works on Linux terminals
        #CURSOR_UP_ONE = '\x1b[1A'
        #ERASE_LINE    = '\x1b[2K'
        #print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)

        check_for_exit_condition()

        get_device_id()

        handle_device_id_duplicates()

        output_data()
