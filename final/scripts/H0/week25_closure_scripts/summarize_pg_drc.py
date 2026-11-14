from pathlib import Path
import xml.etree.ElementTree as ET,json
C=Path(__file__).resolve().parents[1]
root=ET.parse(C/'runs/pg_stream_a/2-klayout-drc/reports/drc.klayout.lyrdb').getroot()
items=[{k:item.findtext(k) for k in ('category','cell')}|{'values':[v.text for v in item.findall('values/value')]} for item in root.findall('items/item')]
(C/'reports/pg_stream_a_markers.json').write_text(json.dumps(items,indent=2)+'\n')
print(json.dumps(items,indent=2))
