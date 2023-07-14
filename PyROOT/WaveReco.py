import ROOT, uproot
import awkward as ak
import scipy.signal
import numpy as np
import types
from tqdm import tqdm

class WaveReco:
    
    inTreeName,outTreeName,inFileName,outFileName,anaFileName= None, None, None, None, None
    inTree,outTree,outFile,anaFile,inFile = None, None, None, None, None
    UserBegin, UserLoop, UserTerminate = None, None, None
    spline_t = ROOT.TSpline3
    maxEvents = -1
    specsToSave = 10
    dryRun = False
    saveEventNumber=None
    waveF = ""
    wboxes = []        
    lowPassFilter = "butt"
    lowPassOrder = 2
    gignoreLevel = ROOT.kFatal
    
    @staticmethod 
    def MkBranch(tree, varName, varType = 'd', varDims=None):
        var = np.zeros(varDims if varDims != None else 1, dtype=varType)
        tree.Branch(varName, var, F"{varName}{str.join('', [F'[{ii}]' for ii in varDims]) if varDims != None else ''}/{varType.capitalize()}")
        return var      

    def Msg(self, msg, err=False):
        print(F"      WaveReco: {'ERROR:' if err else ''}{msg}")   
    
    class Digi_t():
        def __init__(self, wSz = 1024, wFs = 4096, wAmpFs = 1000, tBin = 0.2, aErr = 0.15, tErr = 0.0, name = "digi", inZ = 50.0, varTyp=np.ushort):
            self.name,self.wSz,self.wFs,self.wAmpFs,self.tBin,self.tErr,self.aErr,self.inZ,self.varTyp=name,wSz,wFs,wAmpFs,tBin,tErr,aErr,inZ,varTyp
            self.compute()
            self.wTimeBooked = False
        def compute(self):
            self.wTimSz = float(self.wSz)*self.tBin
            self.aBin = float(self.wAmpFs)/float(self.wFs)
        def BookOutput(self, tout):
            if self.wTimeBooked: return
            self.wtime = self.tBin * np.arange(0,self.wSz,1)
            bname = self.name + "_wtim"
            tout.Branch(bname, self.wtime, F"{bname}[{self.wSz}]/F") 
            
    class WaveBox_t():

        def __init__(self, digi, inWvs, bRng, qRng, spRng, outNam, pkRng=None, pkCut=None, saveW=True, saveTemplate=False,
                            lowPass=None, cfScan=None, cf=0.1, gain=1.0, opts=None, thr=None, thrScan=None):

            self.digi,self.inWvs,self.qRng,self.bRng,self.spRng,self.spRng,self.outNam,self.pkRng,self.pkCut,\
            self.saveW,self.lowPass,self.cfScan,self.cf,self.gain,self.opts,self.thr,self.thrScan,self.saveTemplate=\
            digi,inWvs,qRng,bRng,spRng,spRng,outNam,pkRng,pkCut,saveW,lowPass,cfScan,cf,gain,opts,thr,thrScan,saveTemplate

            self.nChan = len(self.inWvs)
            self.sign = float(self.gain<0)
            self.waveIn = []
            self.addbase = - self.digi.wFs if self.sign < 0 else 0.0
            self.bRngSam = np.array(np.array(bRng, dtype=float) / self.digi.tBin, dtype=int)
            self.qRngSam = np.array(np.array(qRng, dtype=float) / self.digi.tBin, dtype=int)
            self.spRngSam = np.array(np.array(spRng, dtype=float) / self.digi.tBin, dtype=int)
            self.specSaved = 0

        def BookOutput(self, tout):
            
            if self.saveTemplate != None:
                pass
            
            self.digi.BookOutput(tout)
            
            self.b_bline =  WaveReco.MkBranch(tout, self.outNam+"_bline", "d", [self.nChan])
            self.b_brms =   WaveReco.MkBranch(tout, self.outNam+"_brms", "d", [self.nChan])
            self.b_peak =   WaveReco.MkBranch(tout, self.outNam+"_peak", "d", [self.nChan])
            self.b_charge = WaveReco.MkBranch(tout, self.outNam+"_charge", "d", [self.nChan])
            self.b_timcf =  WaveReco.MkBranch(tout, self.outNam+"_timcf", "d", [self.nChan])
            self.b_timtr =  WaveReco.MkBranch(tout, self.outNam+"_timtr", "d", [self.nChan])
            self.b_timpk =  WaveReco.MkBranch(tout, self.outNam+"_timpk", "d", [self.nChan])
            self.b_wok   =  WaveReco.MkBranch(tout, self.outNam+"_wok", "i", [self.nChan])
            
            if self.saveW:
                self.b_wave = WaveReco.MkBranch(tout, self.outNam+"_wav", "f", [self.nChan, self.digi.wSz])
            
            if self.cfScan != None:
                self.b_cfscan = WaveReco.MkBranch(tout, self.outNam+"_cfscan", "d", [self.nChan, len(self.cfScan)])
            
            if self.thrScan != None:
                self.b_trscan = WaveReco.MkBranch(tout, self.outNam+"_trscan", "d", [self.nChan, len(self.thrScan)])
            
        def BookInput(self, tin):
            self.waveIn = []
            for ii in self.inWvs:
                self.waveIn.append(ak.to_numpy(tin[ii].array()))
                        
    def Begin(self):
        
        if self.anaFileName == "" : self.anaFileName = None
        if self.outTreeName == "" or self.outTreeName == None : self.outTreeName = self.inTreeName
        self.inFile = uproot.open(self.inFileName)
        self.inTree = self.inFile[self.inTreeName]
        self.outFile = ROOT.TFile(self.outFileName, "recreate")
        self.anaFile = ROOT.TFile(self.anaFileName, "recreate") if self.anaFileName != None else self.outFile
        self.outFile.cd()
        self.outTree = ROOT.TTree(self.outTreeName, self.outTreeName) 
        
    def Terminate(self):
        
        self.outFile.cd()
        self.outTree.Write()
        self.outFile.Close()
        if self.anaFileName != None : self.anaFile.Close()
    
    def Book(self):
        self.b_evt = WaveReco.MkBranch(self.outTree, "evt", "i")
        
        for ii in self.wboxes:
            ii.BookInput(self.inTree)
            ii.BookOutput(self.outTree)
  
    def Launch(self):
        
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("---------------------------- Universal Wave Reco -----------------------------")
        self.Msg("------------------------ daniele.paesani@lnf.infn.it -------------------------")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("------------------------------------------------------------------------------")       
        self.Msg(F"                           --- channel map ---")
        ii: self.WaveBox_t
        for iii, ii in enumerate(self.wboxes): 
            self.Msg(F"  {iii}{' '*(5-len(str(iii)))}   {ii.digi.name} {' '*(12-len(ii.digi.name))}[{ii.inWvs[0]} ... {ii.inWvs[-1]}] {'-'*(25-len(ii.inWvs[-1])-len(ii.inWvs[0]))}->  {ii.outNam}[{ii.nChan}]")
        self.Msg(F"                         --- channel map end ---")
        self.Msg(F"input:   {self.inFileName}")
        self.Msg(F"output:  {self.outFileName}")
        self.Msg(F"ana:     {self.anaFileName}")
        if (self.dryRun) : 
            self.Msg(F"end of dry run")
            self.Msg("------------------------------------------------------------------------------")
            return
        self.Msg("starting...")
        self.Begin()
        if self.UserBegin != None: self.UserBegin() 
        self.Msg("booking io...") 
        self.Book()
        self.entries = len(self.wboxes[0].waveIn[0])
        self.Msg(F"entries: {self.entries}")
        self.etp = min(self.entries, self.maxEvents) if self.maxEvents > 0  else self.entries
        self.Msg(F"to process: {self.etp}")
        self.Msg("starting loop...") 
        prev = ROOT.gErrorIgnoreLevel
        gErrorIgnoreLevel = self.gignoreLevel
        self.LoopEntries()
        gErrorIgnoreLevel = prev
        self.Msg("terminating...") 
        self.Terminate()
        if self.UserTerminate != None: self.UserTerminate() 
        self.Msg("processing done")
        self.Msg("------------------------------------------------------------------------------")
        self.Msg("---------------------------- Universal Wave Reco -----------------------------")
        self.Msg("------------------------------------------------------------------------------\n\n")
        
    def LoopEntries(self):

        savedSpecs = 0
                
        for ientry in tqdm(range(self.etp), colour='green', bar_format='{desc:<5.5}{percentage:3.0f}%|{bar:45}{r_bar:10}'):
            self.b_evt[0] = ientry
            for ibox, box in enumerate(self.wboxes):
                        
                gain = box.gain
                sign = box.sign
                wsize = box.digi.wSz
                addbase = box.addbase
                digi = box.digi
                digi: WaveReco.Digi_t
                wtime = digi.wtime.astype(np.float32)
                wzeros, wones = np.zeros(wsize).astype(np.float32),np.ones(wsize).astype(np.float32)
    
                if box.lowPass != None: 
                    if self.lowPassFilter == "butt":
                        lopanum, lopaden = scipy.signal.butter(N=self.lowPassOrder, Wn=box.lowPass, btype="low", fs=1.0/digi.tBin)
                    
                if box.pkRng != None: pkstart, pkstop = int(box.pkRng[0]*digi.wSz), int(box.pkRng[1]*digi.wSz)
                else: pkstart, pkstop = 0, -1
                    
                for iwave, win in enumerate(box.waveIn):
                    
                    box.b_wok[iwave] = 0
                    wave = win[ientry]
                    wave = np.multiply(np.add(wave, addbase), gain * digi.aBin)
                    ipeak = pkstart + np.argmax(wave[pkstart:pkstop])
                    peak = wave[ipeak]
                    
                    if box.lowPass != None: 
                        wave_raw = wave.copy()
                        wave = scipy.signal.filtfilt(lopanum, lopaden, wave)
                        
                    wbline = wave[ max(int(ipeak+box.bRngSam[0]),0) : min(int(ipeak+box.bRngSam[1]),wsize) ]
                    if len(wbline) == 0: continue
                    bline,brms = wbline.mean(),wbline.std()
                    peak = peak - bline
                    if box.pkCut != None:
                        if (box.pkCut[0]!=None and peak<box.pkCut[0]): continue
                        if (box.pkCut[1]!=None and peak>box.pkCut[1]): continue
                    wave = np.add(wave, -bline)
                    wcharge = wave[ max(int(ipeak+box.qRngSam[0]),0) : min(int(ipeak+box.qRngSam[1]),wsize) ]
                    if len(wcharge) == 0: continue
                    charge = np.sum(wcharge)*digi.tBin/digi.inZ
                    gra = ROOT.TGraphErrors(wsize, wtime, wave.astype(np.float32), wzeros, np.multiply(wones, brms))
                    tpeak = ipeak*digi.tBin        
                    
                    spfrom, spto = tpeak+box.spRng[0], tpeak+box.spRng[1]
                    wspline = self.spline_t("wspline", gra)
                    def ffwspline(x, p): return wspline.Eval(x[0])
                    fwspline = ROOT.TF1("fwspline", ffwspline, spfrom, spto, 0)
                    peak = fwspline.GetMaximum(spfrom, spto)
                    tpeak = fwspline.GetMaximumX(spfrom, spto)
                    tcf = fwspline.GetX(peak*box.cf)
                    ttr = fwspline.GetX(box.thr) if box.thr != None else -9999.99
                    
                    box.b_bline[iwave] = bline
                    box.b_brms[iwave] = brms
                    box.b_charge[iwave] = charge
                    box.b_peak[iwave] = peak
                    box.b_timpk[iwave] = tpeak
                    box.b_timcf[iwave] = tcf
                    box.b_timtr[iwave] = ttr
                    box.b_wok[iwave] = 1
                    
                    if (box.saveW): box.b_wave[iwave][:] = wave
                    if (box.cfScan != None):  box.b_cfscan[iwave][:] = np.array([fwspline.GetX(peak*icf) for icf in box.cfScan])       
                    if (box.thrScan != None): box.b_trscan[iwave][:] = np.array([fwspline.GetX(itr) for itr in box.thrScan])       

                    if (box.specSaved < self.specsToSave):
                        riset = fwspline.GetX(0.9*peak) - fwspline.GetX(0.1*peak)
                        box.specSaved +=1
                        self.anaFile.mkdir("specimens", "", 1).mkdir(box.outNam,"", 1).cd()
                        title = F"ev{ientry}_{box.outNam}{iwave}"
                        cc = ROOT.TCanvas(title)
                        
                        if box.lowPass != None: 
                            cc.Divide(1,2)
                            cc.cd(2)
                            graraw = ROOT.TGraphErrors(wsize, wtime, (np.add(wave_raw, -bline)).astype(np.float32), wzeros, np.multiply(wones, brms))
                            graraw.SetTitle(F"unfiltered waveform;tim [ns]; amp [mV]")
                            graraw.SetLineWidth(1); graraw.SetMarkerStyle(20); graraw.SetMarkerSize(0.25); graraw.SetMarkerColor(ROOT.kBlue); graraw.Draw("AP"); 
                            cc.cd(1)
                            
                        gra.SetTitle(F"event: {ientry}   chan: {box.outNam}{iwave};tim [ns]; amp [mV]")
                        gra.SetLineWidth(1); gra.SetMarkerStyle(20); gra.SetMarkerSize(0.25); gra.SetMarkerColor(ROOT.kBlack); gra.Draw("AP"); 
                        fwspline.SetLineColor(ROOT.kViolet); fwspline.Draw("same")
                        
                        for ii, iic in zip([tpeak, tcf], [ROOT.kRed, ROOT.kRed]):
                            tp = ROOT.TMarker(ii, fwspline.Eval(ii), 2)
                            tp.SetMarkerSize(3); tp.SetMarkerColor(iic); tp.DrawClone("same")
                        
                        if box.thr != None: 
                            tp = ROOT.TMarker(ttr, fwspline.Eval(ttr), 2)
                            tp.SetMarkerSize(3); tp.SetMarkerColor(ROOT.kOrange+2); tp.DrawClone("same")
                            
                        for ii, iic, iia in zip([box.bRng,box.qRng,box.spRng,[-tpeak+box.pkRng[jj]*digi.wTimSz for jj in range(2)]], [ROOT.kOrange+2,ROOT.kBlue,ROOT.kGreen,ROOT.kYellow], [0.25*peak, 0.5*peak, 0.6*peak, 0.8*peak]):
                            for iii in range(2):
                                vv = max(0.0, min(tpeak+ii[iii], digi.wTimSz))
                                tt = ROOT.TLine(vv,-0.05*peak,vv,iia)
                                tt.SetLineWidth(1); tt.SetLineStyle(1); tt.SetLineColor(iic); tt.DrawClone("same")
                            vv1, vv2 = max(0.0, tpeak+ii[0]), min(tpeak+ii[1], digi.wTimSz)
                            aa = ROOT.TArrow(vv1, iia, vv2, iia, 0.01, "<>")
                            aa.SetLineStyle(1); aa.SetLineWidth(1); aa.SetLineColor(iic); aa.DrawClone("same")
                            
                        pt = ROOT.TPaveText(0.7,0.65,0.95,0.97, "NB NDC ARC") 
                        pt.SetFillColor(0)
                        pt.SetLineColor(0)
                        ptnams = ["bline [mV]", "brms [mV]", "peak [mV]", "charge [pC]", "timpk [ns]", "timcf [ns]", "timtr [ns]", "riset [ns]"]
                        ptvars = [bline, brms, peak, charge, tpeak, tcf, ttr, riset]
                        for ii, iii in zip(ptnams, ptvars):
                            pt.AddText(F"{ii}:   {iii:.2f}")
                        pt.SetAllWith("]", "align", 22)
                        pt.SetAllWith("]", "size", 25)
                        pt.Draw("same")
                        
                        cc.Write()
                        self.outFile.cd()
                        
            self.outTree.Fill()
            if self.UserLoop != None: self.UserLoop()   




                    





