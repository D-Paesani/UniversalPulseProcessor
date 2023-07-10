#pragma once
using namespace std;

#define ANA_CLASS_NAME WaveProcessor

#include "RootIncludes.h"
#include "Waves.h"
#include "Utils.h"
#include "User.h"

class ANA_CLASS_NAME
{
public:

  Waves waves;
  VarsUser vars_User;

  struct Conf {

    TString options, runName, inFileName, outFileName, anaFileName, inTreeName, outTreeName;
    TFile *inFile{0}, *outFile{0}, *anaFile{0};
    TTree *inTree{0}, *outTree{0};
    Long64_t etp{0}, evLimit{-1}, inTreeEntries{0};
    int evtsToSave{-1}, evtsSaved{0};

  } conf;

  ANA_CLASS_NAME() {};

  void Begin(); 
  void Terminate();
  void Loop();
  void LoopEntries(Long64_t);  
  virtual void Begin_User();
  virtual void Terminate_User();
  virtual void LoopEntries_User(Long64_t);
  void Msg(TString msg) { cout<<"-----> "<<msg<<endl; }

  void Launch() {
    Begin(); 
    Begin_User(); 
    Loop();
    Terminate();
    Terminate_User();
  }


};

#undef ANA_CLASS_NAME