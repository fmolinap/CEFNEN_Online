    //
    //  NewSpec.cpp
    //  
    //
    //  Created by Jorge Agramunt Ros on 5/30/12.
    //  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
    //

#include <iostream>
#include <string>
#include <deque>

#include "NewSpec.h"

NewSpec::NewSpec(string Name,int id,int ch,int Bins,double Xlow,double Xhigh,int TBins,double TXlow,double TXhigh){
    MyName=Name;
    Id=id;
    XLow=Xlow;
    XHigh=Xhigh;
    NBin=Bins;
    TXLow=TXlow;
    TXHigh=TXhigh;
    TNBin=TBins;
    TCalFact=1;
    TCalOff=0;
    ECalFact=1;
    ECalOff=0;
    HistName=MyName+"_E";
    hE=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);

    HistName=MyName+"_Clean_E";
    hEC=new TH1D(HistName.data() ,HistName.data() ,NBin,XLow,XHigh);
    HistName=MyName+"_Clean_T";
    hTC=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow/1000,TXHigh/1000);
    HistName=MyName+"_T";
    hT=new TH1D(HistName.data() ,HistName.data() ,TNBin,TXLow/1000,TXHigh/1000);
//    HistName=MyName+"_BuffData";
//    hB=new TH1D(HistName.data() ,HistName.data() ,30000,0,30000);
//    HistName=MyName+"_CycleData";
//    hC=new TH1D(HistName.data() ,HistName.data() ,300,0,300);
//    HistName=MyName+"_VsTime";
//    h2T=new TH2D(HistName.data() ,HistName.data() ,TNBin,TXLow,TXHigh,300,0,300);
      cout<<"New NewSpec: "<<MyName<<" defined"<<endl;
  
#ifdef DEB
#endif
}

NewSpec::~NewSpec(){
        //    hT->Delete();
        //    hTC->Delete();
        //    hEC->Delete();
        //    hE->Delete();
        //    hB->Delete();
        //    hC->Delete();
    
#ifdef DEB
    cout<<"NewSpec destroid"<<endl;
#endif
}

double NewSpec::Data(double Tdata,double Edata,int buff,int cycle){
    
    Now=Tdata*TCalFact+TCalOff;
    En=Edata*ECalFact+ECalOff;
    hE->Fill(En);
    hT->Fill(Now/1000);
    return En;
    
}
void NewSpec::SetTimeCalibration(double Tf,double To){
    TCalFact=Tf;
    TCalOff=To;
#ifdef DEB
    cout << "New "<<MyName<<" Time calibration Farctor "<< TCalFact<<" Offset "<<TCalOff<<endl;
#endif
}
void NewSpec::SetEnCalibration(double Ef,double Eo){
    ECalFact=Ef;
    ECalOff=Eo;
#ifdef DEB
    cout << "New "<<MyName<<" En calibration Farctor "<< ECalFact<<" Offset "<<ECalOff<<endl;
#endif
}

void NewSpec::SayYeah(){
    cout<<MyName<<" Say YEAHHH!!!"<<endl;
}
double NewSpec::GetTimeQueVal(int index){
    if(index>=Timeque.size()){
        cout<<"Deque no so long"<<endl;
        return 0;
    }
        //cout<<"index "<<index<<endl;
    double dT=Timeque[index];
    return dT;
}
int NewSpec::GetTimeQueSize(){
    return Timeque.size();
}
    //double NewSpec::GetNowTime(){
    //    return Now;
    //}

int NewSpec::SetTimeMark(double tm){
    TM=tm;
    return 0;
}

int NewSpec::SetNoisRejection(deque<noisst> cy){
    _VetoTimes=cy;
    
    return 0;
}
int NewSpec::GetTotoalECounts(){
    return 0;// hEC->Integral(XLow,XHigh);
    
}
int NewSpec::Correlation(){
    return  hE->Integral(0,1000)-hE->Integral(501,1000)*2;
    
}


int NewSpec::HalfNoise(){
    return hE->Integral(501,1000);
    
}





int NewSpec::Total(){
    return hE->Integral(0,1000);
    
}





