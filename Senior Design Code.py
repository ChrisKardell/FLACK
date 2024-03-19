# coding:UTF-8
# Version: V1.0.1
import serial
import csv
import os
from datetime import datetime

ACCData = [0.0]*8
GYROData = [0.0]*8
AngleData = [0.0]*8
acc = (0.0, 0.0, 0.0)  # Default accelerometer values
gyro = (0.0, 0.0, 0.0)  # Default gyroscope values
Angle = (0.0, 0.0, 0.0)  # Default angle values
FrameState = 0  # What is the state of the judgment
Bytenum = 0  # Read the number of digits in this paragraph
CheckSum = 0  # Sum check bit
h = 0

a = [0.0]*3
w = [0.0]*3
Angle = [0.0]*3

# Function to get the test run number and update it
def get_test_run_number():
    try:
        # Try to read the test run number from a file
        with open('/home/flack/FLACK_Prog/test_run_number.txt', 'r') as file:
            test_run_number = int(file.read().strip())
    except FileNotFoundError:
        # If the file doesn't exist, start with test run number 1
        test_run_number = 1
    
    # Increment the test run number
    test_run_number += 1
    
    # Write the updated test run number back to the file
    with open('/home/flack/FLACK_Prog/test_run_number.txt', 'w') as file:
        file.write(str(test_run_number))
    
    return test_run_number

def DueData(inputdata, path, h, result1, result2):  # New core procedures, read the data partition, each read to the corresponding array 
    global FrameState    # Declare global variables
    global Bytenum
    global CheckSum
    global acc
    global gyro
    global Angle
    for data in inputdata:  # Traversal the input data
        if FrameState == 0:  # When the state is not determined, enter the following judgment
            if data == 0x55 and Bytenum == 0:  # When 0x55 is the first digit, start reading data and increment bytenum
                CheckSum = data
                Bytenum = 1
                continue
            elif data == 0x51 and Bytenum == 1:  # Change the frame if byte is not 0 and 0x51 is identified
                CheckSum += data
                FrameState = 1
                Bytenum = 2
            elif data == 0x52 and Bytenum == 1:
                CheckSum += data
                FrameState = 2
                Bytenum = 2
            elif data == 0x53 and Bytenum == 1:
                CheckSum += data
                FrameState = 3
                Bytenum = 2
        elif FrameState == 1:  # acc

            if Bytenum < 10:            # Read 8 data
                ACCData[Bytenum-2] = data  # Starting from 0
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):  # verify check bit
                    acc = get_acc(ACCData)
                CheckSum = 0  # Each data is zeroed and a new circular judgment is made
                Bytenum = 0
                FrameState = 0
        elif FrameState == 2:  # gyro

            if Bytenum < 10:
                GYROData[Bytenum-2] = data
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):
                    gyro = get_gyro(GYROData)
                CheckSum = 0
                Bytenum = 0
                FrameState = 0
        elif FrameState == 3:  # angle

            if Bytenum < 10:
                AngleData[Bytenum-2] = data
                CheckSum += data
                Bytenum += 1
            else:
                if data == (CheckSum & 0xff):
                    Angle = get_angle(AngleData)
                    result0 = acc + gyro + Angle
                
                    if h == 0:
                        result1 = list(result0)
                
                    elif h == 1:
                        result2 = list(result0)
                        
                    print("Result 1:", result1)
                    print("Result 2:", result2)
                    
                    if result1 is not None and result2 is not None:  # If both sets of data are available
                        result_combined = result1 + result2  # Combine the data
                        print("Combined Result:", result_combined)
                        with open(path, 'a', newline='') as csvfile:
                            csv_writer = csv.writer(csvfile)
                            csv_writer.writerow(result_combined)
                        
                CheckSum = 0
                Bytenum = 0
                FrameState = 0


def get_acc(datahex):
    axl = datahex[0]
    axh = datahex[1]
    ayl = datahex[2]
    ayh = datahex[3]
    azl = datahex[4]
    azh = datahex[5]
    k_acc = 16.0
    acc_x = (axh << 8 | axl) / 32768.0 * k_acc
    acc_y = (ayh << 8 | ayl) / 32768.0 * k_acc
    acc_z = (azh << 8 | azl) / 32768.0 * k_acc
    if acc_x >= k_acc:
        acc_x -= 2 * k_acc
    if acc_y >= k_acc:
        acc_y -= 2 * k_acc
    if acc_z >= k_acc:
        acc_z -= 2 * k_acc
    return acc_x, acc_y, acc_z


def get_gyro(datahex):
    wxl = datahex[0]
    wxh = datahex[1]
    wyl = datahex[2]
    wyh = datahex[3]
    wzl = datahex[4]
    wzh = datahex[5]
    k_gyro = 2000.0
    gyro_x = (wxh << 8 | wxl) / 32768.0 * k_gyro
    gyro_y = (wyh << 8 | wyl) / 32768.0 * k_gyro
    gyro_z = (wzh << 8 | wzl) / 32768.0 * k_gyro
    if gyro_x >= k_gyro:
        gyro_x -= 2 * k_gyro
    if gyro_y >= k_gyro:
        gyro_y -= 2 * k_gyro
    if gyro_z >= k_gyro:
        gyro_z -= 2 * k_gyro
    return gyro_x, gyro_y, gyro_z


def get_angle(datahex):
    rxl = datahex[0]
    rxh = datahex[1]
    ryl = datahex[2]
    ryh = datahex[3]
    rzl = datahex[4]
    rzh = datahex[5]
    k_angle = 180.0
    angle_x = (rxh << 8 | rxl) / 32768.0 * k_angle
    angle_y = (ryh << 8 | ryl) / 32768.0 * k_angle
    angle_z = (rzh << 8 | rzl) / 32768.0 * k_angle
    if angle_x >= k_angle:
        angle_x -= 2 * k_angle
    if angle_y >= k_angle:
        angle_y -= 2 * k_angle
    if angle_z >= k_angle:
        angle_z -= 2 * k_angle
    return angle_x, angle_y, angle_z


if __name__ == '__main__':
    port1 = '/dev/ttyUSB0' # First USB serial port 
    port2 = '/dev/ttyUSB1' # Second USB serial port
    baud = 9600   # Same baud rate as the INERTIAL navigation module
    ser1 = serial.Serial(port1, baud, timeout=0.5)
    ser2 = serial.Serial(port2, baud, timeout=0.5)
    print("Serial 1 is Opened:", ser1.is_open)
    print("Serial 2 is Opened:", ser2.is_open)

    test_number = get_test_run_number() # Get the test run number
    title = f"Test run #{test_number}" # Create data file name

    path = '/home/flack/FLACK_Data/' + title + '.csv'
    '''
    try:
        while(1):
            datahex1 = ser1.read(33)
            result1 = []
            DueData(datahex1,path,h,result1)
            h = 1
            datahex2 = ser2.read(33)
            DueData(datahex2,path,h,result1)
            h = 0
    '''
    result1 = []
    result2 = []
    try:
        while True:
            datahex1 = ser1.read(33)
            DueData(datahex1, path, h, result1, result2)
            h = 1
            datahex2 = ser2.read(33)
            DueData(datahex2, path, h, result1, result2)
            h = 0
    except KeyboardInterrupt:
         print("\nUser interrupted the program.")
