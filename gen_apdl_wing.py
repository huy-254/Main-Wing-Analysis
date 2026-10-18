# -*- coding: utf-8 -*-
"""
Sinh file APDL (ANSYS 2023R2) mo hinh shell nhieu lop cho toan canh CW,
dung truc tiep du lieu va xep lop trong main_CW.m / cross_section_analysis_CW.m.
Chay:  python gen_apdl_wing.py   -> tao wing_CW_shell.inp
"""
import numpy as np

# ---------------------------------------------------------------- tham so
OUT        = 'wing_CW_shell.inp'
DY_MAX     = 0.04          # buoc luoi doc sai lon nhat (m)
N_LE, N_MID, N_AFT = 12, 16, 10   # so phan tu: mep truoc->dai gia cuong truoc, giua 2 dam, dam sau->mep sau
N_FOAM     = 4             # so phan tu trong vung foam cua bung dam (them 4 phan tu: 2 vung vo + 2 vung mu)
NL         = N_FOAM + 4    # tong so phan tu theo chieu cao bung dam / rib
FIX_Y      = 0.26          # vi tri ngam (m)
P_TIP      = 100.0         # luc thu tinh tai dau mut phai (N)
NMODE      = 12
XI1, XI2   = 0.22125, 0.710625         # vi tri tam dam (phan day cung tu mep truoc)
RIBS       = [0, 375, 880, 1560, 2645, 3650, 3830, 4220, 4670, 5405, 5845, 6260, 6745, 7700, 7950]
Y_KV1, Y_KV2, Y_TIP = 1.75, 3.75, 8.0
W_REINF    = 0.050         # be rong dai vo gia cuong (m), canh ben
EXT_DUMMY  = 0.010         # vung canh giua: khoang cach nut phu (khong co gia cuong)

# vat lieu (giong material_2D.m / ply.m / ply3D.m 'foye')
E1f, E2f, G12f, nu12f, rhof, vf = 235e9, 15e9, 27e9, 0.2, 1810.0, 0.63
Em, G12m, num, rhom = 4.3e9, 1.6e9, 0.35, 1270.0
nu23f = 0.4
sv = np.sqrt(vf)
E1 = E1f*vf + Em*(1-vf)
E2 = Em*((1-sv) + sv/(1-sv*(1-Em/E2f)))
G12 = G12m*((1-sv) + sv/(1-sv*(1-G12m/G12f)))
nu12 = nu12f*vf + num*(1-vf)
nu23 = vf*nu23f + (1-vf)*(2*num - nu12*E2/E1)
G23 = E2/(2*(1+nu23))
RHO_UD = rhof*vf + rhom*(1-vf)
T_UD = 0.3/rhof/vf
E_F, NU_F, RHO_F = 70e6, 0.3, 60.0

# ---------------------------------------------------------------- hinh hoc
up_raw = np.array([[800,1.76],[760,16.88],[720,30.8],[640,55.28],[560,76],[480,92.8],[400,105.44],
    [320,113.28],[240,114.16],[200,111.04],[160,105.36],[120,96.32],[80,82.8],[60,73.92],[40,62.56],
    [20,46.72],[10,35.6],[0,0]])/800.0
lo_raw = np.array([[0,0],[10,-19.36],[20,-27.84],[40,-38.24],[60,-44.96],[80,-49.2],[120,-54],[160,-55.84],
    [200,-55.36],[240,-54.08],[320,-49.28],[400,-42.72],[480,-35.2],[560,-26.8],[640,-18.48],[720,-10.16],
    [760,-5.92],[800,-1.76]])/800.0
def zu(xi): o = np.argsort(up_raw[:,0]); return np.interp(xi, up_raw[o,0], up_raw[o,1])
def zl(xi): o = np.argsort(lo_raw[:,0]); return np.interp(xi, lo_raw[o,0], lo_raw[o,1])

def chord(y):
    a = abs(y)
    return 0.8 if a < Y_KV1 else 0.8*(1-(a-Y_KV1)/6.25) + 0.4*(a-Y_KV1)/6.25
def xle(y):
    a = abs(y)
    return 0.8 if a < Y_KV1 else -0.08*(a-Y_KV1)/6.25 + 0.8
def zone(ya):           # 1 = KV1, 2 = KV2, 3 = canh ben (theo |y| cua tam phan tu)
    return 1 if ya < Y_KV1 else (2 if ya <= Y_KV2 else 3)

