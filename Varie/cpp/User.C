#pragma once
using namespace std; 

#include "WaveProcessor.h"
#define ANA_CLASS_NAME WaveProcessor

void ANA_CLASS_NAME::Begin_User() { 
}

void ANA_CLASS_NAME::Terminate_User() {

}

void ANA_CLASS_NAME::LoopEntries_User(Long64_t entry) {  

}


   // wp.waves.wlist.insert(wp.waves.wlist.end(), {&w_cindy});


   // //tracks
   // static constexpr double zT1T2 = 15100; 
   // static constexpr double zT1Cry = zT1T2 + 1800;

   // int clu = 0;
   // for (int i = 0; i < 4; i++) { 
   //    clu += !(read->nHit[i] == 1);
   // }
   // if (clu != 0) {return;}

   // NEWB.cryPos[0] = read->xRaw[0] + (read->xRaw[2] - read->xRaw[0])*(PAR.zT1Cry/PAR.zT1T2);
   // NEWB.cryPos[1] = read->xRaw[1] + (read->xRaw[3] - read->xRaw[1])*(PAR.zT1Cry/PAR.zT1T2);
   // //tracks

