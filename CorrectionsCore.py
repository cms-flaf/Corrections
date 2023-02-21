
from Common.Utilities import *

central = 'Central'
up = 'Up'
down = 'Down'
nano = 'nano'

def getScales(source=None):
    if source is None:
        return [ central, up, down ]
    if source == central:
        return [ central ]
    return [ up, down ]

def getSystName(source, scale):
    if source == central:
        if scale == central:
            return central
    else:
        if scale in [ up, down ]:
            return source + scale
    raise RuntimeError(f'getSystName: inconsistent source:scale combination = {source}:{scale}')

def updateSourceDict(source_dict, source, obj):
    if source not in source_dict:
        source_dict[source] = []
    if obj in source_dict[source]:
        raise RuntimeError(f"addUncSource: dupblicated {source} definition for {obj}")
    source_dict[source].append(obj)


def createWPChannelMap(map_wp_python):
    ch_list = []
    channels = ['eTau', 'muTau', 'tauTau']
    for ch,ch_data in map_wp_python.items():
        if ch not in channels: continue
        wp_list = []
        for k in ['e', 'mu', 'jet']:
            wp_class = globals()[f'WorkingPointsTauVS{k}']
            wp_name = ch_data[f'VS{k}']
            wp_value = getattr(wp_class, wp_name).value
            wp_entry = f'{{ "{wp_name}", {wp_value} }} '
            wp_list.append(wp_entry)
        wp_str = ', '.join(wp_list)
        ch_str = f'{{ Channel::{ch}, {{ {wp_str} }} }}'
        ch_list.append(ch_str)
    map_str = '::correction::TauCorrProvider::wpsMapType({' + ', '.join(ch_list) + '})'
    return map_str

def createTauSFTypeMap(map_sf_python):
    ch_list = []
    map_sf_cpp = 'std::map<Channel, std::string>({'
    for ch, ch_data in map_sf_python.items():
        map_sf_cpp += f'{{ Channel::{ch}, "{ch_data}" }}, '
    map_sf_cpp += '})'
    return map_sf_cpp

