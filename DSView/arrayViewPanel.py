#!/usr/bin/python

##################
# myviewpanel_numarray.py
#
# Copyright David Baddeley, 2009
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################


import wx
import sys
sys.path.append(".")
import scrolledImagePanel
from displayOptions import DisplayOpts
from DisplayOptionsPanel import OptionsPanel

import numpy
import scipy
#import tables
import time




            
class ArrayViewPanel(scrolledImagePanel.ScrolledImagePanel):
    def __init__(self, parent, dstack = None, aspect=1):
        
        if (dstack == None):
            dstack = scipy.zeros(10,10)

        self.do = DisplayOpts(dstack, aspect=aspect)
        self.do.Optimise()

        scrolledImagePanel.ScrolledImagePanel.__init__(self, parent, self.DoPaint, style=wx.SUNKEN_BORDER|wx.TAB_TRAVERSAL)

        self.do.WantChangeNotification.append(self.GetOpts)

        self.SetVirtualSize(wx.Size(self.do.ds.shape[0],self.do.ds.shape[1]))
        #self.imagepanel.SetSize(wx.Size(self.do.ds.shape[0],self.do.ds.shape[1]))
        

        self.points =[]
        self.pointsR = []
        self.pointMode = 'confoc'
        self.pointTolNFoc = {'confoc' : (5,5,5), 'lm' : (2, 5, 5), 'splitter' : (2,5,5)}

        self.psfROIs = []
        self.psfROISize=[30,30,30]

        self.lastUpdateTime = 0
        self.lastFrameTime = 2e-3

        self.do.scale = 2
        self.crosshairs = True
        self.selection = True

        self.aspect = 1.

#        if not aspect == None:
#            if scipy.isscalar(aspect):
#                self.do.aspects[2] = aspect
#            elif len(aspect) == 3:
#                self.do.aspects = aspect

        self.ResetSelection()
        #self.SetOpts()
        #self.optionspanel.RefreshHists()
        self.updating = 0
        self.showOptsPanel = 1

        self.refrTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRefrTimer)

        wx.EVT_MOUSEWHEEL(self, self.OnWheel)
        wx.EVT_KEY_DOWN(self.imagepanel, self.OnKeyPress)
        wx.EVT_LEFT_UP(self.imagepanel, self.OnLeftClick)
        
        wx.EVT_RIGHT_DOWN(self.imagepanel, self.OnRightDown)
        wx.EVT_RIGHT_UP(self.imagepanel, self.OnRightUp)

        #
        wx.EVT_ERASE_BACKGROUND(self.imagepanel, self.DoNix)
        wx.EVT_ERASE_BACKGROUND(self, self.DoNix)

    def OnRefrTimer(self, event):
        self.Refresh()
        
    def SetDataStack(self, ds):
        self.do.SetDataStack(ds)
        self.SetVirtualSize(wx.Size(self.do.ds.shape[0],self.do.ds.shape[1]))
                
        self.do.xp=0
        self.do.yp=0
        self.do.zp=0
        self.do.Optimise()
            
        self.ResetSelection()
        
        self.Layout()
