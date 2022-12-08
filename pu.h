#pragma once
#include "correction.h"
#include "corrections.h"

namespace correction {

class puCorrProvider {
public:

    static void Initialize(const std::string& fileName)
    {
        _getGlobal() = std::make_unique<puCorrProvider>(fileName);
    }

    static const puCorrProvider& getGlobal()
    {
        const auto& corr = _getGlobal();
        if(!corr)
            throw std::runtime_error("puCorrProvider: not initialized.");
        return *corr;
    }

    static const std::string& getScaleStr(UncScale scale)
    {
        static const std::map<UncScale, std::string> names = {
            { UncScale::Down, "down" },
            { UncScale::Central, "nominal" },
            { UncScale::Up, "up" },
        };
        return names.at(scale);
    }
    puCorrProvider(const std::string& fileName) :
        corrections_(CorrectionSet::from_file(fileName)),
        puweight(corrections_->at("Collisions18_UltraLegacy_goldenJSON"))
    {
    }

    float getWeight(UncScale scale, const float& Pileup_nTrueInt) const{
        const std::string& scale_str = getScaleStr(scale);
        const double w = puweight->evaluate({Pileup_nTrueInt, scale_str});

        return w;
    }
private:
    static std::unique_ptr<puCorrProvider>& _getGlobal()
    {
        static std::unique_ptr<puCorrProvider> corr;
        return corr;
    }
    std::unique_ptr<CorrectionSet> corrections_;
    Correction::Ref puweight;

};

} // namespace correction