# be rong (m): hop dam = chieu day sandwich bung dam; side cap mot ben, huong vao trong
def widths(z):
    w1 = 20*T_UD + (0.029 if z < 3 else 0.015)
    w2 = 12*T_UD + 0.0138
    s1 = 0.015 if z < 3 else 0.012
    s2 = 0.012
    return w1, w2, s1, s2

def xi_list(y, z):
    c = chord(y); w1, w2, s1, s2 = widths(z)
    c1a, c1b = XI1 - w1/2/c, XI1 + w1/2/c
    s1b = c1b + s1/c
    s2a = XI2 - w2/2/c - s2/c
    c2a, c2b = XI2 - w2/2/c, XI2 + w2/2/c
    if z == 3:   # dai gia cuong 50 mm dat doi xung tren (mu + side cap)
        m1, m2 = (c1a+s1b)/2, (s2a+c2b)/2
        r1a, r1b = m1 - W_REINF/2/c, m1 + W_REINF/2/c
        r2a, r2b = m2 - W_REINF/2/c, m2 + W_REINF/2/c
    else:
        r1a, r1b = c1a - EXT_DUMMY/c, s1b + EXT_DUMMY/c
        r2a, r2b = s2a - EXT_DUMMY/c, c2b + EXT_DUMMY/c
    br = [0, r1a, c1a, XI1, c1b, s1b, r1b, r2a, s2a, c2a, XI2, c2b, r2b, 1.0]
    assert all(np.diff(br) > 0), (y, br)
    xs = [0.0]
    # S0: cum cosine ve mep truoc
    s = np.linspace(0, 1, N_LE+1)[1:]
    xs += list(r1a*(1-np.cos(np.pi*s/2)))
    for a, b in zip(br[1:6], br[2:7]): xs.append(b)          # S1..S5 (1 phan tu moi doan)
    xs += list(np.linspace(r1b, r2a, N_MID+1)[1:])           # S6
    for a, b in zip(br[7:12], br[8:13]): xs.append(b)        # S7..S11
    xs += list(np.linspace(r2b, 1.0, N_AFT+1)[1:])           # S12
    return np.array(xs)

# phan doan (segment) cua phan tu k (giua xi_k va xi_k+1)
SEG = [0]*N_LE + [1, 2, 3, 4, 5] + [6]*N_MID + [7, 8, 9, 10, 11] + [12]*N_AFT
M = len(SEG)
K1 = N_LE + 2           # chi so xi cua tam dam truoc
K2 = N_LE + 5 + N_MID + 3
REGION = {0:'plain', 6:'plain', 12:'plain', 1:'reinf', 5:'reinf', 7:'reinf', 11:'reinf',
          2:'cap1', 3:'cap1', 4:'side1', 8:'side2', 9:'cap2', 10:'cap2'}

# ---------------------------------------------------------------- xep lop
P45, M45 = 45.0, -45.0
def W(n=1): return [('UD', T_UD, P45), ('UD', T_UD, M45)]*n
def U(n=1): return [('UD', T_UD, 0.0)]*n
def F(t):   return [('F', t, 0.0)]
def skin(z):                # ngoai -> trong
    if z == 1: return W() + U() + F(0.010) + U() + W()
    return W() + F(0.010 if z == 2 else 0.005) + W()
SKR = W() + U(3) + W()
def cap(nrep): return (W() + U(4))*nrep + W()
def cap1(z, upper):
    if upper: return cap({1:27, 2:14, 3:11}[z])
    return cap({1:27, 2:11, 3:11}[z])
def cap2(z, upper):
    if z < 3: return cap(4 if upper else 3)
    return cap(2)
def side1(z): return W(5)
def side2(z): return W(5) if z < 3 else W(3)
def skin_lam(z, region, upper):
    base = SKR if (z == 3 and region != 'plain') else skin(z)
    if region in ('plain', 'reinf'): return base
    if region == 'cap1':  return base + cap1(z, upper)
    if region == 'cap2':  return base + cap2(z, upper)
    if region == 'side1': return base + side1(z)
    if region == 'side2': return base + side2(z)
def web1(z): return W(5) + F(0.029 if z < 3 else 0.015) + W(5)
def web2(z): return W(3) + F(0.0138) + W(3)
def rib(z):  return W(2) + F(0.010 if z < 3 else 0.005) + W(2)