#        self.Refresh()

    def ResetDataStack(self, ds):
        self.do.SetDataStack(ds)
        
    def DoPaint(self, dc):
        
        dc.Clear()
                                     
        im = self.Render()

        sc = pow(2.0,(self.do.scale-2))
        im.Rescale(im.GetWidth()*sc,im.GetHeight()*sc*self.aspect)

        x0,y0 = self.CalcUnscrolledPosition(0,0)
        dc.DrawBitmap(wx.BitmapFromImage(im),-sc/2,-sc/2)
        
        sX, sY = im.GetWidth(), im.GetHeight()

        if self.crosshairs:
            dc.SetPen(wx.Pen(wx.CYAN,0))
            if(self.do.slice == self.do.SLICE_XY):
                lx = self.do.xp
                ly = self.do.yp
            elif(self.do.slice == self.do.SLICE_XZ):
                lx = self.do.xp
                ly = self.do.zp
            elif(self.do.slice == self.do.SLICE_YZ):
                lx = self.do.yp
                ly = self.do.zp
        
            
            if (self.do.orientation == self.do.UPRIGHT):
                dc.DrawLine(0, ly*sc*self.aspect - y0, sX, ly*sc*self.aspect - y0)
                dc.DrawLine(lx*sc - x0, 0, lx*sc - x0, sY)
            else:
                dc.DrawLine(0, lx*sc - y0, sX, lx*sc - y0)
                dc.DrawLine(ly*sc - x0, 0, ly*sc - x0, sY)
            dc.SetPen(wx.NullPen)
            
        if self.selection:
            dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('YELLOW'),0))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            if(self.do.slice == self.do.SLICE_XY):
                lx = self.selection_begin_x
                ly = self.selection_begin_y
                hx = self.selection_end_x
                hy = self.selection_end_y
            elif(self.do.slice == self.do.SLICE_XZ):
                lx = self.selection_begin_x
                ly = self.selection_begin_z
                hx = self.selection_end_x
                hy = self.selection_end_z
            elif(self.do.slice == self.do.SLICE_YZ):
                lx = self.selection_begin_y
                ly = self.selection_begin_z
                hx = self.selection_end_y
                hy = self.selection_end_z
        
            
            if (self.do.orientation == self.do.UPRIGHT):
                dc.DrawRectangle(lx*sc - x0,ly*sc*self.aspect - y0, (hx-lx)*sc,(hy-ly)*sc*self.aspect)
            else:
                dc.DrawRectangle(ly*sc - x0,lx*sc - y0, (hy-ly)*sc,(hx-lx)*sc)
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.NullBrush)

        if (len(self.psfROIs) > 0):
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('GREEN'),0))
            if(self.do.slice == self.do.SLICE_XY):
                for p in self.psfROIs:
                    dc.DrawRectangle(sc*p[0]-self.psfROISize[0]*sc - x0,sc*p[1] - self.psfROISize[1]*sc - y0, 2*self.psfROISize[0]*sc,2*self.psfROISize[1]*sc)
            elif(self.do.slice == self.do.SLICE_XZ):
                for p in self.psfROIs:
                    dc.DrawRectangle(sc*p[0]-self.psfROISize[0]*sc - x0,sc*p[2]*self.aspect - self.psfROISize[2]*sc*self.aspect - y0, 2*self.psfROISize[0]*sc,2*self.psfROISize[2]*sc*self.aspect)
            elif(self.do.slice == self.do.SLICE_YZ):
                for p in self.psfROIs:
                    dc.DrawRectangle(sc*p[1]-self.psfROISize[1]*sc - x0,sc*p[2]*self.aspect - self.psfROISize[2]*sc*self.aspect - y0, 2*self.psfROISize[1]*sc,2*self.psfROISize[2]*sc*self.aspect)


        if len(self.points) > 0:
            #if self.pointsMode == 'confoc':
            pointTol = self.pointTolNFoc[self.pointMode]
            if(self.do.slice == self.do.SLICE_XY):
                pFoc = self.points[abs(self.points[:,2] - self.do.zp) < 1][:,:2]
                if self.pointMode == 'splitter':
                    pCol = self.pointColours[abs(self.points[:,2] - self.do.zp) < 1]
                pNFoc = self.points[abs(self.points[:,2] - self.do.zp) < pointTol[0]][:,:2]

            elif(self.do.slice == self.do.SLICE_XZ):
                pFoc = self.points[abs(self.points[:,1] - self.do.yp) < 1][:, ::2]
                pNFoc = self.points[abs(self.points[:,1] - self.do.yp) < pointTol[1]][:,::2]

            else:#(self.do.slice == self.do.SLICE_YZ):
                pFoc = self.points[abs(self.points[:,0] - self.do.xp) < 1][:, 1:]
                pNFoc = self.points[abs(self.points[:,0] - self.do.xp) < pointTol[2]][:,1:]

            #pFoc = numpy.atleast_1d(pFoc)
            #pNFoc = numpy.atleast_1d(pNFoc)


            dc.SetBrush(wx.TRANSPARENT_BRUSH)

            dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('BLUE'),0))
            for p in pNFoc:
                dc.DrawRectangle(sc*p[0]-2*sc - x0,sc*p[1]*self.aspect - 2*sc*self.aspect - y0, 4*sc,4*sc*self.aspect)

                if self.pointMode == 'splitter' and self.do.slice == self.do.SLICE_XY:
                    dc.DrawRectangle(sc*p[0]-2*sc - x0,sc*(self.do.ds.shape[1] - p[1])*self.aspect - 2*sc*self.aspect - y0, 4*sc,4*sc*self.aspect)


            pGreen = wx.Pen(wx.TheColourDatabase.FindColour('GREEN'),0)
            pRed = wx.Pen(wx.TheColourDatabase.FindColour('RED'),0)
            dc.SetPen(pGreen)
            if self.pointMode == 'splitter' and self.do.slice == self.do.SLICE_XY:
                for p, c in zip(pFoc, pCol):
                    if c:
                        dc.SetPen(pGreen)
                    else:
                        dc.SetPen(pRed)
                    dc.DrawRectangle(sc*p[0]-2*sc - x0,sc*p[1]*self.aspect - 2*sc*self.aspect - y0, 4*sc,4*sc*self.aspect)
                    dc.DrawRectangle(sc*p[0]-2*sc - x0,sc*(self.do.ds.shape[1] - p[1])*self.aspect - 2*sc*self.aspect - y0, 4*sc,4*sc*self.aspect)
            else:
                for p in pFoc:
                    dc.DrawRectangle(sc*p[0]-2*sc - x0,sc*p[1]*self.aspect - 2*sc*self.aspect - y0, 4*sc,4*sc*self.aspect)



