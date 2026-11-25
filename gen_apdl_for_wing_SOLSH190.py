# -*- coding: utf-8 -*-
"""
gen_apdl_for_wing_SOLSH190.py - Sinh file APDL mo hinh KHOI nhieu lop cho toan canh chinh CW.

Cung cach lam voi ../2. phan tich duoi ngang/gen_apdl_for_DN_v2.py, du lieu lay tu
main_CW.m / cross_section_analysis_CW.m / gen_apdl_for_wing.py:
  B1. Chia diem tren mat ngoai (OML) cua mat cat, mep truoc chia day (cosine).
      Day cung thuon tu y = 1.75 m nen cac cot theo day cung tinh rieng cho tung tram
      (be rong dam, side cap, dai gia cuong la kich thuoc tuyet doi).
  B2. Tai moi diem, offset vao trong theo chieu day cac "tang" xep lop:
        tang 1 = woven ngoai, tang 2 = loi, tang 3 = woven trong,
        tang A, B = mu dam / side cap (chi co o vung dam); tang B chia thanh N_CAP_B phan tu.
      Mu dam + side cap: offset theo phuong THANG DUNG; noi khac (ke ca dai gia cuong) theo phap tuyen.
  B3. Mep sau: vo tren + vo duoi khong du cho -> giam loi, khe giua lap bang foam.
  B4. Bung dam: thanh truoc / foam / thanh sau, noi mat trong mu duoi voi mat trong mu tren.
  B5. Cac tram doc sai (trung vi tri tai, rib, ranh gioi vung xep lop, ngam),
      noi hai tram lien tiep thanh phan tu khoi 8 nut.
  B6. Rib: khoi day t_rib theo y, nam giua hai dam; them 2 dai phan tu doc mat trong vo
      de lap kin goc mu dam / side cap.
  B7. Kiem tra (Jacobian 8 goc, khoi luong theo TYPE), ve mat cat, ghi APDL.

Phan tu:
  SOLSH190: cac tang composite cua vo, mu dam, side cap, thanh bung dam, rib.
            Lop 1 nam o mat duoi (I-J-K-L), xep dan len mat tren (M-N-O-P).
  SOLID185: foam loi bung dam, foam lap mep sau.

Chay:  py -3 gen_apdl_for_wing_SOLSH190.py   -> tao APDL_for_wing_SOLSH190.inp

Ghi chu cho nguoi quen MATLAB:
  - Chi so bat dau tu 0; range(a, b) la a, a+1, ..., b-1 (khong gom b).
  - dict giong struct, list giong cell array mot chieu, tuple la list khong sua duoc.
  - Moi lop cua mot xep lop (layup) la mot bo (vat lieu, chieu day (m), goc (do)).
  - So hieu nut duoc cap theo thu tu nut duoc goi lan dau (ham get_node), nen KHONG doi
    thu tu cac vong lap tao phan tu neu muon giu nguyen so hieu nut.
"""
import os
import numpy as np


# =============================================================================
# 1. THAM SO (ten giu nguyen vi bao cao va CLAUDE.md nhac den)
# =============================================================================
OUT = 'APDL_for_wing_SOLSH190.inp'
OUT_DIRS = ['.', r'E:\luan an\ve lai UAV - ANSYS\APDL canh chinh SOLSH190']
RES = 'wing_SOLSH190_results'         # file ket qua APDL ghi ra (.txt)
PNG_PREFIX = 'wing_SOLSH190_section_y'
dy = 0.04                             # buoc luoi doc sai lon nhat (m)
N_LE = 12                             # so phan tu tu mep truoc den dai gia cuong truoc
N_MID = 16                            # so phan tu giua hai dam
N_AFT = 10                            # so phan tu tu dam sau den mep sau
N_FOAM_X = 3                          # so phan tu foam theo be rong bung dam
N_H = 8                               # so phan tu theo chieu cao bung dam / rib
N_CAP_B = 2                           # so phan tu chia tang B cua mu dam theo chieu day (mu dam co 1 + N_CAP_B phan tu)
FIX_Y = 0.26                          # vi tri ngam (m), nhu gen_apdl_for_wing.py
FIX_MODE = 'all'                    # 'all': ca mat cat | 'webs' ('caps' nhu 'webs'): moi nut co x trong be rong bung 2 dam
NMODE = 12
XI1 = 0.22125                         # vi tri tam dam truoc (phan day cung tu mep truoc)
XI2 = 0.710625                        # vi tri tam dam sau
RIBS = [0, 375, 880, 1560, 2645, 3650, 3830, 4220, 4670, 5405, 5845, 6260, 6745, 7700, 7950]   # mm, doi xung
Y_KV1 = 1.75
Y_KV2 = 3.75
Y_TIP = 8.0
W_REINF_1 = 0.050                     # be rong dai vo gia cuong canh ngoai, dam truoc (d_reinf_1 trong main_CW.m)
W_REINF_2 = 0.047                     # dam sau (d_reinf_2)
EXT_DUMMY = 0.010                     # canh giua: khoang cach cot phu ngoai mu + side cap (khong gia cuong)
TE_FILL = 0.8                         # mep sau: chieu day vo moi ben <= TE_FILL * nua chieu day bien dang
FRONT_SHARE = 0.8                     # ty le tai vao dam truoc (nhu M_t trong cross_section_analysis_CW.m)
LOAD_SCALE = 1.3*3.8/2                # aerodynamic_load.txt: chia 2 (moi nua canh), nhan 1.3*3.8 (nhu main_CW.m)
G_ACC = 9.81                          # trong luong ban than (n_load = 1)
PLOT_SECTIONS = True
SECTION_Y = [0.369, 1.0, 3.0, 6.0]    # mat cat can ve (m): 0.369 = mat rib y = 375 mm, roi moi vung mot mat cat
OUT_Y = [-8.0, -6.0, -4.0, -2.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]

# Vat lieu (giong material_2D.m / ply.m / ply3D.m 'foye')
E1f = 235e9
E2f = 15e9
G12f = 27e9
nu12f = 0.2
rhof = 1810.0
vf = 0.63
Em = 4.3e9
G12m = 1.6e9
num = 0.35
rhom = 1270.0
nu23f = 0.4

square_root_vf = np.sqrt(vf)
E1 = E1f*vf + Em*(1-vf)
E2 = Em*((1-square_root_vf) + square_root_vf/(1-square_root_vf*(1-Em/E2f)))
G12 = G12m*((1-square_root_vf) + square_root_vf/(1-square_root_vf*(1-G12m/G12f)))
nu12 = nu12f*vf + num*(1-vf)
nu23 = vf*nu23f + (1-vf)*(2*num - nu12*E2/E1)
G23 = E2/(2*(1+nu23))
RHO_UD = rhof*vf + rhom*(1-vf)
T_UD = 0.3/rhof/vf                    # chieu day 1 lop UD (m)
E_F = 70e6                            # PVC_Foam.m
NU_F = 0.3
RHO_F = 60.0


# =============================================================================
# 2. XEP LOP (giong cross_section_analysis_CW.m)
#    Ky hieu nhu bao cao: W = 1 woven (2 lop UD +-45), U = 1 lop UD 0 do, F = foam.
#    Vung: 1 = KV1 (|y| < 1.75), 2 = KV2 (<= 3.75), 3 = canh ngoai.
# =============================================================================
def woven(count=1):
    one_woven = [('UD', T_UD, 45.0), ('UD', T_UD, -45.0)]
    return one_woven*count            # nhan list voi so nguyen = lap lai list (giong repmat)


def ud(count=1):
    return [('UD', T_UD, 0.0)]*count


def foam(thickness):
    return [('F', thickness, 0.0)]


def layup_thickness(layup):
    total = 0
    for material, thickness, angle in layup:
        total = total + thickness
    return total


def zone(y_abs):
    """Vung xep lop theo |y|: 1 (KV1, < 1.75), 2 (KV2, <= 3.75) hoac 3 (canh ngoai)."""
    if y_abs < Y_KV1:
        return 1
    if y_abs <= Y_KV2:
        return 2
    return 3


