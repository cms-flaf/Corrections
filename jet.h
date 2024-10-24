#pragma once

#include "correction.h"
#include "corrections.h"
#include "JMESystematicsCalculators.h"

namespace correction {

    // base class for jet corrections
    template <typename CorrClass>
    class JetCorrProviderBase : public CorrectionsBase<CorrClass>
    {
        public:
        enum class UncSource : int
        {
            Central = -1,
            JER = 0,
            Total = 1,
            RelativeBal = 2,
            HF = 3,
            BBEC1 = 4,
            EC2 = 5,
            Absolute = 6,
            FlavorQCD = 7,
            BBEC1_year = 8,
            Absolute_year = 9,
            EC2_year = 10,
            HF_year = 11,
            RelativeSample_year = 12
        };
    };

    class JetCorrProvider : public CorrectionsBase<JetCorrProvider> {
    public:
        static const std::string getFullNameUnc(const std::string source_name, const std::string year, bool need_year){
            return need_year ? source_name+year : source_name;
        }
        static const std::string& getScaleStr(UncScale scale)
        {
            static const std::map<UncScale, std::string> names = {
                { UncScale::Down, "down" },
                { UncScale::Central, "nom" },
                { UncScale::Up, "up" },
            };
            return names.at(scale);
        }
        static const int GetScaleIdx(UncScale scale){
            static const std::map<UncScale, int> scale_indexes = {
                {UncScale::Up, 1},
                {UncScale::Down,2},
                {UncScale::Central,0},
            };
            return scale_indexes.at(scale);
        }
        static const int GetJesIdx(UncSource source, UncScale scale){
            int index = static_cast<int>(source) * 2 + GetScaleIdx(scale);
            return std::max(index, 0);
        }
        static const std::map<UncSource,std::tuple<std::string,bool,bool>> getUncMap (){
            static const std::map<UncSource,std::tuple<std::string,bool,bool>> UncMap = {
                {UncSource::Central, {"Central", false,false}},
                {UncSource::JER, {"JER", false,false}},
                {UncSource::FlavorQCD,{"FlavorQCD",true,false}},
                {UncSource::RelativeBal,{"RelativeBal",true,false}},
                {UncSource::HF,{"HF",true,false}},
                {UncSource::BBEC1,{"BBEC1",true,false}},
                {UncSource::EC2,{"EC2",true,false}},
                {UncSource::Absolute,{"Absolute",true,false}},
                {UncSource::Total,{"Total",true,false}},
                {UncSource::BBEC1_year,{"BBEC1_",true,true}},
                {UncSource::Absolute_year,{"Absolute_",true,true}},
                {UncSource::EC2_year,{"EC2_",true,true}},
                {UncSource::HF_year,{"HF_",true,true}},
                {UncSource::RelativeSample_year,{"RelativeSample_",true,true}},
            };
            return UncMap;
        }

        JetCorrProvider(const std::string& ptResolution,const std::string& ptResolutionSF, const std::string& JesTxtFile, const std::string& year)
        {
            jvc_total.setSmearing(ptResolution, ptResolutionSF, false, true, 0.2, 3);
            jvc_total.setAddHEM2018Issue(year=="2018");
            for (auto& [unc_source ,unc_features] : getUncMap()){
                if(! std::get<1>(unc_features) ) continue;
                std::string jes_name = getFullNameUnc(std::get<0>(unc_features), year, std::get<2>(unc_features));
                jvc_total.addJESUncertainty(jes_name,JetCorrectorParameters{JesTxtFile,jes_name});
            }
        }


        std::map<std::pair<UncSource,UncScale>, RVecLV> getShiftedP4(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi,
                        const RVecF& Jet_mass, const RVecF& Jet_rawFactor, const RVecF& Jet_area,
                        const RVecI& Jet_jetId, const float rho, const RVecI& Jet_partonFlavour,
                        std::uint32_t seed, const RVecF& GenJet_pt, const RVecF& GenJet_eta,
                        const RVecF& GenJet_phi, const RVecF& GenJet_mass, int event) const {
            std::map<std::pair<UncSource,UncScale>, RVecLV> all_shifted_p4;
            auto result = jvc_total.produce(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_rawFactor,
                                        Jet_area, Jet_jetId, rho, Jet_partonFlavour, seed,
                                        GenJet_pt, GenJet_eta, GenJet_phi, GenJet_mass, event);
            std::vector<UncScale> uncScales={UncScale::Central, UncScale::Up, UncScale::Down};
            for (auto& uncScale : uncScales){
                for (auto & [unc_source ,unc_features] : getUncMap()){
                    RVecLV shifted_p4(Jet_pt.size());
                    if(unc_source != UncSource::Central && uncScale == UncScale::Central) continue;
                    if(unc_source == UncSource::Central && uncScale != UncScale::Central) continue;
                    int scale_idx = GetJesIdx(unc_source, uncScale);
                    for (int jet_idx= 0 ; jet_idx < Jet_pt.size(); ++jet_idx){
                        shifted_p4[jet_idx] = LorentzVectorM(result.pt(scale_idx)[jet_idx], Jet_eta[jet_idx],
                        Jet_phi[jet_idx], result.mass(scale_idx)[jet_idx]);
                    }
                all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                }
            }
            return all_shifted_p4;
        }
        RVecF getResolution(const RVecF& Jet_pt, const RVecF& Jet_eta, const float rho) const {
            return jvc_total.getResolution(Jet_pt, Jet_eta, rho);
        }

