#pragma once

#include "corrections.h"

namespace recoil {

struct PolarVector { double pt{0.}; double phi{0.}; };
struct XYVector { double px{0.}; double py{0.}; };

struct RecoilResult {
    double upara{0.}; double uperp{0.};
    double upara_corr{0.}; double uperp_corr{0.};
    double met_pt_corr{0.}; double met_phi_corr{0.};
};

struct RecoilSystematics {
    double hpara{0.}; double hperp{0.};
    double hpara_variation{0.}; double hperp_variation{0.};
    double met_pt{0.}; double met_phi{0.};
};

class BosonicRecoilCorrection {
public:
ic:
    explicit BosonicRecoilCorrection(const std::string& period, const std::string& analysis_path) {
        static const std::map<std::string, std::string> json_map = {
            {"Run3_2022", "Recoil_corrections_2022preEE_v5.json.gz"},
            {"Run3_2022EE", "Recoil_corrections_2022postEE_v5.json.gz"},
            {"Run3_2023", "Recoil_corrections_2023preBPix_v5.json.gz"},
            {"Run3_2023BPix", "Recoil_corrections_2023postBPix_v5.json.gz"},
            {"Run3_2024", "Recoil_corrections_2024_v5.json.gz"},
        };

        const auto it = json_map.find(period);
        if (it == json_map.end()) {
            throw std::runtime_error("Unsupported recoil period: " + period);
        }

        const std::string json_path =
            analysis_path + "/Corrections/data/hleprare/recoil/" + it->second;
        cset_ = correction::CorrectionSet::from_file(json_path);
        corr_rescaling_ = cset_->at("Recoil_correction_Rescaling");
        corr_qmphist_ = cset_->at("Recoil_correction_QuantileMapHist");
        corr_qmpfit_ = cset_->at("Recoil_correction_QuantileMapFit");
        corr_unc_ = cset_->at("Recoil_correction_Uncertainty");
    }

    static XYVector ptPhiToXY(double pt, double phi) {
        return {pt * std::cos(phi), pt * std::sin(phi)};
    }

    static PolarVector xyToPtPhi(double px, double py) {
        return {std::hypot(px, py), std::atan2(py, px)};
    }

    static std::pair<double, double> projectParallelPerp(double x, double y, double refx, double refy) {
        const double refpt = std::hypot(refx, refy);
        if (refpt < 1e-12) return {0., 0.};
        const double ux = refx / refpt;
        const double uy = refy / refpt;
        const double vx = -uy;
        const double vy = ux;
        return {x * ux + y * uy, x * vx + y * vy};
    }

    static XYVector buildFromParallelPerp(double para, double perp, double refx, double refy) {
        const double refpt = std::hypot(refx, refy);
        if (refpt < 1e-12) return {0., 0.};
        const double ux = refx / refpt;
        const double uy = refy / refpt;
        const double vx = -uy;
        const double vy = ux;
        return {para * ux + perp * vx, para * uy + perp * vy};
    }

    static std::pair<double, double> computeU(
        double genPt, double genPhi,
        double visPt, double visPhi,
        double metPt, double metPhi
    ) {
        const auto V = ptPhiToXY(genPt, genPhi);
        const auto Vvis = ptPhiToXY(visPt, visPhi);
        const auto MET = ptPhiToXY(metPt, metPhi);

        const double Ux = MET.px + Vvis.px - V.px;
        const double Uy = MET.py + Vvis.py - V.py;
        return projectParallelPerp(Ux, Uy, V.px, V.py);
    }

    static std::pair<double, double> computeH(
        double genPt, double genPhi,
        double visPt, double visPhi,
        double metPt, double metPhi
    ) {
        const auto V = ptPhiToXY(genPt, genPhi);
        const auto Vvis = ptPhiToXY(visPt, visPhi);
        const auto MET = ptPhiToXY(metPt, metPhi);

        const double Hx = -Vvis.px - MET.px;
        const double Hy = -Vvis.py - MET.py;
        return projectParallelPerp(Hx, Hy, V.px, V.py);
    }

