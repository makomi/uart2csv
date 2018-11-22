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

serial_baud_rate    = 115200
serial_timeout_read = 2            # number of seconds after which we consider the serial read operation to have failed
serial_timeout_msg  = "--READ-TIMEOUT--"
serial_cmd          = "print_id"   # command sent to request the device ID

# -----------------------------------------------------------------------------
# global variables
# -----------------------------------------------------------------------------

global selected_port
global uart
global file_csv
global operator_initials

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
        print("[!] No serial port found.")
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

# -----------------------------------------------------------------------------
# main program
# -----------------------------------------------------------------------------

if __name__ == '__main__':

    select_a_serial_port(get_available_serial_ports())
    open_selected_serial_port()

    set_operator_initials()

    # create the output folder for the CSV files if it does not already exist
    mkdir(folder_output)

    # filepointer to CSV file
    bufsize = -1                                                                 # FIXME: make sure the file is continuously flushed
    file_csv = open('%s/%s.csv' % (folder_output,datetime.now().strftime("%Y-%m-%d %H-%M-%S")), 'w+', bufsize)

    # read lines from the serial port and append them to the CSV file
    print("\nPress ENTER to read a line from the serial port.")
    print("Press 'q' and ENTER to exit.\n")

    while True:

        # wait for enter
        user_input = raw_input("")

        # avoid empty line between results                                       # FIXME: this only works on Linux terminals
        #CURSOR_UP_ONE = '\x1b[1A'
        #ERASE_LINE    = '\x1b[2K'
        #print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)

        check_for_exit_condition()

        # request the device's ID and read the response
        uart.write(serial_cmd)
        line = uart.readline().decode('ascii')

        # extract the device_id (expected: "<16 character device ID>\n")
        device_id = line[0:16]

        # display dummy address for demo purposes
        if len(device_id) == 0:
            device_id = serial_timeout_msg

        # TODO: check if the device_id is a duplicate

        # TODO: create a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # display the result
        print("%s  %s" % (timestamp,device_id))

        # append the result to the CSV
        if device_id != serial_timeout_msg:
            file_csv.write("%s, %s, %s\n" % (timestamp,device_id,operator_initials))

        # TODO: print the device_id on paper
        # Zebra S4M, v53.17.11Z