RHO = {'UD': RHO_UD, 'F': RHO_F, 'UD0': 0.0, 'F0': 0.0}
MATID = {'UD': 1, 'F': 2, 'UD0': 3, 'F0': 4}
def areal(lam): return sum(RHO[m]*t for m, t, _ in lam)
def massless(lam): return [(m + '0', t, th) for m, t, th in lam]

SECS = {}      # (tuple lam, offset) -> id
def secid(lam, off):
    key = (tuple(lam), off)
    if key not in SECS: SECS[key] = len(SECS) + 1
    return SECS[key]

def lam_t(lam): return sum(t for _, t, _ in lam)
def web_fracs(y, z, w, zU, zL):
    # cao do cac muc nut tren bung dam: OML duoi, mat trong vo, mat trong mu, ...foam..., mat trong mu, mat trong vo, OML tren
    tsk = lam_t(SKR) if z == 3 else lam_t(skin(z))
    if w == 0: tcu, tcl = lam_t(cap1(z, True)), lam_t(cap1(z, False))
    else:      tcu, tcl = lam_t(cap2(z, True)), lam_t(cap2(z, False))
    H = zU - zL
    lv = [0.0, tsk, tsk+tcl] + list(np.linspace(tsk+tcl, H-tsk-tcu, N_FOAM+1)[1:-1]) + [H-tsk-tcu, H-tsk, H]
    f = np.array(lv)/H
    assert np.all(np.diff(f) > 0), (y, w, f)
    return f
def walls(w, z): return (W(5) + W(5)) if w == 0 else (W(3) + W(3))   # 2 thanh, khong foam

# ---------------------------------------------------------------- tram doc sai
yh = sorted(set([0.0, FIX_Y, Y_KV1, Y_KV2, Y_TIP] + [r/1000 for r in RIBS]))
st = [yh[0]]
for a, b in zip(yh[:-1], yh[1:]):
    n = int(np.ceil((b-a)/DY_MAX - 1e-9))
    st += list(np.linspace(a, b, n+1)[1:])
st = np.array(st)
Y = np.concatenate([-st[:0:-1], st])
NS = len(Y)
NC = 2*M + 1           # so nut tren duong bao moi tram (vong kin)

nodes = {}             # id -> (x,y,z)
def nid_c(j, i): return j*NC + i + 1                     # nut duong bao
NBASE_W = NS*NC
def nid_w(j, w, k):                                       # nut trong bung dam, k = 1..NL-1
    return NBASE_W + (j*2 + w)*(NL-1) + k
NBASE_R = NBASE_W + NS*2*(NL-1)

def contour(j):
    y = Y[j]; c = chord(y); xl = xle(y)
    z = zone(abs(y))   # zone cua tram (dung cho vi tri nut)
    xs = xi_list(y, z)
    pts = []
    for k in range(M, 0, -1): pts.append((xl - xs[k]*c, y, zu(xs[k])*c))   # tren: mep sau -> mep truoc
    pts.append((xl, y, 0.0))                                               # mep truoc
    for k in range(1, M+1):  pts.append((xl - xs[k]*c, y, zl(xs[k])*c))   # duoi: mep truoc -> mep sau
    return pts, xs

FR = {}
for j in range(NS):
    pts, xs = contour(j)
    for i, p in enumerate(pts): nodes[nid_c(j, i)] = p
    for w, K in enumerate([K1, K2]):
        pu = np.array(nodes[nid_c(j, M-K)]); pl = np.array(nodes[nid_c(j, M+K)])
        FR[j, w] = web_fracs(Y[j], zone(abs(Y[j])), w, pu[2], pl[2])
        for k in range(1, NL):
            nodes[nid_w(j, w, k)] = tuple(pl + (pu-pl)*FR[j, w][k])

def web_node(j, w, k):         # k = 0 (duoi) .. NL (tren)
    K = K1 if w == 0 else K2
    if k == 0: return nid_c(j, M+K)
    if k == NL: return nid_c(j, M-K)
    return nid_w(j, w, k)

