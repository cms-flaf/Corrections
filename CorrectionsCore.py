from FLAF.Common.Utilities import *

central = "Central"
up = "Up"
down = "Down"
nano = "nano"

pog_folder_names = {
    "BTV": {
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv9",
        "2018_UL": "Run2-2018-UL-NanoAODv9",
        "JER": "Run3-22CDJun23-Summer22-NanoAODv11",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
        "2025_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",
        "2025_Winter25": "",
        "2026_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",  # placeholder: no 2026 POG set yet
    },
    "JERC": {
        "2018_UL": "Run2-2018-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv9",
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv9",
        "JER": "JER-Smearing",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12/2026-06-05",  #
        "2022_Prompt": "Run3-22Prompt-Winter22-NanoAODv12/2025-04-11",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12/2026-06-05",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12/2026-06-05",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12/2026-06-05",
        "2024_Winter24": "Run3-24Prompt-Winter24-NanoAODv14/2025-06-09",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2026-06-05",  # https://cms-jerc.web.cern.ch/Recommendations/#2024
        "2025_Summer24": "Run3-25Prompt-Winter25-NanoAODv15/2026-06-05",  # TMP PATCH # --> Run3-25Prompt-Summer24-NanoAODv15 IS NOT AVAILABLE FOR JME but JME is the only one having Winter25 available. So by the time being we can have this tmp fix
        "2025_Winter25": "Run3-25Prompt-Winter25-NanoAODv15/2026-06-05",
        "2026_Summer24": "Run3-25Prompt-Winter25-NanoAODv15/2026-06-05",  # placeholder: same as 2025 JME
    },
    "EGM": {
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv15",
        # "2016postVFP_UL":"Run2-2016postVFP-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv15",
        # "2016preVFP_UL":"Run2-2016preVFP-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv15",
        # "2017_UL":"Run2-2017-UL-NanoAODv9",
        "2018_UL": "Run2-2018-UL-NanoAODv15",
        # "2018_UL":"Run2-2018-UL-NanoAODv9",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
        "2025_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",
        "2025_Winter25": "",
        "2026_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",  # placeholder
    },
    "LUM": {
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv9",
        "2018_UL": "Run2-2018-UL-NanoAODv9",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
        "2025_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",
        "2025_Winter25": "",
        "2026_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",  # placeholder
    },
    "MUO": {
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv9",
        "2018_UL": "Run2-2018-UL-NanoAODv9",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
        "2025_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",
        "2025_Winter25": "",
        "2026_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",  # placeholder
    },
    "TAU": {
        "2016postVFP_UL": "Run2-2016postVFP-UL-NanoAODv15",
        # "2016postVFP_UL":"Run2-2016postVFP-UL-NanoAODv9",
        "2016preVFP_UL": "Run2-2016preVFP-UL-NanoAODv15",
        # "2016preVFP_UL":"Run2-2016preVFP-UL-NanoAODv9",
        "2017_UL": "Run2-2017-UL-NanoAODv15",
        # "2017_UL":"Run2-2017-UL-NanoAODv9",
        "2018_UL": "Run2-2018-UL-NanoAODv15",
        # "2018_UL":"Run2-2018-UL-NanoAODv9",
        "2022_Summer22": "Run3-22CDSep23-Summer22-NanoAODv12",
        "2022_Summer22EE": "Run3-22EFGSep23-Summer22EE-NanoAODv12",
        "2023_Summer23": "Run3-23CSep23-Summer23-NanoAODv12",
        "2023_Summer23BPix": "Run3-23DSep23-Summer23BPix-NanoAODv12",
        "2024_Summer24": "Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15",
        "2025_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",
        "2025_Winter25": "",
        "2026_Summer24": "Run3-25Prompt-Summer24-NanoAODv15",  # placeholder
    },
}

period_names = {
    "Run2_2016_HIPM": "2016preVFP_UL",
    "Run2_2016": "2016postVFP_UL",
    "Run2_2017": "2017_UL",
    "Run2_2018": "2018_UL",
    "Run3_2022": "2022_Summer22",
    "Run3_2022EE": "2022_Summer22EE",
    "Run3_2023": "2023_Summer23",
    "Run3_2023BPix": "2023_Summer23BPix",
    "Run3_2024": "2024_Summer24",  # 2024_Winter24
    "Run3_2025": "2025_Summer24",  # "2025_Winter25" is also a valid entry, but has files only only for JME
    "Run3_2026": "2026_Summer24",  # placeholder: 2026 POG sets not published yet
}

periods = {
    "2026_Summer24": "2026",
    "2025_Winter25": "2025",
    "2025_Summer24": "2025",
    "2024_Summer24": "2024",
    "2023_Summer23BPix": "2023",
    "2023_Summer23": "2023",
    "2022_Summer22EE": "2022",
    "2022_Summer22": "2022",
    "2018_UL": "2018",
    "2017_UL": "2017",
    "2016preVFP_UL": "2016",
    "2016postVFP_UL": "2016",
}