#            elif(self.do.slice == self.do.SLICE_XZ):
#                pFoc = self.points[abs(self.points[:,1] - self.do.yp) < 1]
#                pNFoc = self.points[abs(self.points[:,1] - self.do.yp) < pointTol[1]]
#
#
#                dc.SetBrush(wx.TRANSPARENT_BRUSH)
#
#                dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('BLUE'),0))
#                for p in pNFoc:
#                    dc.DrawRectangle(sc*p[0]-2*sc,sc*p[2] - 2*sc, 4*sc,4*sc)
#
#                dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('GREEN'),0))
#                for p in pFoc:
#                    dc.DrawRectangle(sc*p[0]-2*sc,sc*p[2] - 2*sc, 4*sc,4*sc)
#
#            else:#(self.do.slice == self.do.SLICE_YZ):
#                pFoc = self.points[abs(self.points[:,0] - self.do.xp) < 1]
#                pNFoc = self.points[abs(self.points[:,0] - self.do.xp) < pointTol[2] ]
#
#
#                dc.SetBrush(wx.TRANSPARENT_BRUSH)
#
#                dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('BLUE'),0))
#                for p in pNFoc:
#                    dc.DrawRectangle(sc*p[1]-2*sc,sc*p[2] - 2*sc, 4*sc,4*sc)
#
#                dc.SetPen(wx.Pen(wx.TheColourDatabase.FindColour('GREEN'),0))
#                for p in pFoc:
#                    dc.DrawRectangle(sc*p[1]-2*sc,sc*p[2] - 2*sc, 4*sc,4*sc)
            
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.NullBrush)
            
