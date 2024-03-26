#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
class EleCorrProvider : public CorrectionsBase<EleCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        EleID = 0,
        EleES = 1,
        Ele_dEsigma = 2,
    };

    static std::string getESScaleStr(UncScale scale)
    {

        static const std::map<UncScale, std::string> scale_names = {
            { UncScale::Down, "scaledown" },
            { UncScale::Up, "scaleup" },
        };
        return scale_names.at(scale);
    }

    static std::string getIDScaleStr(UncScale scale)
    {

        static const std::map<UncScale, std::string> scale_names = {
            { UncScale::Down, "sfdown" },
            { UncScale::Central, "sf" },
            { UncScale::Up, "sfup" },
        };
        return scale_names.at(scale);
    }

    static bool sourceApplies(UncSource source)
    {
        if ( source == UncSource::EleID ) return true;
        if ( source == UncSource::EleES ) return true;
        return false;
    }

    EleCorrProvider(const std::string& EleIDFile, const std::string& EleESFile) :
        corrections_(CorrectionSet::from_file(EleIDFile)),
        correctionsES_(CorrectionSet::from_file(EleESFile)),
        EleIDSF_(corrections_->at("UL-Electron-ID-SF")),
        EleES_(correctionsES_->at("UL-EGM_ScaleUnc"))
    {
    }


    float getID_SF(const LorentzVectorM& Electron_p4, int TauEle_genMatch, std::string working_point, std::string period, UncSource source, UncScale scale) const
    {
        const GenLeptonMatch genMatch = static_cast<GenLeptonMatch>(TauEle_genMatch);
        if((genMatch != GenLeptonMatch::Electron && genMatch != GenLeptonMatch::TauElectron)) return 1.;
        const UncScale jet_scale = sourceApplies(source) ? scale : UncScale::Central;
        return EleIDSF_->evaluate({period, getIDScaleStr(jet_scale), working_point, Electron_p4.eta(), Electron_p4.pt()});

    }
    /*
     RVecLV getES(const RVecLV& Electron_p4, std::string period, UncSource source, UncScale scale) const
    {
        RVecLV final_p4 = Tau_p4;
        for(size_t n = 0; n < Tau_p4.size(); ++n) {

        }
        const GenLeptonMatch genMatch = static_cast<GenLeptonMatch>(TauEle_genMatch);
        if((genMatch != GenLeptonMatch::Electron && genMatch != GenLeptonMatch::TauElectron)) return 1.;
        const UncScale jet_scale = sourceApplies(source)
                                           ? scale : UncScale::Central;
        if(UncSource == UncSource::eleES){
            return EleIDSF_->evaluate({period, getESScaleStr(source), Electron_p4.eta(), 1});
        }
        else if (UncSource == UncSource::ele_dEsigma){

        }
        return 1. ;
    }
    */

private:
    std::unique_ptr<CorrectionSet> corrections_, correctionsES_;
    Correction::Ref EleIDSF_, EleES_;
};

} //namespace correction