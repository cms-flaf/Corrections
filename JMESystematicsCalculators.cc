#include "JMESystematicsCalculators.h"
#include "CondFormats/JetMETObjects/interface/FactorizedJetCorrectorCalculator.h"

#include <Math/GenVector/LorentzVector.h>
#include <Math/GenVector/PtEtaPhiM4D.h>
#include "Math/VectorUtil.h"

#include <cassert>

// #define BAMBOO_JME_DEBUG // uncomment to debug

#ifdef BAMBOO_JME_DEBUG
#define LogDebug_JME std::cout
#else
#define LogDebug_JME if (false) std::cout
#endif

void JetMETVariationsCalculatorBase::setJEC(const std::vector<JetCorrectorParameters>& jecParams)
{
  if ( ! jecParams.empty() ) {
    m_jetCorrector = std::unique_ptr<FactorizedJetCorrectorCalculator>{new FactorizedJetCorrectorCalculator(jecParams)};
  }
}

namespace {

  double GetRandomNumber(int event, double jet_pt, double jet_eta, double jet_phi, double sigma){
    std::normal_distribution<> d(0, sigma);

    // Initialize random generator with seed dependent on the jet for future reproducibility and sync
    size_t seed = event + size_t(jet_pt * 100) + size_t(std::abs(jet_eta) * 100) * 100 + size_t(std::abs(jet_phi) * 100) * 10000;
    std::mt19937_64 random_generator_(seed);
    double randomNumber = d(random_generator_);
    //std::cout << "seed = " << seed << std::endl;
    //std::cout << "random number = " << randomNumber << std::endl;
    return randomNumber;
  }

  double jetESmearFactor( double pt, double eOrig, float genPt, float ptRes, float sfUncert, double rand )
  {
    double smear = 1.;
    if ( genPt > 0. ) {
      smear = 1. + (sfUncert-1.)*(pt - genPt)/pt;
    } else if ( sfUncert > 1. ) {
      smear = 1. + rand*std::sqrt(sfUncert*sfUncert-1.);
    }
    if ( smear*eOrig < 1.e-2 ) {
      smear = 1.e-2/eOrig;
    }
    //std::cout << " pt " << pt << " eOrig " << eOrig << " genPt " << genPt << " ptRes " << ptRes << " sfUncert "<< sfUncert << " rand " << rand << std::endl;
    return smear;
  }

  // because something goes wrong with linking ROOT::Math::VectorUtil::Phi_mpi_pi
  template<typename T>
  T phi_mpi_pi(T angle) {
    if ( angle <= M_PI && angle > -M_PI ) {
      return angle;
    }
    if ( angle > 0 ) {
      const int n = static_cast<int>(.5*(angle*M_1_PI+1.));
      angle -= 2*n*M_PI;
    } else {
      const int n = static_cast<int>(-.5*(angle*M_1_PI-1.));
      angle += 2*n*M_PI;
    }
    return angle;
  }

  std::vector<float> fillVector(const std::vector<std::string>& names, const JME::JetParameters::value_type& jetParams)
  {
    static const std::unordered_map<std::string,JME::Binning> jmeBinningFromString = {
        {"JetEta", JME::Binning::JetEta},
        {"JetPt" , JME::Binning::JetPt},
        // TODO JetPhi, JetEMF, LepPx, LepPy, LepPz
        {"JetE"  , JME::Binning::JetE}
      };
    std::vector<float> result;
    result.reserve(names.size());
    for ( const auto& nm : names ) {
      const auto it_key = jmeBinningFromString.find(nm);
      if ( std::end(jmeBinningFromString) == it_key ) {
        throw std::runtime_error{"Unknown binning variable: "+nm};
      } else {
        const auto it_par = jetParams.find(it_key->second);
        if ( std::end(jetParams) == it_par ) {
          throw std::runtime_error{"Binning variable "+nm+" not found"};
        } else {
          result.push_back(it_par->second);
        }
      }
    }
    return result;
  }

  float getUncertainty(const SimpleJetCorrectionUncertainty& uncert, const JME::JetParameters::value_type& jetParams, bool direction)
  {
    const auto vx = fillVector(uncert.parameters().definitions().binVar(), jetParams);
    const auto vy = fillVector(uncert.parameters().definitions().parVar(), jetParams);
    return uncert.uncertainty(vx, vy[0], direction);
  }

