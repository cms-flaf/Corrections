#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

    // Bosonic recoil corrections following Higgs LepRare recommendation: https://cms-higgs-leprare.docs.cern.ch/htt-common/V_recoil/

    class BosonicRecoilProvider : public CorrectionsBase<BosonicRecoilProvider> {
      public:
        using LorentzVectorM = correction::LorentzVectorM;
        using RVecF = correction::RVecF;
        using RVecI = correction::RVecI;

        struct PolarVector {
            double pt{0.};
            double phi{0.};
        };
        struct XYVector {
            double px{0.};
            double py{0.};
        };

        struct RecoilResult {
            double upara{0.};
            double uperp{0.};
            double upara_corr{0.};
            double uperp_corr{0.};
            double met_pt_corr{0.};
            double met_phi_corr{0.};
        };

        struct RecoilSystematics {
            double hpara{0.};
            double hperp{0.};
            double hpara_variation{0.};
            double hperp_variation{0.};
            double met_pt{0.};
            double met_phi{0.};
        };

        BosonicRecoilProvider(const std::string& jsonFile)
            : cset_(CorrectionSet::from_file(jsonFile)),
              corr_rescaling_(cset_->at("Recoil_correction_Rescaling")),
              corr_qmphist_(cset_->at("Recoil_correction_QuantileMapHist")),
              corr_qmpfit_(cset_->at("Recoil_correction_QuantileMapFit")),
              corr_unc_(cset_->at("Recoil_correction_Uncertainty")) {}

        // start of workaround if AnaProd does not save GenPart inputs
        static bool IsNeutrino(const int pdgId) {
            const int apdg = std::abs(pdgId);
            return apdg == 12 || apdg == 14 || apdg == 16;
        }

        static bool IsChargedLepton(const int pdgId) {
            const int apdg = std::abs(pdgId);
            return apdg == 11 || apdg == 13 || apdg == 15;
        }

        static bool PassLHEBosonParticleSelection(const int pdgId, const int status, const bool includeNeutrinos) {
            // LHEPart_status == -1 incoming, 1 outgoing
            if (status != 1)
                return false;

            const bool isChargedLep = IsChargedLepton(pdgId);
            const bool isNu = IsNeutrino(pdgId);

            if (isChargedLep)
                return true;
            if (includeNeutrinos && isNu)
                return true;
            return false;
        }

        static LorentzVectorM GetLHEBosonP4(const RVecF& pt,
                                            const RVecF& eta,
                                            const RVecF& phi,
                                            const RVecF& mass,
                                            const RVecI& pdgId,
                                            const RVecI& status) {
            const size_t n = pt.size();
            if (eta.size() != n || phi.size() != n || mass.size() != n || pdgId.size() != n || status.size() != n) {
                throw std::runtime_error("GetLHEBosonP4: inconsistent LHEPart collection sizes");
            }

            LorentzVectorM p4;
            for (size_t i = 0; i < n; ++i) {
                if (!PassLHEBosonParticleSelection(pdgId[i], status[i], true))
                    continue;
                p4 += LorentzVectorM(pt[i], eta[i], phi[i], mass[i]);
            }
            return p4;
        }

        static bool HasValidLepVisGenMatch(const int lep1_gen_kind, const int lep2_gen_kind) {
            // for bbtautau anaTuples, tau1_gen_kind==NoMatch is the default when gen matching is unavailable
            // the following is used for the workaround calculations.
            return lep1_gen_kind != 6 &&
                   lep2_gen_kind != 6;  // 6 = GenLeptonMatch::NoMatch in anaTuples for tau_gen_kind
        }

        static LorentzVectorM GetVisibleBosonP4FromLepGenVis(const float lep1_pt,
                                                             const float lep1_eta,
                                                             const float lep1_phi,
                                                             const float lep1_mass,
                                                             const float lep2_pt,
                                                             const float lep2_eta,
                                                             const float lep2_phi,
                                                             const float lep2_mass) {
            LorentzVectorM lep1(lep1_pt, lep1_eta, lep1_phi, lep1_mass);
            LorentzVectorM lep2(lep2_pt, lep2_eta, lep2_phi, lep2_mass);
            return lep1 + lep2;
        }

        // the function below is called when NoMatch for tau1_gen_kind or tau2_gen_kind
        // the puppimet_pt and puppimet_phi are returned
        static RecoilResult GetIdentityRecoilResult(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double metPt, double metPhi) {
            const auto [upara, uperp] = computeU(bosonPt, bosonPhi, visPt, visPhi, metPt, metPhi);
            return {upara, uperp, upara, uperp, metPt, metPhi};
        }

        // the function below is called when NoMatch for tau1_gen_kind or tau2_gen_kind
        // the puppimet_pt and puppimet_phi are returned
        static RecoilSystematics GetIdentityRecoilSystematics(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double metPt, double metPhi) {
            const auto [hpara, hperp] = computeH(bosonPt, bosonPhi, visPt, visPhi, metPt, metPhi);
            return {hpara, hperp, hpara, hperp, metPt, metPhi};
        }

        // end of workaround if AnaProd does not save GenPart inputs

        static bool PassRecoilJetHornLogic(const float pt, const float eta) {
            const float abs_eta = std::abs(eta);
            const bool in_horn = (abs_eta > 2.5f && abs_eta < 3.0f);
            if (in_horn)
                return pt > 50.f;
            return pt > 30.f;
        }

        static float GetRecoilNJetFromReco(const float b1_pt,
                                           const float b1_eta,
                                           const float b2_pt,
                                           const float b2_eta,
                                           const RVecF& vbf_pt,
                                           const RVecF& vbf_eta) {
            if (vbf_pt.size() != vbf_eta.size()) {
                throw std::runtime_error("GetRecoilNJetFromReco: inconsistent VBF jet collection size");
            }
            int nbjet = 0;
            if (PassRecoilJetHornLogic(b1_pt, b1_eta))
                ++nbjet;
            if (PassRecoilJetHornLogic(b2_pt, b2_eta))
                ++nbjet;

            int nvbfjet = 0;
            for (std::size_t i = 0; i < vbf_pt.size(); ++i) {
                if (PassRecoilJetHornLogic(vbf_pt[i], vbf_eta[i]))
                    ++nvbfjet;
            }

            const int njet = nbjet + nvbfjet;
            if (njet <= 0)
                return 0.f;
            if (njet == 1)
                return 1.f;
            return 2.f;
        }

        static XYVector ptPhiToXY(double pt, double phi) { return {pt * std::cos(phi), pt * std::sin(phi)}; }

        static PolarVector xyToPtPhi(double px, double py) { return {std::hypot(px, py), std::atan2(py, px)}; }

        static std::pair<double, double> projectParallelPerp(double x, double y, double refx, double refy) {
            const double refpt = std::hypot(refx, refy);
            if (refpt < 1e-12)
                return {0., 0.};
            const double ux = refx / refpt;
            const double uy = refy / refpt;
            const double vx = -uy;
            const double vy = ux;
            return {x * ux + y * uy, x * vx + y * vy};
        }

        static XYVector buildFromParallelPerp(double para, double perp, double refx, double refy) {
            const double refpt = std::hypot(refx, refy);
            if (refpt < 1e-12)
                return {0., 0.};
            const double ux = refx / refpt;
            const double uy = refy / refpt;
            const double vx = -uy;
            const double vy = ux;
            return {para * ux + perp * vx, para * uy + perp * vy};
        }

        static std::pair<double, double> computeU(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double metPt, double metPhi) {
            const auto V = ptPhiToXY(bosonPt, bosonPhi);
            const auto Vvis = ptPhiToXY(visPt, visPhi);
            const auto MET = ptPhiToXY(metPt, metPhi);
            const double Ux = MET.px + Vvis.px - V.px;
            const double Uy = MET.py + Vvis.py - V.py;
            return projectParallelPerp(Ux, Uy, V.px, V.py);
        }

        static std::pair<double, double> computeH(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double metPt, double metPhi) {
            const auto V = ptPhiToXY(bosonPt, bosonPhi);
            const auto Vvis = ptPhiToXY(visPt, visPhi);
            const auto MET = ptPhiToXY(metPt, metPhi);
            const double Hx = -Vvis.px - MET.px;
            const double Hy = -Vvis.py - MET.py;
            return projectParallelPerp(Hx, Hy, V.px, V.py);
        }

        static PolarVector metFromU(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double upara, double uperp) {
            const auto V = ptPhiToXY(bosonPt, bosonPhi);
            const auto Vvis = ptPhiToXY(visPt, visPhi);
            const auto U = buildFromParallelPerp(upara, uperp, V.px, V.py);
            return xyToPtPhi(U.px - Vvis.px + V.px, U.py - Vvis.py + V.py);
        }

        static PolarVector metFromH(
            double bosonPt, double bosonPhi, double visPt, double visPhi, double hpara, double hperp) {
            const auto V = ptPhiToXY(bosonPt, bosonPhi);
            const auto Vvis = ptPhiToXY(visPt, visPhi);
            const auto H = buildFromParallelPerp(hpara, hperp, V.px, V.py);
            return xyToPtPhi(-H.px - Vvis.px, -H.py - Vvis.py);
        }

        double correctComponent(const std::string& order,
                                double njet,
                                double ptll,
                                const std::string& var,
                                double val,
                                const std::string& method) const {
            if (method == "Rescaling") {
                return safeEvaluate(corr_rescaling_, order, njet, ptll, var, val);
            }
            if (method == "QuantileMapHist") {
                return safeEvaluate(corr_qmphist_, order, njet, ptll, var, val);
            }
            if (method == "QuantileMapFit") {
                if (std::abs(val) > 150.) {
                    return safeEvaluate(corr_rescaling_, order, njet, ptll, var, val);
                }
                throw std::runtime_error("QuantileMapFit not implemented in the current setup");
            }
            throw std::runtime_error("Unknown recoil correction method: " + method);
        }

        RecoilResult correctMET(const std::string& order,
                                double njet,
                                double ptll,
                                double bosonPt,
                                double bosonPhi,
                                double visPt,
                                double visPhi,
                                double metPt,
                                double metPhi,
                                const std::string& method) const {
            const auto [upara, uperp] = computeU(bosonPt, bosonPhi, visPt, visPhi, metPt, metPhi);
            const double uparaCorr = correctComponent(order, njet, ptll, "Upara", upara, method);
            const double uperpCorr = correctComponent(order, njet, ptll, "Uperp", uperp, method);
            const auto metCorr = metFromU(bosonPt, bosonPhi, visPt, visPhi, uparaCorr, uperpCorr);
            return {upara, uperp, uparaCorr, uperpCorr, metCorr.pt, metCorr.phi};
        }

        RecoilSystematics applyUncertainty(const std::string& order,
                                           double njet,
                                           double ptll,
                                           double bosonPt,
                                           double bosonPhi,
                                           double visPt,
                                           double visPhi,
                                           double metPtNom,
                                           double metPhiNom,
                                           const std::string& syst) const {
            if (syst != "RespUp" && syst != "RespDown" && syst != "ResolUp" && syst != "ResolDown") {
                throw std::runtime_error("Unknown recoil systematic: " + syst);
            }

            const auto [hpara, hperp] = computeH(bosonPt, bosonPhi, visPt, visPhi, metPtNom, metPhiNom);
            const double hparaVar = safeEvaluate(corr_unc_, order, njet, ptll, std::string("Hpara"), hpara, syst);
            const double hperpVar = safeEvaluate(corr_unc_, order, njet, ptll, std::string("Hperp"), hperp, syst);
            const auto metVar = metFromH(bosonPt, bosonPhi, visPt, visPhi, hparaVar, hperpVar);
            return {hpara, hperp, hparaVar, hperpVar, metVar.pt, metVar.phi};
        }

      private:
        std::unique_ptr<CorrectionSet> cset_;
        Correction::Ref corr_rescaling_, corr_qmphist_, corr_qmpfit_, corr_unc_;
    };

}  //namespace correction