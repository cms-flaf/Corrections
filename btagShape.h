#ifndef CORRECTION_BTAGSHAPECORRPROVIDER_H
#define CORRECTION_BTAGSHAPECORRPROVIDER_H

#include "corrections.h"
#include "jet.h"

#include <set>

namespace correction {
    class bTagShapeCorrProvider {
      public:
        enum class UncSource : int {
            Central = -1,
            lf = 0,
            hf = 1,
            lfstats1 = 2,
            lfstats2 = 3,
            hfstats1 = 4,
            hfstats2 = 5,
            cferr1 = 6,
            cferr2 = 7,
            jesRelativeBal = 8,
            jesHF = 9,
            jesBBEC1 = 10,
            jesEC2 = 11,
            jesAbsolute = 12,
            jesFlavorQCD = 13,
            jesBBEC1_year = 14,
            jesAbsolute_year = 15,
            jesEC2_year = 16,
            jesHF_year = 17,
            jesRelativeSample_year = 18,
            jesTotal = 19
        };
        static bool needYear(UncSource source) {
            if (source == UncSource::jesBBEC1_year || source == UncSource::jesAbsolute_year ||
                source == UncSource::jesEC2_year || source == UncSource::jesHF_year ||
                source == UncSource::jesRelativeSample_year) {
                return true;
            }
            return false;
        }
        static const std::map<UncSource, std::string> getUncName() {
            static const std::map<UncSource, std::string> UncMapNames = {
                {UncSource::Central, "Central"},
                {UncSource::lf, "lf"},
                {UncSource::hf, "hf"},
                {UncSource::lfstats1, "lfstats1"},
                {UncSource::lfstats2, "lfstats2"},
                {UncSource::hfstats1, "hfstats1"},
                {UncSource::hfstats2, "hfstats2"},
                {UncSource::cferr1, "cferr1"},
                {UncSource::cferr2, "cferr2"},
                {UncSource::jesRelativeBal, "jesRelativeBal"},
                {UncSource::jesHF, "jesHF"},
                {UncSource::jesBBEC1, "jesBBEC1"},
                {UncSource::jesEC2, "jesEC2"},
                {UncSource::jesAbsolute, "jesAbsolute"},
                {UncSource::jesFlavorQCD, "jesFlavorQCD"},
                {UncSource::jesBBEC1_year, "jesBBEC1_"},
                {UncSource::jesAbsolute_year, "jesAbsolute_"},
                {UncSource::jesEC2_year, "jesEC2_"},
                {UncSource::jesHF_year, "jesHF_"},
                {UncSource::jesRelativeSample_year, "jesRelativeSample_"},
                {UncSource::jesTotal, "jes"}};
            return UncMapNames;
        }

        static std::string getScaleStr(UncScale scale) {
            static const std::map<UncScale, std::string> scale_names = {
                {UncScale::Down, "down_"},
                {UncScale::Up, "up_"},
            };
            if (scale == UncScale::Central)
                return "central";
            return scale_names.at(scale);
        }

        static const std::string getFullNameUnc(const std::string scale_name,
                                                const std::string source_name,
                                                const std::string year,
                                                bool need_year,
                                                bool isCentral) {
            if (isCentral)
                return "central";
            return need_year ? scale_name + source_name + year : scale_name + source_name;
        }
        //"description": "deepJet reshaping scale factors for UL 2018.
        //The scale factors have 8 default uncertainty sources (hf,lf,hfstats1/2,lfstats1/2,cferr1/2).
        //All except the cferr1/2 uncertainties are to be applied to light and b jets.
        // The cferr1/2 uncertainties are to be applied to c jets.
        //hf/lfstats1/2 uncertainties are to be decorrelated between years, the others correlated.
        //Additional jes-varied scale factors are supplied to be applied for the jes variations.",
        // Note the flavor convention: hadronFlavor is b = 5, c = 4, f = 0

