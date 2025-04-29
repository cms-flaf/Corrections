#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class VptCorrProvider : public CorrectionsBase<VptCorrProvider> {
public:
    enum class UncSource : int {
        Central = -1,
        ewcorr = 0,
        Vpt = 1,
    };

    static bool sourceApplies(UncSource source)
    {
        if(source == UncSource::ewcorr) return true;
        if(source == UncSource::Vpt) return true;
        return false;
    }

    VptCorrProvider(const std::string& VptCorrFileName, const std::string& hist_name, const std::string& hist_ewcorr_weight){
        auto VptCorrFile = root_ext::OpenRootFile(VptCorrFileName);
        histo_Vpt_SF.reset(root_ext::ReadCloneObject<TH1>(*VptCorrFile, hist_name.c_str(), hist_name.c_str(), true));
        histo_ewcorr_SF.reset(root_ext::ReadCloneObject<TH1>(*VptCorrFile, hist_ewcorr_weight.c_str(), hist_ewcorr_weight.c_str(), true));
    }

    float getSF_fromRootFile(const float& LHE_Vpt, UncSource source, UncScale scale) const {
        float sf = 1.;
        if (source == UncSource::Vpt){
            const UncScale Vpt_scale = source== UncSource::Vpt ? scale : UncScale::Central;
            sf= getSFsFromHisto(histo_Vpt_SF, LHE_Vpt, Vpt_scale);
        }
        if (source == UncSource::ewcorr){
            const UncScale nom_scale = source== UncSource::ewcorr ? scale : UncScale::Central;
            sf= getSFsFromHisto(histo_ewcorr_SF, LHE_Vpt, nom_scale);
        }
        return sf;
    }


    float getSFsFromHisto(const std::unique_ptr<TH1>& histo, const float& LHE_Vpt, UncScale scale) const
    {
        const auto x_axis = histo->GetXaxis();
        int x_bin = x_axis->FindFixBin(LHE_Vpt);
        if(x_bin < 1)
            x_bin = 1;
        if( x_bin > x_axis->GetNbins() )
            x_bin = x_axis->GetNbins();
        return histo->GetBinContent(x_bin) + static_cast<int>(scale) * histo->GetBinError(x_bin);
    }


private:

    std::unique_ptr<TH1> histo_Vpt_SF;
    std::unique_ptr<TH1> histo_ewcorr_SF;

} ;



} // namespace correction