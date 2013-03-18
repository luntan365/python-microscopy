#!/usr/bin/python

##################
# piezo_e816.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
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
#
##################

import serial;
import time

#C867 controller for PiLine piezo linear motor stages
#NB units are mm not um as for piezos

class piezo_c867:    
    def __init__(self, portname='COM1', maxtravel = 25.00, hasTrigger=False, reference=True):
        self.max_travel = maxtravel
        
        self.ser_port = serial.Serial(portname, 38400, timeout=.1, writeTimeout=.1)
        
        #turn servo mode on
        self.ser_port.write('SVO 1 1\n')
        self.ser_port.write('SVO 2 1\n')
        
        if reference:
            #find reference switch (should be in centre of range)
            self.ser_port.write('FRF\n')
        
        #self.lastPos = self.GetPos()

        #self.driftCompensation = False
        self.hasTrigger = hasTrigger

    def ReInit(self, reference=True):
        #self.ser_port.write('WTO A0\n')
        self.ser_port.write('SVO 1 1\n')
        self.ser_port.write('SVO 2 1\n')
        
        if reference:
            #find reference switch (should be in centre of range)
            self.ser_port.write('FRF\n')
        
        self.lastPos = self.GetPos()
        
    def MoveTo(self, iChannel, fPos, bTimeOut=True):
        if (fPos >= 0):
            if (fPos <= self.max_travel):
                self.ser_port.write('MOV %d %3.4f\n' % (iChannel, fPos))
                self.lastPos = fPos
            else:
                self.ser_port.write('MOV %d %3.4f\n' % (iChannel, self.max_travel))
                self.lastPos = self.max_travel
        else:
            self.ser_port.write('MOV %d %3.4f\n' % (iChannel, 0.0))
            self.lastPos = 0.0
            
    def MoveToXY(self, xPos, yPos, bTimeOut=True):
        xPos = min(max(xPos, 0),self.max_travel)
        yPos = min(max(yPos, 0),self.max_travel)
        
        self.ser_port.write('MOV 1 %3.4f 2 %3.4f\n' % (xPos, yPos))
        #self.lastPos = fPos
            

    def GetPos(self, iChannel=0):
        self.ser_port.flush()
        time.sleep(0.05)
        self.ser_port.write('POS? %d\n' % iChannel)
        self.ser_port.flushOutput()
        time.sleep(0.05)
        res = self.ser_port.readline()
        
        return float(res.split('=')[1]) 
        
    def GetPosXY(self):
        self.ser_port.flush()
        time.sleep(0.05)
        self.ser_port.write('POS? 1 2\n')
        self.ser_port.flushOutput()
        time.sleep(0.05)
        res1 = self.ser_port.readline()
        res2 = self.ser_port.readline()
        
        return float(res1.split('=')[1]), float(res2.split('=')[1])


    
    def GetControlReady(self):
        return True
    def GetChannelObject(self):
        return 1
    def GetChannelPhase(self):
        return 2
    def GetMin(self,iChan=1):
        return 0
    def GetMax(self, iChan=1):
        return self.max_travel
        
    def GetFirmwareVersion(self):
        import re
        self.ser_port.write('*IDN?\n')
        self.ser_port.flush()
        
        verstring = self.ser_port.readline()
        return float(re.findall(r'V(\d\.\d\d)', verstring)[0])
        
        
        