  float deltaHEM2018Issue(float pt_nom, int jetId, float phi, float eta ) {
    float delta = 1.;
    if ( pt_nom > 15. && ( jetId & 0x2 ) && phi > -1.57 && phi < -0.87 ) {
      if ( eta > -2.5 && eta < -1.3 ) {
        delta = 0.8;
      } else if ( eta <= -2.5 && eta > -3. ) {
        delta = 0.65;
      }
    }
    return delta;
  }

  int jerSplitID(float pt, float eta) {
    const auto aEta = std::abs(eta);
    if ( aEta < 1.93 )
      return 0;
    else if ( aEta < 2.5 )
      return 1;
    else if ( aEta < 3. )
      if ( pt < 50. )
        return 2;
      else
        return 3;
    else
      if ( pt < 50. )
        return 4;
      else
        return 5;
  }

  std::vector<JetCorrectorParameters> makeJCPList(const std::vector<std::string>& paths) {
    std::vector<JetCorrectorParameters> params;
    std::transform(std::begin(paths), std::end(paths), std::back_inserter(params),
      [] (const std::string& path) { return JetCorrectorParameters{path}; });
    return params;
  }

  template<typename CALC>
  void configureBaseCalc(CALC& calc,
    const std::vector<std::string>& jecParams,
    const std::vector<std::pair<std::string,std::string>>& jesUncertainties,
    const std::string& ptResolution, const std::string& ptResolutionSF, bool splitJER,
    bool doGenMatch, float genMatch_maxDR, float genMatch_maxDPT)
  {
    calc.setJEC(makeJCPList(jecParams));
    for (const auto& entry : jesUncertainties) {
      calc.addJESUncertainty(entry.first, JetCorrectorParameters{entry.second, entry.first});
    }
    if (!ptResolution.empty()) {
      calc.setSmearing(ptResolution, ptResolutionSF, splitJER,
                       doGenMatch, genMatch_maxDR, genMatch_maxDPT);
    }
  }

  template<typename CALC>
  void configureMETCalc_common(CALC& calc,
    const std::vector<std::string>& jecParams, const std::vector<std::string>& jecParamsL1,
    float unclEnThreshold,
    const std::vector<std::pair<std::string,std::string>>& jesUncertainties,
    bool isT1SmearedMET,
    const std::string& ptResolution, const std::string& ptResolutionSF, bool splitJER,
    bool doGenMatch, float genMatch_maxDR, float genMatch_maxDPT)
  {
    configureBaseCalc(calc, jecParams, jesUncertainties,
      ptResolution, ptResolutionSF, splitJER, doGenMatch, genMatch_maxDR, genMatch_maxDPT);
    calc.setL1JEC(makeJCPList(jecParamsL1));
    calc.setUnclusteredEnergyTreshold(unclEnThreshold);
    if (isT1SmearedMET) {
      calc.setIsT1SmearedMET(isT1SmearedMET);
    }
  }
}

// TODO with orig MET and jets (sumpx,sumpy): calc modif MET(sig), produce bigger results type

std::size_t JetMETVariationsCalculatorBase::findGenMatch(const double pt, const float eta, const float phi, const ROOT::VecOps::RVec<float>& gen_pt, const ROOT::VecOps::RVec<float>& gen_eta, const ROOT::VecOps::RVec<float>& gen_phi, const double resolution ) const
{
  auto dr2Min = std::numeric_limits<float>::max();
  std::size_t igBest{gen_pt.size()};
  LogDebug_JME << "(DRs: ";
  for ( std::size_t ig{0}; ig != gen_pt.size(); ++ig ) {
    const auto dphi = phi_mpi_pi(gen_phi[ig]-phi);
    const auto deta = (gen_eta[ig]-eta);
    const auto dr2 = dphi*dphi + deta*deta;
    LogDebug_JME << "dr2=" << dr2;
    if ( ( dr2 < dr2Min ) && ( dr2 < m_genMatch_dR2max ) ) {
      LogDebug_JME << "->dpt=" << std::abs(gen_pt[ig]-pt) << ",res=" << resolution;
      if ( std::abs(gen_pt[ig]-pt) < m_genMatch_dPtmax*resolution ) {
        LogDebug_JME << "->best:" << ig;
        dr2Min = dr2;
        igBest = ig;
      }
    }
    LogDebug_JME << ", ";
  }
  LogDebug_JME << ")";
  return igBest;
}

