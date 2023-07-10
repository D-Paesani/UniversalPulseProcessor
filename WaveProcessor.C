#pragma once
using namespace std; 

#include "WaveProcessor.h"
#define ANA_CLASS_NAME WaveProcessor

void ANA_CLASS_NAME::Begin() { 
   
   Msg("");
   Msg(Form("runName: %s", conf.runName.Data()));
   Msg(Form("inFile: %s", conf.inFileName.Data()));
   Msg(Form("outFile: %s", conf.outFileName.Data()));
   Msg(Form("anaFile: %s", conf.anaFileName.Data()));

   if (conf.inTree == 0) {

      if (conf.inFile == 0) {
         conf.inFile = new TFile(conf.inFileName); 
      } 

      conf.inFile->GetObject(conf.inTreeName, conf.inTree); 
   }

   conf.inTreeEntries = conf.inTree->GetEntriesFast();
   conf.etp = conf.evLimit < 0 ? (Long64_t)conf.inTreeEntries : min((Long64_t)conf.evLimit, (Long64_t)conf.inTreeEntries); 

   if (conf.outFile == nullptr) {
      conf.outFile = new TFile(conf.outFileName, "RECREATE");
   }  
   Msg(Form("Tree entries: %lld", conf.inTreeEntries));
   Msg(Form("Events to process: %lld", conf.etp));
   
   conf.anaFile = new TFile(conf.anaFileName, "RECREATE");
   conf.outFile = new TFile(conf.outFileName, "RECREATE");
   conf.outFile ->cd();
   conf.outTree = new TTree(conf.outTreeName, conf.outTreeName);
   
   Msg("---------------- WaveMap ----------------"); 
   for(Waves::WaveBox *ww: waves.wlist) { 
      ostringstream ss; 
      ss<<"["<<Form(ww->inFormat,ww->inChan[0])<<" ... "<<Form(ww->inFormat,ww->inChan[ww->nChan-1])<<"] -> ["
      <<Form(ww->outFormat,ww->outChan[0])<<" ... "<<Form(ww->outFormat,ww->outChan[ww->nChan-1])<<"]";
      Msg(ss.str());      
   }
   Msg("---------------- WaveMap ----------------");
   Msg("");

   waves.branchAll(conf.inTree, conf.outTree);

}

void ANA_CLASS_NAME::Terminate() {

   conf.outFile->cd();
   // conf.outTree->CloneTree()->Write();
   conf.outTree->Write();
   conf.outFile->Close();

   conf.anaFile->Close();

   Msg("\n");
   Msg(Form("      outFile: \n         root %s", conf.outFileName.Data()));
   Msg(Form("      anaFile: \n         root %s", conf.anaFileName.Data()));

}

void ANA_CLASS_NAME::Loop() {  
   
  Long64_t nbytes = 0, nb = 0; 
  Long64_t evmod = conf.etp / 9;

  for (Long64_t jentry=0; jentry<conf.etp; jentry++) { 

      Long64_t ientry = conf.inTree->LoadTree(jentry); 
      if (ientry < 0) {break;}
      nb = conf.inTree->GetEntry(jentry); 
      nbytes += nb;
      if (!(jentry%evmod)) { 
         Msg( Form( "    processing evt %lld / %lld  ( %.0f%% )", jentry, conf.etp, (float)(100*jentry/conf.etp) ) );
      }
      LoopEntries(jentry);
  } 
}




