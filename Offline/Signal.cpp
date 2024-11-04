//
//  Signal.cpp
//  
//
//  Created by Jorge Agramunt Ros on 5/30/12.
//  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
//

#include <iostream>
#include <string>
#include <deque>
#include "Signal.h"

#define DEB 0


Signal::Signal(string Name,int id,int ch,int Bins,double Xlow,double Xhigh,int TBins,double TXlow,double TXhigh,int ModId,int crate=0,std::string Parameter="EFIR"){

    MyName=Name;
    Id=id;
    _ModId=ModId;
    _MyChan=ch;
    _Crate=crate;
    XLow=Xlow;
    XHigh=Xhigh;
    NBin=Bins;
    TXLow=TXlow;
    TXHigh=TXhigh;
    TNBin=TBins;
    TCalFact=1;
    if(Parameter=="EFIR")_Parameter=0;
    else if(Parameter=="Acc1")_Parameter=1;
    else if(Parameter=="Acc2")_Parameter=2;
    else if(Parameter=="Acc3")_Parameter=3;
    else if(Parameter=="Acc4")_Parameter=4;
    else if(Parameter=="Acc5")_Parameter=5;
    else if(Parameter=="Acc6")_Parameter=6;
    else if(Parameter=="Acc7")_Parameter=7;
    else if(Parameter=="Acc8")_Parameter=8;
    else if(Parameter=="PeakHigh")_Parameter=9;

    TCalOff=0;
    ECalFact=1;
    ECalOff=0;
    MaxTime=0;
    _OldNCycles=0;
    _AnaCycles=0;
    HistName=MyName+"_E";
    hE=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_T";
    hT=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow/1000,TXHigh/1000);
    HistName=MyName+"_P";
    hP=new TH1D(HistName.data() ,HistName.data() ,TNBin,XLow,XHigh);
    HistName=MyName+"_Clean_P";
    hPC=new TH1D(HistName.data() ,HistName.data() ,TNBin,XLow,XHigh);
    
    HistName=MyName+"_Raw_E";
    hERaw=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_Raw_T";
    hTRaw=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow,TXHigh);

    HistName=MyName+"_Clean_E";
    hEC=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_Clean_T";
    hTC=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow,TXHigh);

    _RunningTime=0;
    _CycleRunningTime=0;
    _MyCycleCount=0;
    NCycles=0;
    Beafore=0;
    SecCalActive=false;
#ifdef DEB
    cout<<"New Signal "<<MyName<<" are defined"<<endl;
#endif
    cout<<"New Signal "<<MyName<<" are defined XHigh "<<XHigh<<endl;
    BDdefined=false;
}

Signal::Signal(string Name,int id,int ch,int Bins,double Xlow,double Xhigh,int TBins,double TXlow,double TXhigh,int ModId,int crate=0,std::string Parameter="EFIR", int Type=0,int index1=0,double index2=0,bool Hist=false){
    _Hist=Hist;
    MyName=Name;
    Id=id;
    _ModId=ModId;
    _Type=Type;
    _Index1=index1;
    _Index2=index2;
    _MyChan=ch;
    _Crate=crate;
    XLow=Xlow;
    XHigh=Xhigh;
    NBin=Bins;
    TXLow=TXlow;
    TXHigh=TXhigh;
    TNBin=TBins;
    TCalFact=1;
    if(Parameter=="EFIR")_Parameter=0;
    else if(Parameter=="Acc1")_Parameter=1;
    else if(Parameter=="Acc2")_Parameter=2;
    else if(Parameter=="Acc3")_Parameter=3;
    else if(Parameter=="Acc4")_Parameter=4;
    else if(Parameter=="Acc5")_Parameter=5;
    else if(Parameter=="Acc6")_Parameter=6;
    else if(Parameter=="Acc7")_Parameter=7;
    else if(Parameter=="Acc8")_Parameter=8;
    else if(Parameter=="PeakHigh")_Parameter=9;
    
    TCalOff=0;
    ECalFact=1;
    ECalOff=0;
    MaxTime=0;
    _OldNCycles=0;
    _AnaCycles=0;
    if(_Hist){
    HistName=MyName+"_E";
    hE=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_T";
    hT=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow/1000,TXHigh/1000);
    HistName=MyName+"_P";
    hP=new TH1D(HistName.data() ,HistName.data() ,TNBin,XLow,XHigh);
    HistName=MyName+"_Clean_P";
    hPC=new TH1D(HistName.data() ,HistName.data() ,TNBin,XLow,XHigh);
    
    HistName=MyName+"_Raw_E";
    hERaw=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_Raw_T";
    hTRaw=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow,TXHigh);
    
    HistName=MyName+"_Clean_E";
    hEC=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_Clean_T";
    hTC=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow,TXHigh);
    }
    _RunningTime=0;
    _CycleRunningTime=0;
    _MyCycleCount=0;
    NCycles=0;
    Beafore=0;
    SecCalActive=false;
#ifdef DEB
    cout<<"New Signal "<<MyName<<" are defined"<<endl;
#endif
    cout<<"New Signal "<<MyName<<" are defined XHigh "<<XHigh<<endl;
    BDdefined=false;
}

