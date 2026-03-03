#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {
    float DeltaPhi(float phi1, float phi2) {
        float dPhi = phi1 - phi2;
        if (dPhi > M_PI)
            dPhi -= 2 * M_PI;
        else if (dPhi < -M_PI)
            dPhi += 2 * M_PI;
        return dPhi;
    }

    float DeltaR(const float eta1, const float phi1, const float eta2, const float phi2) {
        float dEta = eta1 - eta2;
        float dPhi = DeltaPhi(phi1, phi2);
        return sqrt(dEta * dEta + dPhi * dPhi);
    }

    LorentzVectorM fsr_corrected_p4(float mu_pt,
                                    float mu_eta,
                                    float mu_phi,
                                    float mu_mass,
                                    int mu_fsrIdx,
                                    const RVecF& fsr_pt,
                                    const RVecF& fsr_eta,
                                    const RVecF& fsr_phi,
                                    const RVecF& fsr_dROverEt2,
                                    const RVecF& fsr_relIso03,
                                    const RVecF& fsr_electronIdx) {
        LorentzVectorM res{mu_pt, mu_eta, mu_phi, mu_mass};

        if (mu_fsrIdx == -1) {
            return res;
        }

        float deltaR_mu_fsr = DeltaR(mu_eta, mu_phi, fsr_eta[mu_fsrIdx], fsr_phi[mu_fsrIdx]);

        if (!((deltaR_mu_fsr > 0.0001) && (deltaR_mu_fsr < 0.5))) {
            return res;
        }

        if (fsr_electronIdx[mu_fsrIdx] != -1) {
            return res;
        }

        if (fsr_pt[mu_fsrIdx] / mu_pt > 0.4) {
            return res;
        }

        if (fsr_dROverEt2[mu_fsrIdx] > 0.012) {
            return res;
        }

        if (fsr_relIso03[mu_fsrIdx] / mu_pt > 1.8) {
            return res;
        }

        res += LorentzVectorM{fsr_pt[mu_fsrIdx], fsr_eta[mu_fsrIdx], fsr_phi[mu_fsrIdx], 0.0};

        return res;
    }

    RVec<LorentzVectorM> fsr_corrected_p4(const RVecF& mu_pt,
                                          const RVecF& mu_eta,
                                          const RVecF& mu_phi,
                                          const RVecF& mu_mass,
                                          const RVecI& mu_fsrIdx,
                                          const RVecF& fsr_pt,
                                          const RVecF& fsr_eta,
                                          const RVecF& fsr_phi,
                                          const RVecF& fsr_dROverEt2,
                                          const RVecF& fsr_relIso03,
                                          const RVecF& fsr_electronIdx) {
        RVec<LorentzVectorM> res_vec(mu_pt.size());
        for (size_t i = 0; i < mu_pt.size(); ++i) {
            res_vec[i] = fsr_corrected_p4(mu_pt[i],
                                          mu_eta[i],
                                          mu_phi[i],
                                          mu_mass[i],
                                          mu_fsrIdx[i],
                                          fsr_pt,
                                          fsr_eta,
                                          fsr_phi,
                                          fsr_dROverEt2,
                                          fsr_relIso03,
                                          fsr_electronIdx);
        }
        return res_vec;
    }
}  // namespace correction