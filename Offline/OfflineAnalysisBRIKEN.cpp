
//  //
//  OfflineAnalysis.cpp
//  GASIFIC_70
//
//  Created by Jorge Agramunt Ros on 27/11/14.
//
//
#include <iostream>
#include <fstream>
#include "../inc/GIUnpackSIS3316.h"
#include "../inc/GIUnpackSIS3302.h"
#include "../inc/GIUnpack.h"
//#include "GIUnpackSIS3316.h"
#include <stdlib.h>     /* strtoul */

#include "Signal.h"
#include "NewSpec.h"
#include <unistd.h>
#include "Komparators.h"
#include "MyDefinition.h"
#include "../inc/GUICommon.h"
#include <map>
#include <utility>      // std::pair
#include "TH1F.h"
#include "TTree.h"
#include "TFile.h"
#include <vector>
#include "../inc/ShMemTempl.h"
#include "../inc/CommonStruc.h"
#include <thread>         // std::thread
#include <sstream>
#include<fstream>
#include "OfflineAnalysisBRIKEN.cxx"

#define NUMOFCHAN       200
#define MAXLENGTHMAP    200000
#define EVENTSIZE       1000  // in clock steeps units
#define TREE  1
//#define CYCLES 1
#define DTCORRECTION 1
#define k_function "["<<__pretty_function__<<"]"
#define HEX   std::stw(8)<<std:fill(0)<<:std::hex<<"0x"
#define YSOEVENTLENGTH 100

#ifdef __MAKECINT__
#pragma link C++ class vector<float>+;
#endif
struct ConditionPar2{
    ConditionPar2(){};
    ConditionPar2(const ConditionPar2& New) {
        //        std::cout << "A::operator=(A&)" << std::endl;
        toDelete=New.toDelete;
        Defined=New.Enable;
        Enable=New.Enable;
        CalibConition=New.CalibConition;
        Name=New.Name;
        Type=New.Type;
        SourceType=New.SourceType;
        ConditionType=New.ConditionType;
        std::copy( New.CharInfo.cbegin(),New.CharInfo.cend(),CharInfo.begin());
        //        CharInfo=New.CharInfo;//0->XName 1->XUnits 2->YName 3->YUnits
        //        CharInfo=New.CharInfo;//0->XName 1->XUnits 2->YName 3->YUnits
        std::copy( New.Source.cbegin(),New.Source.cend(),Source.begin());
        std::copy( New.Condition.cbegin(),New.Condition.cend(),Condition.begin());
        Condition=New.Condition;
        Id=New.Id;
        HistBins=New.HistBins;
        Range=New.Range;
        SourceMod=New.SourceMod;
        SourceChan=New.SourceChan;
        ConditionMod=New.ConditionMod;
        ConditionChan=New.ConditionChan;
        std::copy( New.IntParameter.cbegin(),New.IntParameter.cend(),IntParameter.begin());
        std::copy( New.DoubParameter.cbegin(),New.DoubParameter.cend(),DoubParameter.begin());
        
        CalOffset=New.CalOffset;
        CalFactor=New.CalFactor;
        RangeMin=New.RangeMin;
        RangeMax=New.RangeMax;
        SocketId=New.SocketId;
        Send2Socket=New.Send2Socket;
        LevelGerar=New.LevelGerar;
        
        
    }
    
    bool    toDelete;
    bool    Defined;
    bool    Enable;
    bool    CalibConition;
    std::array<int8_t,100> Name;
    std::array<int8_t,100> Type;
    std::array<int8_t,1000> SourceType;
    std::array<int8_t,1000> ConditionType;
    std::array<std::array<int8_t,1000>,100> CharInfo;//0->XName 1->XUnits 2->YName 3->YUnits
    std::array<int16_t,2> Source;
    std::array<int16_t,2> Condition;
    int32_t Id;
    int32_t HistBins;
    int32_t Range;
    int32_t SourceMod;
    int32_t SourceChan;
    int32_t ConditionMod;
    int32_t ConditionChan;
    std::array<std::array<int32_t,1000>,2> IntParameter;
    
    double CalOffset,CalFactor;
    std::array<std::array<double,1000>,2> DoubParameter;
    double RangeMin;
    double RangeMax;
    int SocketId;
    bool Send2Socket;
    int32_t LevelGerar;
    
    
};