#    def OnPaint(self,event):
#        self.painting = True
#        DC = wx.PaintDC(self.imagepanel)
#        if not time.time() > (self.lastUpdateTime + 2*self.lastFrameTime): #avoid paint floods
#            if not self.refrTimer.IsRunning():
#                self.refrTimer.Start(.2, True) #make sure we do get a refresh after disposing of flood
#            return
#
#        frameStartTime = time.time()
#        self.imagepanel.impanel.PrepareDC(DC)
#
#        x0,y0 = self.imagepanel.CalcUnscrolledPosition(0,0)
#
#        #s = self.imagepanel.GetVirtualSize()
#        s = self.imagepanel.impanel.GetClientSize()
#        MemBitmap = wx.EmptyBitmap(s.GetWidth(), s.GetHeight())
#        #del DC
#        MemDC = wx.MemoryDC()
#        OldBitmap = MemDC.SelectObject(MemBitmap)
#        try:
#            DC.BeginDrawing()
#            #DC.Clear()
#            #Perform(WM_ERASEBKGND, MemDC, MemDC);
#            #Message.DC := MemDC;
#            self.DoPaint(MemDC);
#            #Message.DC := 0;
#            #DC.BlitXY(0, 0, s.GetWidth(), s.GetHeight(), MemDC, 0, 0)
#            DC.Blit(x0, y0, s.GetWidth(), s.GetHeight(), MemDC, 0, 0)
#            DC.EndDrawing()
#        finally:
#            #MemDC.SelectObject(OldBitmap)
#            del MemDC
#            del MemBitmap
#
#        self.lastUpdateTime = time.time()
#        self.lastFrameTime = self.lastUpdateTime - frameStartTime
#
#        self.painting = False
#        #print self.lastFrameTime
            
    def OnWheel(self, event):
        rot = event.GetWheelRotation()
        if rot < 0:
            self.do.zp = max(self.do.zp - 1, 0)
        if rot > 0:
            self.do.zp = min(self.do.zp + 1, self.do.ds.shape[2] -1)
        if ('update' in dir(self.GetParent())):
             self.GetParent().update()
        else:
            self.imagepanel.Refresh()
    
    def OnKeyPress(self, event):
        if event.GetKeyCode() == wx.WXK_PRIOR:
            self.do.zp = max(0, self.do.zp - 1)
            #self.optionspanel.RefreshHists()
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
            else:
                #if not self.painting:
                self.imagepanel.Refresh()
                #else:
                #    if not self.refrTimer.IsRunning():
                #        self.refrTimer.Start(.2, True)

        elif event.GetKeyCode() == wx.WXK_NEXT:
            self.do.zp = min(self.do.zp + 1, self.do.ds.shape[2] - 1)
            #self.optionspanel.RefreshHists()
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
                #print 'upd'
            else:
                #if not self.painting:
                self.imagepanel.Refresh()
                #else:
                #    if not self.refrTimer.IsRunning():
                        #print 'upt'
                #        self.refrTimer.Start(.2, True)
                
        elif event.GetKeyCode() == 74:
            self.do.xp = (self.do.xp - 1)
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
            else:
                self.imagepanel.Refresh()
        elif event.GetKeyCode() == 76:
            self.do.xp +=1
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
            else:
                self.imagepanel.Refresh()
        elif event.GetKeyCode() == 73:
            self.do.yp += 1
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
            else:
                self.imagepanel.Refresh()
        elif event.GetKeyCode() == 75:
            self.do.yp -= 1
            if ('update' in dir(self.GetParent())):
                self.GetParent().update()
            else:
                self.imagepanel.Refresh()
        else:
            event.Skip()
        

        
    def GetOpts(self,event=None):
        if (self.updating == 0):

            sc = pow(2.0,(self.do.scale-2))
            s = self.CalcImSize()
            self.SetVirtualSize(wx.Size(s[0]*sc,s[1]*sc))

            #if not event == None and event.GetId() in [self.cbSlice.GetId(), self.cbScale.GetId()]:
            #recenter the view
            if(self.do.slice == self.do.SLICE_XY):
                lx = self.do.xp
                ly = self.do.yp
                self.aspect = self.do.aspect[1]/self.do.aspect[0]
            elif(self.do.slice == self.do.SLICE_XZ):
                lx = self.do.xp
                ly = self.do.zp
                self.aspect = self.do.aspect[2]/self.do.aspect[0]
            elif(self.do.slice == self.do.SLICE_YZ):
                lx = self.do.yp
                ly = self.do.zp
                self.aspect = self.do.aspect[2]/self.do.aspect[1]

            sx,sy =self.imagepanel.GetClientSize()

            #self.imagepanel.SetScrollbars(20,20,s[0]*sc/20,s[1]*sc/20,min(0, lx*sc - sx/2)/20, min(0,ly*sc - sy/2)/20)
            ppux, ppuy = self.GetScrollPixelsPerUnit()
            #self.imagepanel.SetScrollPos(wx.HORIZONTAL, max(0, lx*sc - sx/2)/ppux)
            #self.imagepanel.SetScrollPos(wx.VERTICAL, max(0, ly*sc - sy/2)/ppuy)
            self.Scroll(max(0, lx*sc - sx/2)/ppux, max(0, ly*sc*self.aspect - sy/2)/ppuy)

            #self.imagepanel.Refresh()
            self.Refresh()
            
    def Optim(self, event = None):
        self.do.Optimise(self.do.ds, int(self.do.zp))
        self.updating=1
        #self.SetOpts()
        #self.optionspanel.RefreshHists()
        self.Refresh()
        self.updating=0
        
    def CalcImSize(self):
        if (self.do.slice == self.do.SLICE_XY):
            if (self.do.orientation == self.do.UPRIGHT):
                return (self.do.ds.shape[0],self.do.ds.shape[1])
            else:
                return (self.do.ds.shape[1],self.do.ds.shape[0])
        elif (self.do.slice == self.do.SLICE_XZ):
            return (self.do.ds.shape[0],self.do.ds.shape[2])
        else:
            return(self.do.ds.shape[1],self.do.ds.shape[2] )
        
    def DoNix(self, event):
        pass
    
            
    def OnLeftClick(self,event):
        dc = wx.ClientDC(self.imagepanel)
        self.imagepanel.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos = self.CalcUnscrolledPosition(*pos)

        #print pos
        sc = pow(2.0,(self.do.scale-2))
        if (self.do.slice == self.do.SLICE_XY):
            self.do.xp =int(pos[0]/sc)
            self.do.yp = int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_XZ):
            self.do.xp =int(pos[0]/sc)
            self.do.zp =int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_YZ):
            self.do.yp =int(pos[0]/sc)
            self.do.zp =int(pos[1]/(sc*self.aspect))
        if ('update' in dir(self.GetParent())):
             self.GetParent().update()
        else:
            self.imagepanel.Refresh()

    def PointsHitTest(self):
        if len(self.points) > 0:
            iCand = numpy.where((abs(self.points[:,2] - self.do.zp) < 1)*(abs(self.points[:,0] - self.do.xp) < 3)*(abs(self.points[:,1] - self.do.yp) < 3))[0]

            if len(iCand) == 0:
                return None
            elif len(iCand) == 1:
                return iCand[0]
            else:
                pCand = self.points[iCand, :]

                iNearest = numpy.argmin((pCand[:,0] - self.do.xp)**2 + (pCand[:,1] - self.do.yp)**2)

                return iCand[iNearest]
        else:
            return None



            
    def OnRightDown(self,event):
        dc = wx.ClientDC(self.imagepanel)
        self.imagepanel.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos = self.CalcUnscrolledPosition(*pos)
        print pos
        sc = pow(2.0,(self.do.scale-2))
        if (self.do.slice == self.do.SLICE_XY):
            self.selection_begin_x = int(pos[0]/sc)
            self.selection_begin_y = int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_XZ):
            self.selection_begin_x = int(pos[0]/sc)
            self.selection_begin_z = int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_YZ):
            self.selection_begin_y = int(pos[0]/sc)
            self.selection_begin_z = int(pos[1]/(sc*self.aspect))
            
    def OnRightUp(self,event):
        dc = wx.ClientDC(self.imagepanel)
        self.imagepanel.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos = self.CalcUnscrolledPosition(*pos)
        print pos
        sc = pow(2.0,(self.do.scale-2))
        if (self.do.slice == self.do.SLICE_XY):
            self.selection_end_x = int(pos[0]/sc)
            self.selection_end_y = int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_XZ):
            self.selection_end_x = int(pos[0]/sc)
            self.selection_end_z = int(pos[1]/(sc*self.aspect))
        elif (self.do.slice == self.do.SLICE_YZ):
            self.selection_end_y = int(pos[0]/sc)
            self.selection_end_z = int(pos[1]/(sc*self.aspect))
        if ('update' in dir(self.GetParent())):
             self.GetParent().update()
        else:
            self.imagepanel.Refresh()
            
    def ResetSelection(self):
        self.selection_begin_x = 0
        self.selection_begin_y = 0
        self.selection_begin_z = 0
        
        self.selection_end_x = self.do.ds.shape[0] - 1
        self.selection_end_y = self.do.ds.shape[1] - 1
        self.selection_end_z = self.do.ds.shape[2] - 1
        
    def SetSelection(self, (b_x,b_y,b_z),(e_x,e_y,e_z)):
        self.selection_begin_x = b_x
        self.selection_begin_y = b_y
        self.selection_begin_z = b_z
        
        self.selection_end_x = e_x
        self.selection_end_y = e_y
        self.selection_end_z = e_z
        
