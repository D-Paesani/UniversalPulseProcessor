#pragma once
using namespace std; 

#include "WaveProcessor.h"
#define ANA_CLASS_NAME WaveProcessor

void ANA_CLASS_NAME::LoopEntries(Long64_t thisEntry) { 

   LoopEntries_User(thisEntry); 

   int deb = 0;

   int saveEvt = conf.evtsToSave > conf.evtsSaved;
   conf.evtsSaved += saveEvt;
   
   waves.vars.out_evt = waves.vars.in_evt;

   if (deb) {cout<<endl<<"--- event: "<<waves.vars.in_evt<<endl;}

   for(Waves::WaveBox *wbox: waves.wlist) {

      if (deb) {cout<<"---------- wbox: "<<wbox->inFormat<<" -> "<<wbox->outFormat<<endl;}

      int nChan = wbox->nChan;
      Waves::DigiPar *digi = wbox->digi;
      wbox->initHits();

      for (int ich = 0; ich < nChan; ich++) { 

         if (deb) {cout<<"----------------------- chan: "<<Form(wbox->inFormat, wbox->inChan[ich])<<" -> "<<Form(wbox->outFormat, wbox->outChan[ich])<<endl;}
   
         Hit *hit = &(wbox->hits[ich]); 

         hit->wgood = 0;
         UShort_t *wave = wbox->waves[ich];
         float sign = 1 - 2 * int(wbox->invert);
         float addbase = wbox->invert ? digi->wFs : 0.0;

         double charge, bline, brms, bline2, timcf, timpk, amp, tim;
         double peak{-99999};
         int basen{0}, chargen{0};

         for (int isam = int(digi->wSize*wbox->pkStart); isam < int(digi->wSize*wbox->pkStop); isam++) {
            amp = ((wave[isam])) * sign + addbase;
            amp *=wbox->gain;
            if (amp > peak) { 
               peak = amp;
               timpk = isam;
            } 
         } 

         addbase *= digi->aBin;
         peak *= digi->aBin;
         timpk *= digi->tBin;

         float bfrom = max((0.0), (timpk+wbox->bStart));
         float bto = min((digi->wTimSz), (timpk+wbox->bStop));
         float qfrom = max((0.0), (timpk+wbox->qStart));
         float qto = min((digi->wTimSz), (timpk+wbox->qStop));
         // float bfrom = timpk+wbox->bStart;
         // float bto = timpk+wbox->bStop;
         // float qfrom = timpk+wbox->qStart;
         // float qto = timpk+wbox->qStop;
         float spfrom = timpk+wbox->spStart;
         float spto = timpk+wbox->spStop;

         TGraphErrors wgra; 
         TGraphErrors wried;  

         for (int isam = 0; isam < digi->wSize; isam++) {           

            amp = ((wave[isam])) * sign * digi->aBin + addbase;
            amp *=wbox->gain;
            tim = digi->tBin * isam;

            fillGraph(&wgra, tim, amp, digi->tErr, digi->aErr);
            hit->wave[isam] = amp; 

            if (tim > bfrom && tim < bto) { 
               bline += amp;
               bline2 += amp*amp;
               basen++;
            }

            if (tim > qfrom && tim < qto) {  
               charge += amp;
               chargen++;
            }

            if (tim > spfrom && tim < timpk) {
               fillGraph(&wried, amp, tim, digi->aErr, digi->tErr);
            }

         } 

         if (basen == 0 || chargen == 0) {continue;}

         bline = bline/float(basen);
         wgra.MovePoints(0, -bline);   
         brms = TMath::Sqrt(bline2/(double)basen - bline*bline);
         peak += - bline;
         charge += -float(chargen*bline);
         charge *= digi->tBin/digi->Z; 

         for (int isam = 0; isam < digi->wSize; isam++) {hit->wave[isam] += -bline;} 

         if (wbox->pkCutMin > 0 && peak < wbox->pkCutMin) {continue;}   

         Waves::spline_t wspl = Waves::spline_t("wspl", &wgra); 
         auto wsplfun = [&wspl](double *x, double *){ return wspl.Eval(x[0]); }; 
         TF1 wspltf = TF1("wspltf", wsplfun, spfrom, spto, 0); 
         peak = wspltf.GetMaximum(spfrom, spto);
         timpk = wspltf.GetMaximumX(spfrom, spto);    
         double thr = wbox->cf * peak;
         timcf = wspltf.GetX(thr, spfrom, timpk); 
         // Waves::spline_t wspl2 = Waves::spline_t("wspl", &wried);
         // auto wsplfun2 = [&wspl2](double *x, double *){ return wspl2.Eval(x[0]); }; 
         // TF1 wspltf2 = TF1("wspwspltf2ltf", wsplfun2, wried.GetHistogram()->GetMinimum(), wried.GetHistogram()->GetMaximum(), 0);  
         // timcf = wspltf2.Eval(wbox->cf * peak);

         hit->bline = bline;
         hit->brms = brms;
         hit->charge = charge;
         hit->peak = peak;
         hit->timpk = timpk;
         hit->timcf = timcf;

         if (saveEvt) { 

            // conf.anaFile->mkdir("specimens", "", 1)->cd();
            conf.anaFile->mkdir(Form("%s%s", Form(wbox->outFormat, wbox->inChan[0]), Form("_%d", wbox->inChan[wbox->nChan-1])), "", 1)->cd();
            
            TString nam = Form( "e%d_%s", waves.vars.in_evt, Form(wbox->outFormat, wbox->outChan[ich]) );

            TCanvas *cc = new TCanvas(nam, nam); 
            cc->cd(); 
            wgra.SetTitle(Form("bl=%.3f brms=%.3f pk=%.3f qq=%.3f tpk=%.3f tcf=%.3f;tim [ns];amp [mV]", bline, brms, peak, charge, timpk, timcf));
            wgra.SetLineWidth(1); 
            wgra.SetMarkerStyle(20); 
            wgra.SetMarkerSize(0.5); 
            wgra.SetMarkerColor(kBlack); 
            wgra.Draw("AP"); 

            wspltf.SetLineColor(kTeal); 
            wspltf.Draw("same"); 
            TMarker tp = TMarker(timpk, peak, 2); 
            tp.SetMarkerSize(3); 
            tp.SetMarkerColor(kRed); 
            tp.Draw("same"); 
            TMarker tp1 = TMarker(timcf, thr, 2); 
            tp1.SetMarkerSize(3);  
            tp1.SetMarkerColor(kOrange+7); 
            tp1.Draw("same"); 

            TLine t0 = TLine(bfrom, 0, bfrom, peak);  
            t0.SetLineColor(kYellow); 
            t0.Draw("same");
            TLine t1 = TLine(bto, 0, bto, peak);  
            t1.SetLineColor(kYellow); 
            t1.Draw("same");
            TLine t2 = TLine(qfrom, 0, qfrom, peak); 
            t2.SetLineColor(kBlue); 
            t2.Draw("same");
            TLine t3 = TLine(qto, 0, qto, peak); 
            t3.SetLineColor(kBlue); 
            t3.Draw("same");
            TLine t5 = TLine(spfrom, 0, spfrom, peak);  
            t5.SetLineColor(kGreen); 
            t5.Draw("same");
            TLine t6 = TLine(spto, 0, spto, peak);  
            t6.SetLineColor(kGreen); 
            t6.Draw("same");

            cc->Write(); 
            conf.anaFile->cd();
         }

         hit->wgood = 1;

      }
   }

   conf.outTree->Fill();
    
} 




