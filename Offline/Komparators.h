//
//  Komparators.h
//  DataChk
//
//  Created by Jorge Agramunt Ros on 1/29/13.
//  Copyright (c) 2013 Jorge Agramunt Ros. All rights reserved.
//
//
//  Komparators.h
//
//
//  Created by Kiko Albiol Colomer on 6/25/12.
//  Copyright (c) 2012 Instituto de Física Corpuscular. All rights reserved.
//

#ifndef _Komparators_h
#define _Komparators_h

#include <algorithm>
#include <cmath>

namespace CMP {
    
    class range
    {
        double _lowerbound;
        double _size;
    public:
        static const CMP::range zerorange;
        double lowerbound() const {return _lowerbound;}
        void lowerbound(double const avalue) {_lowerbound=avalue;}
        double size() const {return _size;}
        void size(double const avalue) {_size=std::abs(avalue);}
        
        double minval() const {return _lowerbound;}
        double maxval() const {return _lowerbound+_size;}
        double midval() const {return _lowerbound+0.5*_size;}
        
        range():_lowerbound(),_size(){}
        range(double abound,double asize):_lowerbound(abound),_size(asize){}
        range(double abound,double otherbound,bool isvaluerange):
        _lowerbound(abound),_size(otherbound)
        {
            if(isvaluerange)
            {
                _lowerbound=std::min(abound,otherbound);
                _size=std::max(abound,otherbound)-_lowerbound;
            }
        }
        
        
        void minmaxrange(double avaluefrom,double avalueto)
        {
            _lowerbound=std::min(avaluefrom,avalueto);
            _size=std::max(avaluefrom,avalueto)-_lowerbound;
        }
        
        static inline bool isintersect(const CMP::range &firstr ,const CMP::range &secondr )
        {
            return firstr.isintersect(secondr);
        }
        
        
        bool isintersect(const CMP::range &other ) const
        {
            const CMP::range &minvalrange=std::min(*this,other);
            const CMP::range &maxvalrange=std::max(*this,other);
            return maxvalrange.minval()<minvalrange.maxval();
        }
        
        
        CMP::range intersection_range(const CMP::range &other ) const
        {
            if(false==this->isintersect(other))
                return CMP::range::zerorange;
            const CMP::range &minvalrange=std::min(*this,other);
            const CMP::range &maxvalrange=std::max(*this,other);
            
            return CMP::range(maxvalrange.minval(),
                              minvalrange.maxval()-maxvalrange.minval());
        }
        
        CMP::range union_range(const CMP::range &other ) const
        {
            const CMP::range &minvalrange=std::min(*this,other);
            const CMP::range &maxvalrange=std::max(*this,other);
            
            return CMP::range(minvalrange.minval(),
                              maxvalrange.maxval()-minvalrange.minval());
        }
        
        bool operator <(const CMP::range &b) const
        {
            return this->minval()<b.minval();
        }
        bool operator >(const CMP::range &b) const
        {
            return this->minval()>b.minval();
        }
        bool operator <=(const CMP::range &b) const
        {
            return this->minval()<=b.minval();
        }
        bool operator >=(const CMP::range &b) const
        {
            return this->minval()>=b.minval();
        }
        
        
        bool operator ==(const CMP::range &b) const
        {
            return this->minval()==b.minval();
        }
        
        
        bool operator <(const double &b) const
        {
            return this->minval()<b;
        }
        bool operator >(const double &b) const
        {
            return this->minval()>b;
        }
        
        bool operator <=(const double &b) const
        {
            return this->minval()<b;
        }
        bool operator >=(const double &b) const
        {
            return this->minval()>b;
        }
        
        bool operator ==(const double &b) const
        {
            return this->minval()==b;
        }
        
    };
    
    
    template <typename T,typename T1>
    inline bool upper(const T &reference,const T1 &value)
    {
        return value > reference;
    }
    
    
    template <typename T,typename T1>
    inline bool between(const T &reference1,const T &reference2,const T1 &value)
    {
        const T &minval=std::min(reference1,reference2);
        const T &maxval=std::max(reference1,reference2);
        return (value>minval && value < maxval) ? true : false;
    }
    
    
    template <typename T,typename T1>
    inline bool outside(const T &reference1,const T &reference2,const T1 &value)
    {
        const T &minval=std::min(reference1,reference2);
        const T &maxval=std::max(reference1,reference2);
        return (value>minval && value < maxval) ? false : true;
    }
    
    
    
}


    // if( CMP::upper(time1,tref) || CMP::between(t0,t1,tref) )

#endif