def skin_lam(zone_number, kind):
    """Xep lop 3 tang cua vo [ngoai, loi, trong] tai mot doan vo.
    kind: 'skin', 'skin_reinf', 'side' hoac 'cap'.
    Canh ngoai: dai gia cuong (ke ca duoi mu dam, side cap) = 1woven/3UD/1woven.
    """
    if zone_number == 3 and kind != 'skin':
        return [woven(), ud(3), woven()]
    if zone_number == 1:
        return [woven(), ud() + foam(0.010) + ud(), woven()]     # 1woven/1UD/F10/1UD/1woven
    if zone_number == 2:
        return [woven(), foam(0.010), woven()]                    # 1woven/F10/1woven
    return [woven(), foam(0.005), woven()]                        # 1woven/F5/1woven


def cap_full(zone_number, spar, upper):
    """Xep lop day du cua mu dam: n lan (woven + 4 UD) roi them 1 woven.
    spar: 1 = dam truoc, 2 = dam sau; upper: True = mu tren.
    """
    if spar == 1:
        if upper:
            repeats = {1: 27, 2: 14, 3: 11}[zone_number]
        else:
            repeats = {1: 27, 2: 11, 3: 11}[zone_number]
    else:
        if zone_number < 3:
            if upper:
                repeats = 4
            else:
                repeats = 3
        else:
            repeats = 2
    return (woven() + ud(4))*repeats + woven()


def side_lam(zone_number, spar):
    """Side cap: 5 woven (dam truoc; dam sau canh giua), 3 woven (dam sau canh ngoai)."""
    if spar == 1 or zone_number < 3:
        return woven(5)
    return woven(3)


def cap_lam(zone_number, kind, spar, upper):
    """Cac tang [A, B_1, ..., B_N] (N = N_CAP_B) dap tiep vao mat trong vo.
      kind = 'cap'  : A = cac lop dau cua mu dam (cung so lop side cap),
                      phan con lai (B) chia deu theo so lop thanh N_CAP_B tang
      kind = 'side' : A = side cap, cac tang B rong
      vung khac     : tat ca rong
    Tach A/B nhu vay de mu dam va side cap deu la khoi chu nhat, dung chung nut.
    """
    tiers = []
    if kind == 'cap':
        cap = cap_full(zone_number, spar, upper)
        number_in_A = len(side_lam(zone_number, spar))
        tiers.append(cap[:number_in_A])
        rest = cap[number_in_A:]
        for part in range(N_CAP_B):
            first_layer = round(len(rest)*part/N_CAP_B)
            last_layer = round(len(rest)*(part + 1)/N_CAP_B)
            tiers.append(rest[first_layer:last_layer])
        return tiers
    if kind == 'side':
        tiers.append(side_lam(zone_number, spar))
    else:
        tiers.append([])
    for part in range(N_CAP_B):
        tiers.append([])
    return tiers


def web_wall(spar):
    """Moi thanh bung dam: 5 woven (dam truoc), 3 woven (dam sau)."""
    if spar == 1:
        return woven(5)
    return woven(3)


def web_core(zone_number, spar):
    """Chieu day loi foam bung dam (m): dam truoc 29 mm (canh giua) / 15 mm (canh ngoai), dam sau 13.8 mm."""
    if spar == 1:
        if zone_number < 3:
            return 0.029
        return 0.015
    return 0.0138


def rib_lam(zone_number):
    """Rib: 2woven / foam 10 mm (canh ngoai 5 mm) / 2woven."""
    if zone_number < 3:
        return woven(2) + foam(0.010) + woven(2)
    return woven(2) + foam(0.005) + woven(2)


def cut_lam(layup, start, end):
    """Lay phan xep lop nam trong khoang chieu day [start, end] (m, tinh tu mat ngoai lop dau).
    Dung cho rib bi chia thanh nhieu phan tu theo y.
    """
    result = []
    position = 0.0
    for material, thickness, angle in layup:
        a = max(position, start)
        b = min(position + thickness, end)
        if b - a > 1e-12:
            result.append((material, b - a, angle))
        position += thickness                                     # a += b nghia la a = a + b
    return result


def fit_lam(layup, target):
    """Thu xep lop ve chieu day target: giam foam truoc, het foam moi thu nho cac lop con lai.
    Giu nguyen neu target >= chieu day hien co, hoac xep lop chi co mot loai vat lieu
    (khi do ANSYS tu co gian deu cac lop).
    """
    excess = layup_thickness(layup) - target
    materials = set()
    for material, thickness, angle in layup:
        materials.add(material)
    if excess <= 1e-9 or len(materials) < 2:
        return layup

    foam_thickness = 0
    for material, thickness, angle in layup:
        if material == 'F':
            foam_thickness = foam_thickness + thickness
    if foam_thickness - excess > 1e-6:
        factor = (foam_thickness - excess)/foam_thickness
        result = []
        for material, thickness, angle in layup:
            if material == 'F':
                result.append((material, thickness*factor, angle))
            else:
                result.append((material, thickness, angle))
        return result

    without_foam = []
    for material, thickness, angle in layup:
        if material != 'F':
            without_foam.append((material, thickness, angle))
    factor = target/layup_thickness(without_foam)
    result = []
    for material, thickness, angle in without_foam:
        result.append((material, thickness*factor, angle))
    return result


# =============================================================================
# 3. BIEN DANG CANH VA HINH DANG TRONG MAT BANG
#    File .dat: cot [x z] (mm), NACA 4421, day cung 800 mm. Noi suy theo sqrt(x/c).
# =============================================================================
def load_airfoil(file_name):
    """Doc mot mat bien dang: tra ve mang (n, 2) [x/c, z/c], sap xep tang theo x."""
    data = np.loadtxt(file_name)[:, [0, -1]]        # cot dau (x) va cot cuoi (z)
    data = data[np.argsort(data[:, 0])]
    return data/data[:, 0].max()


upper_surface = load_airfoil('upper_point.dat')
lower_surface = load_airfoil('lower_point.dat')


def z_upper(xi):
    return np.interp(np.sqrt(xi), np.sqrt(upper_surface[:, 0]), upper_surface[:, 1])


def z_lower(xi):
    return np.interp(np.sqrt(xi), np.sqrt(lower_surface[:, 0]), lower_surface[:, 1])


def chord(y):
    """Day cung (m): 0.8 khi |y| < 1.75, thuon tuyen tinh ve 0.4 tai |y| = 8."""
    distance = abs(y)
    if distance < Y_KV1:
        return 0.8
    return 0.8*(1 - (distance - Y_KV1)/6.25) + 0.4*(distance - Y_KV1)/6.25


def xle(y):
    """Toa do x cua mep truoc (x huong ve phia truoc), nhu main_CW.m."""
    distance = abs(y)
    if distance < Y_KV1:
        return 0.8
    return -0.08*(distance - Y_KV1)/6.25 + 0.8


# =============================================================================
# 4. B1 - CAU TRUC COT THEO DAY CUNG (chung cho moi tram)
#    Chi so cot k = 0 (mep truoc) .. M (mep sau); vi tri xi cua cot doi theo tram.
# =============================================================================
K1A = N_LE + 1                        # mat truoc dam truoc (dai gia cuong bat dau o cot N_LE)
K1B = K1A + N_FOAM_X + 2              # mat sau dam truoc
K1S = K1B + 1                         # mep side cap dam truoc
K2S = K1S + N_MID + 2                 # mep side cap dam sau
K2A = K2S + 1                         # mat truoc dam sau
K2B = K2A + N_FOAM_X + 2              # mat sau dam sau
M = K2B + 1 + N_AFT                   # cot mep sau
NC = 2*M + 1                          # so cot tren duong bao kin

# Muc nut theo chieu day tai moi cot: 0 = OML, 1..3 = sau woven ngoai / loi / woven trong,
# 4 = sau tang A, 5 .. 4+N_CAP_B = sau cac tang B. INNER_LEVEL = mat trong mu dam (noi voi bung dam, rib).
INNER_LEVEL = 4 + N_CAP_B
NUMBER_OF_LEVELS = INNER_LEVEL + 1


