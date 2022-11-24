#pragma once

#include "corrections.h"

namespace correction {

LorentzVectorM ShiftMet(const LorentzVectorM& met_p4, const std::vector<RVecLV>& all_delta_p4)
{
  LorentzVectorXYZ met_p4_shifted(met_p4);
  for(const auto& obj_delta_p4 : all_delta_p4) {
    for(const auto& delta_p4 : obj_delta_p4) {
      met_p4_shifted -= delta_p4;
    }
  }
  return LorentzVectorM(met_p4_shifted.pt(), 0., met_p4_shifted.phi(), 0.);
}

} // namespace correction