typedef int64_t TSTime_t;

enum InputTypes {Neutron=1, Gamma=2, Anc=3,YSOI=4,YSOD=5};
ConditionPar2 MyConditions;
typedef std::vector<double>      DataVector;
//std::multimap<uint64_t,BrikenTreeData>  GetSoftSumEL(std::map<int, std::map <u_int64_t, std::vector <Double32_t> > > & ThisBlockDataMap,BrikenTreeData &TestData, std::vector<int> TasDetInc);
void Usage(char *progname) {
    fprintf(stderr,"Usage\n%s -f [DLT-file-path-name] -o [OutputFile] -c [Path-to-configuration-files]\n or \n %s - l [File-name-list-of-DLT] -o [OutputFile] -c [Path-to-configuration-files]\n ",progname,progname);
    exit(1);
}

class Unpacker{
public:
    Unpacker(std::string name,std::string type,int mod, int chan,int crate,int clk){
        if(type=="SIS3316"){
            _Unpack3316=GIUnpackSIS3316(name,mod,chan,crate,clk);
            _Im=3316;
            
        }
        else if(type=="SIS3302"){
            _Unpack3302=GIUnpackSIS3302(name,mod,chan,crate,clk);
            _Im=3302;
        }
        
        
        
    };
    ~Unpacker(){};
    void Unpack(const BasicData &data,std::vector <struct SingleData>&MyData,std::vector <struct Samples> &MySamples){
        
        if(_Im==3316){
            _Unpack3316.Unpack(data,MyData,MySamples);
        }
        else if(_Im==3302){
            _Unpack3302.Unpack(data,MyData,MySamples);
            
        }
        
    };
protected:
    GIUnpackSIS3316 _Unpack3316;
    GIUnpackSIS3302 _Unpack3302;
    int _Im;
    
};

