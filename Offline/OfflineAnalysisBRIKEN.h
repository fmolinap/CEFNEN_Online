//
//  OfflineAnalysisCreateTree.h
//  
//
//  Created by Jorge Agramunt Ros on 5/30/12.
//  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
//
#ifndef _OfflineAnalysisCreateTree_h
#define _OfflineAnalysisCreateTree_h

#include <string>
#include <unistd.h>
#include <vector>
#include <TTree.h>

class BrikenTreeData {
public:
    BrikenTreeData( );
    ~BrikenTreeData();
//    std::vector<double> CorrE;
//    std::vector<double> CorrT;
//    std::vector<uint64_t> CorrTS;
//    std::vector<uint16_t> CorrId;
//    std::vector<uint16_t> CorrType;
    double E;
    uint64_t T;
    uint16_t Id;
    uint16_t type;
    uint16_t Index1;
    uint16_t Index2;
    uint16_t InfoFlag;
    std::string Name;
    std::vector<uint16_t> Samples;
    std::vector<int32_t> FIR;
    std::vector<int32_t> TasSIngles;

    void clear();
};
class AidaTreeData {
public:
    AidaTreeData( ){};
    ~AidaTreeData(){};
    
    
    ULong64_t       T;
    ULong64_t       Tfast;
    Double_t        E;
    Double_t        EX;
    Double_t        EY;
    Double_t        x;
    Double_t        y;
    Double_t        z;
    int32_t         nx;
    int32_t         ny;
    int32_t         nz;
    UChar_t         ID;
    void clear(){
        T=0;
        Tfast=0;
        E=0;
        EX=0;
        EY=0;
        x=0;
        y=0;
        z=0;
        ID=0;
        
    }
    
};

typedef BrikenTreeData NeuData;
typedef BrikenTreeData GammaData;
typedef BrikenTreeData AncData;
typedef BrikenTreeData YSOBData;
typedef AidaTreeData YSOData;


#endif
