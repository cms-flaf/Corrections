#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class JetVetoMapProvider : public CorrectionsBase<JetVetoMapProvider> {
public:

    JetVetoMapProvider(const std::string& fileName, const std::string& entry_name) :
    corrections_(CorrectionSet::from_file(fileName))
    {
        JetVetoMap_value=corrections_->at(entry_name); //bisogna capire il nome delle ere

    }
    float GetJetVetoMapValue(const LorentzVectorM & Jet_p4) const {
        return JetVetoMap_value->evaluate({"jetvetomap", (Jet_p4.Eta()),Jet_p4.Phi()}) ;
    }

private:
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref JetVetoMap_value;

};


} // namespace correction

