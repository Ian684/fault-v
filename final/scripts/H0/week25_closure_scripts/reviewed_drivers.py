"""Keep the original 50-driver evidence immutable while binding the selected one-cell overlay."""
import json
def load_driver_review(C):
    drivers=json.loads((C/'reports/cached_input.json').read_text())['equivalent_drivers'];assert len(drivers)==50
    selected=json.loads((C/'reports/signal_selection.json').read_text());overlay=None
    if selected.get('driver_overlay'):
        assert selected['driver_overlay']=='reports/driver51_trial_b.json'
        overlay=json.loads((C/selected['driver_overlay']).read_text())
        assert overlay['placement_pass'] and overlay['Boolean_and_signal_pin_contract_equal']
        assert selected['source_sha256']==overlay['output_sha256'] and selected['previous_source_sha256']==overlay['source_sha256']
        assert overlay['cell']=='_30389_' and overlay['old_master']=='sky130_fd_sc_hd__buf_1' and overlay['new_master']=='sky130_fd_sc_hd__buf_2'
        assert [d['name'] for d in overlay['removed_passive_diodes']]==['ANTENNA_7502']
        assert all(not x[0] and not x[1] for x in overlay['target_net_contacts'].values())
        assert overlay['cell'] not in drivers
        drivers[overlay['cell']]={'master':overlay['new_master'],'location':overlay['position'],'orientation':overlay['orientation'],'peer':overlay['native_access_peer']}
    assert len(drivers)==(51 if overlay else 50)
    return drivers,overlay
