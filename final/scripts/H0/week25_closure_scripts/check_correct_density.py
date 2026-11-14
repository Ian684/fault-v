from pathlib import Path
source=Path('/work/week25_signoff/scripts/density_minimum.py').read_text()
for old,new in [("Path('/work/week25_signoff')","Path('/work/week25_closure')"),("'input_state.json'","'correct_stream_state.json'"),("'reports/density_minimum.json'","'reports/density_correct_stream.json'")]:
    assert source.count(old)==1,old
    source=source.replace(old,new)
exec(compile(source,'frozen_density_screen_with_corrected_input','exec'))
