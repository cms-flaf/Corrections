#pragma once

namespace correction {

using LorentzVectorXYZ = ROOT::Math::LorentzVector<ROOT::Math::PxPyPzE4D<double>>;
using LorentzVectorM = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>;
using LorentzVectorE = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiE4D<double>>;
using RVecI = ROOT::VecOps::RVec<int>;
using RVecS = ROOT::VecOps::RVec<size_t>;
using RVecShort = ROOT::VecOps::RVec<short>;
using RVecUC = ROOT::VecOps::RVec<UChar_t>;
using RVecF = ROOT::VecOps::RVec<float>;
using RVecB = ROOT::VecOps::RVec<bool>;
using RVecVecI = ROOT::VecOps::RVec<RVecI>;
using RVecLV = ROOT::VecOps::RVec<LorentzVectorM>;
using RVecUL = ROOT::VecOps::RVec<unsigned long>;

enum class UncScale : int {
    Down = -1,
    Central = 0,
    Up = +1,
};



template <typename CorrectionClass>
class CorrectionsBase {
public:
    template<typename ...Args>
    static void Initialize(Args&&... args)
    {
        _getGlobal() = std::make_unique<CorrectionClass>(args...);
    }

    static const CorrectionClass& getGlobal()
    {
        const auto& corr = _getGlobal();
        if(!corr)
            throw std::runtime_error("Class not initialized.");
        return *corr;
    }

private:
    static std::unique_ptr<CorrectionClass>& _getGlobal()
    {
        static std::unique_ptr<CorrectionClass> corr;
        return corr;
    }
};
} // end of namespace correction