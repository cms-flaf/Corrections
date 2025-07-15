#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
    class JetVetoMapProvider : public CorrectionsBase<JetVetoMapProvider> {
    public:

        JetVetoMapProvider(std::string const& fileName, std::string const& entry_name) :
        corrections_(CorrectionSet::from_file(fileName))
        {
            std::cout << "JetVetoMapProvider: init" << std::endl;
            JetVetoMap_value = corrections_->at(entry_name); //bisogna capire il nome delle ere

        }
        RVecB GetJetVetoMapValues(const RVecLV& Jet_p4, const RVecB& JetVetoMapCondition) const {
            RVecB veto_values(Jet_p4.size()); // Default value is 1.0 (no veto)
            for (int jet_idx = 0; jet_idx < Jet_p4.size(); jet_idx++) {
                float jvm_factor = JetVetoMapCondition[jet_idx] ? JetVetoMap_value->evaluate({"jetvetomap", Jet_p4[jet_idx].Eta(),Jet_p4[jet_idx].Phi()}) : 1.0 ;
                veto_values[jet_idx] = static_cast<bool>(jvm_factor); // Apply the correction factor
            }
        return veto_values;
        }

    private:
        std::unique_ptr<CorrectionSet> corrections_;
        Correction::Ref JetVetoMap_value;

    };


} // namespace correction