# ---------------------------------------------------------------- phan tu
elems = []     # (type, sec, esys, n1..n4, comp)
for j in range(NS-1):
    ya = abs((Y[j]+Y[j+1])/2); z = zone(ya)
    for i in range(NC):
        n1, n2 = nid_c(j, i), nid_c(j, (i+1) % NC)
        n3, n4 = nid_c(j+1, (i+1) % NC), nid_c(j+1, i)
        if i == NC-1:                       # dai khep mep sau
            reg, upper = 'plain', True
        elif i < M:                         # mat tren: giua xi_(M-i) va xi_(M-i-1)
            reg, upper = REGION[SEG[M-i-1]], True
        else:                               # mat duoi: giua xi_(i-M) va xi_(i-M+1)
            reg, upper = REGION[SEG[i-M]], False
        lam = skin_lam(z, reg, upper)
        etype = {'plain':1, 'reinf':(4 if z == 3 else 1), 'cap1':2, 'cap2':2, 'side1':3, 'side2':3}[reg]
        elems.append((etype, secid(lam, 'TOP'), 11, n1, n2, n3, n4))
    for w in (0, 1):
        for k in range(NL):
            if 2 <= k < NL-2: lam = web1(z) if w == 0 else web2(z)   # vung foam
            elif k in (1, NL-2): lam = walls(w, z)                   # vung mu: chi 2 thanh
            else: lam = massless(walls(w, z))                        # trung voi chieu day vo: chi giu lien ket, khong khoi luong
            elems.append((5+w, secid(lam, 'MID'), 11, web_node(j, w, k), web_node(j, w, k+1),
                          web_node(j+1, w, k+1), web_node(j+1, w, k)))

# rib: mat phang y = hang so, giua tam hai dam
rib_y = sorted(set([r/1000 for r in RIBS] + [-r/1000 for r in RIBS]))
nr = NBASE_R
for yr in rib_y:
    j = int(np.argmin(abs(Y - yr))); assert abs(Y[j]-yr) < 1e-9
    z = 1 if abs(yr) < Y_KV1 else (2 if abs(yr) <= Y_KV2 else 3)
    sid = secid(rib(z), 'MID')
    grid = {}
    for K in range(K1, K2+1):
        pu = np.array(nodes[nid_c(j, M-K)]); pl = np.array(nodes[nid_c(j, M+K)])
        fr = FR[j, 0] + (FR[j, 1]-FR[j, 0])*(K-K1)/(K2-K1)
        for k in range(NL+1):
            if K == K1: grid[K, k] = web_node(j, 0, k)
            elif K == K2: grid[K, k] = web_node(j, 1, k)
            elif k == 0: grid[K, k] = nid_c(j, M+K)
            elif k == NL: grid[K, k] = nid_c(j, M-K)
            else:
                nr += 1; nodes[nr] = tuple(pl + (pu-pl)*fr[k]); grid[K, k] = nr
    sid0 = secid(massless(rib(z)), 'MID')
    for K in range(K1, K2):
        for k in range(NL):
            elems.append((7, sid0 if k in (0, NL-1) else sid, 0, grid[K, k], grid[K+1, k], grid[K+1, k+1], grid[K, k+1]))

# ---------------------------------------------------------------- kiem tra trong Python
P = {n: np.array(p) for n, p in nodes.items()}
def quad_area_normal(e):
    a, b, c_, d = (P[n] for n in e[3:7])
    nv = np.cross(c_-a, d-b)/2
    return np.linalg.norm(nv), nv
inv_sec = {v: k for k, v in SECS.items()}
mass_type = {}
bad = 0
for e in elems:
    A, nv = quad_area_normal(e)
    assert A > 1e-8, e
    mass_type[e[0]] = mass_type.get(e[0], 0) + A*areal(inv_sec[e[1]][0])
    if e[0] <= 4:   # phap tuyen vo phai huong ra ngoai
        jy = P[e[3]][1]; j = int(np.argmin(abs(Y-jy)))
        cen = np.mean([P[nid_c(j, i)] for i in range(NC)], axis=0)
        ec = np.mean([P[n] for n in e[3:7]], axis=0)
        r = ec - cen; r[1] = 0
        if np.dot(nv, r) <= 0: bad += 1
assert bad == 0, f'{bad} phan tu vo co phap tuyen huong vao trong'
split = {'skin': 0.0, 'cap1': 0.0, 'cap2': 0.0, 'side': 0.0}
for e in elems:
    if e[0] in (2, 3):
        A, _ = quad_area_normal(e)
        lam = inv_sec[e[1]][0]
        zc = abs(np.mean([P[n][1] for n in e[3:7]])); z = zone(zc)
        base = SKR if (z == 3) else skin(z)
        split['skin'] += A*areal(base)
        xc = np.mean([P[n][0] for n in e[3:7]]); xi = (xle(zc) - xc)/chord(zc)
        key = 'side' if e[0] == 3 else ('cap1' if xi < 0.5 else 'cap2')
        split[key] += A*(areal(lam) - areal(base))
    elif e[0] in (1, 4):
        A, _ = quad_area_normal(e); split['skin'] += A*areal(inv_sec[e[1]][0])