Signal::~Signal(){
//    hT->Delete();
//    hTC->Delete();
//    hEC->Delete();
//    hE->Delete();
//    hcp->Delete();
//    hbp->Delete();
//    hB->Delete();
    
#ifdef DEB
  if(DEB)  cout<<"Signal destroid"<<endl;
#endif
}

double Signal::Data(unsigned long Tdata,int Edata,int blk,int Cycle,bool Hist){
    Now=Tdata*TCalFact+TCalOff;
    
    if(_CycleRunningTime<Now)_CycleRunningTime=Now;
    else {
        _RunningTime+=_CycleRunningTime;
        _CycleRunningTime=Now;
        _MyCycleCount++;
        
    }
    if(SecCalActive){
        En=0;
        for (auto &it: _MySecCal){
               double Dummy1=Edata*it.CalFact2;
                double Dummy2= Dummy1*Edata;
                double Dummy3= Edata*it.CalFact;
                double Dummy4=Dummy2+Dummy3+it.CalOffSet;
//                En=Edata*Edata*it.CalFact2+Edata*it.CalFact+it.CalOffSet;
//            break;
                   if(Dummy4>=it.Xlow && En<=it.XHigh){
                       En=Dummy4;
                       break;
     }
        }
    }
    else En=Edata*ECalFact+ECalOff;
    auto thisEn=En;
    if(Hist){
        hERaw->Fill(En);
        if(Id<40 && En>Eth  && _LastEn>Eth && Id<48 && En<Emin && _LastEn<Emin && (Now-_LastTS)<0.5&&(Now-_LastTS)>0){
          if(En>Eth  && _LastEn>Eth && Id<48 && En<Emin && _LastEn<Emin)  std::cerr<<"Id "<<Id<<" Now "<<Now<< " _LastTS "<<_LastTS<<" En "<<En<<std::endl;
            IsTheFirst=false;
            En=0;
        }
        else IsTheFirst=true;
        hTRaw->Fill(Now);
        if(En>Eth  &&  En<Emin){
            hE->Fill(En);
            hT->Fill(Now/1000);//if(Now>TXLow && Now<TXHigh) In sec
            if(_MyCycleCount>0){
                hEC->Fill(En);
                hTC->Fill(Now);//if(Now>TXLow && Now<TXHigh)
                
            }

        }
        if(En>Emin){
            if(_MyCycleCount>0)  hPC->Fill(En);
            hP->Fill(En);
//            if (Id==49)cout << "New "<<MyName<<" Pulser "<< En<<endl;

        }
//        if(En>Eth   &&  En<Emin)    hT->Fill(Now);//if(Now>TXLow && Now<TXHigh)
    }
    _LastTS=Now;
    _LastEn=thisEn;
    return En;
    
}

void Signal::SetTimeCalibration(double Tf,double To){
    TCalFact=Tf;
    TCalOff=To;
#ifdef DEB
    cout << "New "<<MyName<<" Time calibration Farctor "<< TCalFact<<" Offset "<<TCalOff<<endl;
#endif
}
void Signal::SetEnCalibration(double Ef,double Eo){
    ECalFact=Ef;
    ECalOff=Eo;
#ifdef DEB
    cout << "New "<<MyName<<" En calibration Farctor "<< ECalFact<<" Offset "<<ECalOff<<endl;
#endif
}


void Signal::SayYeah(){
    cout<<MyName<<" Say YEAHHH!!!"<<endl;
}
double Signal::GetTimeQueVal(int index){
    return Timeque.at(index);
}
int Signal::GetTimeQueSize(){
    return Timeque.size();
}

double Signal::GetPulsTimeQueVal(int index){
    return PulsTimeque.at(index);
}
int Signal::GetPulsTimeQueSize(){
    return PulsTimeque.size();
}

double Signal::GetNow(){
    return Now;
}
double Signal::GetTime(unsigned long Tdata){
    return Tdata*TCalFact+TCalOff;
}
double Signal::GetEnergy(int Edata){
    return   Edata*ECalFact+ECalOff;
}
int Signal::GetNCycles(){
    return NCycles;
}
string Signal::WhoAreYou(){
    return MyName;
    
}
int Signal::SetTimeMark(double tm){
    TM=tm;
    return NCycles;
}
int Signal::AddCycle(){
    NCycles++;
    return NCycles;
}
int Signal::ResetCycle(){
    NCycles=0;
    return NCycles;
}

int Signal::SetNoisRejection(deque<noisst> cy){
    _VetoTimes=cy;

    
    return 0;
}
int Signal::GetTotoalECleanCounts(){

    return hE->Integral();
}

int Signal::GetTotoalPCounts(){
    
    return hP->Integral();
    
}

int Signal::SetLastCycle(int value){
    
    _LastCycle=value;
    
    return _LastCycle;
    
}
double Signal::GetMaxTime(){
    return MaxTimeReal;
}
double Signal::DesvCycles(){
    return 0;
}

bool Signal::IsPulse(int d){
    if(d>Emin && d<Esmax) return 1;
    else return 0;
}