    static PolarVector metFromU(
        double genPt, double genPhi,
        double visPt, double visPhi,
        double upara, double uperp
    ) {
        const auto V = ptPhiToXY(genPt, genPhi);
        const auto Vvis = ptPhiToXY(visPt, visPhi);
        const auto U = buildFromParallelPerp(upara, uperp, V.px, V.py);

        const double metx = U.px - Vvis.px + V.px;
        const double mety = U.py - Vvis.py + V.py;
        return xyToPtPhi(metx, mety);
    }

    static PolarVector metFromH(
        double genPt, double genPhi,
        double visPt, double visPhi,
        double hpara, double hperp
    ) {
        const auto V = ptPhiToXY(genPt, genPhi);
        const auto Vvis = ptPhiToXY(visPt, visPhi);
        const auto H = buildFromParallelPerp(hpara, hperp, V.px, V.py);

        const double metx = -H.px - Vvis.px;
        const double mety = -H.py - Vvis.py;
        return xyToPtPhi(metx, mety);
    }

    double correctComponent(const std::string& order, double njet, double ptll,
                            const std::string& var, double val,
                            const std::string& method = "QuantileMapHist") const {
        if (method == "Rescaling") {
            return corr_rescaling_->evaluate({order, njet, ptll, var, val});
        }
        if (method == "QuantileMapHist") {
            return corr_qmphist_->evaluate({order, njet, ptll, var, val});
        }
        if (method == "QuantileMapFit") {
            if (std::abs(val) > 150.) {
                return corr_rescaling_->evaluate({order, njet, ptll, var, val});
            }
            throw std::runtime_error(
                "QuantileMapFit requires manual inversion of the Data CDF; "
                "use QuantileMapHist or implement numerical inversion."
            );
        }
        throw std::runtime_error("Unknown recoil method: " + method);
    }

    RecoilResult correctMET(
        const std::string& order,
        double njet,
        double genPt, double genPhi,
        double visPt, double visPhi,
        double metPt, double metPhi,
        const std::string& method = "QuantileMapHist"
    ) const {
        const double ptll = genPt;
        const auto [upara, uperp] = computeU(genPt, genPhi, visPt, visPhi, metPt, metPhi);

        const double uparaCorr = correctComponent(order, njet, ptll, "Upara", upara, method);
        const double uperpCorr = correctComponent(order, njet, ptll, "Uperp", uperp, method);

        const auto metCorr = metFromU(genPt, genPhi, visPt, visPhi, uparaCorr, uperpCorr);

        return {upara, uperp, uparaCorr, uperpCorr, metCorr.pt, metCorr.phi};
    }

    RecoilSystResult applyUncertainty(
        const std::string& order,
        double njet,
        double genPt, double genPhi,
        double visPt, double visPhi,
        double metPtNom,
        double metPhiNom,
        const std::string& syst
    ) const {
        if (syst != "RespUp" && syst != "RespDown" &&
            syst != "ResolUp" && syst != "ResolDown") {
            throw std::runtime_error("Unknown recoil systematic: " + syst);
        }

        const double ptll = genPt;
        const auto [hpara, hperp] = computeH(genPt, genPhi, visPt, visPhi, metPtNom, metPhiNom);

        const double hparaVar = corr_unc_->evaluate({order, njet, ptll, std::string("Hpara"), hpara, syst});
        const double hperpVar = corr_unc_->evaluate({order, njet, ptll, std::string("Hperp"), hperp, syst});

        const auto metVar = metFromH(genPt, genPhi, visPt, visPhi, hparaVar, hperpVar);

        return {hpara, hperp, hparaVar, hperpVar, metVar.pt, metVar.phi};
    }

private:
    std::unique_ptr<correction::CorrectionSet> cset_;
    const correction::Correction* corr_rescaling_{nullptr};
    const correction::Correction* corr_qmphist_{nullptr};
    const correction::Correction* corr_qmpfit_{nullptr};
    const correction::Correction* corr_unc_{nullptr};

} // BosonicRecoilCorrection

} //namespace recoil