#!/usr/bin/env python3
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
import io
import sys
import operator
import serial
import serial.tools.list_ports
from datetime import datetime

folder_output = "csv"
#file_cfg      = "settings.cfg"

# -----------------------------------------------------------------------------
# global variables
# -----------------------------------------------------------------------------

global selected_port
global uart
global file_csv
global operator_name

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

# -----------------------------------------------------------------------------
# main program
# -----------------------------------------------------------------------------

if __name__ == '__main__':

    # get serial ports
    available_ports_all = list(serial.tools.list_ports.comports())               # get all available serial ports
    available_ports = [port for port in available_ports_all if port[2] != 'n/a'] # remove all unfit serial ports
    available_ports.sort(key=operator.itemgetter(1))                             # sort the list

    # determine serial port
    # TODO: Check file_cfg for preselected serial port
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
            selected_item = int(input(">>> "))         # TODO: Handle character input
            # check if a valid item was selected
            if (selected_item > 0) and (selected_item <= len(available_ports)):
                (selected_port,_,_) = available_ports[selected_item-1]
                successful_selection = True
            else:
                print("[!] Invalid serial port.\n")

    # open serial port
    try:
        uart = serial.Serial(
            selected_port,
            115200,
            timeout  = 1,
            parity   = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE,
            bytesize = serial.EIGHTBITS
            )
        print("[+] Successfully connected.")
    except serial.SerialException:
        print("[!] Unable to open '%s'." % selected_port)
        exit(-1)

    # get operator's name
    print("\n[+] Operator's name:")
    operator_name = input(">>> ")

    # create the output folder for the CSV files if it does not already exist
    mkdir(folder_output)

    # filepointer to CSV file
    bufsize = -1                # FIXME: make sure the file is continuously flushed
    file_csv = open('%s/%s.csv' % (folder_output,datetime.now().strftime("%Y-%m-%d %H-%M-%S")), 'w+', bufsize)

    # read lines from the serial port and append them to the CSV file
    print("\nPress ENTER to read a line from the serial port.")
    print("Press 'q' and ENTER to exit.\n")

    while True:

        # wait for enter
        user = input("")

        # avoid empty line between results
        CURSOR_UP_ONE = '\x1b[1A'
        ERASE_LINE    = '\x1b[2K'
        print(CURSOR_UP_ONE + ERASE_LINE + CURSOR_UP_ONE)

        # exit program after releasing all resources
        if user == "q":
            successful_exit = False
            # close serial port
            try:
                uart.close()
                print("[+] Closed serial port: %s" % selected_port)
                successful_exit = True
            except serial.SerialException:
                print("[!] Unable to close serial port: %s" % selected_port)
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

        # request the device's ID and read the response
#        uart.write("print_id\n")
#        line = uart.readline().decode('ascii')

        # TODO: Check if the response conforms to what we expect, i.e. 8 characters and a line feed

        # TODO: Extract the device_id
        device_id = "DEADBEEF" # dummy

        # TODO: Check if the device_id is a duplicate

        # TODO: create a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # display the result
        print("%s %s" % (timestamp,device_id))

        # append the result to the CSV file
        file_csv.write("%s, %s, %s\n" % (timestamp,device_id,operator_name))

        # TODO: print the device_id on paper
        # Zebra S4M, v53.17.11Z