def _seg_kind(k):
    """Vung ket cau cua doan giua cot k va k+1 theo day cung.
    Tra ve (kind, spar): kind = 'cap', 'side', 'skin_reinf' hoac 'skin'; spar = 1, 2 (0 voi vo thuong).
    """
    if K1A <= k < K1B:
        return 'cap', 1
    if k == K1B:
        return 'side', 1
    if K2A <= k < K2B:
        return 'cap', 2
    if k == K2S:
        return 'side', 2
    if k == K1A - 1 or k == K1S:
        return 'skin_reinf', 1
    if k == K2S - 1 or k == K2B:
        return 'skin_reinf', 2
    return 'skin', 0


SEG = []                              # SEG[k] = vung cua doan giua cot k va k+1
for k in range(M):
    SEG.append(_seg_kind(k))

RANK = {'skin': 0, 'skin_reinf': 1, 'side': 2, 'cap': 3}

# COLREG[k] = vung "manh" nhat (theo RANK) trong hai doan ke ben cot k; dung de lay chieu day tai cot
COLREG = []
for k in range(M + 1):
    strongest = None
    for q in (k - 1, k):
        if 0 <= q < M:
            if strongest is None or RANK[SEG[q][0]] > RANK[strongest[0]]:
                strongest = SEG[q]
    COLREG.append(strongest)

# VERT[k] = True: cot thuoc mu dam / side cap -> offset theo phuong thang dung
VERT = []
for k in range(M + 1):
    VERT.append((K1A <= k <= K1S) or (K2S <= k <= K2B))


# Duong bao kin: i = 0..M-1 mat tren (mep sau -> mep truoc), i = M mep truoc, i > M mat duoi.
def kcol(i):
    """Chi so cot theo day cung cua diem i tren duong bao."""
    return abs(M - i)


def is_upper(i):
    return i < M


def seg_region(i):
    """(kind, spar) cua doan vo nam giua cot i va i+1 tren duong bao."""
    return SEG[min(kcol(i), kcol(i + 1))]


def column_region(i):
    """(kind, spar) dung de lay chieu day tai cot i tren duong bao."""
    return COLREG[kcol(i)]


# =============================================================================
# 5. B1, B2, B3 - MAT CAT TAI MOT TRAM
# =============================================================================
def chord_marks(y_station):
    """Vi tri cac moc theo day cung (phan day cung tu mep truoc) tai mot tram.
    Tra ve dict: c1a, c1b (mu dam truoc), s1b (mep side cap truoc), r1a, r1b (dai gia cuong truoc),
    s2a, c2a, c2b, r2a, r2b (tuong tu cho dam sau); tw1, tw2 = chieu day thanh bung dam truoc / sau (m).
    Canh ngoai: dai gia cuong dat doi xung tren (mu + side cap) nhu x_reinf trong MATLAB;
    canh giua: cot phu cach mu + side cap EXT_DUMMY.
    """
    zone_number = zone(abs(y_station))
    c = chord(y_station)
    wall1 = layup_thickness(web_wall(1))
    wall2 = layup_thickness(web_wall(2))
    width1 = 2*wall1 + web_core(zone_number, 1)
    width2 = 2*wall2 + web_core(zone_number, 2)
    if zone_number < 3:
        side_width1 = 0.015
    else:
        side_width1 = 0.012
    side_width2 = 0.012
    c1a = XI1 - width1/2/c
    c1b = XI1 + width1/2/c
    c2a = XI2 - width2/2/c
    c2b = XI2 + width2/2/c
    s1b = c1b + side_width1/c
    s2a = c2a - side_width2/c
    if zone_number == 3:
        middle1 = (c1a + s1b)/2
        middle2 = (s2a + c2b)/2
        r1a = middle1 - W_REINF_1/2/c
        r1b = middle1 + W_REINF_1/2/c
        r2a = middle2 - W_REINF_2/2/c
        r2b = middle2 + W_REINF_2/2/c
    else:
        r1a = c1a - EXT_DUMMY/c
        r1b = s1b + EXT_DUMMY/c
        r2a = s2a - EXT_DUMMY/c
        r2b = c2b + EXT_DUMMY/c
    return {'c1a': c1a, 'c1b': c1b, 's1b': s1b, 'r1a': r1a, 'r1b': r1b, 's2a': s2a, 'c2a': c2a, 'c2b': c2b,
            'r2a': r2a, 'r2b': r2b, 'tw1': wall1, 'tw2': wall2}


def chord_columns(marks, c):
    """Vi tri xi cua cac cot (M+1 gia tri) tang dan tu 0 (mep truoc) den 1 (mep sau)."""
    s = np.linspace(0, 1, N_LE + 1)
    xs = list(marks['r1a']*(1 - np.cos(np.pi*s/2)))                                   # mep truoc -> r1a
    xs.append(marks['c1a'])
    xs.extend(np.linspace(marks['c1a'] + marks['tw1']/c, marks['c1b'] - marks['tw1']/c, N_FOAM_X + 1))
    xs.append(marks['c1b'])
    xs.append(marks['s1b'])
    xs.extend(np.linspace(marks['r1b'], marks['r2a'], N_MID + 1))                       # giua hai dam
    xs.append(marks['s2a'])
    xs.append(marks['c2a'])
    xs.extend(np.linspace(marks['c2a'] + marks['tw2']/c, marks['c2b'] - marks['tw2']/c, N_FOAM_X + 1))
    xs.append(marks['c2b'])
    xs.extend(np.linspace(marks['r2b'], 1.0, N_AFT + 1))                               # dam sau -> mep sau
    xs = np.array(xs)
    assert len(xs) == M + 1 and np.all(np.diff(xs) > 0), xs
    return xs


def inward_dirs(OML):
    """Vector don vi huong vao trong tai moi cot (mang NC x 2, thanh phan [x, z]):
      - mu dam + side cap (VERT): thang dung (xuong o mat tren, len o mat duoi)
      - noi khac: phap tuyen OML (tiep tuyen bang sai phan trung tam).
    """
    directions = np.zeros((NC, 2))
    for i in range(NC):
        if VERT[kcol(i)]:
            if is_upper(i):
                directions[i] = (0.0, -1.0)
            else:
                directions[i] = (0.0, 1.0)
            continue
        tangent = OML[min(i + 1, NC - 1)] - OML[max(i - 1, 0)]
        normal = np.array([tangent[1], -tangent[0]])
        directions[i] = normal/np.linalg.norm(normal)
    return directions


def column_thickness(i, zone_number, xi, half_depth):
    """Chieu day cac tang [t1, t2, t3, tA, tB_1, ..., tB_N] (m) tai cot i, va reduced = True neu vo phai thu nho o mep sau
    (xi > 0.5 va t1+t2+t3 > TE_FILL*half_depth): giam loi truoc, van khong du thi thu nho ca 3 tang.
    """
    kind, spar = column_region(i)
    skin_tiers = skin_lam(zone_number, kind)
    t1 = layup_thickness(skin_tiers[0])
    t2 = layup_thickness(skin_tiers[1])
    t3 = layup_thickness(skin_tiers[2])
    cap_tiers = cap_lam(zone_number, kind, spar, is_upper(i))
    cap_thicknesses = []
    for tier in cap_tiers:
        cap_thicknesses.append(layup_thickness(tier))
    reduced = False
    if xi > 0.5:
        available = TE_FILL*half_depth
        if t1 + t2 + t3 > available:
            reduced = True
            t2 = max(available - t1 - t3, 0.2*available)
            if t1 + t2 + t3 > available:
                factor = available/(t1 + t2 + t3)
                t1 = t1*factor
                t2 = t2*factor
                t3 = t3*factor
    return [t1, t2, t3] + cap_thicknesses, reduced