def getScales(source=None):
    if source is None:
        return [central, up, down]
    if source == central:
        return [central]
    return [up, down]


def getSystName(source, scale):
    if source == central:
        if scale == central:
            return central
    else:
        if scale in [up, down]:
            return source + scale
    raise RuntimeError(
        f"getSystName: inconsistent source:scale combination = {source}:{scale}"
    )


class ShapeWeightRegistry:
    """Which weight branches multiply into each (source, scale) variation.

    The normalisation weight is built once per variation, both as the numerator in
    Corrections.getNormalisationCorrections and as the anaCache denominator in
    FLAF/AnaProd/anaTupleProducer.py. Both need the same answer to the same question:
    for variation (source, scale), which weight branches multiply together?

    The answer is not "the branches of the producer that owns this source". A variation
    of one producer must still carry every *other* producer's central branch, or the
    ratio weight_base_<var> / weight_base_Central retains a spurious factor of one over
    that other producer's central weight. With pileup as the only non-central source
    that never showed up, because the only non-central keys belonged to pileup itself.

    Producers register the sources they own plus a (source, scale) -> branch-name
    callable, and this class does the cross product. Registration is independent of
    whether the producer is enabled at this stage, so a branch written at AnaTuple can
    be named again at AnaTupleMerge without being recomputed.
    """

    def __init__(self):
        self._producers = []  # [(name, owned_sources, branch_fn)]

    def register(self, name, sources, branch_fn):
        if any(name == registered for registered, _, _ in self._producers):
            raise RuntimeError(f"ShapeWeightRegistry: duplicate producer '{name}'")
        self._producers.append((name, list(sources), branch_fn))

    @property
    def sources(self):
        sources = [central]
        for _, owned, _ in self._producers:
            sources.extend(owned)
        return sources

    def branches(self, source, scale):
        """Varied branch from the producer owning `source`, central from the rest."""
        return [
            (
                branch_fn(source, scale)
                if source in owned
                else branch_fn(central, central)
            )
            for _, owned, branch_fn in self._producers
        ]

    def asDict(self):
        return {
            (source, scale): self.branches(source, scale)
            for source in self.sources
            for scale in getScales(source)
        }


def splitSystName(syst_name):
    if syst_name == central:
        return (central, central)
    for suffix in [up, down]:
        if syst_name.endswith(suffix):
            source = syst_name[: -len(suffix)]
            scale = suffix
            return (source, scale)
    raise RuntimeError(f"splitSystName: cannot split syst_name = {syst_name}")


def updateSourceDict(source_dict, source, obj):
    if source not in source_dict:
        source_dict[source] = []
    if obj in source_dict[source]:
        raise RuntimeError(f"addUncSource: duplicated {source} definition for {obj}")
    source_dict[source].append(obj)


def createWPChannelMap(map_wp_python):
    ch_list = []
    for ch, ch_data in map_wp_python.items():
        wp_list = []
        for k in ["e", "mu", "jet"]:
            wp_class = globals()[f"WorkingPointsTauVS{k}"]
            wp_name = ch_data[f"VS{k}"]
            wp_value = getattr(wp_class, wp_name).value
            wp_entry = f'{{ "{wp_name}", {wp_value} }} '
            wp_list.append(wp_entry)
        wp_str = ", ".join(wp_list)
        ch_str = f"{{ Channel::{ch}, {{ {wp_str} }} }}"
        ch_list.append(ch_str)
    map_str = "::correction::TauCorrProvider::wpsMapType({" + ", ".join(ch_list) + "})"
    return map_str


def createTauSFTypeMap(map_sf_python):
    map_sf_cpp = "std::map<Channel, std::string>({"
    for ch, ch_data in map_sf_python.items():
        map_sf_cpp += f'{{ Channel::{ch}, "{ch_data}" }}, '
    map_sf_cpp += "})"
    return map_sf_cpp


def getLegTypeString(df, leg_type_column):
    column_type = df.GetColumnType(leg_type_column)
    if column_type in ["Int_t", "int"]:
        return f"static_cast<Leg>({leg_type_column})"
    elif column_type == "Leg":
        return leg_type_column
    else:
        raise RuntimeError(
            f"getLegTypeString: unsupported column type {column_type} for {leg_type_column}"
        )


def getChannelIdString(df, channel_id_column):
    column_type = df.GetColumnType(channel_id_column)
    if column_type in ["Int_t", "int"]:
        return f"static_cast<Channel>({channel_id_column})"
    elif column_type == "Channel":
        return channel_id_column
    else:
        raise RuntimeError(
            f"getChannelIdString: unsupported column type {column_type} for {channel_id_column}"
        )