int main(int argc, char **argv){
    if( argc < 7 )
    {
        std::cout << "Out -1  "<<std::endl;

        Usage(argv[0]);
        return -7;
    }
    TFile F;
    std::cout << "Starting Offline\n";
    int NofFiles=0;
    std::string FileName=argv[1];
    // LoadCond *Cond= new LoadCond();
    std::string Files[100],line,str,Name;
    std::vector <int> LayersList;
    
    FILE *fd;
    
    //    CSharedStruct <BlockUnpackData> UnPackData("MyData");
    std::multimap<uint64_t,BrikenTreeData> DataMmap;
    std::multimap<uint64_t,BrikenTreeData> YSODMmap;
    std::multimap<uint64_t,BrikenTreeData> YSOIMmap;
    std::multimap<uint64_t,BrikenTreeData> DataMmapTemp;
    std::multimap<uint64_t,AidaTreeData> YSOMmap;
    BrikenTreeData GlobalData;
    AidaTreeData GlobalYSOData;
    int DataCount=0;
    std::string ReadoutFile;
    std::string StrGateLength;
    std::string OutputFile;
    std::string FileList;
    std::string ConfPath;
    ConfPath=".";
    int InputType;
    int IncopOtion=0;
    std::string ModIdStr;
    Time_t GateLength=40;
    if (argc >1) {
        for(int i=1;i <argc;i++) {
            if ( (argv[i][0] == '-') || (argv[i][0] == '/') ) {
                switch(argv[i][1]) {
                    case 'f':
                        ReadoutFile = argv[++i];
                        InputType = 1;
                        IncopOtion++;
                        std::cout << "Readout file "<<ReadoutFile<<std::endl;
                        break;
                    case 'h':
                        std::cout << "Out 0  "<<std::endl;

                        Usage(argv[0]);
                        break;
                    case 'o':
                        OutputFile = argv[++i];
                        std::cout << "Output file "<<OutputFile<<std::endl;
                        break;
                    case 'l':
                        ReadoutFile = argv[++i];
                        InputType = 2;
                        IncopOtion++;
                        std::cout << "Readout file list "<<ReadoutFile<<std::endl;
                        
                        break;
                    case 'c':
                        ConfPath = argv[++i];
                        IncopOtion++;
                        std::cout << "Configure path "<<ConfPath<<std::endl;
                        break;

                    case 'g':
                        GateLength=strtol(argv[++i], nullptr, 0);;
                        IncopOtion++;
                        std::cout << "GateLength  "<<GateLength<<std::endl;

                        break;
                    default:
                        std::cout << "Out 1  "<<std::endl;

                        Usage(argv[0]);
                        break;
                }
            }
            else{
                std::cout << "Out 2  "<<std::endl;

                Usage(argv[0]);
            }
        }
    }
    std::cout << "TAS Gate Length "<< GateLength <<std::endl;

    TFile *Q=new TFile(OutputFile.data(),"RECREATE"," ",1);
    if(!Q){
        std::cout << "Error open file "<<std::endl;
        exit(1);
    }
    //    if(IncopOtion>1)Usage(argv[0]);
    
    TTree *t = new TTree("CEFNENtree","Tree with Neutron Spectrometer data");
    if(!t){
        std::cout << "Error open Tree"<<std::endl;
        exit(1);
    }
    
//    TTree *ysot = new TTree("YSOTree","Tree with YSO data");
//    if(!t){
//        std::cout << "Error open Tree"<<std::endl;
 //       exit(1);
  //  }
    
    
    
    //    FILE *dF;
    //    std::string CsvFile;
    
    //    unsigned long lastindex = OutputFile.find_last_of(".");
    //
    //    CsvFile = OutputFile.substr(0, lastindex)+".csv";
    //    dF=fopen( CsvFile.data(),"w");
    //
    
    // LoadCond *Cond= new LoadCond();
    if (InputType==1){
        Files[0]=ReadoutFile;
        NofFiles=1;
    }
    
    if(InputType==2){    std::ifstream Fd(ReadoutFile.data());
        while ( Fd.good() ) {
            getline (Fd,Files[NofFiles]);
            std::cout<<"File to read :"<<NofFiles<<" "<<Files[NofFiles]<<std::endl;
            std::ifstream FdTemp(Files[NofFiles].data());
            if (!FdTemp.is_open()){
                std::cout<<"Error opening "<<Files[NofFiles]<<std::endl;
                Fd.close();
                //--------                       goto sacabo;
            }
            FdTemp.close();
            NofFiles++;
        }
        Fd.close();
    }
    
    
    
    
    Signal  *Sig[1000];
    bool    NewCycle[1000];
    NeuData    ToNeuFill;
   // GammaData  ToGammaFill;
   // AncData    ToAncFill;
    //    YSOBData   ToYSOBFill;
   // YSOData    ToYSOFill;
    std::map <u_int64_t,std::vector<double>> HistoricalData;
    int NofSignals=0;
    bool SigDef[1000];
    for(int i=0;i<1000;i++)SigDef[i]=false;
    bool SpecDef[1000];
    for(int i=0;i<1000;i++)SpecDef[i]=false;
    int CycleCount=0;
    int PartialCycleCount=0;
    double PartialTCycleMean=0;
    {
        std::cerr<<" paso por 1"<<std::endl;
        FileName=ConfPath+"/OfflineConf_Signals.csv";
        // LoadCond *Cond= new LoadCond();
        // Preparing files to be read
        ifstream Fd(FileName.data());
        while ( Fd.good() ) {
            getline (Fd,line);
            if(line.size()>5){
                std::cerr<<" paso por 2"<<std::endl;
                std::string Name,Module,Type,Parameter;
                int Channel=0,Ebin=0,Tbin=0,ModId=0,Id=0, Crate=0,NumOfCalSections=0,InputType=0,Index1=0;
                double EFactor=0,EOffset=0 ,TFactor=0,TOffset=0,Elow=0,Ehigh=0,Tlow=0,Thigh=0,EThres=0,EMax=0,Index2=0;
                SectionCalDataCollection MyCalSect;
                istringstream iss(line,istringstream::in);
                cout<<"New line: "<<line<<endl;
                iss>>Name;
                iss>>Id;
                iss>>Crate;
                iss>>ModId;
                iss>>InputType;
                iss>>Index1;
                iss>>Index2;
                iss>>Channel;
                iss>>Type;
                iss>>Parameter;
                iss>>EThres;
                iss>>EMax;
                iss>>EOffset;
                iss>>EFactor;
                iss>>TOffset;
                iss>>TFactor;
                iss>>Ebin;
                iss>>Elow;
                iss>>Ehigh;
                iss>>Tbin;
                iss>>Tlow;
                iss>>Thigh;
                SectionCalData ThisSec;
                
                
                
                iss>>NumOfCalSections;
                if(iss.good()){
                    for(int i=0; i<NumOfCalSections;i++){
                        SectionCalData ThisSec;
                        iss>>ThisSec.Xlow;
                        iss>>ThisSec.XHigh;
                        iss>>ThisSec.CalOffSet;
                        iss>>ThisSec.CalFact;
                        iss>>ThisSec.CalFact2;
                        MyCalSect.push_back(ThisSec);
                    }
                }
                if(InputType==4||InputType==5){
                    int MyLayer=Index1;
                    auto it= std::find(LayersList.begin(), LayersList.end(), MyLayer);
                    if(it==LayersList.end()){
                        LayersList.push_back(MyLayer) ;
                    }
                    
                }
                
                cout<<"New Signal: "<<Name<<"  "<<ModId<<"  "<<Type<<"  "<<Channel<<"  "<<EOffset<<"  "<<EFactor<<"  "<<TOffset<<"  "<<TFactor<<"  "<<Tbin<<endl;;
                if(Name!="#"){
                    cout<<Name<<"  "<<ModId<<"  "<<Type<<"  "<<Channel<<"  "<<EOffset<<"  "<<EFactor<<"  "<<TOffset<<"  "<<TFactor<<"  "<<Tbin<<endl;;
                    cout<<"NofSig "<< NofSignals << " New Id "<<Id<<" define for "<<Name  <<endl;
#ifdef DEB
                    cout<<Channel<<"  "<<EOffset<<"  "<<EFactor<<"  "<<TOffset<<"  "<<TFactor<<"  "<<endl;
#endif
                    
                    for (auto & itc: MyCalSect){
                        cout<<itc.Xlow<<" "<<itc.XHigh<<" "<< itc.CalOffSet<<" "<<itc.CalFact<<" "<<itc.CalFact2<<std::endl;
                        
                    }
                    
                    Sig[NofSignals] =new Signal(Name,Id,Channel,Ebin,Elow,Ehigh,Tbin,Tlow,Thigh,ModId,Crate,Parameter,InputType,Index1,Index2,false);
                    Sig[NofSignals]->MyType(Type);
                    if( MyCalSect.size()>0){
                        Sig[NofSignals]->SetSecCalibration(MyCalSect);
                    }
                    else{
                        Sig[NofSignals]->SetEnCalibration(EFactor,EOffset);
                    }
                    Sig[NofSignals]->SetTimeCalibration(TFactor,TOffset);
                    Sig[NofSignals]->SetThreshold(EThres);
                    Sig[NofSignals]->SetEMax(EMax);
                    SigDef[NofSignals]=true;
                    cout<<"NofSig "<< NofSignals << " New Id "<<Id<<" define for "<<Name  <<" GetId() "<< Sig[NofSignals]->GetId() <<endl;
                    
                    
                    NofSignals++;
                    
                    //                t->Branch(Name.data(),Sig[NofSignals]);
                    //                t->Print();
                }
            }
        }
        Fd.close();
        std::string CopyFile ="cp ";
        
        std::size_t lastindex = OutputFile.find_last_of(".");
        std::string SaveConfFile = OutputFile.substr(0, lastindex);
        CopyFile +=FileName;
        
        CopyFile +=" ";
        CopyFile +=SaveConfFile;
        CopyFile +="_RunConf.csv";
        std::cout<<CopyFile.c_str()<<std::endl;
        system(CopyFile.c_str());
        
    }
    t->Branch("Neutrons_",&ToNeuFill);
  //  t->Branch("Gamma.",&ToGammaFill);
  //  t->Branch("Ancillary.",&ToAncFill);
    //    t->Branch("YSO.",&ToYSOBFill);
  //  ysot->Branch("Yso.",&ToYSOFill);
    
    
    
    
    
    
    
    
    
    std::vector<Unpacker> ChannellUnpack;
    
    //    for(int i=0;i<16;i++){
    //
    //        ChannellUnpack[i   ]=*new GIUnpackSIS3316("Mod1",0xA,i);
    //        ChannellUnpack[i+16]=*new GIUnpackSIS3316("Mod2",0xB,i);
    //        ChannellUnpack[i+32]=*new GIUnpackSIS3316("Mod3",0xC,i);
    //        ChannellUnpack[i+48]=*new GIUnpackSIS3316("Mod4",0xD,i);
    //    }
    
    for(int i=0;i<NofSignals;i++){
        
        Unpacker  DummyUnpak = Unpacker("DummyMod",Sig[i]->MyType(),Sig[i]->GetModId(),Sig[i]->GetChan(),Sig[i]->Crate(),50);
        ChannellUnpack.push_back(DummyUnpak);
        
        std::cout<<"Signal to Unpack Name:"<< Sig[i]->MyName <<" Mod:"<<Sig[i]->GetModId()<<" Chan:"<< Sig[i]->GetChan()<<" Crate:"<< Sig[i]->Crate()<<std::endl;
        
    }
    
    
    //--------Check of the total cycles to veto the first and the last of each start and stop command
    bool ValidCycle[1000];
    memset(ValidCycle, 0, sizeof(ValidCycle));
    
    for(int i5=0;i5<NofFiles; i5++){
        //        int TotCycles=0;
        if(i5>0){
            size_t mylastindex = Files[i5-1].find_last_of("_");
            size_t oldlastindex = Files[i5].find_last_of("_");
            if(Files[i5-1].substr(0, mylastindex)!=Files[i5].substr(0, oldlastindex)){
                memset(ValidCycle, 0, sizeof(ValidCycle));
            }
            
        }
        
        int EndFile=1;
        std::cout<<"Try to open file :"<< Files[i5].data() <<std::endl;
        if(access(Files[i5].data(),F_OK)<0  ){perror("Error access file:");	 }
        
        fd = fopen(Files[i5].data(),"r");
        if(fd ==NULL){
            perror("Error open file:");exit(1);
        }
        
        PartialCycleCount=0;
        PartialTCycleMean=0;
        std::cout<<"Open file :"<< Files[i5] <<std::endl;
        u_int32_t head=0;
        int WRead=0;
        uint64_t LastTimes[1000];
        memset(LastTimes, 0, sizeof(LastTimes));
        bool ValidCycle[1000];
        memset(ValidCycle, 0, sizeof(ValidCycle));
        uint64_t LastTime2[1000];
        memset(LastTime2, 0, sizeof(LastTimes));
       for(int i=0;i<NofSignals;i++){ Sig[i]->CyclesInRun(0);}
        std::vector<int> TasDet;
        for(int i=0;i<NofSignals;i++){
            if(Sig[i]->GetIndex2()==25){
                TasDet.push_back(Sig[i]->Id);
            }
        }
        while(EndFile){
            while((!(head == 0xdabadaba))&&EndFile==1){
//                std::cout<<std::hex<<head<<" "<<std::dec<<std::endl;
                if(fread(&head,4,1,fd)<1){EndFile=0;fprintf(stderr," S'acabo 1\n");}
                //                std::cout<<"--0x"<<std::hex<<head<<std::endl;
                //                sleep(1);
                WRead+=4*1;
            }
//            if(!EndFile)break;
            for (int ic=0;ic<1000;ic++)NewCycle[ic]=false;
//            std::map<int, std::map <u_int64_t, std::vector <Double32_t> > >  ThisBlockDataMap;

           if(head==0xdabadaba && EndFile==1){
                BufData ThisBlockData;
                head=0;
                int BlockLength=0;

                
                if(fread(&BlockLength,4,1,fd)<1){EndFile=0;fprintf(stderr," S'acabo 2\n");}
                BasicData Data(BlockLength);
                memcpy(Data.Data.get(), &head, 4);
                memcpy(Data.Data.get()+1, &BlockLength, 4);
                
                if(fread(Data.Data.get()+2,4,BlockLength-(2),fd)<1){EndFile=0;fprintf(stderr," S'acabo 3\n");}
                std::map <u_int64_t,std::vector<double>> DataInOrder;
                std::map <u_int64_t,std::vector<double>> DataInOrder2;
                //                std::cerr<< "NofSignals "<<NofSignals<<std::endl;
              for(int i=0;i<NofSignals;i++){

                    std::map<u_int64_t, std::vector <Double32_t>  >  ThisSigDataMap;
                    std::vector <struct Samples> MyBlockSamples;
                    std::vector <struct SingleData> MyData;
                    MyData.reserve(8000);
                    ChannellUnpack[i].Unpack( Data ,MyData,MyBlockSamples);
                    
                    //                    std::cerr<< "Unpack data size "<<MyData.size()<<" Sampls Size "<< MyBlockSamples.size()<<std::endl;
                    
                    int EventCont=0;
                    
                    for (std::vector <SingleData> :: const_iterator a = MyData.begin(); a != MyData.end(); a++){
                        
                        if(0<=a->Error){
                            // std::cerr<< "TimeStamp "<<a->TimeStamp<<" LastTime2 "<<LastTime2[i]<<std::endl;
                            double En;
                            //                            std::cerr<<"5 SigDef["<<i<<"]="<<SigDef[i]<<std::endl;
                            //                            std::cerr<<"5 ValidCycle["<<i<<"]="<<ValidCycle[i]<<std::endl;
                            
                            if(SigDef[i]){//
                                GlobalData.clear();
                                
                                //
                                En=0;
                                if(Sig[i]->GetParameter()==0){
                                    En=Sig[i]->Data(a->TimeStamp,a->FIRmax - a->FIR0,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==1){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc1,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==2){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc2,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==3){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc3,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==3){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc3,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==4){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc4,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==5){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc5,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==6){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc6,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==7){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc7,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==8){
                                    En=Sig[i]->Data(a->TimeStamp,a->Acc8,0,CycleCount,false);
                                }
                                else if(Sig[i]->GetParameter()==9){
                                    En=Sig[i]->Data(a->TimeStamp,a->PeakHigh,0,CycleCount,false);
                                }
                                
                                
                                
                                //=================== Analisis area  ============
                                if(Sig[i]->GetType()==InputTypes::Neutron){
                                    GlobalData.E=En;
                                    GlobalData.Id=Sig[i]->GetId();
                                    GlobalData.type=1;
                                    GlobalData.Name=Sig[i]->GetName();
                                    GlobalData.Index1=Sig[i]->GetIndex1();
                                    GlobalData.Index2=Sig[i]->GetIndex2();
                                    GlobalData.type=1;
                                    GlobalData.InfoFlag=a->FlagInf;
                                    GlobalData.T=Sig[i]->GetNow();
                                    if(MyBlockSamples.size()>0){
                                        for(int i=0;i<MyBlockSamples[EventCont].RawSamples;i++){
                                            GlobalData.Samples.push_back( MyBlockSamples[EventCont].Samples[i]);
                                        }
                                    }
                                    if(MyBlockSamples.size()>0){
                                        for(int i=0;i<800;i++){
                                            GlobalData.FIR.push_back( MyBlockSamples[EventCont].SamplesMAW[i]);
                                        }
                                    }

                                    
                                    
                                    if(LastTimes[i]>GlobalData.T){
                                        std::cerr<<std::hex<<"0x" <<LastTimes[i]<<" 0x" << GlobalData.T<<std::endl;
                                        //                                        if(!NewCycle[i])std::cerr<<"NewCycle type 1" <<std::endl;
                                        NewCycle[i]=true;
                                        LastTimes[i]=GlobalData.T;
                                        
                                    }
                                    else{
                                        LastTimes[i]=GlobalData.T;
                                    }
                                    if(!NewCycle[i]&& En> Sig[i]->GetThreshold() && En<Sig[i]->GetEMax())DataMmap.emplace(GlobalData.T,GlobalData);
                                    else if( En> Sig[i]->GetThreshold() && En<Sig[i]->GetEMax())DataMmapTemp.emplace(GlobalData.T,GlobalData);
                                }
                               
                                
                            }
                            else {
                            }
                            //                               std::cout<< "Id Asigned  "<<a.MySingleData.Id<<" FIRmax "<<a.MySingleData.FIRmax <<" EFIR "<< a.MySingleData.EFIR<<std::endl;
                            
                        }
                        EventCont++;
                    }
//                  ThisBlockDataMap.emplace(i,ThisSigDataMap);
                }
                
            }
            //            std::cerr<<"First TS "<<DataMmap.begin()->first<<" Last TS "<< (--DataMmap.end())->first<<std::endl;
            auto end = DataMmap.end();
            TSTime_t LastTrigger=0;
//            BrikenTreeData TestData;
//            TestData.Id=888;
//            TestData.type=2;
//            TestData.Index1=0;
//            TestData.Index2=0;
//            std::multimap<uint64_t,BrikenTreeData> TempDataMmap2;

//            TempDataMmap2=GetSoftSumEL(ThisBlockDataMap,TestData,TasDet);

//            BrikenTreeData TasData;
//            TasData.Id=777;
//            TasData.type=0;
//            TasData.Index1=0;
//            TasData.Index2=0;
//            LastTrigger=DataMmap.begin()->first;
            //            if(DataMmap.size()>10)
            //             if(DataMmap.size()>50)std::advance(end, -50);
//            std::multimap<uint64_t,BrikenTreeData> TempDataMmap;
//            bool FirstNo=false;
//           for(auto it=DataMmap.begin();it!=end;it++){
 //                if(it->second.type==2 && it->second.Index2==25){ // Gamma condition && TAS Condition
  //                   if(it->second.T>LastTrigger+GateLength){
//                         if(FirstNo)  TempDataMmap.emplace(TasData.T,TasData);
  //                       if(FirstNo)  DataMmap.emplace(TasData.T,TasData);
   //                      FirstNo=true;
   //                      TasData.E=0;
    //                     TasData.T=it->second.T-10;
    //                     LastTrigger=TasData.T;
                         

     //                }
    //                 TasData.E+=it->second.E;
                    // TasData.TasSIngles.push_back(it->second.E);
     //                TasData.Index2++;
                     
                     
      //           }
                
       //     }
       //     DataMmap.emplace(TasData.T,TasData);
        //    std::cout<<"Block read, size: "<<DataMmap.size()<<std::endl;

 //           TempDataMmap.emplace(TasData.T,TasData); // Fill the last event in the Memory block
//            std::cout<<TempDataMmap.size()<<std::endl;
//            for(auto it:TempDataMmap){
////                std::cout<<" "<<it.second.Id<<std::endl;
//               DataMmap.emplace(it.first,it.second);
//            }
//            for(auto it:TempDataMmap2){
//                //                std::cout<<" "<<it.second.Id<<std::endl;
//                DataMmap.emplace(it.first,it.second);
//            }
            for(auto it=DataMmap.begin();it!=end;it++){
                //                for(auto it:DataMmap){
                ToNeuFill.clear();
               // ToGammaFill.clear();
                //ToAncFill.clear();
                //ToYSOFill.clear();
                //std::cerr<<"TS "<<it.first <<" Datacount "<<DataCount<<std::endl;
                DataCount++;
                if(it->second.type==1 )ToNeuFill=it->second;
                //if(it->second.type==2)ToGammaFill=it->second;
                //if(it->second.type==3)ToAncFill=it->second;
                //if(it->second.type==5){
                 //   ToAncFill=it->second;
                 //   YSODMmap.emplace(it->first,it->second);
                //}
              //  if(it->second.type==4){
               //     ToAncFill=it->second;
               //     YSOIMmap.emplace(it->first,it->second);
                //}
                
                t->Fill();
            }
            DataMmap.clear();
            
            
            
            
                             
            
            
            
            
            
            

    
                    
                
                
                //std::cerr<<"TS "<<it.first <<" Datacount "<<DataCount<<std::endl;
                
                
                

            
            
            
            
        }
        
        
        
        
        
        
        std::cout<<"Closing files"<<std::endl;
        
        
        
        
        
        
        
        
        
        t->Write("", TObject::kOverwrite);
        t->Print();
      //  ysot->Write("", TObject::kOverwrite);
      //  ysot->Print();
        Q->Write("", TObject::kOverwrite);
        
        fclose(fd);
    }
    
    
    
    
    
    
    
    
    
    Q->Close();
    exit(1);
    return 0;
    
}