def station(y_station):
    """Toan bo hinh hoc mat cat tai mot tram doc sai. Tra ve dict:
      y, zone, c, xle, mk (moc day cung), xs (M+1), OML (NC x 2), DIRS (NC x 2),
      TH (NC x NUMBER_OF_LEVELS-1) chieu day cac tang,
      POS (NC x NUMBER_OF_LEVELS x 3) toa do nut cac muc (0 = OML, 1..3 = sau woven ngoai / loi / woven trong,
          4 = sau tang A, 5 .. INNER_LEVEL = sau cac tang B),
      KF = cot dau tien (theo day cung) phai thu nho vo o mep sau (M neu khong co).
    """
    zone_number = zone(abs(y_station))
    c = chord(y_station)
    x_leading_edge = xle(y_station)
    marks = chord_marks(y_station)
    xs = chord_columns(marks, c)

    OML = np.zeros((NC, 2))
    for i in range(NC):
        xi = xs[kcol(i)]
        if i <= M:
            z = z_upper(xi)
        else:
            z = z_lower(xi)
        OML[i] = (x_leading_edge - xi*c, z*c)
    directions = inward_dirs(OML)

    TH = np.zeros((NC, NUMBER_OF_LEVELS - 1))
    POS = np.zeros((NC, NUMBER_OF_LEVELS, 3))
    first_reduced_column = M
    for i in range(NC):
        k = kcol(i)
        half_depth = (z_upper(xs[k]) - z_lower(xs[k]))/2*c
        TH[i], reduced = column_thickness(i, zone_number, xs[k], half_depth)
        if reduced:
            first_reduced_column = min(first_reduced_column, k)
        depth = np.concatenate([[0.0], np.cumsum(TH[i])])       # cumsum giong MATLAB
        for level in range(NUMBER_OF_LEVELS):
            x, z = OML[i] + directions[i]*depth[level]
            POS[i, level] = (x, y_station, z)
    return {'y': y_station, 'zone': zone_number, 'c': c, 'xle': x_leading_edge, 'mk': marks, 'xs': xs,
            'OML': OML, 'DIRS': directions, 'TH': TH, 'POS': POS, 'KF': first_reduced_column}


# =============================================================================
# 6. B5 - CAC TRAM DOC SAI
# =============================================================================
LOADS = np.atleast_2d(np.loadtxt('aerodynamic_load.txt'))   # [y F], F cua toan canh tai |y|

rib_intervals = []                    # (y dau, y cuoi, vung) - khoang y ma rib chiem
for rib_mm in RIBS:
    y_rib = rib_mm/1000
    rib_zone = zone(y_rib)
    rib_thickness = layup_thickness(rib_lam(rib_zone))
    start = y_rib - rib_thickness/2
    end = y_rib + rib_thickness/2
    rib_intervals.append((start, end, rib_zone))
    rib_intervals.append((-end, -start, rib_zone))
rib_intervals = sorted(set(rib_intervals))                  # set(): bo rib trung (rib y = 0)

key_positions = [0.0, FIX_Y, Y_KV1, Y_KV2, Y_TIP]
for y_load in LOADS[:, 0]:
    key_positions.append(abs(y_load))
for start, end, rib_zone in rib_intervals:
    key_positions.append(start)
    key_positions.append(end)
positive_positions = set()
for value in key_positions:
    if value >= 0:
        positive_positions.add(round(value, 9))
key_positions = sorted(positive_positions)

# Nua canh phai: chia moi khoang giua hai vi tri can co nut sao cho buoc <= dy
half_stations = [key_positions[0]]
for index in range(len(key_positions) - 1):
    start = key_positions[index]
    end = key_positions[index + 1]
    number_of_steps = int(np.ceil((end - start)/dy - 1e-9))
    half_stations.extend(np.linspace(start, end, number_of_steps + 1)[1:])
half_stations = np.array(half_stations)

# Toan canh: nua trai (doi dau, dao thu tu, bo diem y = 0 de khong trung) + nua phai
Y = np.concatenate([-half_stations[:0:-1], half_stations])
NS = len(Y)
STA = []                              # STA[j] = hinh hoc mat cat tai tram j (ket qua ham station)
for y_station in Y:
    STA.append(station(y_station))


def rib_of_bay(j):
    """(y dau, y cuoi, vung) cua rib chua trung diem khoang [Y[j], Y[j+1]]; None neu khong co rib."""
    y_middle = (Y[j] + Y[j + 1])/2
    for start, end, rib_zone in rib_intervals:
        if start < y_middle < end:
            return start, end, rib_zone
    return None


# =============================================================================
# 7. NUT
# =============================================================================
node_ids = {}                         # node_ids[khoa] = so hieu nut
node_xyz = []                         # node_xyz[so hieu - 1] = toa do


def get_node(key, xyz):
    """So hieu nut theo khoa (tuple), tao nut moi neu chua co. Cung khoa -> cung nut."""
    if key not in node_ids:
        node_xyz.append(np.array(xyz, dtype=float))
        node_ids[key] = len(node_xyz)
    return node_ids[key]


def skin_node(j, i, level):
    """Nut tren vo: tram j, cot i tren duong bao, muc level theo chieu day (0 = OML ... INNER_LEVEL)."""
    return get_node(('skin', j, i, level), STA[j]['POS'][i, level])


def virtual_depths(j, i):
    """Chieu day tang A va cac tang B "ao" cua rib tai mot cot giua hai side cap:
    tA noi suy tuyen tinh tu side cap truoc (s1b) sang side cap sau (s2a),
    moi tang B noi suy tu tang B tuong ung cua mu truoc (c1b) sang mu sau (c2a), cung mat tren / duoi voi cot i.
    Tra ve (tA, list chieu day cac tang B).
    """
    section = STA[j]
    zone_number = section['zone']
    marks = section['mk']
    xi = section['xs'][kcol(i)]
    upper = is_upper(i)
    tA1 = layup_thickness(side_lam(zone_number, 1))
    tA2 = layup_thickness(side_lam(zone_number, 2))
    fraction_A = np.clip((xi - marks['s1b'])/(marks['s2a'] - marks['s1b']), 0, 1)
    fraction_B = np.clip((xi - marks['c1b'])/(marks['c2a'] - marks['c1b']), 0, 1)
    front_cap_tiers = cap_lam(zone_number, 'cap', 1, upper)
    rear_cap_tiers = cap_lam(zone_number, 'cap', 2, upper)
    tB_parts = []
    for part in range(1, N_CAP_B + 1):
        tB1 = layup_thickness(front_cap_tiers[part])
        tB2 = layup_thickness(rear_cap_tiers[part])
        tB_parts.append(tB1 + (tB2 - tB1)*fraction_B)
    return tA1 + (tA2 - tA1)*fraction_A, tB_parts


def level_node(j, i, level):
    """Nut o mat trong vo (muc 3 .. INNER_LEVEL), dung cho rib va bung dam.
    Nut that cua vo neu cot co tang tuong ung (muc 3 luon co, muc 4 o mu dam / side cap, muc 5 tro di o mu dam);
    nguoc lai la nut "ao" cua rib, offset tu muc 3 theo DIRS[i] mot doan tA (muc 4)
    hoac tA + tong cac tang B den muc do (muc 5 tro di).
    """
    kind, spar = column_region(i)
    if level == 3 or (level == 4 and kind in ('cap', 'side')) or (level >= 5 and kind == 'cap'):
        return skin_node(j, i, level)
    section = STA[j]
    tA, tB_parts = virtual_depths(j, i)
    if level >= 5 and kind == 'side':
        tA = section['TH'][i, 3]
    depth = tA
    for part in range(level - 4):                     # muc 4: chi tA; muc 5: tA + tB_1; muc 6: tA + tB_1 + tB_2 ...
        depth = depth + tB_parts[part]
    direction = np.array([section['DIRS'][i][0], 0.0, section['DIRS'][i][1]])
    return get_node(('rib', j, i, level), section['POS'][i, 3] + direction*depth)


