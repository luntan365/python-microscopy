#!/usr/bin/python
##################
# blobFinding.py
#
# Copyright David Baddeley, 2011
# d.baddeley@auckland.ac.nz
#
# This file may NOT be distributed without express permision from David Baddeley
#
##################

import wx
from PYME.Acquire.mytimer import mytimer

class deconvolver:
    def __init__(self, dsviewer):
        self.dsviewer = dsviewer

        self.image = dsviewer.image

        DECONV_ICTM = wx.NewId()
        DECONV_SAVE = wx.NewId()
        dsviewer.mExtras.Append(DECONV_ICTM, "ICTM Deconvolution", "", wx.ITEM_NORMAL)
        #mDeconvolution.AppendSeparator()
        dsviewer.save_menu.Append(DECONV_SAVE, "Deconvolution", "", wx.ITEM_NORMAL)
        #self.menubar.Append(mDeconvolution, "Deconvolution")

        wx.EVT_MENU(dsviewer, DECONV_ICTM, self.OnDeconvICTM)
        wx.EVT_MENU(dsviewer, DECONV_SAVE, self.saveDeconvolution)

        dsviewer.updateHooks.append(self.update)

    def OnDeconvICTM(self, event):
        from PYME.Deconv.deconvDialogs import DeconvSettingsDialog,DeconvProgressDialog

        dlg = DeconvSettingsDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            from PYME.Deconv import dec, decThread
            nIter = dlg.GetNumIterationss()
            regLambda = dlg.GetRegularisationLambda()

            self.dlgDeconProg = DeconvProgressDialog(self.dsviewer, nIter)
            self.dlgDeconProg.Show()

            psf, vs = numpy.load(dlg.GetPSFFilename())

            self.dec = dec.dec_conv()
            self.dec.psf_calc(psf, self.image.data.shape)

            self.decT = decThread.decThread(self.dec, self.image.data.ravel(), regLambda, nIter)
            self.decT.start()

            self.deconTimer = mytimer()
            self.deconTimer.WantNotification.append(self.OnDeconTimer)

            self.deconTimer.Start(100)


    def OnDeconEnd(self, sucess):
        self.dlgDeconProg.Destroy()
        if sucess:
            if 'decvp' in dir(self):
                for pNum in range(self.dsviewer.notebook1.GetPageCount()):
                    if self.dsviewer.notebook1.GetPage(pNum) == self.decvp:
                        self.dsviewer.notebook1.DeletePage(pNum)
            self.decvp = MyViewPanel(self.dsviewer.notebook1, self.decT.res)
            self.dsviewer.notebook1.AddPage(page=self.decvp, select=True, caption='Deconvolved')


    def OnDeconTimer(self, caller=None):
        if self.decT.isAlive():
            if not self.dlgDeconProg.Tick(self.dec):
                self.decT.kill()
                self.OnDeconEnd(False)
        else:
            self.deconTimer.Stop()
            self.OnDeconEnd(True)

    def saveDeconvolution(self, event=None):
        fdialog = wx.FileDialog(None, 'Save Positions ...',
            wildcard='TIFF Files|*.tif', defaultFile=os.path.splitext(self.seriesName)[0] + '_dec.tif', style=wx.SAVE|wx.HIDE_READONLY)
        succ = fdialog.ShowModal()
        if (succ == wx.ID_OK):
            outFilename = fdialog.GetPath()

            from PYME.FileUtils import saveTiffStack

            saveTiffStack.saveTiffMultipage(self.dec.res, outFilename)

    def update(self):
        if 'decvp' in dir(self):
            self.decvp.imagepanel.Refresh()

def Plug(dsviewer):
    dsviewer.devoncolver = deconvolver(dsviewer)