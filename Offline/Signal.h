//
//  Signal.h
//  
//
//  Created by Jorge Agramunt Ros on 5/30/12.
//  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
//
#ifndef _Signal_h
#define _Signal_h
#define QUEMAX 100
#include <string>
#include <deque>
#include <list>
#include "TH1D.h"
#include "TH2D.h"
#include "TCanvas.h"
#include "MyDefinition.h"
using namespace std;   

 struct SectionCalData {
    double Xlow,XHigh;
    double CalFact,CalFact2,CalOffSet;
    SectionCalData(){
        Xlow=0;
        XHigh=0;
        CalFact=0;
        CalFact2=0;
        CalOffSet=0;
    }
} ;

typedef std::list<SectionCalData>  SectionCalDataCollection;


class Signal{
    
    deque <int> _BadCycles;
    deque<noisst> _VetoTimes;
    int _LastCycle,_OldNCycles,_AnaCycles;
    double _SiTh,_He3Th,_GeTh;

public:
    Signal(string Name,int id,int ch,int Bins,double Xlow,double XHigh,int TBins,double TXlow,double TXHigh,int ModId,int crate,std::string Parameter );
    Signal(string Name,int id,int ch,int Bins,double Xlow,double XHigh,int TBins,double TXlow,double TXHigh,int ModId,int crate,std::string Parameter, int Type,int index1,double index2, bool Hist);
    ~Signal();
    double Data(unsigned long  Tdata,int Edata,int blk,int Cycle,bool Hist);
    double Data(unsigned long  Tdata,int Edata,int blk);
    void SayYeah();
    int ResetCycle();
    string WhoAreYou();
    int AddCycle();

    void SetSecCalibration(SectionCalDataCollection & MySecCal){_MySecCal=MySecCal;SecCalActive=true;}
    
    double DesvCycles();
    deque<int> BadCycles(){return _BadCycles;};
    void BadCycles(deque<int> Bc){ _BadCycles=Bc;BDdefined=true;};
    int AnaCycles()const {return _AnaCycles;};
    double SiTh()const{return _SiTh;};
    void SiTh(double STh){_SiTh=STh;};
    double He3Th()const{return _He3Th;};
    void He3Th(double HTh){_He3Th=HTh;};
    double GeTh()const{return _GeTh;};
    void GeTh(double GTh){_GeTh=GTh;};
    bool IsPulse(int Data);

    double  _LastTS;
    int     GetTotoalECleanCounts();
    int     GetTotoalTCounts();
    int     GetTotoalPCounts();
    int     GetNCycles();
    uint32_t GetId(){return Id;};
    int    GetType(){return _Type;};
    int    GetIndex1(){return _Index1;};
    int    GetIndex2(){return _Index2;};
    std::string    GetName(){return MyName;};
    double  GetTime(unsigned long Tdata);
    double  GetEnergy(int Edata);
    double  GetNow();
    double  GetMaxTime();
    double    GetEMax( ){return Emin;};
    double  GetTimeQueVal(int index);
    double  GetThreshold(){return Eth;};
    int     GetTimeQueSize();
    int     GetPulsTimeQueSize();
    double  GetPulsTimeQueVal(int index);
    int     GetChan(){return _MyChan;};
    int     GetModId(){return _ModId;};
    int     GetParameter(){return _Parameter;};
    double  GetRunTime(){return (_RunningTime+_CycleRunningTime);};
    int     GetMyCycleCount(){return _MyCycleCount;};
    
    void    SetTimeCalibration(double Tf,double To);
    void    SetEnCalibration(double Ef,double Eo);
    int     SetLastCycle(int value);
    void    SetThreshold(double ethres){Eth=ethres;};
    void    SetEMax(double emax){Emin=emax;};
    int     SetNoisRejection(deque<noisst> cy);
    int     SetTimeMark(double tm);
    int     Crate(){return _Crate;};
    void    CyclesInRun(int c){_MyCycleCountinRun=c;};
    int     CyclesInRun(){return _MyCycleCountinRun;};
    void MyType(std::string type){_ChanType=type;};
    const std::string MyType(){return _ChanType; };
    
    bool BDdefined;
    bool _Hist;
    bool IsTheFirst;
    string MyName,HistName;
    int Veto;
    int Id,NBin,TNBin,NCycles;
    double TCalFact,TCalOff,ECalFact,ECalOff;
    double XLow,XHigh,TXLow,TXHigh,TM;
    double En,_LastEn,Now,Beafore,PBeafore;
    deque <double> Timeque;
    deque <double> PulsTimeque;
    deque <double> Enque;
    int Eth;
    int Emin;
    int Esmax;
    int _ModId;
    int _Type;
    int _Index1;
    int _Index2;
    int _Crate;
    int _MyChan;
    double MaxTime,MaxTimeReal;
    TCanvas *c1;
    int nd;
    double _RunningTime,_CycleRunningTime;
    int _MyCycleCount;
    int _MyCycleCountinRun;
    std::vector<float> Ev,Tv,Pv,ERawv,TRawv,ECv,TCv,PCv;

    TH1D *hE,*hT,*hERaw,*hTRaw,*hP,*hTC,*hEC,*hPC;
protected:
    std::string _ChanType;

    int _Parameter;
    std::list<SectionCalData> _MySecCal;
    bool SecCalActive;
};


#endif
