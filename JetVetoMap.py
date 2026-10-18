import os
from .CorrectionsCore import *

# https://twiki.cern.ch/twiki/bin/viewauth/CMS/SWGuideMuonSelection
# https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/tree/master/POG/MUO
# note: at the beginning of february 2024, the names have been changed to muon_Z.json.gz and muon_HighPt.json.gz for high pT muons
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2018
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2017
# https://twiki.cern.ch/twiki/bin/view/CMS/MuonUL2016


class JetVetoMapProvider:
    JME_vetoMap_JsonPath = (
        "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/{}/jetvetomaps.json.gz"
    )

    jetvetomap_names = {
        "2022_Summer22": "Summer22_23Sep2023_RunCD_V1",  # campaign: entry name
        "2022_Summer22EE": "Summer22EE_23Sep2023_RunEFG_V1",
        "2023_Summer23BPix": "Summer23BPixPrompt23_RunD_V1",
        "2023_Summer23": "Summer23Prompt23_RunC_V1",
        "2024_Summer24": "Summer24Prompt24_RunBCDEFGHI_V1",
        "2025_Winter25": "Winter25Prompt25_RunCDEFG_V1",
        "2025_Summer24": "Winter25Prompt25_RunCDEFG_V1",
        "2026_Summer24": "Summer24Prompt26_RunBCD_V1",
    }

    def __init__(self, era):
        campaign = campaign_names[era]
        entry_name = JetVetoMapProvider.jetvetomap_names[campaign]
        JME_vetoMap_JsonFile = os.path.join(
            os.environ["ANALYSIS_PATH"],
            JetVetoMapProvider.JME_vetoMap_JsonPath.format(
                pog_folder_names["JERC"][campaign]
            ),
        )
        declareProviderHeader("JetVetoMap.h")
        self.provider = CppProvider(
            "correction::JetVetoMapProvider", JME_vetoMap_JsonFile, entry_name
        )
        self.campaign = campaign

    def GetJetVetoMap(self, df):
        # jet pT > 15 GeV, tight jet ID, PU jet ID for CHS jets with pT < 50 GeV,  jet EM fraction (charged + neutral) < 0.9
        df = df.Define(
            f"Jet_isInsideVetoRegion",
            f"""{self.provider.ref}->GetJetVetoMapValues(Jet_p4)""",
        )
        return df
