

central = 'Central'
up = 'Up'
down = 'Down'
nano = 'nano'

def getScales(source):
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