def inner_node(j, k, row):
    """Nut trong long hop (bung dam, luoi chinh cua rib) tai cot k, hang row = 0 .. N_H.
    row = 0 la nut mat trong mu dam duoi (muc INNER_LEVEL, cot M+k), row = N_H la nut mat trong mu dam tren
    (cot M-k), cac hang o giua chia deu tren doan thang noi hai nut do.
    """
    lower_column = M + k
    upper_column = M - k
    if row == 0:
        return level_node(j, lower_column, INNER_LEVEL)
    if row == N_H:
        return level_node(j, upper_column, INNER_LEVEL)
    bottom = node_xyz[level_node(j, lower_column, INNER_LEVEL) - 1]
    top = node_xyz[level_node(j, upper_column, INNER_LEVEL) - 1]
    return get_node(('in', j, k, row), bottom + (top - bottom)*row/N_H)


# =============================================================================
# 8. PHAN TU KHOI 8 NUT
# =============================================================================
TYPE_NAME = {1: 'Vo thuong (3 tang)', 2: 'Vo vung dam - dai gia cuong (3 tang)',
             3: 'Mu dam (tang A, B)', 4: 'Side cap (tang A)',
             5: 'Thanh bung dam truoc', 6: 'Thanh bung dam sau', 7: 'Foam bung dam',
             8: 'Rib', 9: 'Foam lap mep sau'}
SOLID_TYPES = (7, 9)

# Moi phan tu la dict: type, layup (None voi foam SOLID185), esys, nodes (8 so nut)
elements = []


def add_hex(element_type, layup, esys, bottom, top):
    """Them mot phan tu khoi 8 nut.
    bottom: 4 nut mat duoi (I, J, K, L) - lop 1 nam o mat nay; top: 4 nut tuong ung o mat tren (M, N, O, P).
    esys: 11 = 0 do doc sai, 0 = tong the.
    Chieu vong nut duoc sua sau trong orient_elements (dao vong neu the tich am).
    """
    elements.append({'type': element_type, 'layup': layup, 'esys': esys, 'nodes': list(bottom) + list(top)})


def skin_face(j, i, level):
    """4 nut [(j, i), (j, i+1), (j+1, i+1), (j+1, i)] o muc level."""
    return [skin_node(j, i, level), skin_node(j, i + 1, level),
            skin_node(j + 1, i + 1, level), skin_node(j + 1, i, level)]


def web_face(j, k, row):
    """Mat thang dung trong bung dam tai cot k: 4 nut [(j, row), (j+1, row), (j+1, row+1), (j, row+1)]."""
    return [inner_node(j, k, row), inner_node(j + 1, k, row),
            inner_node(j + 1, k, row + 1), inner_node(j, k, row + 1)]


def rib_face(j, k, row):
    """O luoi chinh cua rib tai tram j: 4 nut [(k, row), (k+1, row), (k+1, row+1), (k, row+1)]."""
    return [inner_node(j, k, row), inner_node(j, k + 1, row),
            inner_node(j, k + 1, row + 1), inner_node(j, k, row + 1)]


def band_face(j, i0, i1, level_a, level_b):
    """O dai rib chay doc mat trong vo tai tram j: 4 nut [(i0, a), (i1, a), (i1, b), (i0, b)]."""
    return [level_node(j, i0, level_a), level_node(j, i1, level_a),
            level_node(j, i1, level_b), level_node(j, i0, level_b)]


def tier_lam(j, i, tier, layup):
    """Xep lop cua phan tu tang vo, chinh theo chieu day trung binh 4 goc (lam tron 0.01 mm)."""
    thickness = (STA[j]['TH'][i, tier] + STA[j]['TH'][i + 1, tier]
                 + STA[j + 1]['TH'][i, tier] + STA[j + 1]['TH'][i + 1, tier])/4
    return fit_lam(layup, round(thickness, 5))


for j in range(NS - 1):
    zone_number = zone(abs((Y[j] + Y[j + 1])/2))

    # --- vo: 3 tang + tang mu dam / side cap (xep lop tu ngoai vao trong)
    for i in range(NC - 1):
        kind, spar = seg_region(i)
        tiers = skin_lam(zone_number, kind)
        if kind == 'skin':
            skin_type = 1
        else:
            skin_type = 2
        for tier in range(3):
            add_hex(skin_type, tier_lam(j, i, tier, tiers[tier]), 11, skin_face(j, i, tier), skin_face(j, i, tier + 1))
        cap_tiers = cap_lam(zone_number, kind, spar, is_upper(i))
        layup_A = cap_tiers[0]
        if layup_A:                                       # list rong duoc coi la False
            if kind == 'cap':
                cap_type = 3
            else:
                cap_type = 4
            add_hex(cap_type, layup_A, 11, skin_face(j, i, 3), skin_face(j, i, 4))
        for part in range(1, N_CAP_B + 1):                # tang B thu part nam giua muc 3+part va 4+part
            layup_B = cap_tiers[part]
            if layup_B:
                add_hex(3, layup_B, 11, skin_face(j, i, 3 + part), skin_face(j, i, 4 + part))

    # --- bung dam: thanh truoc / foam / thanh sau, tu mu duoi len mu tren
    for spar, first_column, last_column in ((1, K1A, K1B), (2, K2A, K2B)):
        for k in range(first_column, last_column):
            for row in range(N_H):
                if k == first_column or k == last_column - 1:
                    add_hex(4 + spar, web_wall(spar), 11, web_face(j, k, row), web_face(j, k + 1, row))
                else:
                    add_hex(7, None, 0, web_face(j, k, row), web_face(j, k + 1, row))

    # --- rib: giua mat sau dam truoc va mat truoc dam sau, xep lop theo phuong y
    rib = rib_of_bay(j)
    if rib is not None:
        rib_start, rib_end, rib_zone = rib
        layup = cut_lam(rib_lam(rib_zone), Y[j] - rib_start, Y[j + 1] - rib_start)
        for k in range(K1B, K2A):
            for row in range(N_H):
                add_hex(8, layup, 0, rib_face(j, k, row), rib_face(j + 1, k, row))
            for i0, i1 in ((M - k, M - k - 1), (M + k, M + k + 1)):
                # dai rib lap cac tang B (muc 4 -> INNER_LEVEL), roi tang A (muc 3 -> 4) o giua hai side cap
                for level in range(4, INNER_LEVEL):
                    add_hex(8, layup, 0, band_face(j, i0, i1, level, level + 1), band_face(j + 1, i0, i1, level, level + 1))
                if K1S <= k < K2S:
                    add_hex(8, layup, 0, band_face(j, i0, i1, 3, 4), band_face(j + 1, i0, i1, 3, 4))

    # --- mep sau: foam lap khe giua mat trong vo duoi va vo tren
    for k in range(min(STA[j]['KF'], STA[j + 1]['KF']), M):
        bottom = [skin_node(j, M + k, 3), skin_node(j, M + k + 1, 3),
                  skin_node(j + 1, M + k + 1, 3), skin_node(j + 1, M + k, 3)]
        top = [skin_node(j, M - k, 3), skin_node(j, M - k - 1, 3),
               skin_node(j + 1, M - k - 1, 3), skin_node(j + 1, M - k, 3)]
        add_hex(9, None, 0, bottom, top)


# =============================================================================
# 9. B7 - KIEM TRA: JACOBIAN, KHOI LUONG THEO TYPE
#    Phan nay tinh tren ca mang (vectorized) cho nhanh: X[:, q] la toa do goc q cua moi phan tu.
# =============================================================================
XYZ = np.array(node_xyz)
TETS = [(0, 1, 3, 4), (1, 2, 3, 6), (1, 4, 5, 6), (3, 4, 6, 7), (1, 3, 4, 6)]   # chia khoi 8 nut thanh 5 tu dien


def row_dot(a, b):
    """Tich vo huong tung hang cua hai mang (n x 3)."""
    return np.einsum('ij,ij->i', a, b)


