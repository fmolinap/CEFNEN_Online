    //
    //  NewSpec.h
    //  
    //
    //  Created by Jorge Agramunt Ros on 5/30/12.
    //  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
    //
#ifndef _NewSpec_h
#define _NewSpec_h
#define QUEMAX 100
#include <string>
#include <deque>
#include "TH1D.h"
#include "TH2D.h"
#include "MyDefinition.h"
using namespace std;   



class NewSpec{
    
    deque<noisst> _VetoTimes;
    deque <int> _BadCycles;
    int _OldNCycles,_AnaCycles;

public:
    NewSpec(string Name,int id,int ch,int Bins,double Xlow,double XHigh,int TBins,double TXlow,double TXHigh);
    ~NewSpec();
    double Data(double  Tdata,double Edata,int cycle,int buff);
    double GetTimeQueVal(int index);
    int GetTimeQueSize();
    int GetPulsTimeQueSize();
    double GetPulsTimeQueVal(int index);
    int GetTotoalECounts();
    int GetTotoalTCounts();
    int GetTotoalPCounts();
    int EIntegral(){return hT->Integral(XLow,XHigh);};
    void SetTimeCalibration(double Tf,double To);
    void SetEnCalibration(double Ef,double Eo);
    void SayYeah();
        //    double GetNowTime();
    int SetNoisRejection(deque<noisst> cy);
    int SetTimeMark(double tm);
    int Correlation();
    int HalfNoise();
    int Total();
    deque<int> BadCycles(){return _BadCycles;};
    void BadCycles(deque<int> Bc){ _BadCycles=Bc;};
    int AnaCycles()const {return _AnaCycles;};
    int DCorrelation()const {return hT->Integral(0,1000)-hT->Integral(501,1000)*2;};
    int DHalfNoise()const{return hT->Integral(502,1000);};
    int DTotal()const{return hT->Integral(0,1000);};


    string MyName,HistName;
    int Veto;
    int Id,NBin,TNBin,NCycle,NBuff,OldBuff,OldCycle;
    double TCalFact,TCalOff,ECalFact,ECalOff;
    double XLow,XHigh,TXLow,TXHigh,TM;
    double En,Now;
    deque <double> Timeque;
    deque <double> PulsTimeque;
    deque <double> Enque;
    deque <double> NRCy;
    deque <double> NRni;
    deque <double> NRne;
    TH1D *hE,*hT,*hTC,*hEC;//,hTd,*hB,*hC;
    TH2D *h2T;
};


#endif
