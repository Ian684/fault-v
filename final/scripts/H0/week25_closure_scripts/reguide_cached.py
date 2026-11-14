from pathlib import Path
source=Path('/work/week25_closure/scripts/reguide_minimal.py').read_text()
for old,new,count in [('reports/minimal_input.json','reports/cached_input.json',1),('minimal_global_a','cached_global_a',2),('inputs/minimal_partial.odb','inputs/cached_partial.odb',1),('inputs/minimal_guided.odb','inputs/cached_guided.odb',1),('route_state.json','cached_route_state.json',1),('config_global.json','config_cached_global.json',1),('config_route.json','config_cached_route.json',1),('reports/guided_input.json','reports/cached_guided_input.json',1)]:
    assert source.count(old)==count,(old,source.count(old))
    source=source.replace(old,new)
exec(compile(source,'existing_exact_guide_validator_for_cached_candidate','exec'))