#    def Render(self):
#        x0,y0 = self.imagepanel.CalcUnscrolledPosition(0,0)
#        sX, sY = self.imagepanel.Size
#
#        sc = pow(2.0,(self.do.scale-2))
#        sX_ = int(sX/sc)
#        sY_ = int(sY/sc)
#        x0_ = int(x0/sc)
#        y0_ = int(y0/sc)
#
#        #XY
#        if self.do.slice == DisplayOpts.SLICE_XY:
#            if self.do.Chans[0] < self.do.ds.shape[3]:
#                r = (self.do.Gains[0]*(self.do.ds[x0_:(x0_+sX_),y0_:(y0_+sY_),int(self.do.zp), self.do.Chans[0]] - self.do.Offs[0])).astype('uint8').squeeze().T
#            else:
#                r = numpy.zeros(ds.shape[:2], 'uint8').T
#            if self.do.Chans[1] < self.do.ds.shape[3]:
#                g = (self.do.Gains[1]*(self.do.ds[x0_:(x0_+sX_),y0_:(y0_+sY_),int(self.do.zp), self.do.Chans[1]] - self.do.Offs[1])).astype('uint8').squeeze().T
#            else:
#                g = numpy.zeros(ds.shape[:2], 'uint8').T
#            if self.do.Chans[2] < self.do.ds.shape[3]:
#                b = (self.do.Gains[2]*(self.do.ds[x0_:(x0_+sX_),y0_:(y0_+sY_),int(self.do.zp), self.do.Chans[2]] - self.do.Offs[2])).astype('uint8').squeeze().T
#            else:
#                b = numpy.zeros(ds.shape[:2], 'uint8').T
#        #XZ
#        elif self.do.slice == DisplayOpts.SLICE_XZ:
#            if self.do.Chans[0] < self.do.ds.shape[3]:
#                r = (self.do.Gains[0]*(self.do.ds[x0_:(x0_+sX_),int(self.do.yp),y0_:(y0_+sY_), self.do.Chans[0]] - self.do.Offs[0])).astype('uint8').squeeze().T
#            else:
#                r = numpy.zeros((ds.shape[0], ds.shape[2]), 'uint8').T
#            if self.do.Chans[1] < self.do.ds.shape[3]:
#                g = (self.do.Gains[1]*(self.do.ds[x0_:(x0_+sX_),int(self.do.yp),y0_:(y0_+sY_), self.do.Chans[1]] - self.do.Offs[1])).astype('uint8').squeeze().T
#            else:
#                g = numpy.zeros((ds.shape[0], ds.shape[2]), 'uint8').T
#            if self.do.Chans[2] < self.do.ds.shape[3]:
#                b = (self.do.Gains[2]*(self.do.ds[x0_:(x0_+sX_),int(self.do.yp),y0_:(y0_+sY_), self.do.Chans[2]] - self.do.Offs[2])).astype('uint8').squeeze().T
#            else:
#                b = numpy.zeros((ds.shape[0], ds.shape[2]), 'uint8'.T)
#
#        #YZ
#        elif self.do.slice == DisplayOpts.SLICE_YZ:
#            if self.do.Chans[0] < self.do.ds.shape[3]:
#                r = (self.do.Gains[0]*(self.do.ds[int(self.do.xp),x0_:(x0_+sX_),y0_:(y0_+sY_), self.do.Chans[0]] - self.do.Offs[0])).astype('uint8').squeeze().T
#            else:
#                r = numpy.zeros((ds.shape[1], ds.shape[2]), 'uint8').T
#            if self.do.Chans[1] < self.do.ds.shape[3]:
#                g = (self.do.Gains[1]*(self.do.ds[int(self.do.xp),x0_:(x0_+sX_),y0_:(y0_+sY_), self.do.Chans[1]] - self.do.Offs[1])).astype('uint8').squeeze().T
#            else:
#                g = numpy.zeros((ds.shape[1], ds.shape[2]), 'uint8').T
#            if self.do.Chans[2] < self.do.ds.shape[3]:
#                b = (self.do.Gains[2]*(self.do.ds[int(self.do.xp),x0_:(x0_+sX_),y0_:(y0_+sY_), self.do.Chans[2]] - self.do.Offs[2])).astype('uint8').squeeze().T
#            else:
#                b = numpy.zeros((ds.shape[1], ds.shape[2]), 'uint8'.T)
#        r = r.T
#        g = g.T
#        b = b.T
#        r = r.reshape(r.shape + (1,))
#        g = g.reshape(g.shape + (1,))
#        b = b.reshape(b.shape + (1,))
#        ima = numpy.concatenate((r,g,b), 2)
#        return wx.ImageFromData(ima.shape[1], ima.shape[0], ima.ravel())

    def Render(self):
        x0,y0 = self.CalcUnscrolledPosition(0,0)
        sX, sY = self.imagepanel.Size

        aspect = {}

        sc = pow(2.0,(self.do.scale-2))
        sX_ = int(sX/sc)
        sY_ = int(sY/(sc*self.aspect))
        x0_ = int(x0/sc)
        y0_ = int(y0/(sc*self.aspect))

        #XY
        if self.do.slice == DisplayOpts.SLICE_XY:
            ima = numpy.zeros((min(sY_, self.do.ds.shape[1]), min(sX_, self.do.ds.shape[0]), 3), 'uint8')
            for chan, offset, gain, cmap in zip(self.do.Chans, self.do.Offs, self.do.Gains, self.do.cmaps):
                ima[:] = numpy.minimum(ima[:] + (255*cmap(gain*(self.do.ds[x0_:(x0_+sX_),y0_:(y0_+sY_),int(self.do.zp), chan].squeeze().T - offset))[:,:,:3])[:], 255)
        #XZ
        elif self.do.slice == DisplayOpts.SLICE_XZ:
            ima = numpy.zeros((min(sY_, self.do.ds.shape[2]), min(sX_, self.do.ds.shape[0]), 3), 'uint8')

            for chan, offset, gain, cmap in zip(self.do.Chans, self.do.Offs, self.do.Gains, self.do.cmaps):
                ima[:] = ima[:] + 255*cmap(gain*(self.do.ds[x0_:(x0_+sX_),int(self.do.yp),y0_:(y0_+sY_), chan].squeeze().T - offset))[:,:,:3][:]

        #YZ
        elif self.do.slice == DisplayOpts.SLICE_YZ:
            ima = numpy.zeros((min(sY_, self.do.ds.shape[2]), min(sX_, self.do.ds.shape[1]), 3), 'uint8')

            for chan, offset, gain, cmap in zip(self.do.Chans, self.do.Offs, self.do.Gains, self.do.cmaps):
                ima[:] = ima[:] + 255*cmap(gain*(self.do.ds[int(self.do.xp),x0_:(x0_+sX_),y0_:(y0_+sY_), chan].squeeze().T - offset))[:,:,:3][:]