def corner_jacobians(connectivity):
    """Tich hon hop 3 canh di ra tu moi goc, mang (n x 8). Tat ca > 0 -> phan tu hop le."""
    X = XYZ[connectivity - 1]
    result = []
    for q in range(4):
        next_corner = (q + 1) % 4
        previous_corner = (q - 1) % 4
        bottom = row_dot(np.cross(X[:, next_corner] - X[:, q], X[:, previous_corner] - X[:, q]), X[:, 4 + q] - X[:, q])
        top = row_dot(np.cross(X[:, 4 + previous_corner] - X[:, 4 + q], X[:, 4 + next_corner] - X[:, 4 + q]),
                      X[:, q] - X[:, 4 + q])
        result.append(bottom)
        result.append(top)
    return np.column_stack(result)


def tet_volumes(connectivity):
    """The tich cac phan tu (m3) = tong the tich 5 tu dien."""
    X = XYZ[connectivity - 1]
    volume = 0.0
    for a, b, d, e in TETS:
        volume = volume + row_dot(np.cross(X[:, b] - X[:, a], X[:, d] - X[:, a]), X[:, e] - X[:, a])/6
    return volume


def orient_elements():
    """Dao vong nut cac phan tu co the tich am (giu mat duoi / mat tren, giu chieu xep lop).
    Tra ve mang so nut (n x 8) da sua; elements duoc cap nhat tuong ung.
    """
    connectivity = []
    for element in elements:
        connectivity.append(element['nodes'])
    connectivity = np.array(connectivity, dtype=np.int64)
    flip = corner_jacobians(connectivity).sum(axis=1) < 0
    # dao vong: I-J-K-L -> I-L-K-J (va tuong tu mat tren)
    connectivity[flip] = connectivity[flip][:, [0, 3, 2, 1, 4, 7, 6, 5]]
    for n in np.nonzero(flip)[0]:                         # nonzero giong find cua MATLAB
        elements[n]['nodes'] = list(connectivity[n])
    return connectivity


RHO = {'UD': RHO_UD, 'F': RHO_F}


def density(layup):
    """Khoi luong rieng trung binh theo chieu day (kg/m3); None = foam dong nhat."""
    if layup is None:
        return RHO_F
    total = 0
    for material, thickness, angle in layup:
        total = total + RHO[material]*thickness
    return total/layup_thickness(layup)


CONN = orient_elements()
JAC = corner_jacobians(CONN)
VOL = tet_volumes(CONN)
element_types = []
element_densities = []
for element in elements:
    element_types.append(element['type'])
    element_densities.append(density(element['layup']))
ETYPE = np.array(element_types)
RHO_E = np.array(element_densities)

bad = np.nonzero(JAC.min(axis=1) <= 0)[0]
for n in bad[:10]:
    center = XYZ[CONN[n] - 1].mean(axis=0)
    print(f'  Phan tu meo: TYPE {ETYPE[n]} tai x, y, z = {np.round(center*1000, 2)} mm')
assert len(bad) == 0, f'{len(bad)} phan tu co Jacobian <= 0'

mass_type = {}
n_type = {}
for element_type in TYPE_NAME:
    is_this_type = ETYPE == element_type                  # mang True/False, giong so sanh mang trong MATLAB
    if is_this_type.any():
        mass_type[element_type] = float((VOL*RHO_E)[is_this_type].sum())
        n_type[element_type] = int(is_this_type.sum())


def station_web_nodes(y_target, spar, exact=False):
    """Tram gan y_target nhat va cac nut mat cat bung dam (cot ka..kb, hang 0..N_H) tai tram do.
    exact = True: bat buoc co tram dung tai y_target.
    """
    j = int(np.argmin(abs(Y - y_target)))
    if exact:
        assert abs(Y[j] - y_target) < 1e-9, (y_target, Y[j])
    if spar == 1:
        first_column = K1A
        last_column = K1B
    else:
        first_column = K2A
        last_column = K2B
    web_nodes = []
    for k in range(first_column, last_column + 1):
        for row in range(N_H + 1):
            web_nodes.append(inner_node(j, k, row))
    return Y[j], web_nodes


# =============================================================================
# 10. VE MAT CAT (kiem tra hinh hoc)
# =============================================================================
TYPE_COLOR = {1: '#2a78d6', 2: '#eda100', 3: '#cf5829', 4: '#1baf7a', 5: '#e87ba4',
              6: '#008300', 7: '#c3c2b7', 8: '#6250d6', 9: '#9fd3e6'}


