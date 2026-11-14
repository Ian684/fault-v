from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/run_final_fill.sh').read_text()
needle='docker run --rm --name faultv-w25-final-fill-beol'
assert code.count(needle)==1
guard='''# Avoid the 10GiB BEOL job overlapping native IR; generation may run concurrently.
if [[ "${FINAL_FILL_WAIT_FOR_IR:-0}" = 1 ]]; then
  while [[ ! -f logs/final_ir.exit ]]; do sleep 5; done
  test "$(cat logs/final_ir.exit)" = 0
fi

'''
code=code.replace(needle,guard+needle)
p=C/'scripts/run_final_fill_parallel.sh';assert not p.exists();p.write_text(code,newline='\n')
print('FINAL_FILL_RESOURCE_ORDER_PREPARED')