        static bool sourceApplies(UncSource source, int Jet_Flavour) {
            if (source == UncSource::lf && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::hf && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::lfstats1 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::lfstats2 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::hfstats1 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::hfstats2 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::cferr1 && Jet_Flavour == 4)
                return true;
            if (source == UncSource::cferr2 && Jet_Flavour == 4)
                return true;

            if (source == UncSource::jesRelativeBal && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesHF && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesBBEC1 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesEC2 && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesAbsolute && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesFlavorQCD && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesBBEC1_year && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesAbsolute_year && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesEC2_year && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesHF_year && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesRelativeSample_year && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            if (source == UncSource::jesTotal && (Jet_Flavour == 5 || Jet_Flavour == 0))
                return true;
            return false;
        }

        // The light-jet variations whose pT binning can send a jet below the first edge to the
        // wrong content (see variationMinPtLight).
        static bool isLightFlowAffected(UncSource source) {
            return source == UncSource::lf || source == UncSource::hf || source == UncSource::lfstats1 ||
                   source == UncSource::lfstats2 || source == UncSource::hfstats1 || source == UncSource::hfstats2;
        }

        // variationMinPtLight > 0: light jets (hadronFlavour 0) below this pT evaluate the lf, hf,
        // lf/hfstats1/2 variations at this pT. For the BTV files whose light-jet pT binning starts
        // above the jets in scope (2023BPix: first edge 30 GeV), central clamps such a jet to the
        // first bin while the variations' flow content is the one they use above the last edge, so
        // up and down would describe a >200 GeV jet against the central of a 30-50 GeV jet. At this
        // pT they describe the same bin as central.
        bTagShapeCorrProvider(const std::string& fileName,
                              const std::string& year,
                              std::string const& tagger_name,
                              const bool wantShape = true,
                              const double variationMinPtLight = 0.)
            : corrections_(CorrectionSet::from_file(fileName)), _year(year), variationMinPtLight_(variationMinPtLight) {
            if (wantShape) {
                shape_corr_ = corrections_->at(tagger_name + "_shape");
                if (variationMinPtLight_ > 0.) {
                    // Only while the file still clamps the light-jet central below that pT: a file
                    // with a bin of its own there would have it silently replaced.
                    const double below = shape_corr_->evaluate({"central", 0, 1.0, variationMinPtLight_ - 1., 0.03});
                    const double at = shape_corr_->evaluate({"central", 0, 1.0, variationMinPtLight_, 0.03});
                    if (below != at) {
                        throw std::runtime_error(
                            "bTagShapeCorrProvider: " + fileName + " has a light-jet central bin below pT " +
                            std::to_string(variationMinPtLight_) +
                            " GeV, so the light-jet variation clamp no longer applies: remove it for this "
                            "campaign");
                    }
                    std::cerr << "bTagShapeCorrProvider: light-jet lf/hf/stats variations evaluated at pT >= "
                              << variationMinPtLight_ << " GeV, the first bin of the light-jet central" << std::endl;
                }
            }
            std::cerr << "Initialized bTagShapeCorrProvider::bTagShapeCorrProvider()" << std::endl;
        }

        float getBTagShapeSF(const RVecLV& Jet_p4,
                             const RVecI& Jet_Flavour,
                             const RVecF& Jet_bTag_score,
                             UncSource source,
                             UncScale scale) const {
            double sf_product = 1.;
            static const std::set<int> allowed_flavors = {0, 4, 5};
            std::string source_str = getUncName().at(source);
            for (size_t jet_idx = 0; jet_idx < Jet_p4.size(); ++jet_idx) {
                if ((Jet_bTag_score[jet_idx] > 1.0 || Jet_bTag_score[jet_idx] < 0.0) ||
                    std::abs(Jet_p4[jet_idx].eta()) >= 2.5 || Jet_p4[jet_idx].pt() < 20.0 ||
                    !allowed_flavors.contains(Jet_Flavour[jet_idx])) {
                    continue;
                }
                const UncScale jet_tag_scale = sourceApplies(source, Jet_Flavour[jet_idx]) ? scale : UncScale::Central;
                const std::string& scale_str = getScaleStr(jet_tag_scale);
                bool isCentral = jet_tag_scale == UncScale::Central;
                bool need_year = needYear(source);
                const std::string& unc_name = getFullNameUnc(scale_str, source_str, _year, need_year, isCentral);
                double pt = Jet_p4[jet_idx].pt();
                if (!isCentral && Jet_Flavour[jet_idx] == 0 && isLightFlowAffected(source) &&
                    pt < variationMinPtLight_) {
                    pt = variationMinPtLight_;
                }
                try {
                    const auto sf = shape_corr_->evaluate(
                        {unc_name, Jet_Flavour[jet_idx], std::abs(Jet_p4[jet_idx].eta()), pt, Jet_bTag_score[jet_idx]});
                    sf_product *= sf;
                } catch (std::runtime_error& e) {
                    std::cerr << "bTagShapeCorrProvider::getBTagShapeSF : Error in shape_corr_->evaluate() called with "
                                 "following arguments:\n";
                    std::cerr << "\tunc_name=" << unc_name << "\n"
                              << "\tjet_idx=" << jet_idx << "\n"
                              << "\tJet_Flavour=" << Jet_Flavour[jet_idx] << "\n"
                              << "\tabs(Jet_eta)=" << std::abs(Jet_p4[jet_idx].eta()) << "\n"
                              << "\tJet_pt=" << Jet_p4[jet_idx].pt() << "\n"
                              << "\tJetbtag_score=" << Jet_bTag_score[jet_idx] << "\n";
                    throw;
                } catch (...) {
                    std::cerr << "bTagShapeCorrProvider::getBTagShapeSF : Unknown error occurred when evaluating "
                                 "correction\n";
                    std::cerr << "\tunc_name=" << unc_name << "\n"
                              << "\tjet_idx=" << jet_idx << "\n"
                              << "\tJet_Flavour=" << Jet_Flavour[jet_idx] << "\n"
                              << "\tabs(Jet_eta)=" << std::abs(Jet_p4[jet_idx].eta()) << "\n"
                              << "\tJet_pt=" << Jet_p4[jet_idx].pt() << "\n"
                              << "\tJetbtag_score=" << Jet_bTag_score[jet_idx] << "\n";
                    throw;
                }
            }
            return sf_product;
        }

      private:
        std::unique_ptr<CorrectionSet> corrections_;
        Correction::Ref shape_corr_;
        std::string _year;
        double variationMinPtLight_;
    };

}  //namespace correction

#endif  // CORRECTION_BTAGSHAPECORRPROVIDER_H