TYPE_NAME = {1:'Vo thuong (ke ca dai phu canh giua)', 2:'Vo + mu dam (truoc & sau)', 3:'Vo + side cap',
             4:'Vo gia cuong (canh ben, ngoai mu/side cap)', 5:'Bung dam truoc', 6:'Bung dam sau', 7:'Rib'}

# nut de do do vong: nut bung dam truoc & sau tai cac tram
def station_web_nodes(yt):
    j = int(np.argmin(abs(Y - yt)))
    return Y[j], [web_node(j, w, k) for w in (0, 1) for k in range(NL+1)]

# ---------------------------------------------------------------- ghi APDL
L = []
w = L.append
w('! =====================================================================')
w('! Mo hinh shell nhieu lop toan canh CW - sinh tu gen_apdl_wing.py')
w('! Du lieu: main_CW.m, cross_section_analysis_CW.m, material_2D.m, ply.m')
w('! Don vi SI (m, kg, N, Pa).  x: huong ve phia truoc, y: doc sai, z: len')
w('! Nut vo dat tai OML, cac lop dap vao trong (SECOFFSET,TOP, phap tuyen huong ra ngoai)')
w('! Mu dam / side cap / vo gia cuong: ghep vao laminate cua vo, xep tiep sau cac lop vo')
w('! Bung dam (thanh truoc + foam + thanh sau) va rib: shell sandwich dat tai mat giua')
w('! ANSYS 2023R2, SHELL181 KEYOPT(3)=2, KEYOPT(8)=2')
w('! =====================================================================')
w('FINISH')
w('/CLEAR,NOSTART')
w('/TITLE,CW wing - layered shell model from MATLAB data')
w('/PREP7')
w('/NERR,200,10000')
for t in range(1, 8):
    w(f'ET,{t},SHELL181')
    w(f'KEYOPT,{t},3,2')
    w(f'KEYOPT,{t},8,2')
for t, nm in TYPE_NAME.items(): w(f'! TYPE {t}: {nm}')
w('!')
w('! --- Vat lieu 1: lop UD AS4/3501-6 (vi co nhu ply.m; nu23, G23 theo Foye nhu ply3D.m)')
w(f'MP,EX,1,{E1:.6e}'); w(f'MP,EY,1,{E2:.6e}'); w(f'MP,EZ,1,{E2:.6e}')
w(f'MP,PRXY,1,{nu12:.6f}'); w(f'MP,PRYZ,1,{nu23:.6f}'); w(f'MP,PRXZ,1,{nu12:.6f}')
w(f'MP,GXY,1,{G12:.6e}'); w(f'MP,GYZ,1,{G23:.6e}'); w(f'MP,GXZ,1,{G12:.6e}')
w(f'MP,DENS,1,{RHO_UD:.4f}')
w('! --- Vat lieu 2: PVC foam')
w(f'MP,EX,2,{E_F:.6e}'); w(f'MP,PRXY,2,{NU_F}'); w(f'MP,DENS,2,{RHO_F}')
w('! --- Vat lieu 3, 4: nhu 1, 2 nhung khong khoi luong (doan bung dam / rib trung voi chieu day vo)')
w('MPCOPY,,1,3'); w('MP,DENS,3,1e-6')
w('MPCOPY,,2,4'); w('MP,DENS,4,1e-6')
w(f'! Chieu day 1 lop UD = {T_UD*1e3:.5f} mm; woven = 2 lop UD +-45 (nhu code MATLAB)')
w('!')
w('! --- He toa do dinh huong: truc x cuc bo // truc y tong the (0 do doc sai)')
w('LOCAL,11,0,0,0,0,90')
w('CSYS,0')
w('!')
w('! --- Section (SECDATA liet ke tu lop trong cung -> lop ngoai cung)')
for (lam, off), sid in sorted(SECS.items(), key=lambda kv: kv[1]):
    w(f'SECTYPE,{sid},SHELL')
    for m, t, th in reversed(lam):
        w(f'SECDATA,{t:.8f},{MATID[m]},{th:.1f},3')
    w(f'SECOFFSET,{off}')