JetVariationsCalculator JetVariationsCalculator::create(
    const std::vector<std::string>& jecParams,
    const std::vector<std::pair<std::string,std::string>>& jesUncertainties,
    bool addHEM2018Issue,
    const std::string& ptResolution, const std::string& ptResolutionSF, bool splitJER,
    bool doGenMatch, float genMatch_maxDR, float genMatch_maxDPT)
{
  JetVariationsCalculator inst{};
  configureBaseCalc(inst, jecParams, jesUncertainties,
    ptResolution, ptResolutionSF, splitJER, doGenMatch, genMatch_maxDR, genMatch_maxDPT);
  inst.setAddHEM2018Issue(addHEM2018Issue);
  return std::move(inst);
}

JetVariationsCalculator::result_t JetVariationsCalculator::produce(
    const p4compv_t& jet_pt, const p4compv_t& jet_eta, const p4compv_t& jet_phi, const p4compv_t& jet_mass,
    const p4compv_t& jet_rawcorr, const p4compv_t& jet_area,
    const ROOT::VecOps::RVec<int>& jet_jetId,
    const float rho,
    const ROOT::VecOps::RVec<int>& jet_partonFlavour,
    const std::uint32_t seed,
    const p4compv_t& genjet_pt, const p4compv_t& genjet_eta, const p4compv_t& genjet_phi, const p4compv_t& genjet_mass , int event) const
{
  const auto nVariations = 1+( m_doSmearing ? 2*( m_splitJER ? 6 : 1 ) : 0 )+2*m_jesUncSources.size()+( m_addHEM2018Issue ? 2 : 0 ); // 1(nom)+2(JER)+2*len(JES)[+2(HEM)]
  LogDebug_JME << "JME:: hello from JetVariations produce. Got " << jet_pt.size() << " jets" << std::endl;
  const auto nJets = jet_pt.size();
  result_t out{nVariations, jet_pt, jet_mass};
  ROOT::VecOps::RVec<double> pt_nom{jet_pt}, mass_nom{jet_mass};
  if ( m_jetCorrector ) {
    LogDebug_JME << "JME:: reapplying JEC" << std::endl;
    FactorizedJetCorrectorCalculator::VariableValues vals;
    for ( std::size_t i{0}; i != nJets; ++i ) {
      vals.setJetEta(jet_eta[i]);
      vals.setJetPt(jet_pt[i]*(1.-jet_rawcorr[i]));
      vals.setJetA(jet_area[i]);
      vals.setRho(rho);
      const auto corr = m_jetCorrector->getCorrection(vals);
      if ( corr > 0. ) {
        const double newc = (1.-jet_rawcorr[i])*corr;
        pt_nom[i]   *= newc;
        mass_nom[i] *= newc;
      }
    }
#ifdef BAMBOO_JME_DEBUG
    LogDebug_JME << "JME:: with reapplied JEC: ";
    for ( std::size_t i{0}; i != nJets; ++i ) {
      LogDebug_JME << "(PT=" << pt_nom[i] << ", ETA=" << jet_eta[i] << ", PHI=" << jet_phi[i] << ", M=" << mass_nom[i] << ") ";
    }
    LogDebug_JME << std::endl;
#endif
  } else {
    LogDebug_JME << "JME:: Not reapplying JEC" << std::endl;
  }
  // smearing and JER
  std::size_t iVar = 1; // after nominal
  if ( m_doSmearing ) {
    LogDebug_JME << "JME:: Smearing (seed=" << seed << ")" << std::endl;
    p4compv_t pt_jerUp(pt_nom.size(), 0.), mass_jerUp(mass_nom.size(), 0.);
    p4compv_t pt_jerDown(pt_nom.size(), 0.), mass_jerDown(mass_nom.size(), 0.);
    for ( std::size_t i{0}; i != nJets; ++i ) {
      const auto eOrig = ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<double>>(pt_nom[i], jet_eta[i], jet_phi[i], mass_nom[i]).E();
      double smearFactor_nom{1.}, smearFactor_down{1.}, smearFactor_up{1.};
      if ( pt_nom[i] > 0. ) {
        JME::JetParameters jPar{
            {JME::Binning::JetPt , pt_nom[i]},
            {JME::Binning::JetEta, jet_eta[i]},
            {JME::Binning::Rho   , rho} };
        const auto ptRes  = m_jetPtRes.getResolution(jPar);
        LogDebug_JME << "JME:: JetParameters: pt=" << pt_nom[i] << ", eta=" << jet_eta[i] << ", rho=" << rho << "; ptRes=" << ptRes << std::endl;
        LogDebug_JME << "JME:: ";
        float genPt = -1;
        if ( m_smearDoGenMatch ) {
          const auto iGen = findGenMatch(pt_nom[i], jet_eta[i], jet_phi[i], genjet_pt, genjet_eta, genjet_phi, ptRes*pt_nom[i]);
          if ( iGen != genjet_pt.size() ) {
            genPt = genjet_pt[iGen];
            LogDebug_JME << "genPt=" << genPt << " ";
          }
        }
        //std::cout<<std::endl;
        //std::cout << "pt nom " << i << " = " << pt_nom[i] << std::endl;
        //const auto rand = ( genPt < 0. ) ? rg.Gaus(0, ptRes) : -1.;
        const auto rand = ( genPt < 0. ) ? GetRandomNumber(event, pt_nom[i], jet_eta[i], jet_phi[i], ptRes) : -1.;
        LogDebug_JME << "jet_pt_resolution: " << ptRes << ", rand: " << rand << std::endl;
        //std::cout << " nominal " << std::endl;
        smearFactor_nom  = jetESmearFactor(pt_nom[i], eOrig, genPt, ptRes, m_jetEResSF.getScaleFactor(jPar, Variation::NOMINAL), rand);
        //std::cout << " nominal ended " << std::endl;
        //std::cout << std::endl;
        smearFactor_down = jetESmearFactor(pt_nom[i], eOrig, genPt, ptRes, m_jetEResSF.getScaleFactor(jPar, Variation::DOWN   ), rand);
        smearFactor_up   = jetESmearFactor(pt_nom[i], eOrig, genPt, ptRes, m_jetEResSF.getScaleFactor(jPar, Variation::UP     ), rand);
        // LogDebug_JME << "  scalefactors are NOMINAL=" << m_jetEResSF.getScaleFactor(jPar, Variation::NOMINAL) << ", DOWN=" << m_jetEResSF.getScaleFactor(jPar, Variation::DOWN) << ", UP=" << m_jetEResSF.getScaleFactor(jPar, Variation::UP) << std::endl;
        // LogDebug_JME << "  smearfactors are NOMINAL=" << smearFactor_nom << ", DOWN=" << smearFactor_down << ", UP=" << smearFactor_up << std::endl;
      }
      pt_jerDown[i]   = pt_nom[i]*smearFactor_down;
      mass_jerDown[i] = mass_nom[i]*smearFactor_down;
      pt_jerUp[i]     = pt_nom[i]*smearFactor_up;
      mass_jerUp[i]   = mass_nom[i]*smearFactor_up;
      pt_nom[i]       *= smearFactor_nom;
      //std::cout << "pt smeared " << i << " = " << pt_nom[i] << std::endl;

      mass_nom[i]     *= smearFactor_nom;
    }
    if ( m_splitJER ) {
      ROOT::VecOps::RVec<int> jerBin(pt_nom.size(), -1);
      for ( std::size_t j{0}; j != nJets; ++j ) {
        jerBin[j] = jerSplitID(pt_nom[j], jet_eta[j]);
      }
      for ( int i{0}; i != 6; ++i ) {
        p4compv_t pt_jeriUp{pt_nom}, mass_jeriUp{mass_nom};
        p4compv_t pt_jeriDown{pt_nom}, mass_jeriDown{mass_nom};
        for ( std::size_t j{0}; j != nJets; ++j ) {
          if ( jerBin[j] == i ) {
            pt_jeriUp[j] = pt_jerUp[j];
            pt_jeriDown[j] = pt_jerDown[j];
            mass_jeriUp[j] = mass_jerUp[j];
            mass_jeriDown[j] = mass_jerDown[j];
          }
        }
        out.set(iVar++, std::move(pt_jeriUp)  , std::move(mass_jeriUp)  );
        out.set(iVar++, std::move(pt_jeriDown), std::move(mass_jeriDown));
      }
    } else {
      out.set(iVar++, std::move(pt_jerUp)  , std::move(mass_jerUp)  );
      out.set(iVar++, std::move(pt_jerDown), std::move(mass_jerDown));
    }
    LogDebug_JME << "JME:: Done with smearing" << std::endl;
  } else {
    LogDebug_JME << "JME:: No smearing" << std::endl;
  }
  out.set(0, pt_nom, mass_nom);

  // HEM issue 2018, see https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/2000.html
  if ( m_addHEM2018Issue ) {
    p4compv_t pt_down(pt_nom.size(), 0.), mass_down(mass_nom.size(), 0.);
    for ( std::size_t j{0}; j != nJets; ++j ) {
      const auto delta = deltaHEM2018Issue(pt_nom[j], jet_jetId[j], jet_phi[j], jet_eta[j]);
      pt_down[j] = pt_nom[j]*delta;
      mass_down[j] = mass_nom[j]*delta;
    }
    out.set(iVar++, pt_nom, mass_nom);
    out.set(iVar++, std::move(pt_down), std::move(mass_down));
  }
  // JES uncertainties
  for ( auto& jesUnc : m_jesUncSources ) {
    LogDebug_JME << "JME:: evaluating JES uncertainty: " << jesUnc.first << std::endl;
    p4compv_t pt_jesDown(pt_nom.size(), 0.), mass_jesDown(mass_nom.size(), 0.);
    p4compv_t pt_jesUp(pt_nom.size(), 0.), mass_jesUp(mass_nom.size(), 0.);
    for ( std::size_t i{0}; i != nJets; ++i ) {
      float delta = 0.;
      const auto partonFlav = std::abs(jet_partonFlavour[i]);
      if (!(jesUnc.first == "FlavorPureGluon" && partonFlav != 21) &&
          !(jesUnc.first == "FlavorPureQuark" && !(partonFlav >= 1 && partonFlav <= 3)) &&
          !(jesUnc.first == "FlavorPureCharm" && partonFlav != 4) &&
          !(jesUnc.first == "FlavorPureBottom" && partonFlav != 5)) {
          delta = getUncertainty(jesUnc.second, { {JME::Binning::JetPt, pt_nom[i]}, {JME::Binning::JetEta, jet_eta[i]} }, true);
      }
      LogDebug_JME << "JME:: jet " << i << ", parton flavour = " << partonFlav << ", delta = " << delta << std::endl;
      pt_jesDown[i]   = pt_nom[i]*(1.-delta);
      mass_jesDown[i] = mass_nom[i]*(1.-delta);
      pt_jesUp[i]     = pt_nom[i]*(1.+delta);
      mass_jesUp[i]   = mass_nom[i]*(1.+delta);
    }
    out.set(iVar++, std::move(pt_jesUp)  , std::move(mass_jesUp)  );
    out.set(iVar++, std::move(pt_jesDown), std::move(mass_jesDown));
  }

  #ifdef BAMBOO_JME_DEBUG
    assert(iVar == out.size());
    LogDebug_JME << "JME:: returning " << out.size() << " modified jet collections" << std::endl;
    const auto varNames = available();
    assert(varNames.size() == nVariations);
    for ( std::size_t i{0}; i != nVariations; ++i ) {
      LogDebug_JME << "JME:: Jet_" << varNames[i] << ": ";
      for ( std::size_t j{0}; j != nJets; ++j ) {
        LogDebug_JME << "(PT=" << out.pt(i)[j] << ", ETA=" << jet_eta[j] << ", PHI=" << jet_phi[j] << ", M=" << out.mass(i)[j] << ") ";
      }
      LogDebug_JME << std::endl;
    }
  #endif
  return out;
}

std::vector<std::string> JetVariationsCalculator::available(const std::string&) const
{
  std::vector<std::string> products = { "nominal" };
  if ( m_doSmearing ) {
    if ( m_splitJER ) {
      for ( int i = 0; i != 6; ++i ) {
        products.emplace_back("jer"+std::to_string(i)+"up");
        products.emplace_back("jer"+std::to_string(i)+"down");
      }
    } else {
      products.emplace_back("jerup");
      products.emplace_back("jerdown");
    }
  }
  if ( m_addHEM2018Issue ) {
    products.emplace_back("jesHEMIssueup");
    products.emplace_back("jesHEMIssuedown");
  }
  for ( const auto& src : m_jesUncSources ) {
    products.emplace_back("jes"+src.first+"up");
    products.emplace_back("jes"+src.first+"down");
  }
  return products;
}
