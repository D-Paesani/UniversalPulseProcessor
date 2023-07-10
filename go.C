
using namespace std;

#include <iostream> 

#include "TChain.h"
#include "TString.h" 
#include "TSystem.h" 

#include "WaveProcessor.h"
#include "WaveProcessor.C"
#include "User.h"
#include "User.C"
#include "Loop.C"

#define _run 309
#define _runName "run650%d"
#define _maxEvents -5000
#define _dryrun 0

void go(int run = _run) {

    // int run = _run;
    TString runName = Form(_runName, run);

    typedef Waves::WaveBox wbox_t;
    WaveProcessor wp;

    wp.conf.evLimit = _maxEvents;
    wp.conf.runName = runName;
    wp.conf.inFileName = Form("../data/roottople/%s.root", runName.Data());
    wp.conf.anaFileName = Form("../data/recod_ana/%s.root", runName.Data());
    wp.conf.outFileName = Form("../data/recod/%s.root", runName.Data());
    wp.conf.inTreeName = "t";
    wp.conf.outTreeName = "t";
    wp.conf.evtsToSave = 100;

    Waves::DigiPar digi_5gsps = {.name = "digi"};
    Waves::DigiPar digi_2gsps5 = {.name = "digi", .tBin = 0.4, .wTimSz = 0.4 * 1024 };

    wbox_t w_cindy = {   
        .digi = &digi_5gsps,
        .inFormat = "wave%d", .outFormat = "cindy%d", .inChan = {6,7}, .outChan = {0,1},
        .pkStart=0.05, .pkStop=0.5, .bStart=-15.0, .bStop=-4.5, .qStart=-4.0, .qStop=15.0, .spStart=-8.0, .spStop=8.0,
        .pkCutMin = 50.0, .cf = 0.06, .invert = 1
    };

    wbox_t w_ciax = {   
        .digi = &digi_5gsps,
        .inFormat = "wave%d", .outFormat = "ciax%d", .inChan = {9,10}, .outChan = {0,1},
        .pkStart=0.05, .pkStop=0.5, .bStart=-19.0, .bStop=-9, .qStart=-8.5, .qStop=12.5, .spStart=-12.0, .spStop=6.0, 
        .pkCutMin = -5.0, .cf = 0.08, .invert = 1
    };

    wbox_t w_series = {   
        .digi = &digi_5gsps,
        .inFormat = "wave%d", .outFormat = "cris%d", 
        .inChan = {18,19}, .outChan = {8,9},
        .pkStart=0.05, .pkStop=0.5, .bStart=-30.0, .bStop=-12.5, .qStart=-12, .qStop=40.0, .spStart=-11.5, .spStop=6.0,
        .pkCutMin = 10.0, .cf = 0.12, .invert = 0
    };

    wbox_t w_para = {   
        .digi = &digi_5gsps,
        .inFormat = "wave%d", .outFormat = "crip%d", 
        .inChan = {10+32,11+32}, .outChan = {8,9},
        .pkStart=0.05, .pkStop=0.5, .bStart=-36.0, .bStop=-14.5, .qStart=-14, .qStop=110.0, .spStart=-13.5, .spStop=6.0,
        .pkCutMin = 10.0, .cf = 0.12, .invert = 0
    };

    if (run == 0) {
        return;
    } else if (run == 341 || run == 342 || run == 343) {
        w_cindy.inChan = {11, 12};
        wp.waves.wlist = {&w_cindy, &w_ciax};
    } else if (run == 333 || run == 332 || run == 316 || run == 309) {
        // wp.waves.wlist = {&w_cindy, &w_para, &w_series};
        wp.waves.wlist = {&w_para, &w_series};
        wp.conf.evtsToSave = 500;
    }

    if (_dryrun) {wp.Begin();}
    else  {wp.Launch();}

}

