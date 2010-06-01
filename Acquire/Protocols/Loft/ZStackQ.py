#import all the stuff to make this work
from PYME.Acquire.protocol import *
import numpy

#define a list of tasks, where T(when, what, *args) creates a new task
#when is the frame number, what is a function to be called, and *args are any
#additional arguments
taskList = [
T(-1, scope.turnAllLasersOff),
#T(1, scope.l488.TurnOn),
#T(20, scope.lFibre.TurnOn),
T(20, scope.l488.TurnOn),
T(30, MainFrame.pan_spool.OnBAnalyse, None)
]

#optional - metadata entries
metaData = [
('Protocol.DarkFrameRange', (0, 20)),
('Protocol.DataStartsAt', 21)
]

#must be defined for protocol to be discovered
PROTOCOL = ZStackTaskListProtocol(taskList, 20, 10, metaData, randomise = False)
PROTOCOL_STACK = ZStackTaskListProtocol(taskList, 20, 10, metaData, randomise = False)