
#ifndef _OfflineAnalysisCreateTree_cxx
#define _OfflineAnalysisCreateTree_cxx

#include "OfflineAnalysisBRIKEN.h"


    BrikenTreeData::BrikenTreeData(){};
    BrikenTreeData::~BrikenTreeData(){};

    void BrikenTreeData::clear(){
        Name.clear();
        E=0;
        T=0;
        type=0;
        Id=0;
        Index1=0;
        Index2=0;
        InfoFlag=0;
        Samples.clear();
        FIR.clear();
    }
    
#endif