#        
        return wx.ImageFromData(ima.shape[1], ima.shape[0], ima.ravel())


    def GetProfile(self,halfLength=10,axis = 2, pos=None, roi=[2,2], background=None):
        if not pos == None:
            px, py, pz = pos
        else:
            px, py, pz = self.do.xp, self.do.yp, self.do.zp

        points = self.points
        d = None
        pts = None

        if axis == 2: #z
            p = self.do.ds[(px - roi[0]):(px + roi[0]),(py - roi[1]):(py + roi[1]),(pz - halfLength):(pz + halfLength)].mean(2).mean(1)
            x = numpy.mgrid[(pz - halfLength):(pz + halfLength)]
            if len(points) > 0:
                d = numpy.array([((abs(points[:,0] - px) < 2*roi[0])*(abs(points[:,1] - py) < 2*roi[1])*(points[:,2] == z)).sum() for z in x])

                pts = numpy.where((abs(points[:,0] - px) < 2*roi[0])*(abs(points[:,1] - py) < 2*roi[1])*(abs(points[:,2] - pz) < halfLength))
            #print p.shape
            #p = p.mean(1).mean(0)
            if not background == None:
                p -= self.do.ds[(px - background[0]):(px + background[0]),(py - background[1]):(py + background[1]),(pz - halfLength):(pz + halfLength)].mean(2).mean(1)
        elif axis == 1: #y
            p = self.do.ds[(px - roi[0]):(px + roi[0]),(py - halfLength):(py + halfLength),(pz - roi[1]):(pz + roi[1])].mean(1).mean(0)
            x = numpy.mgrid[(py - halfLength):(py + halfLength)]
            if len(points) > 0:
                d = numpy.array([((abs(points[:,1] - py) < 2*roi[0])*(abs(points[:,2] - pz) < 2*roi[1])*(points[:,0] == z)).sum() for z in x])

                pts = numpy.where((abs(points[:,0] - px) < 2*roi[0])*(abs(points[:,1] - py) < halfLength)*(abs(points[:,2] - pz) < 2*roi[1]))
            if not background == None:
                p -= self.do.ds[(px - background[0]):(px + background[0]),(py - halfLength):(py + halfLength),(pz - background[1]):(pz + background[1]),(pz - halfLength):(pz + halfLength)].mean(1).mean(0)
        elif axis == 0: #x
            p = self.do.ds[(px - halfLength):(px + halfLength), (py - roi[0]):(py + roi[0]),(pz - roi[1]):(pz + roi[1])].mean(2).mean(0)
            x = numpy.mgrid[(px - halfLength):(px + halfLength)]
            if len(points) > 0:
                d = numpy.array([((abs(points[:,0] - px) < 2*roi[0])*(abs(points[:,2] - pz) < 2*roi[1])*(points[:,1] == z)).sum() for z in x])

                pts = numpy.where((abs(points[:,0] - px) < halfLength)*(abs(points[:,1] - py) < 2*roi[0])*(abs(points[:,2] - pz) < 2*roi[1]))
            if not background == None:
                p -= self.do.ds[(px - halfLength):(px + halfLength),(py - background[0]):(py + background[0]),(pz - background[1]):(pz + background[1])].mean(2).mean(0)

        return x,p,d, pts
