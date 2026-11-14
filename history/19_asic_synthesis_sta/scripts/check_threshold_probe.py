from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[1]
def slews(name):
 text=(R/'reports'/name).read_text()
 return [float(m[1]) for m in re.findall(r'^sram\d+/wmask0\[\d+\]\s+([\d.]+)\s+([\d.]+)',text,re.M)]
old=slews('threshold_probe.log');new=slews('threshold_probe_fixed.log')
assert len(old)==len(new)==32
assert max(old)/min(old)>1000
assert max(new)-min(new)<1e-8 and abs(new[0]-.468540996)<1e-8
result={'pass':True,'same_net_loads':32,'old_slew_ns_range':[min(old),max(old)],'new_slew_ns_range':[min(new),max(new)],'scope':'Threshold conversion regression only; this deliberately overloaded fixture is not a CPU timing pass.'}
(R/'reports/threshold_regression.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS same-net threshold conversion regression (32 identical loads).')
