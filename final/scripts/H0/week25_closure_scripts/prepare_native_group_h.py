from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_g.py').read_text().replace('native_group_g','native_group_h')
code=code.replace("source=Path('/runtime_final/native_group_c.odb')", "source=Path('/runtime_final/native_group_g.odb')").replace('reports/native_group_c/result.json','reports/native_group_g/result.json',1)
start=code.index('added_guides=[]\n');end=code.index('oldg=guides(b)\n',start)+len('oldg=guides(b)\n')
code=code[:start]+"added_guides=json.loads((C/'reports/native_group_g/result.json').read_text())['added_local_escape_guides']\n"+code[end:]
code=code.replace("design.evalTclString('set_thread_count 4')", "design.evalTclString('set_thread_count 2')")
needle="reply=design.evalTclString('detailed_route -or_seed 53 -or_k 7 -droute_end_iter 20 -drc_report_iter_step 1 -verbose 1 -output_drc '+str(out/'router.drc'))"
assert code.count(needle)==1
replacement="""reply=design.evalTclString('detailed_route -or_seed 59 -or_k 7 -no_pin_access -single_step_dr -droute_end_iter 64 -drc_report_iter_step 1 -verbose 1 -output_drc '+str(out/'router.drc'))
assert reply in ('',None),reply
step_results=[]
for size,offset,maze,cost,mode in [(11,0,8,128,0),(15,-1,16,256,0),(13,-2,16,512,2),(17,0,16,1024,0),(19,-2,32,2048,0)]:
    cmd=f'drt::step_dr {size} {offset} {maze} {cost} {cost} {cost*8} 0.99 {mode} 0'
    reply=design.evalTclString(cmd+'; set _w25_step_ok ""');assert reply in ('',None),reply
    count=int(design.evalTclString('detailed_route_num_drvs'));step_results.append({'size':size,'offset':offset,'maze_iterations':maze,'cost':cost,'ripup_mode':mode,'native_DRC':count})
    print('LARGE_CONTEXT_STEP',step_results[-1],flush=True)
    (out/'step_progress.json').write_text(json.dumps(step_results,indent=2)+'\\n')
    if count==0:break
reply=design.evalTclString('drt::step_end; set _w25_step_end_ok ""')"""
code=code.replace(needle,replacement)
code=code.replace("'router_reported_DRC':raw", "'large_context_steps':step_results,'router_reported_DRC':raw")
code=code.replace("'native_pin_access_regenerated':True", "'native_pin_access_from_group_G':True")
p=C/'scripts/route_native_group_h.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_H_LARGER_ALL_NET_LOCAL_WORKERS_PREPARED')