# end of class ViewPanel

class ArraySettingsAndViewPanel(wx.Panel):
    def __init__(self, parent, dstack = None, aspect=1, horizOptions = False, **kwds):
        kwds["style"] = wx.TAB_TRAVERSAL
        wx.Panel.__init__(self, parent, **kwds)
        self.showOptsPanel = 1

        vpsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.view = ArrayViewPanel(self, dstack, aspect)
        #self.imagepanel.SetMinSize((50,50))
        #self.imagepanel.SetScrollRate(10, 10)
        vpsizer.Add(self.view, 1, wx.EXPAND, 0)

        self.bShowOpts = wx.Button(self, -1, "", size=wx.Size(7,-1))
        vpsizer.Add(self.bShowOpts, 0, wx.EXPAND, 0)

        self.do = self.view.do

        self.optionspanel = OptionsPanel(self, self.view.do,horizOrientation = horizOptions)
        #self.optionspanel = wx.ScrolledWindow(self, -1)
        #self.optionspanel.SetScrollRate(10, 10)
        vpsizer.Add(self.optionspanel, 0, wx.EXPAND, 0)


        self.SetSizer(vpsizer)
        self.updating = False

        wx.EVT_BUTTON(self, self.bShowOpts.GetId(), self.ShowOpts)

    def update(self):
        if not self.updating:
            self.updating = True
            self.view.Refresh()
            if ('update' in dir(self.GetParent())):
                 self.GetParent().update()
            self.updating = False

    def ShowOpts(self, event):
        if (self.showOptsPanel == 1):
            self.showOptsPanel = 0
            self.GetSizer().Show(self.optionspanel, 0)
            self.Layout()
        else:
            self.showOptsPanel = 1
            self.GetSizer().Show(self.optionspanel, 1)
            self.Layout()
        