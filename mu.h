#pragma once

#include "correction.h"
#include "corrections.h"

namespace correction {

class MuCorrProvider : public CorrectionsBase<MuCorrProvider> {
public:
    static const std::map<float, std::set<std::pair<float, float>>>& getRecoSFMap()
        {
            static const std::map<float, std::set<std::pair<float, float>>> RecoSFMap = {
                {50., { std::pair<float,float>(1.6, 0.9943),std::pair<float,float>(2.4, 1.0)} },
                {100., { std::pair<float,float>(1.6, 0.9948), std::pair<float,float>(2.4, 0.993)} },
                {150., { std::pair<float,float>(1.6, 0.9950), std::pair<float,float>(2.4, 0.990)} },
                {200., { std::pair<float,float>(1.6, 0.994), std::pair<float,float>(2.4, 0.988)} },
                {300., { std::pair<float,float>(1.6, 0.9914), std::pair<float,float>(2.4, 0.981)} },
                {400., { std::pair<float,float>(1.6, 0.993), std::pair<float,float>(2.4, 0.983)} },
                {600., { std::pair<float,float>(1.6, 0.991), std::pair<float,float>(2.4, 0.978)} },
                {1500., { std::pair<float,float>(1.6, 1.0), std::pair<float,float>(2.4, 0.98)} },
            };
            return RecoSFMap;
        }


    MuCorrProvider()
    {
    }
    float getRecoSF(LorentzVectorM& muon_p4){
        for (const auto & map_element : getRecoSFMap()){
                if(muon_p4.mag() > map_element.first) continue;
                for (const auto & set_element : map_element.second){
                    if(abs(muon_p4.Eta()) > set_element.first) continue;
                    return set_element.second;
                }
            }
            return 1.;
        }

private:

};

} // namespace correction