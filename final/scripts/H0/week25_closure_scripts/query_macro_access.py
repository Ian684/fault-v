import odb
db=odb.dbDatabase.create();odb.read_db(db,'/work/week25_closure/inputs/cached_guided.odb');b=db.getChip().getBlock()
for inst in b.getInsts():
    if inst.getMaster().isBlock():
        print('MACRO',inst.getName(),'INDEX',inst.getPinAccessIdx())
        for pin in inst.getITerms():
            if pin.getNet() and str(pin.getMTerm().getSigType()) not in ('POWER','GROUND'):
                print('PIN',pin.getMTerm().getName(),'PREF',len(pin.getPrefAccessPoints()))
                print('MPIN_METHODS',[n for n in dir(odb.dbMPin) if 'ccess' in n])
                for mpin in pin.getMTerm().getMPins():
                    caches=mpin.getPinAccess()
                    print('CACHES',type(caches),len(caches))
                    cache=caches[inst.getPinAccessIdx()]
                    print('PIN_ACCESS',cache,'METHODS',[n for n in dir(cache) if 'oint' in n])
                    if cache is not None:print('POINTS',len(cache.getAccessPoints()))
                break
        break
