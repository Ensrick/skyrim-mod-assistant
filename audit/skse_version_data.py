"""Read the SKSEPlugin_Version bytes out of an SKSE plugin DLL and apply
SKSE's own master-plugin gate to them.

Parks are cheap to assert and expensive to leave standing, so this reads the
exported struct rather than trusting a Nexus page or a ledger note. Three mods
were parked on inference alone and passed the moment anyone looked (issue #79).

The gate mirrors ianpatt/skse64 skse64/PluginManager.cpp:657-668. The part that
catches people: claiming kVersionIndependent_AddressLibraryPostAE without
kVersionIndependentEx_AddressLibraryV5 is only fatal when the PE TimeDateStamp
lands in [520128000, 1748217600) - anything built after 2025-05-26 passes on the
stamp alone, no flag needed.

  py -3 audit/skse_version_data.py "<instance>/mods/*/SKSE/Plugins/*.dll"
"""
import struct, sys, datetime, os, glob

KVI_ADDRLIB_POSTAE=1; KVI_SIG=2; KVI_STRUCTS629=4
KVIEX_NOSTRUCT=1; KVIEX_ADDRLIBV5=2
PACKED_RUNTIME=(1<<24)|(7<<16)|(104<<4)|0   # MAKE_EXE_VERSION(major,minor,build)

def make_ver(a,b,c,d=0): return (a<<24)|(b<<16)|(c<<4)|d
def unmake(v): return f"{(v>>24)&0xff}.{(v>>16)&0xff}.{(v>>4)&0xfff}.{v&0xf}"

def parse(path):
    d=open(path,'rb').read()
    e_lfanew=struct.unpack_from('<I',d,0x3c)[0]
    assert d[e_lfanew:e_lfanew+4]==b'PE\0\0', 'not PE'
    fh=e_lfanew+4
    machine,nsec,tds,_,_,osz,chars=struct.unpack_from('<HHIIIHH',d,fh)
    oh=fh+20
    magic=struct.unpack_from('<H',d,oh)[0]
    ddoff = oh + (112 if magic==0x20b else 96)
    nrva=struct.unpack_from('<I',d,oh+(108 if magic==0x20b else 92))[0]
    exp_rva,exp_sz=struct.unpack_from('<II',d,ddoff)
    secs=[]
    so=oh+osz
    for i in range(nsec):
        nm,vsz,vad,rsz,rpt=struct.unpack_from('<8sIIII',d,so+i*40)
        secs.append((vad,vsz,rsz,rpt))
    def r2o(rva):
        for vad,vsz,rsz,rpt in secs:
            if vad<=rva<vad+max(vsz,rsz): return rpt+(rva-vad)
        return None
    eo=r2o(exp_rva)
    (_,_,_,_,_,_,nfun,nnam,afun,anam,aord)=struct.unpack_from('<IIHHIIIIIII',d,eo)
    names={}
    for i in range(nnam):
        nr=struct.unpack_from('<I',d,r2o(anam)+i*4)[0]
        o=r2o(nr); en=d[o:d.index(b'\0',o)].decode()
        ordi=struct.unpack_from('<H',d,r2o(aord)+i*2)[0]
        frva=struct.unpack_from('<I',d,r2o(afun)+ordi*4)[0]
        names[en]=frva
    out={'file':path,'timestamp':tds,'exports':sorted(names)}
    if 'SKSEPlugin_Version' not in names:
        out['vd']=None; return out
    vo=r2o(names['SKSEPlugin_Version'])
    dv,pv=struct.unpack_from('<II',d,vo)
    nm=d[vo+8:vo+8+256].split(b'\0')[0].decode('latin1')
    au=d[vo+264:vo+264+256].split(b'\0')[0].decode('latin1')
    em=d[vo+520:vo+520+252].split(b'\0')[0].decode('latin1')
    vix,vi=struct.unpack_from('<II',d,vo+772)
    cv=list(struct.unpack_from('<16I',d,vo+780))
    se=struct.unpack_from('<I',d,vo+844)[0]
    cvl=[]
    for v in cv:
        if v==0: break
        cvl.append(v)
    out['vd']=dict(dataVersion=dv,pluginVersion=pv,name=nm,author=au,email=em,
                   versionIndependenceEx=vix,versionIndependence=vi,
                   compatibleVersions=[unmake(v) for v in cvl],
                   compatRaw=[hex(v) for v in cvl],seVersionRequired=se)
    return out

def gate(o):
    if o['vd'] is None: return 'NO VERSION DATA (would be refused / not an SKSE plugin)'
    v=o['vd']; msgs=[]
    if v['dataVersion']!=1: return 'FAIL: unsupported version data version'
    if v['versionIndependence'] & ~(KVI_ADDRLIB_POSTAE|KVI_SIG|KVI_STRUCTS629):
        return 'FAIL: unsupported version independence method'
    vind = bool(v['versionIndependence'] & (KVI_ADDRLIB_POSTAE|KVI_SIG))
    if v['versionIndependence'] & KVI_ADDRLIB_POSTAE:
        if not (v['versionIndependenceEx'] & KVIEX_ADDRLIBV5):
            bt=o['timestamp']
            # Upper bound is 2026-08-21, the day CommonLibSSE-NG gained Address
            # Library format 5 support (alandtse/CommonLibVR 7b47c5a8f1, release
            # 6.4.0). A DLL linked before that date CANNOT parse a v5 address
            # library no matter what it advertises. The old bound was 2025-05-26,
            # 15 months early, which is why Smart Talk (stamp 2025-12-22) passed
            # this gate on 2026-09-02 and then aborted the SKSE load at plugin 28
            # of 36 with 'failed to open address library file' (#197). Plugins
            # built after the date pass without needing the V5 bit - Better
            # Jumping (2026-08-29) does not set it and loads correctly.
            if 520128000 <= bt < 1787270400:
                msgs.append('addrlib-v5 flag missing AND stamp inside reject window')
                vind=False
    if vind and not (v['versionIndependence'] & KVI_STRUCTS629):
        if not (v['versionIndependenceEx'] & KVIEX_NOSTRUCT):
            return 'FAIL: only compatible with versions earlier than 1.6.629'
    if not vind:
        if any(int(x,16)==PACKED_RUNTIME for x in v['compatRaw']):
            return 'PASS (explicit compatibleVersions entry for 1.7.104)'
        return 'FAIL: incompatible with current version of the game' + (' [%s]'%'; '.join(msgs) if msgs else '')
    return 'PASS (version independent)'

for p in sys.argv[1:]:
    for f in glob.glob(p):
        try:
            o=parse(f)
        except Exception as ex:
            print(f"{f}\n  ERROR {ex}\n"); continue
        ts=datetime.datetime.fromtimestamp(o['timestamp'], datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
        print(f"{f}")
        print(f"  PE stamp: {o['timestamp']} ({ts})")
        if o['vd']:
            v=o['vd']
            print(f"  name={v['name']!r} pluginVersion={v['pluginVersion']} ({unmake(v['pluginVersion']) if v['pluginVersion']>0xffff else v['pluginVersion']}) author={v['author']!r}")
            print(f"  versionIndependence={v['versionIndependence']} versionIndependenceEx={v['versionIndependenceEx']} (V5 bit={'YES' if v['versionIndependenceEx']&2 else 'NO'})")
            print(f"  compatibleVersions={v['compatibleVersions']} raw={v['compatRaw']}")
        else:
            print("  no SKSEPlugin_Version export")
        print(f"  VERDICT: {gate(o)}\n")
