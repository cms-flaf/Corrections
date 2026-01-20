#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
    class JetCorrectionProvider : public CorrectionsBase<JetCorrectionProvider> {
      public:
        enum class UncSource : int {
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

        // json_file_name - path to json file with corrections
        // e.g. /cvmfs/cms-griddata.cern.ch/cat/metadata/JME/2022_Summer2022/jet_jerc.json.gz

        // jecTag_corrName_algoType

        // jec_tag - a string describing when sample was produced and type of sample
        // e.g. Summer22_22Sep2023_V2_MC

        // algo - type of jet algorithm
        // e.g. AK4PFPuppi
        JetCorrectionProvider(std::string const& json_file_name,
                              std::string const& jetsmear_file_name,
                              std::string const& jec_tag,
                              std::string const& other_jec_tag,
                              std::string const& jer_tag,
                              std::string const& algo,
                              std::string const& fatjson_file_name,
                              std::string const& fatjec_tag,
                              std::string const& other_fatjec_tag,
                              std::string const& fatjer_tag,
                              std::string const& fatalgo,
                              std::string const& year,
                              bool is_data,
                              bool use_regrouped,
                              bool apply_compound)
            : corrset_(CorrectionSet::from_file(json_file_name)),
              jersmear_corr_(CorrectionSet::from_file(jetsmear_file_name)->at("JERSmear")),
              corr_jer_sf_(corrset_->at(jer_tag + "_ScaleFactor_" + algo)),
              corr_jer_res_(corrset_->at(jer_tag + "_PtResolution_" + algo)),
              cmpd_corr_(corrset_->compound().at(other_jec_tag + "_L1L2L3Res_" + algo)),
              fat_corrset_(CorrectionSet::from_file(fatjson_file_name)),
              fat_jersmear_corr_(CorrectionSet::from_file(jetsmear_file_name)->at("JERSmear")),
              fat_corr_jer_sf_(fat_corrset_->at(fatjer_tag + "_ScaleFactor_" + fatalgo)),
              fat_corr_jer_res_(fat_corrset_->at(fatjer_tag + "_PtResolution_" + fatalgo)),
              fat_cmpd_corr_(fat_corrset_->compound().at(other_fatjec_tag + "_L1L2L3Res_" + fatalgo)),
              is_data_(is_data),
              year_(year),
              apply_cmpd_(apply_compound) {
            // map with uncertainty sources should only be filled for MC
            std::cout << "JetCorrectionProvider: init" << std::endl;
            if (!is_data_) {
                auto const& unc_map_ref = use_regrouped ? unc_map_regrouped : unc_map_total;
                for (auto const& [unc_source, unc_name] : unc_map_ref) {
                    std::string full_name = jec_tag;
                    full_name += '_';
                    full_name += unc_name;
                    full_name += '_';
                    if (year_dep_map.at(unc_source)) {
                        full_name += year;
                        full_name += '_';
                    }
                    full_name += algo;
                    unc_map_[unc_source] = full_name;
                }
            }
        }

        std::map<std::pair<UncSource, UncScale>, RVecLV> getShiftedP4(RVecF Jet_pt,
                                                                      const RVecF& Jet_eta,
                                                                      const RVecF& Jet_phi,
                                                                      RVecF Jet_mass,
                                                                      const RVecF& Jet_rawFactor,
                                                                      const RVecF& Jet_area,
                                                                      const float rho,
                                                                      int event,
                                                                      bool apply_jer,
                                                                      bool require_run_number,
                                                                      const unsigned int run,
                                                                      bool wantPhi,
                                                                      bool apply_forward_jet_horns_fix,
                                                                      const RVecF& GenJet_pt = {},
                                                                      const RVecI& Jet_genJetIdx = {}) const {
            std::map<std::pair<UncSource, UncScale>, RVecLV> all_shifted_p4;
            std::vector<UncScale> uncScales = {UncScale::Up, UncScale::Down};

            size_t sz = Jet_pt.size();
            std::vector<float> jer_pt_resolutions(sz);
            RVecLV central_p4(sz);
            for (size_t i = 0; i < sz; ++i) {
                bool is_jet_in_horn =
                    std::abs(Jet_eta[i]) >= 2.5 && std::abs(Jet_eta[i]) <= 3 && Jet_genJetIdx[i] != -1;
                // uscaling
                if (apply_cmpd_) {
                    Jet_pt[i] *= 1.0 - Jet_rawFactor[i];
                    Jet_mass[i] *= 1.0 - Jet_rawFactor[i];
                }
                if (!is_data_ && apply_jer) {
                    // extract jer scale factor and resolution
                    float jer_sf = corr_jer_sf_->evaluate({Jet_eta[i], Jet_pt[i], "nom"});
                    float jer_pt_res = corr_jer_res_->evaluate({Jet_eta[i], Jet_pt[i], rho});
                    jer_pt_resolutions[i] = jer_pt_res;

                    int genjet_idx = Jet_genJetIdx[i];
                    float genjet_pt = genjet_idx != -1 ? GenJet_pt[genjet_idx] : -1.0;
                    float jersmear_factor =
                        jersmear_corr_->evaluate({Jet_pt[i], Jet_eta[i], genjet_pt, rho, event, jer_pt_res, jer_sf});
                    // temporary fix for jet horn issue --> do not apply JER for eta range and jet matched to genjet

                    if (is_jet_in_horn) {
                        jersmear_factor = 1.0;  // do not apply JER for jets in the horn
                    }

                    // // apply jer smearing (only for MC)
                    Jet_pt[i] *= jersmear_factor;
                    Jet_mass[i] *= jersmear_factor;
                }

                // evaluate and apply compound correction
                if (apply_cmpd_) {
                    float cmpd_sf = 1.0;
                    if (require_run_number) {
                        // for run3_2023BPix data and 2024 they want also phi ..
                        if (wantPhi) {
                            cmpd_sf = cmpd_corr_->evaluate(
                                {Jet_area[i], Jet_eta[i], Jet_pt[i], rho, Jet_phi[i], static_cast<float>(run)});
                        } else {
                            cmpd_sf = cmpd_corr_->evaluate(
                                {Jet_area[i],
                                 Jet_eta[i],
                                 Jet_pt[i],
                                 rho,
                                 static_cast<float>(run)});  // for 2023, 2024 data and 2023BPix data&MC, need also run number
                        }
                    } else {
                        if (wantPhi) {
                            cmpd_sf = cmpd_corr_->evaluate(
                                {Jet_area[i], Jet_eta[i], Jet_pt[i], rho, Jet_phi[i]}); // for 2024 MC, need phi but NOT run number...
                        } else {
                            cmpd_sf = cmpd_corr_->evaluate(
                                {Jet_area[i],
                                 Jet_eta[i],
                                 Jet_pt[i],
                                 rho});
                        }
                    }
                    Jet_pt[i] *= cmpd_sf;
                    Jet_mass[i] *= cmpd_sf;
                }

                central_p4[i] = LorentzVectorM(Jet_pt[i], Jet_eta[i], Jet_phi[i], Jet_mass[i]);
            }

            all_shifted_p4.insert({{UncSource::Central, UncScale::Central}, central_p4});

            // apply uncertainties from uncertainty map
            // this part should not be executed for data
            if (!is_data_) {
                for (auto const& uncScale : uncScales) {
                    for (auto const& [unc_source, unc_name] : unc_map_) {
                        RVecLV shifted_p4(sz);
                        if (unc_source == UncSource::JER) {
                            if (apply_jer) {
                                for (size_t jet_idx = 0; jet_idx < sz; ++jet_idx) {
                                    float sf = 1.0;
                                    bool is_jet_in_horn = std::abs(Jet_eta[jet_idx]) >= 2.5 &&
                                                          std::abs(Jet_eta[jet_idx]) <= 3 &&
                                                          Jet_genJetIdx[jet_idx] != -1;
                                    sf += static_cast<int>(uncScale) * jer_pt_resolutions[jet_idx];
                                    if (is_jet_in_horn) {
                                        sf = 1.0;  // do not apply JER for jets in the horn
                                    }
                                    shifted_p4[jet_idx] = LorentzVectorM(sf * Jet_pt[jet_idx],
                                                                         Jet_eta[jet_idx],
                                                                         Jet_phi[jet_idx],
                                                                         sf * Jet_mass[jet_idx]);
                                }
                                all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                            }
                        } else {
                            for (size_t jet_idx = 0; jet_idx < sz; ++jet_idx) {
                                float sf = 1.0;
                                Correction::Ref corr = corrset_->at(unc_name);
                                float unc = corr->evaluate({Jet_eta[jet_idx], Jet_pt[jet_idx]});
                                sf += static_cast<int>(uncScale) * unc;
                                shifted_p4[jet_idx] = LorentzVectorM(
                                    sf * Jet_pt[jet_idx], Jet_eta[jet_idx], Jet_phi[jet_idx], sf * Jet_mass[jet_idx]);
                            }
                            all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                        }
                    }
                }
            }
            return all_shifted_p4;
        }

        std::map<std::pair<UncSource, UncScale>, RVecLV> getShiftedP4_FatJet(RVecF FatJet_pt,
                                                                             const RVecF& FatJet_eta,
                                                                             const RVecF& FatJet_phi,
                                                                             RVecF FatJet_mass,
                                                                             const RVecF& FatJet_rawFactor,
                                                                             const RVecF& FatJet_area,
                                                                             const float rho,
                                                                             int event,
                                                                             bool apply_jer,
                                                                             bool require_run_number,
                                                                             const unsigned int run,
                                                                             bool wantPhi,
                                                                             bool apply_forward_jet_horns_fix,
                                                                             const RVecF& GenFatJet_pt = {},
                                                                             const RVecI& FatJet_genJetIdx = {}) const {
            std::map<std::pair<UncSource, UncScale>, RVecLV> all_shifted_p4;
            std::vector<UncScale> uncScales = {UncScale::Up, UncScale::Down};

            size_t sz = FatJet_pt.size();
            std::vector<float> fatjer_pt_resolutions(sz);
            RVecLV central_p4(sz);
            for (size_t i = 0; i < sz; ++i) {
                bool is_jet_in_horn =
                    std::abs(FatJet_eta[i]) >= 2.5 && std::abs(FatJet_eta[i]) <= 3 && FatJet_genJetIdx[i] != -1;
                // uscaling
                if (apply_cmpd_) {
                    FatJet_pt[i] *= 1.0 - FatJet_rawFactor[i];
                    FatJet_mass[i] *= 1.0 - FatJet_rawFactor[i];
                }
                if (!is_data_ && apply_jer) {
                    // extract jer scale factor and resolution
                    float fatjer_sf = fat_corr_jer_sf_->evaluate({FatJet_eta[i], FatJet_pt[i], "nom"});
                    float fatjer_pt_res = fat_corr_jer_res_->evaluate({FatJet_eta[i], FatJet_pt[i], rho});
                    fatjer_pt_resolutions[i] = fatjer_pt_res;

                    int genjet_idx = FatJet_genJetIdx[i];
                    float genjet_pt = genjet_idx != -1 ? GenFatJet_pt[genjet_idx] : -1.0;
                    float jersmear_factor = fat_jersmear_corr_->evaluate(
                        {FatJet_pt[i], FatJet_eta[i], genjet_pt, rho, event, fatjer_pt_res, fatjer_sf});
                    // temporary fix for jet horn issue --> do not apply JER for eta range and jet matched to genjet

                    if (is_jet_in_horn) {
                        jersmear_factor = 1.0;  // do not apply JER for jets in the horn
                    }

                    // // apply jer smearing (only for MC)
                    FatJet_pt[i] *= jersmear_factor;
                    FatJet_mass[i] *= jersmear_factor;
                }

                // evaluate and apply compound correction
                if (apply_cmpd_) {
                    float cmpd_sf = 1.0;
                    if (require_run_number) {
                        // for run3_2023BPix data they want also phi ..
                        if (wantPhi) {
                            cmpd_sf = fat_cmpd_corr_->evaluate({FatJet_area[i],
                                                                FatJet_eta[i],
                                                                FatJet_pt[i],
                                                                rho,
                                                                FatJet_phi[i],
                                                                static_cast<float>(run)});
                        } else {
                            cmpd_sf = fat_cmpd_corr_->evaluate(
                                {FatJet_area[i],
                                 FatJet_eta[i],
                                 FatJet_pt[i],
                                 rho,
                                 static_cast<float>(run)});  // for 2023 data and 2023BPix data&MC, need also run number
                        }
                    } else {
                        cmpd_sf = cmpd_corr_->evaluate({FatJet_area[i], FatJet_eta[i], FatJet_pt[i], rho});
                    }
                    FatJet_pt[i] *= cmpd_sf;
                    FatJet_mass[i] *= cmpd_sf;
                }

                central_p4[i] = LorentzVectorM(FatJet_pt[i], FatJet_eta[i], FatJet_phi[i], FatJet_mass[i]);
            }

            all_shifted_p4.insert({{UncSource::Central, UncScale::Central}, central_p4});

            // apply uncertainties from uncertainty map
            // this part should not be executed for data
            if (!is_data_) {
                for (auto const& uncScale : uncScales) {
                    for (auto const& [unc_source, unc_name] : unc_map_) {
                        RVecLV shifted_p4(sz);
                        if (unc_source == UncSource::JER) {
                            if (apply_jer) {
                                for (size_t jet_idx = 0; jet_idx < sz; ++jet_idx) {
                                    float sf = 1.0;
                                    bool is_jet_in_horn = std::abs(FatJet_eta[jet_idx]) >= 2.5 &&
                                                          std::abs(FatJet_eta[jet_idx]) <= 3 &&
                                                          FatJet_genJetIdx[jet_idx] != -1;
                                    sf += static_cast<int>(uncScale) * fatjer_pt_resolutions[jet_idx];
                                    if (is_jet_in_horn) {
                                        sf = 1.0;  // do not apply JER for jets in the horn
                                    }
                                    shifted_p4[jet_idx] = LorentzVectorM(sf * FatJet_pt[jet_idx],
                                                                         FatJet_eta[jet_idx],
                                                                         FatJet_phi[jet_idx],
                                                                         sf * FatJet_mass[jet_idx]);
                                }
                                all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                            }
                        } else {
                            for (size_t jet_idx = 0; jet_idx < sz; ++jet_idx) {
                                float sf = 1.0;
                                Correction::Ref corr = fat_corrset_->at(unc_name);
                                float unc = corr->evaluate({FatJet_eta[jet_idx], FatJet_pt[jet_idx]});
                                sf += static_cast<int>(uncScale) * unc;
                                shifted_p4[jet_idx] = LorentzVectorM(sf * FatJet_pt[jet_idx],
                                                                     FatJet_eta[jet_idx],
                                                                     FatJet_phi[jet_idx],
                                                                     sf * FatJet_mass[jet_idx]);
                            }
                            all_shifted_p4.insert({{unc_source, uncScale}, shifted_p4});
                        }
                    }
                }
            }
            return all_shifted_p4;
        }

        RVecF GetResolutions(RVecF pt, RVecF mass, RVecF const& raw_factor, RVecF const& eta, float rho) const {
            size_t sz = pt.size();
            RVecF res(sz);
            for (size_t i = 0; i < sz; ++i) {
                pt[i] *= 1.0 - raw_factor[i];
                mass[i] *= 1.0 - raw_factor[i];
                float jer_sf = corr_jer_sf_->evaluate({eta[i], pt[i], "nom"});
                float jer_pt_res = corr_jer_res_->evaluate({eta[i], pt[i], rho});
                res[i] = jer_pt_res;
            }
            return res;
        }

      private:
        std::map<UncSource, std::string> unc_map_;
        std::unique_ptr<CorrectionSet> corrset_;
        Correction::Ref jersmear_corr_;  // aka shared_ptr<Correction const>, sizeof = 8
        Correction::Ref corr_jer_sf_;
        Correction::Ref corr_jer_res_;
        CompoundCorrection::Ref cmpd_corr_;
        std::unique_ptr<CorrectionSet> fat_corrset_;
        Correction::Ref fat_jersmear_corr_;  // aka shared_ptr<Correction const>, sizeof = 8
        Correction::Ref fat_corr_jer_sf_;
        Correction::Ref fat_corr_jer_res_;
        CompoundCorrection::Ref fat_cmpd_corr_;
        bool is_data_;
        std::string year_;
        bool apply_cmpd_;

        inline static const std::map<UncSource, std::string> unc_map_total = {{UncSource::Total, "Total"},
                                                                              {UncSource::JER, "JER"}};

        inline static const std::map<UncSource, bool> year_dep_map = {{UncSource::Central, false},
                                                                      {UncSource::JER, false},
                                                                      {UncSource::Total, false},
                                                                      {UncSource::RelativeBal, false},
                                                                      {UncSource::HF, false},
                                                                      {UncSource::BBEC1, false},
                                                                      {UncSource::EC2, false},
                                                                      {UncSource::Absolute, false},
                                                                      {UncSource::FlavorQCD, false},
                                                                      {UncSource::BBEC1_year, true},
                                                                      {UncSource::Absolute_year, true},
                                                                      {UncSource::EC2_year, true},
                                                                      {UncSource::HF_year, true},
                                                                      {UncSource::RelativeSample_year, true}};

        inline static const std::map<UncSource, std::string> unc_map_regrouped = {
            {UncSource::JER, "JER"},
            {UncSource::RelativeBal, "Regrouped_RelativeBal"},
            {UncSource::HF, "Regrouped_HF"},
            {UncSource::BBEC1, "Regrouped_BBEC1"},
            {UncSource::EC2, "Regrouped_EC2"},
            {UncSource::Absolute, "Regrouped_Absolute"},
            {UncSource::FlavorQCD, "Regrouped_FlavorQCD"},
            {UncSource::BBEC1_year, "Regrouped_BBEC1"},
            {UncSource::Absolute_year, "Regrouped_Absolute"},
            {UncSource::EC2_year, "Regrouped_EC2"},
            {UncSource::HF_year, "Regrouped_RelativeStatHF"},
            {UncSource::RelativeSample_year, "Regrouped_RelativeSample"}};
    };

}  // namespace correction
