"""Reset/CDC and the four activity workloads on the exact H1 netlist (H0 run_closure_functional.py method).

Runs inside the pinned image: python3 signoff/run_functional_c.py <netlist under cand_gap90x95/runs> <tag>
Same models, testbenches, workload images, plusargs and pass criteria as H0; only the netlist and the output
folder (cand_gap90x95/functional/<tag>) differ. The H0-only reviewed-driver check does not apply to H1.
"""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys

H = Path('/work/ppa/h1/cand_gap90x95')
R = Path('/work')
P = R / 'ppa'
W = R / 'week25_signoff'
netlist = Path(sys.argv[1]).resolve()
tag = sys.argv[2]
assert netlist.is_relative_to(H / 'runs') and netlist.suffix == '.v' and re.fullmatch('[a-z0-9_]+', tag)
out = H / 'functional' / tag
cache = Path('/var/tmp') / ('faultv-h1c-functional-' + tag)
assert not out.exists() and not cache.exists()
out.mkdir(parents=True)
cache.mkdir()


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


models = [R / 'design/macros' / n for n in ('primitives_xsim.v', 'sky130_fd_sc_hd_xsim.v', 'model.v')]
reset_tb = W / 'controls/tb_reset_cdc.sv'
activity_tb = P / 'scripts/tb_activity.sv'
contract = json.loads((P / 'experiment_contract.json').read_text())
for row in contract['source_copies']:
    assert sha(P / row['copy']) == row['sha256'], ('Changed workload', row['copy'])
text = netlist.read_text()
assert 'force dut._52970_.Q' in (P / 'workloads/boot_force.svh').read_text()
assert re.search(r'sky130_fd_sc_hd__dfxtp_\d\s+_52970_\s*\(', text)
sources = models + [netlist, reset_tb, activity_tb, P / 'workloads/boot_force.svh']
receipt = {'netlist': str(netlist), 'netlist_sha256': sha(netlist),
           'source_sha256': {str(p): sha(p) for p in sources},
           'scope': 'Exact H1 candidate zero-delay gate simulation; no SDF, analog metastability, '
                    'recovery/removal or silicon qualification.',
           'activity_runs': []}


def compile_tb(tb, top, name):
    exe = cache / (name + '.vvp')
    with (out / (name + '_compile.log')).open('w') as f:
        subprocess.run(['iverilog', '-g2012', '-DFUNCTIONAL', '-I/work/ppa/workloads', '-s', top, '-o', str(exe),
                        *[str(p) for p in models], str(netlist), str(tb)],
                       stdout=f, stderr=subprocess.STDOUT, check=True)
    return exe


exe = compile_tb(reset_tb, 'tb_reset_cdc', 'reset_cdc')
reset = subprocess.run(['vvp', '-N', str(exe)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
(out / 'reset_cdc.log').write_text(reset.stdout)
m = re.search(r'PASS exact-final-netlist reset/CDC: (\d+) cycles, 8 release phases;', reset.stdout)
assert reset.returncode == 0 and m and int(m[1]) >= 90, reset.stdout[-1000:]
receipt['reset_CDC'] = {'passed': True, 'cycles': int(m[1]), 'release_phases': 8}
print('RESET_CDC_PASS', int(m[1]), flush=True)

exe = compile_tb(activity_tb, 'tb_activity', 'activity')
for work in contract['workloads']:
    name = work['id']
    dest = out / name
    dest.mkdir()
    vcd = cache / (name + '.vcd')
    args = ['vvp', '-N', str(exe), '+CASE=' + name, '+VCD=' + str(vcd)]
    if name != 'idle':
        args += ['+IMAGE=/work/ppa/workloads/' + work['image'], '+WORDS=' + str(work['words']),
                 '+HALT_PC=' + str(work['halt_pc'])]
    run = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    (dest / 'simulation.log').write_text(run.stdout)
    m = re.search(r'PPA_PASS case=(\S+) start_ns=(\d+) end_ns=(\d+) cycles=(\d+) status=(\w+) pc=(\d+)', run.stdout)
    assert run.returncode == 0 and m and m[1] == name and int(m[3]) > int(m[2]) and vcd.stat().st_size > 1000, \
        (name, run.stdout[-1500:])
    final = dest / 'activity.vcd'
    with vcd.open('rb') as inp, final.open('xb') as f:
        shutil.copyfileobj(inp, f, 1024 * 1024)
    assert sha(final) == sha(vcd)
    vcd.unlink()
    row = {'id': name, 'passed': True, 'start_ns': int(m[2]), 'end_ns': int(m[3]), 'cycles': int(m[4]),
           'status': m[5], 'halt_pc': int(m[6]), 'vcd': str(final), 'bytes': final.stat().st_size, 'sha256': sha(final)}
    receipt['activity_runs'].append(row)
    (out / 'progress.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('WORKLOAD_PASS', name, int(m[4]), flush=True)
assert len(receipt['activity_runs']) == 4 and sha(netlist) == receipt['netlist_sha256']
receipt['all_reset_CDC_and_four_workloads_pass'] = True
(out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('FUNCTIONAL_CANDIDATE_COMPLETE', tag, receipt['netlist_sha256'], flush=True)