w('!')
w('! --- Nut')
for n in sorted(nodes):
    x, y, zc = nodes[n]
    w(f'N,{n},{x:.7f},{y:.7f},{zc:.7f}')
w('!')
w('! --- Phan tu')
cur = (None, None, None)
for e in sorted(elems, key=lambda e: (e[0], e[1], e[2])):
    if e[:3] != cur:
        w(f'TYPE,{e[0]}'); w(f'SECNUM,{e[1]}'); w(f'ESYS,{e[2]}')
        cur = e[:3]
    w(f'E,{e[3]},{e[4]},{e[5]},{e[6]}')
w('ESYS,0')
w('FINISH')
w('!')
w('! =================== 1. Phan tich tinh: 100 N tai dau mut phai ===================')
w('/SOLU')
w('ANTYPE,STATIC')
w('IRLF,-1                 ! in "PRECISE MASS SUMMARY" va khoi luong theo TYPE trong output')
w(f'NSEL,S,LOC,Y,{FIX_Y-1e-5},{FIX_Y+1e-5}')
w(f'NSEL,A,LOC,Y,{-FIX_Y-1e-5},{-FIX_Y+1e-5}')
w('D,ALL,ALL')
w('NSEL,ALL')
yt, tipn = station_web_nodes(Y_TIP)
for n in tipn: w(f'F,{n},FZ,{P_TIP/len(tipn):.6f}')
w('SOLVE')
w('FINISH')
w('/POST1')
w('SET,LAST')
w('*CFOPEN,wing_CW_results,txt')
w("*VWRITE")
w("('Do vong UZ trung binh tai bung hai dam, luc 100 N o dau mut y = +8 m')")
for yy in [1, 2, 4, 6, 8]:
    ya, ns = station_web_nodes(yy)
    w('UZS=0')
    for n in ns:
        w(f'*GET,UZN,NODE,{n},U,Z')
        w('UZS=UZS+UZN')
    w(f'UZAVG=UZS/{len(ns)}*1000')
    w(f'YST={ya:.4f}')
    w('*VWRITE,YST,UZAVG')
    w("('  y = ',F8.3,' m   UZ = ',F10.3,' mm')")
w('*CFCLOS')
w('FINISH')
w('!')
w('! =================== 2. Phan tich dao dong rieng ===================')
w('/SOLU')
w('ANTYPE,MODAL,NEW')
w('FDELE,ALL,ALL')
w(f'NSEL,S,LOC,Y,{FIX_Y-1e-5},{FIX_Y+1e-5}')
w(f'NSEL,A,LOC,Y,{-FIX_Y-1e-5},{-FIX_Y+1e-5}')
w('D,ALL,ALL')
w('NSEL,ALL')
w(f'MODOPT,LANB,{NMODE}')
w(f'MXPAND,{NMODE}')
w('SOLVE')
w('FINISH')
w('/POST1')
w('SET,LIST')
w('*CFOPEN,wing_CW_results,txt,,APPEND')
w("*VWRITE")
w("('Tan so rieng (Hz)')")
w(f'*DO,II,1,{NMODE}')
w('*GET,FRQ,MODE,II,FREQ')
w('*VWRITE,II,FRQ')
w("('  Mode ',F4.0,'   f = ',F10.4,' Hz')")
w('*ENDDO')
w('*CFCLOS')
w('SET,1,1')
w('/VIEW,1,-1,-1,1')
w('PLDISP,1')
w('! Xem cac mode khac: SET,1,<mode>  roi  PLNSOL,U,SUM')

open(OUT, 'w', encoding='ascii', errors='replace').write('\n'.join(L) + '\n')

# ---------------------------------------------------------------- tom tat
print(f'Tram doc sai: {NS}, nut: {len(nodes)}, phan tu: {len(elems)}, section: {len(SECS)}')
tot = 0
for t in sorted(mass_type):
    print(f'  TYPE {t} {TYPE_NAME[t]:45s} {mass_type[t]:8.3f} kg'); tot += mass_type[t]
print(f'  Tong khoi luong toan canh: {tot:.3f} kg')
print('  Tach: ' + ', '.join(f'{k} {v:.2f} kg' for k, v in split.items()))
print(f'UD: E1={E1/1e9:.3f} E2={E2/1e9:.3f} G12={G12/1e9:.3f} G23={G23/1e9:.3f} GPa nu12={nu12:.4f} nu23={nu23:.4f} rho={RHO_UD:.1f} t={T_UD*1e3:.5f} mm')
