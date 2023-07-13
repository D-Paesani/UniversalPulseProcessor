#pragma once
#include "TString.h"
#include "TBranch.h"

struct Hit {
    double bline, brms, peak, charge, timpk, timcf;
    int wgood;
    float *wave;
};

class Waves {
    public:

    typedef TSpline3 spline_t;

    struct DigiPar {
        
        int wSize = 1024;
        int wFs = 4096;
        int wAmpFs = 1000;
        double tBin = 0.2;
        double tErr = 0; 
        double aErr = 0.15;
        double aBin = (float)wAmpFs/(float)wFs;
        double wTimSz = (float)wSize*tBin;
        double Z = 50.0;
        
        TString name = "digi";
        float *wtime;
        int wtimeBooked = 0;

        void bookBranchesOut(TTree *tree){
            if (wtimeBooked) {return;}
            wtime = new float[wSize];
            for(int ii = 0; ii < wSize; ii++) { wtime[ii] = float(ii*tBin);}
            TString bname = Form("%s_wtime", name.Data());
            tree->Branch( bname.Data(), wtime, Form("%s[%d]/F", bname.Data(), wSize) );
            wtimeBooked = 1;
        }

    };

    struct WaveBox {

        double pkStart, pkStop, qStart, qStop, bStart, bStop, spStart, spStop;
        double cf;
        TString inFormat, outFormat;
        vector <int> inChan, outChan;
        DigiPar *digi;

        TString opts = "";
        int saveWave = true;
        int invert = false;
        double gain = 1.0;
        double *cfScan = nullptr;
        int nCfScan = -1;
        double pkCutMin = -1;
        double lowPass = -1;

        UShort_t **waves = nullptr;
        // TBranch **waveBranches = nullptr; 
        Hit *hits;

        int nChan = min(inChan.size(), outChan.size());

        void bookBranchesIn(TTree *tree){ 
            // waveBranches = new TBranch*[nChan];
            waves = new UShort_t*[nChan];
            for(int ii = 0; ii < nChan; ii++) {
                waves[ii] = new UShort_t[digi->wSize]();
                tree->SetBranchAddress(Form(inFormat, inChan[ii]), waves[ii]);
                // tree->SetBranchAddress(Form(inFormat, inChan[ii]), waves[ii], &(waveBranches[ii]));
            }

        }
        
        void bookBranchesOut(TTree *tree){ 

            digi->bookBranchesOut(tree);
            hits = new Hit[nChan];

            for(int ii = 0; ii < nChan; ii++) {

                hits[ii].wave = new float[digi->wSize];
                
                TString chname = Form(outFormat.Data(), outChan[ii]) + TString("");
                // tree->Branch(chname.Data(), &hits[ii]);
                // tree->Branch(chname.Data(), &hits[ii], getLeafString(chname, digi->wSize).Data());
                tree->Branch(chname.Data(), &hits[ii], getLeafString(chname, -1).Data());

                TString chwname = Form(outFormat.Data(), outChan[ii]) + TString("_wave");
                TString chwname2 = chwname + Form("[%d]/F", digi->wSize);
                tree->Branch(chwname, &(hits[ii].wave[0]), chwname2);
                
            }

        }

        void initHits(){
        }

        TString getLeafString(TString cname, int nwpst = -1){
            vector <TString> lnames = {"bline/D", "brms/D", "peak/D", "charge/D", "timpk/D", "timcf/D", "wgood/I"};
            TString vv;
            for (TString ll : lnames) {
                vv += cname + TString (".");
                vv += ll;
                vv += TString(":");
            }
            if (nwpst == -1) {
                vv = vv.Strip(TString::kTrailing, ':');
                return vv;
            }
            vv += cname + TString (".");
            vv += Form("wave[%d]/F", nwpst);
            return vv;
        }



    };

    typedef vector <WaveBox*> Wlist_t;
    vector <WaveBox*> wlist;

    struct Vars {
        // TBranch *b_evt;
        Long64_t out_evt;
        Int_t in_evt;
    } vars; 

    void branchAll(TTree *intree, TTree *outree) {

        for(WaveBox *ww: wlist) { 
            ww->bookBranchesIn(intree);
            ww->bookBranchesOut(outree);
        }
        
        outree->Branch("evt", &vars.out_evt, "evt/I");
        // intree->SetBranchAddress("eventNumber", &vars.in_evt, &vars.b_evt);
        intree->SetBranchAddress("eventNumber", &vars.in_evt);

    };

};