    private:
        JetVariationsCalculator jvc_total ;
    };


    // run3 code starts here
    // main difference: all corrections are retrieved from json file using correctionlib
    class JetCorrectionProvider : public JetCorrProviderBase<JetCorrectionProvider>
    {
        public:
        // json_file_name - path to json file with corrections
        // e.g. /cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/2022_Summer2022/jet_jerc.json.gz

        // jecTag_corrName_algoType

        // jec_tag - a string describing when sample was produced and type of sample
        // e.g. Summer22_22Sep2023_V2_MC

        // algo - type of jet algorithm
        // e.g. AK4PFPuppi
        JetCorrectionProvider(std::string const& json_file_name, std::string const& jec_tag, std::string const& algo, std::string const& year)
        :   corrset_(CorrectionSet::from_file(json_file_name))
        ,   jec_tag_(jec_tag)
        ,   algo_(algo)
        ,   year_(year)
        {}

        std::map<std::pair<UncSource, UncScale>, RVecLV> getShiftedP4(const RVecF& Jet_pt, const RVecF& Jet_eta, const RVecF& Jet_phi, const RVecF& Jet_mass) const
        {
            std::map<std::pair<UncSource, UncScale>, RVecLV> all_shifted_p4;
            std::vector<UncScale> uncScales = { UncScale::Central, UncScale::Up, UncScale::Down };
            for (auto const& uncScale: uncScales)
            {
                for (auto const& [unc_source, unc_name]: unc_map)
                {
                    if (unc_source != UncSource::Central && uncScale == UncScale::Central)
                    {
                        continue;
                    }

                    if (unc_source == UncSource::Central && uncScale != UncScale::Central)
                    {
                        continue;
                    }

                    RVecLV shifted_p4(Jet_pt.size());
                    for (size_t jet_idx = 0 ; jet_idx < Jet_pt.size(); ++jet_idx)
                    {
                        double sf = 1.0;
                        if (unc_source != UncSource::Central)
                        {
                            auto last = --unc_name.end();
                            std::string name = unc_name;
                            if (*last == '_')
                            {
                                name += year_;
                            }
                            name += '_';
                            std::string full_name = jec_tag_ + name + algo_;
                            Correction::Ref corr = corrset_->at(full_name);
                            double unc = corr->evaluate({Jet_eta[jet_idx], Jet_pt[jet_idx]});
                            sf += static_cast<int>(uncScale)*unc;
                        }
                        shifted_p4[jet_idx] = LorentzVectorM(sf*Jet_pt[jet_idx], Jet_eta[jet_idx], Jet_phi[jet_idx], sf*Jet_mass[jet_idx]);
                    }
                    all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                }
            }
            return all_shifted_p4;
        }

        private:
        std::unique_ptr<CorrectionSet> corrset_;
        std::string jec_tag_;
        std::string algo_;
        std::string year_;

        inline static const std::map<UncSource, std::string> unc_map = { { UncSource::Central, "_Central" },
                                                                         { UncSource::Total, "_Total" } };

        // inline static const std::map<UncSource, std::string> unc_map = { { UncSource::Central, "Central" },
        //                                                                  { UncSource::JER, "JER" },
        //                                                                  { UncSource::Total, "Total" },
        //                                                                  { UncSource::RelativeBal, "Regrouped_RelativeBal" },
        //                                                                  { UncSource::HF, "Regrouped_HF" },
        //                                                                  { UncSource::BBEC1, "Regrouped_BBEC1" },
        //                                                                  { UncSource::EC2, "Regrouped_EC2" },
        //                                                                  { UncSource::Absolute, "Regrouped_Absolute" },
        //                                                                  { UncSource::FlavorQCD, "Regrouped_FlavorQCD" },
        //                                                                  { UncSource::BBEC1_year, "Regrouped_BBEC1_" },
        //                                                                  { UncSource::Absolute_year, "Regrouped_Absolute_" },
        //                                                                  { UncSource::EC2_year, "Regrouped_EC2_" },
        //                                                                  { UncSource::HF_year, "Regrouped_RelativeStatHF_" },
        //                                                                  { UncSource::RelativeSample_year, "Regrouped_RelativeSample_" } };
    };

} // namespace correction