def plot_section(y_target):
    """Ve mat cat cac phan tu tai tram gan y_target nhat (lay phan tu phia +y cua tram).
    7 khung: toan mat cat, nua tren / nua duoi dam truoc, nua tren / nua duoi dam sau, mep truoc, mep sau.
    Tra ve ten file PNG.
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Patch

    j = int(np.argmin(abs(Y - y_target)))
    section = STA[j]
    y_station = Y[j]
    if j < NS - 1:
        side = 1
    else:
        side = -1

    # Moi phan tu co dung 4 nut nam tren mat phang tram -> mot da giac trong mat (x, z)
    polygons = []
    for n in range(len(elements)):
        X = XYZ[CONN[n] - 1]
        on_station = X[np.abs(X[:, 1] - y_station) < 1e-9]
        if len(on_station) != 4 or np.sign(X[:, 1].mean() - y_station) != side:
            continue
        xz = on_station[:, [0, 2]]*1000
        center = xz.mean(axis=0)
        angle_order = np.argsort(np.arctan2(xz[:, 1] - center[1], xz[:, 0] - center[0]))   # sap dinh theo goc
        polygons.append((elements[n]['type'], xz[angle_order]))

    positions_mm = section['POS']*1000

    def spar_box(first_column, last_column, upper):
        """Gioi han truc x, z cua khung zoom vao mot dam."""
        columns = []
        for k in range(first_column, last_column + 1):
            if upper:
                columns.append(M - k)
            else:
                columns.append(M + k)
        x_values = positions_mm[columns][:, :, 0]
        z_outer = positions_mm[columns, 0, 2]
        z_inner = positions_mm[columns, INNER_LEVEL, 2]
        x_limits = (x_values.max() + 15, x_values.min() - 15)
        if upper:
            z_limits = (z_inner.min() - 8, z_outer.max() + 3)
        else:
            z_limits = (z_outer.min() - 3, z_inner.max() + 8)
        return x_limits, z_limits

    c = section['c']*1000
    x_leading_edge = section['xle']*1000

    def x_range(xi_start, xi_end):
        return (x_leading_edge - xi_start*c + 3, x_leading_edge - xi_end*c - 3)

    def z_range(xi_start, xi_end):
        if xi_end < 0.5:
            return (z_lower(xi_end)*c - 3, z_upper(xi_end)*c + 3)
        return (z_lower(xi_start)*c - 3, z_upper(xi_start)*c + 3)

    front_upper = spar_box(K1A, K1S, True)
    front_lower = spar_box(K1A, K1S, False)
    rear_upper = spar_box(K2S, K2B, True)
    rear_lower = spar_box(K2S, K2B, False)
    views = [('Toan mat cat', None, None),
             ('Dam truoc (nua tren)', front_upper[0], front_upper[1]),
             ('Dam truoc (nua duoi)', front_lower[0], front_lower[1]),
             ('Dam sau (nua tren)', rear_upper[0], rear_upper[1]),
             ('Dam sau (nua duoi)', rear_lower[0], rear_lower[1]),
             ('Mep truoc', x_range(0, 0.06), z_range(0, 0.06)),
             ('Mep sau', x_range(0.88, 1.0), z_range(0.88, 1.0))]

    def rib_first(polygon):
        return polygon[0] != 8       # False (rib) dung truoc True khi sap xep -> rib ve truoc, nam duoi

    fig = plt.figure(figsize=(14, 17))
    grid = fig.add_gridspec(4, 2, height_ratios=[1, 1.1, 1.1, 1.1])
    axes = [fig.add_subplot(grid[0, :])]
    for grid_row in (1, 2, 3):
        for grid_column in (0, 1):
            axes.append(fig.add_subplot(grid[grid_row, grid_column]))

    for ax, view in zip(axes, views):
        title, x_limits, z_limits = view
        if x_limits is None:
            line_width = 0.15
        else:
            line_width = 0.4
        for element_type, points in sorted(polygons, key=rib_first):
            if element_type == 8:
                transparency = 0.5
            else:
                transparency = 1.0
            ax.add_patch(Polygon(points, fc=TYPE_COLOR[element_type], ec='#0b0b0b', lw=line_width, alpha=transparency))
        ax.set_aspect('equal')
        ax.autoscale_view()
        if x_limits is None:
            ax.set_xlim(max(ax.get_xlim()), min(ax.get_xlim()))      # dao truc x: mep truoc ben trai
        else:
            ax.set_xlim(*x_limits)                                   # *x_limits: tach tuple thanh 2 doi so
            ax.set_ylim(*z_limits)
        ax.set_title(f'{title}, y = {y_station:.3f} m (vung {section["zone"]}, c = {section["c"]*1000:.0f} mm)', fontsize=10)
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('z (mm)')
        ax.grid(True, color='#e5e4df', lw=0.5)
        ax.set_axisbelow(True)

    used_types = set()
    for polygon in polygons:
        used_types.add(polygon[0])
    legend_items = []
    for element_type in sorted(used_types):
        legend_items.append(Patch(fc=TYPE_COLOR[element_type], label=f'TYPE {element_type}: {TYPE_NAME[element_type]}'))
    axes[0].legend(handles=legend_items, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=8, frameon=False)
    fig.tight_layout()
    file_name = f'{PNG_PREFIX}{round(y_station*1000):04d}.png'
    fig.savefig(file_name, dpi=200)
    plt.close(fig)
    return file_name


if PLOT_SECTIONS:
    for y_target in SECTION_Y:
        print('Da ve mat cat:', plot_section(y_target))


# =============================================================================
# 11. GHI APDL
# =============================================================================
# Tai tap trung: moi luc trong aerodynamic_load.txt dat tai +y va -y, chia cho bung dam truoc va sau
load_groups = []                      # moi phan tu: (luc (N), ty le cho dam nay, list nut bung dam)
for y_load, force in LOADS:
    for sign in (1, -1):
        for spar, share in ((1, FRONT_SHARE), (2, 1 - FRONT_SHARE)):
            y_station, web_nodes = station_web_nodes(sign*y_load, spar, exact=True)
            load_groups.append((force*LOAD_SCALE, share, web_nodes))

output_stations = []                  # moi phan tu: (y tram, nut dam truoc, nut dam sau)
for y_output in OUT_Y:
    y_station, front_nodes = station_web_nodes(y_output, 1)
    y_rear, rear_nodes = station_web_nodes(y_output, 2)
    output_stations.append((y_station, front_nodes, rear_nodes))

J_FIX = int(np.argmin(abs(Y - FIX_Y)))
assert abs(Y[J_FIX] - FIX_Y) < 1e-9

# Moi xep lop khac nhau la mot section. So hieu cap theo thu tu gap lan dau,
# nen thu tu duyet SECS cung la thu tu so hieu.
SECS = {}


def secid(layup):
    key_parts = []
    for material, thickness, angle in layup:
        key_parts.append((material, round(thickness, 10), angle))
    key = tuple(key_parts)
    if key not in SECS:
        SECS[key] = len(SECS) + 1
    return SECS[key]


MATID = {'UD': 1, 'F': 2}

apdl = []                             # moi lenh APDL la mot dong trong list nay


def write_fix():
    """Ghi lenh ngam tai hai tram y = +-FIX_Y theo FIX_MODE.
    'all': moi nut cua tram; 'webs' / 'caps': nut co x nam trong be rong bung dam truoc / sau
    (gom ca vo, mu dam phia tren / duoi bung dam).
    """
    apdl.append(f'NSEL,S,LOC,Y,{FIX_Y-1e-5},{FIX_Y+1e-5}')
    apdl.append(f'NSEL,A,LOC,Y,{-FIX_Y-1e-5},{-FIX_Y+1e-5}')
    if FIX_MODE != 'all':
        section = STA[J_FIX]
        apdl.append('CM,FIXSTN,NODE                ! moi nut tai 2 tram ngam')
        for name, first_column, last_column in (('FIXF', K1A, K1B), ('FIXR', K2A, K2B)):
            x_start = section['xle'] - section['xs'][last_column]*section['c']
            x_end = section['xle'] - section['xs'][first_column]*section['c']
            apdl.append('CMSEL,S,FIXSTN')
            apdl.append(f'NSEL,R,LOC,X,{x_start-1e-5:.6f},{x_end+1e-5:.6f}')
            apdl.append(f'CM,{name},NODE')
        apdl.append('CMSEL,S,FIXF')
        apdl.append('CMSEL,A,FIXR')
    apdl.append('D,ALL,ALL')
    apdl.append('NSEL,ALL')


apdl.append('! =====================================================================')
apdl.append('! Mo hinh KHOI nhieu lop toan canh chinh CW - sinh tu gen_apdl_for_wing_SOLSH190.py')
apdl.append(f'! NACA 4421, day cung 800 mm (|y| < 1.75) thuon ve 400 mm, sai -8..8 m, ngam tai y = +-{FIX_Y} m ({FIX_MODE})')
apdl.append('! Don vi SI (m, kg, N, Pa).  x: huong ve phia truoc, y: doc sai, z: len')
apdl.append('! Vo = 3 tang (woven ngoai / loi / woven trong), mu dam = tang A + B; mu dam + side cap offset thang dung')
apdl.append('! SOLSH190: lop 1 o mat I-J-K-L; chieu day lop duoc co gian theo chieu day that cua phan tu')
apdl.append('! SOLID185: foam bung dam, foam lap mep sau')
apdl.append('! Huong 0 do cua lop vo / bung dam: doc sai (LOCAL 11); rib: truc x tong the')
apdl.append('! =====================================================================')
apdl.append('FINISH')
apdl.append('/CLEAR,NOSTART')
apdl.append('/TITLE,CW main wing - layered solid model (SOLSH190)')
apdl.append('/PREP7')
apdl.append('/NERR,200,10000')
for element_type in TYPE_NAME:
    if element_type in SOLID_TYPES:
        apdl.append(f'ET,{element_type},SOLID185')
        apdl.append(f'KEYOPT,{element_type},2,2           ! enhanced strain, tranh khoa cat')
    else:
        apdl.append(f'ET,{element_type},SOLSH190')
for element_type in TYPE_NAME:
    apdl.append(f'! TYPE {element_type}: {TYPE_NAME[element_type]}')
apdl.append('!')
apdl.append('! --- Vat lieu 1: lop UD AS4/3501-6 (vi co nhu ply.m; nu23, G23 theo Foye nhu ply3D.m)')
apdl.append(f'MP,EX,1,{E1:.6e}')
apdl.append(f'MP,EY,1,{E2:.6e}')
apdl.append(f'MP,EZ,1,{E2:.6e}')
apdl.append(f'MP,PRXY,1,{nu12:.6f}')
apdl.append(f'MP,PRYZ,1,{nu23:.6f}')
apdl.append(f'MP,PRXZ,1,{nu12:.6f}')
apdl.append(f'MP,GXY,1,{G12:.6e}')
apdl.append(f'MP,GYZ,1,{G23:.6e}')
apdl.append(f'MP,GXZ,1,{G12:.6e}')
apdl.append(f'MP,DENS,1,{RHO_UD:.4f}')
apdl.append('! --- Vat lieu 2: PVC foam (PVC_Foam.m)')
apdl.append(f'MP,EX,2,{E_F:.6e}')
apdl.append(f'MP,PRXY,2,{NU_F}')
apdl.append(f'MP,DENS,2,{RHO_F}')
apdl.append(f'! Chieu day 1 lop UD = {T_UD*1e3:.5f} mm; woven = 2 lop UD +-45 (nhu code MATLAB)')
apdl.append('!')
apdl.append('! --- He toa do dinh huong: truc x cuc bo // truc y tong the (0 do doc sai)')
apdl.append('LOCAL,11,0,0,0,0,90')
apdl.append('CSYS,0')
apdl.append('!')

# Gan so hieu section cho tung phan tu (foam SOLID185 khong co section: dung 0)
element_rows = []
for element in elements:
    if element['layup'] is None:
        section_number = 0
    else:
        section_number = secid(element['layup'])
    element_rows.append({'type': element['type'], 'section': section_number, 'esys': element['esys'],
                         'nodes': element['nodes']})

apdl.append('! --- Section (SECDATA: lop 1 = mat duoi I-J-K-L cua phan tu)')
for layup in SECS:                    # thu tu duyet = thu tu so hieu section
    apdl.append(f'SECTYPE,{SECS[layup]},SHELL')
    for material, thickness, angle in layup:
        apdl.append(f'SECDATA,{thickness:.8f},{MATID[material]},{angle:.1f},3')
apdl.append('!')
apdl.append('! --- Nut')
for index in range(len(node_xyz)):
    x, y, z = node_xyz[index]
    apdl.append(f'N,{index + 1},{x:.7f},{y:.7f},{z:.7f}')
apdl.append('!')
apdl.append('! --- Phan tu')


def element_sort_key(row):
    return (row['type'], row['section'], row['esys'])


# Sap xep theo (TYPE, section, ESYS) de chi ghi lai TYPE/SECNUM/ESYS khi chung doi.
# sorted() giu nguyen thu tu cu cua cac phan tu co cung khoa.
current_key = None
for row in sorted(element_rows, key=element_sort_key):
    if element_sort_key(row) != current_key:
        apdl.append(f"TYPE,{row['type']}")
        if row['section'] != 0:
            apdl.append(f"SECNUM,{row['section']}")
        else:
            apdl.append('MAT,2')
        apdl.append(f"ESYS,{row['esys']}")
        current_key = element_sort_key(row)
    node_texts = []
    for node_number in row['nodes']:
        node_texts.append(str(node_number))
    apdl.append('E,' + ','.join(node_texts))
apdl.append('ESYS,0')
apdl.append('MAT,1')
apdl.append('/VUP,1,Z')
apdl.append('/VIEW,1,-1,-1,1')
apdl.append('/AUTO,1')
apdl.append('EPLOT')
apdl.append('FINISH')
apdl.append('!')

apdl.append('! =================== 1. Phan tich tinh: tai khi dong + trong luong ===================')
apdl.append('/SOLU')
apdl.append('ANTYPE,STATIC')
apdl.append('IRLF,-1                 ! in "PRECISE MASS SUMMARY" va khoi luong theo TYPE trong output')
write_fix()
apdl.append(f'ACEL,0,0,{G_ACC}            ! trong luong ban than theo -z')
apdl.append(f'! Luc tap trung tu aerodynamic_load.txt x {LOAD_SCALE:.4f} (= /2*1.3*3.8) tai +-y:')
apdl.append(f'! {FRONT_SHARE:.0%} vao bung dam truoc, phan con lai vao bung dam sau (chia deu cho cac nut mat cat bung dam)')
for force, share, web_nodes in load_groups:
    for node_number in web_nodes:
        apdl.append(f'F,{node_number},FZ,{force*share/len(web_nodes):.6f}')
apdl.append('SOLVE')
apdl.append('*GET,MTOT,ELEM,0,MTOT,X  ! tong khoi luong mo hinh (can IRLF,-1 truoc SOLVE)')
apdl.append('FINISH')
apdl.append('/POST1')
apdl.append('SET,LAST')
apdl.append(f'*CFOPEN,{RES},txt')
apdl.append('*VWRITE,MTOT')
apdl.append("('Tong khoi luong canh: ',F10.3,' kg')")
apdl.append('*VWRITE')
apdl.append("('Do vong UZ trung binh tai bung dam truoc / dam sau (mm)')")
for y_station, front_nodes, rear_nodes in output_stations:
    for spar_number, web_nodes in ((1, front_nodes), (2, rear_nodes)):
        apdl.append('UZS=0')
        for node_number in web_nodes:
            apdl.append(f'*GET,UZN,NODE,{node_number},U,Z')
            apdl.append('UZS=UZS+UZN')
        apdl.append(f'UZ{spar_number}=UZS/{len(web_nodes)}*1000')
    apdl.append(f'YST={y_station:.4f}')
    apdl.append('*VWRITE,YST,UZ1,UZ2')
    apdl.append("('  y = ',F8.3,' m   UZ dam truoc = ',F10.4,' mm   UZ dam sau = ',F10.4,' mm')")
apdl.append('*CFCLOS')
apdl.append('FINISH')
apdl.append('!')

apdl.append('! =================== 2. Phan tich dao dong rieng ===================')
apdl.append('/SOLU')
apdl.append('ANTYPE,MODAL,NEW')
apdl.append('FDELE,ALL,ALL')
apdl.append('ACEL,0,0,0')
write_fix()
apdl.append(f'MODOPT,LANB,{NMODE}')
apdl.append(f'MXPAND,{NMODE}')
apdl.append('SOLVE')
apdl.append('FINISH')
apdl.append('/POST1')
apdl.append('SET,LIST')
apdl.append(f'*CFOPEN,{RES},txt,,APPEND')
apdl.append('*VWRITE')
apdl.append("('Tan so rieng (Hz)')")
apdl.append(f'*DO,II,1,{NMODE}')
apdl.append('*GET,FRQ,MODE,II,FREQ')
apdl.append('*VWRITE,II,FRQ')
apdl.append("('  Mode ',F4.0,'   f = ',F10.4,' Hz')")
apdl.append('*ENDDO')
apdl.append('*CFCLOS')
apdl.append('SET,1,1')
apdl.append('/VUP,1,Z')
apdl.append('/VIEW,1,-1,-1,1')
apdl.append('/AUTO,1')
apdl.append('PLDISP,1')
apdl.append('! Xem cac mode khac: SET,1,<mode>  roi  PLNSOL,U,SUM')

apdl_text = '\n'.join(apdl) + '\n'
written_paths = []
for folder in OUT_DIRS:
    try:
        os.makedirs(folder, exist_ok=True)
        output_path = os.path.join(folder, OUT)
        with open(output_path, 'w', encoding='ascii', errors='replace') as output_file:
            output_file.write(apdl_text)
        written_paths.append(os.path.abspath(output_path))
    except OSError as error:          # try/except giong try/catch cua MATLAB
        print(f'Khong ghi duoc vao {folder}: {error}')


# =============================================================================
# 12. TOM TAT
# =============================================================================
print(f'Cot theo day cung: {M+1}, tram doc sai: {NS}, nut: {len(node_xyz)}, phan tu: {len(elements)}, section: {len(SECS)}')
first_reduced = M
first_reduced_xi = 1.0
for section in STA:
    first_reduced = min(first_reduced, section['KF'])
    first_reduced_xi = min(first_reduced_xi, section['xs'][section['KF']])
print(f'Jacobian goc nho nhat: {JAC.min():.3e}; foam lap mep sau tu cot {first_reduced} (xi ~ {first_reduced_xi:.3f})')
total_mass = 0.0
for element_type in sorted(mass_type):
    print(f'  TYPE {element_type} {TYPE_NAME[element_type]:38s} {n_type[element_type]:7d} pt  {mass_type[element_type]:8.3f} kg')
    total_mass = total_mass + mass_type[element_type]
print(f'  Tong khoi luong canh: {total_mass:.3f} kg')
groups = {'Vo (TYPE 1, 2)': (1, 2), 'Mu dam + side cap (3, 4)': (3, 4),
          'Bung dam (5, 6, 7)': (5, 6, 7), 'Rib (8)': (8,), 'Foam mep sau (9)': (9,)}
group_texts = []
for group_name in groups:
    group_mass = 0
    for element_type in groups[group_name]:
        group_mass = group_mass + mass_type.get(element_type, 0)     # get(khoa, 0): 0 neu khong co TYPE nay
    group_texts.append(f'{group_name} {group_mass:.3f} kg')
print('  ' + ', '.join(group_texts))
for path in written_paths:
    print(f'Da ghi {path}')
