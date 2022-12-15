#pragma once

namespace correction {

using LorentzVectorXYZ = ROOT::Math::LorentzVector<ROOT::Math::PxPyPzE4D<double>>;
using LorentzVectorM = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>;
using LorentzVectorE = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiE4D<double>>;
using RVecI = ROOT::VecOps::RVec<int>;
using RVecS = ROOT::VecOps::RVec<size_t>;
using RVecUC = ROOT::VecOps::RVec<UChar_t>;
using RVecF = ROOT::VecOps::RVec<float>;
using RVecB = ROOT::VecOps::RVec<bool>;
using RVecVecI = ROOT::VecOps::RVec<RVecI>;
using RVecLV = ROOT::VecOps::RVec<LorentzVectorM>;

enum class UncScale : int {
    Down = -1,
    Central = 0,
    Up = +1,
};

}

float GetStitchingWeight(const SampleType& sampleType, const float LHE_Vpt, const int LHE_Njets ){
    if(sampleType==SampleType::DY)
    {
        if(LHE_Vpt==0.) return 1/2.;
        else return 1/3.;
    }
    else if(sampleType==SampleType::W)
    {
        if(LHE_Njets>0) return 1/2.;
        else return 1.;
    }
    return 1.;
}
