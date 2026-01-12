from FLAF.Common.Utilities import *

central = "Central"
up = "Up"
down = "Down"
nano = "nano"

period_names = {
    "Run2_2016_HIPM": "2016preVFP_UL",
    "Run2_2016": "2016postVFP_UL",
    "Run2_2017": "2017_UL",
    "Run2_2018": "2018_UL",
    "Run3_2022": "2022_Summer22",
    "Run3_2022EE": "2022_Summer22EE",
    "Run3_2023": "2023_Summer23",
    "Run3_2023BPix": "2023_Summer23BPix",
    "Run4_2024": "2024_Summer24",
}

periods = {
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
