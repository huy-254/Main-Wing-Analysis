# -*- coding: utf-8 -*-
"""
tao_macro_so_sanh.py - Sinh cac macro APDL bo sung de so sanh MATLAB - SOLSH190.

Khong sua file .inp goc. Doc nut / phan tu tu .inp goc, roi ghi vao thu muc mo hinh SOLSH190:
  loads_design_SOLSH190.mac (trich nguyen cac lenh F cua input goc)
  loads_tip_SOLSH190.mac (100 N tai y = +8 m, chia deu cho cac nut hai thanh dam)
  post_sup_SOLSH190.mac, run_all_SOLSH190.inp (chay input goc roi chay bo sung)
Nut dung de doc chuyen vi (thanh dam) xac dinh bang ESEL theo TYPE trong APDL, khong can liet ke.

Chay:  py -3 tao_macro_so_sanh.py
"""
import os
import numpy as np

ROOT = r'E:\luan an\ve lai UAV - ANSYS'
D_SO = os.path.join(ROOT, 'APDL canh chinh SOLSH190')
INP_SO = os.path.join(D_SO, 'APDL_for_wing_SOLSH190.inp')
P_TIP = 100.0
NMODE_SUP = 24          # so mode cua lan modal bo sung SOLSH190 (de co mode xoan)


def read_model(fn):
    """Doc nut va phan tu (TYPE) tu file .inp.
    Dau vao:
      fn : duong dan .inp
    Dau ra:
      (xyz: dict id -> (x, y, z), etype: dict TYPE -> list cac list nut, lines: list dong)
    """
    xyz, etype, cur = {}, {}, None
    lines = open(fn, encoding='ascii', errors='replace').read().splitlines()
    for s in lines:
        if s.startswith('N,'):
            p = s.split(',')
            xyz[int(p[1])] = (float(p[2]), float(p[3]), float(p[4]))
        elif s.startswith('TYPE,'):
            cur = int(s.split(',')[1])
        elif s.startswith('E,'):
            etype.setdefault(cur, []).append([int(v) for v in s.split(',')[1:]])
        elif s.startswith('/SOLU'):
            break
    return xyz, etype, lines


def web_nodes_by_station(xyz, etype, types_front, types_rear_or_all, split_x=None):
    """Nhom cac nut bung dam theo tram y.
    Dau vao:
      xyz, etype : tu read_model
      types_front : TYPE bung dam truoc (None -> dung split_x)
      types_rear_or_all : TYPE bung dam sau (hoac tat ca TYPE bung dam neu types_front = None)
      split_x : ham x_chia(y) tach dam truoc / sau khi types_front = None
    Dau ra:
      dict y (lam tron 1e-6) -> (list nut dam truoc, list nut dam sau)
    """
    out = {}
    def add(n, side):
        y = round(xyz[n][1], 6)
        out.setdefault(y, ([], []))[side].append(n)
    if types_front is not None:
        for side, ts in ((0, types_front), (1, types_rear_or_all)):
            ns = sorted({n for t in ts for e in etype[t] for n in e})
            for n in ns: add(n, side)
    else:
        ns = sorted({n for t in types_rear_or_all for e in etype[t] for n in e})
        for n in ns:
            add(n, 0 if xyz[n][0] > split_x(xyz[n][1]) else 1)
    return out


def nearest(st, y):
    ys = np.array(sorted(st))
    return ys[np.argmin(abs(ys - y))]


def xle(y):
    a = abs(y); return 0.8 if a < 1.75 else -0.08*(a - 1.75)/6.25 + 0.8
def chord(y):
    a = abs(y); return 0.8 if a < 1.75 else 0.8*(1 - (a - 1.75)/6.25) + 0.4*(a - 1.75)/6.25
def split_x(y):   # giua hai dam (xi = 0.466)
    return xle(y) - 0.466*chord(y)


def tip_lines(st):
    ys = nearest(st, 8.0)
    ns = st[ys][0] + st[ys][1]
    return [f'F,{n},FZ,{P_TIP/len(ns):.6f}' for n in ns], ys, len(st[ys][0]), len(st[ys][1])


def prnsol_block(tag, cm='WEBN'):
    return ['CMSEL,S,' + cm, f'/OUTPUT,{tag},txt', 'PRNSOL,U,COMP', '/OUTPUT', 'ALLSEL']


POST_HDR = ['/PAGE,99999999,256,99999999,240', '/HEADER,OFF,OFF,OFF,OFF,ON,OFF',
            '/FORMAT,10,G,16,8']

# ---------------------------------------------------------------- SOLSH190
xyz, etype, lines = read_model(INP_SO)
st = web_nodes_by_station(xyz, etype, None, [5, 6, 7], split_x)
i0 = next(i for i, s in enumerate(lines) if s.startswith('ACEL,0,0,9.81'))
i1 = next(i for i in range(i0, len(lines)) if lines[i].startswith('SOLVE'))
Fd = [s for s in lines[i0:i1] if s.startswith('F,')]
open(os.path.join(D_SO, 'loads_design_SOLSH190.mac'), 'w').write(
    '! Trich nguyen %d lenh F (tai khi dong) cua APDL_for_wing_SOLSH190.inp - tao boi tao_macro_so_sanh.py\n' % len(Fd)
    + '\n'.join(Fd) + '\n')
tl, ytip, nf, nr = tip_lines(st)
open(os.path.join(D_SO, 'loads_tip_SOLSH190.mac'), 'w').write(
    f'! 100 N tai y = {ytip} m, chia deu {nf}+{nr} nut thanh dam truoc + sau\n' + '\n'.join(tl) + '\n')
post = ['! post_sup_SOLSH190.mac - chay sau APDL_for_wing_SOLSH190.inp (tao boi tao_macro_so_sanh.py)',
        'FINISH', '/POST1'] + POST_HDR + [
        'ESEL,S,TYPE,,5,7', 'NSLE,S', 'CM,WEBN,NODE', 'ALLSEL',
        '! ---- 1. Mode cua input goc (12 mode)',
        'SET,FIRST', '/OUTPUT,sup_SOLSH190_freq12,txt', 'SET,LIST', '/OUTPUT',
        '*DO,II,1,12', 'SET,1,II'] + prnsol_block('sup_SOLSH190_m12_mode%II%') + ['*ENDDO', 'FINISH',
        '! ---- 2. Doi jobname de giu nguyen ket qua cua input goc',
        '/FILNAME,wing_SOLSH190_sup',
        '! ---- 3. Tinh: tai thiet ke (lenh F cua input goc) + trong luong, cung dieu kien ngam',
        '/SOLU', 'ANTYPE,STATIC,NEW', 'FDELE,ALL,ALL', 'ACEL,0,0,9.81',
        '/INPUT,loads_design_SOLSH190,mac', 'SOLVE', 'FINISH', '/POST1', 'SET,LAST'] + POST_HDR + prnsol_block('sup_SOLSH190_static_design') + ['FINISH',
        '! ---- 4. Tinh: 100 N dau mut, khong trong luong',
        '/SOLU', 'ANTYPE,STATIC,NEW', 'FDELE,ALL,ALL', 'ACEL,0,0,0',
        '/INPUT,loads_tip_SOLSH190,mac', 'SOLVE', 'FINISH', '/POST1', 'SET,LAST'] + POST_HDR + prnsol_block('sup_SOLSH190_static_tip') + ['FINISH',
        f'! ---- 5. Modal bo sung {NMODE_SUP} mode (de co mode xoan)',
        '/SOLU', 'ANTYPE,MODAL,NEW', 'FDELE,ALL,ALL', 'ACEL,0,0,0',
        f'MODOPT,LANB,{NMODE_SUP}', f'MXPAND,{NMODE_SUP}', 'SOLVE', 'FINISH', '/POST1'] + POST_HDR + [
        f'/OUTPUT,sup_SOLSH190_freq{NMODE_SUP},txt', 'SET,LIST', '/OUTPUT',
        f'*DO,II,1,{NMODE_SUP}', 'SET,1,II'] + prnsol_block(f'sup_SOLSH190_m{NMODE_SUP}_mode%II%') + ['*ENDDO', 'FINISH']
open(os.path.join(D_SO, 'post_sup_SOLSH190.mac'), 'w').write('\n'.join(post) + '\n')
open(os.path.join(D_SO, 'run_all_SOLSH190.inp'), 'w').write(
    '/BATCH\n/INPUT,APDL_for_wing_SOLSH190,inp\n/INPUT,post_sup_SOLSH190,mac\n')
print(f'SOLSH190: {len(xyz)} nut, {len(st)} tram co bung dam, {len(Fd)} lenh F, tip {nf}+{nr} nut tai y = {ytip}')

# ---------------------------------------------------------------- Ung suat tung lop cho tinh ben (tai thiet ke)
# SOLSH190 mac dinh chi luu ket qua mat duoi lop dau va mat tren lop cuoi; KEYOPT(8) = 1 de luu moi lop,
# vi vay phai giai lai bai toan tinh. Mo lai database cua lan chay bo sung (co san luoi, section, ngam).
# Chay rieng:  ANSYS231.exe -b -smp -np 12 -j ben -i do_ben_SOLSH190.mac -o ben.out
# Ket qua: ben_ung_suat_lop.txt, moi dong: so lop, so phan tu, S1 (doc soi), S2 (ngang soi), S12 (cat) (Pa),
#          o giua chieu day lop (SHELL,MID), trung binh tai tam phan tu, he toa do lop (RSYS,LSYS).
#          ben_kiem_tra_PRESOL.txt: PRESOL cua vai phan tu de doi chieu voi ETABLE.
# Mu dam co toi 77 lop, nen voi moi lop chi chon cac section co du so lop do (file ket qua khong qua lon).
LAYERED_TYPES = [1, 2, 3, 4, 5, 6, 8]       # cac TYPE SOLSH190 (7, 9 la foam SOLID185)
section_layer_count = {}
current_section = None
for line in lines:
    if line.startswith('SECTYPE,'):
        current_section = int(line.split(',')[1])
        section_layer_count[current_section] = 0
    elif line.startswith('SECDATA,'):
        section_layer_count[current_section] = section_layer_count[current_section] + 1
    elif line.startswith('N,'):
        break
max_layer_count = max(section_layer_count.values())

strength_macro = ['/BATCH', 'RESUME,wing_SOLSH190_sup,db', '/FILNAME,wing_SOLSH190_ben', '/PREP7']
for element_type in LAYERED_TYPES:
    strength_macro.append(f'KEYOPT,{element_type},8,1')
strength_macro = strength_macro + [
    'FINISH',
    '/SOLU', 'ANTYPE,STATIC,NEW', 'FDELE,ALL,ALL', 'ACEL,0,0,9.81',
    'OUTRES,ERASE', 'OUTRES,ALL,NONE', 'OUTRES,NSOL,LAST', 'OUTRES,RSOL,LAST', 'OUTRES,STRS,LAST',
    '/INPUT,loads_design_SOLSH190,mac', 'SOLVE', 'FINISH',
    '/POST1', 'SET,LAST', 'RSYS,LSYS', 'SHELL,MID',
    'ALLSEL',
    '*GET,EMAX,ELEM,0,NUM,MAXD',
    '*DEL,EID,,NOPR', '*DEL,ESTAT,,NOPR', '*DEL,SX1,,NOPR', '*DEL,SY1,,NOPR', '*DEL,SXY1,,NOPR',
    '*DIM,EID,ARRAY,EMAX', '*DIM,ESTAT,ARRAY,EMAX',
    '*DIM,SX1,ARRAY,EMAX', '*DIM,SY1,ARRAY,EMAX', '*DIM,SXY1,ARRAY,EMAX',
    '*VFILL,EID,RAMP,1,1',
    '*CFOPEN,ben_ung_suat_lop,txt']
for layer in range(1, max_layer_count + 1):
    strength_macro.append(f'! --- lop {layer}')
    strength_macro.append('ESEL,NONE')
    for section_number in section_layer_count:
        if section_layer_count[section_number] >= layer:
            strength_macro.append(f'ESEL,A,SEC,,{section_number}')
    strength_macro.append('ESEL,U,TYPE,,7')      # foam SOLID185 khong co section rieng (SECNUM con lai cua nhom truoc)
    strength_macro.append('ESEL,U,TYPE,,9')
    strength_macro = strength_macro + [
        '*VGET,ESTAT,ELEM,1,ESEL',
        f'LAYER,{layer}',
        'ETABLE,ESX,S,X', 'ETABLE,ESY,S,Y', 'ETABLE,ESXY,S,XY',
        '*VGET,SX1,ELEM,1,ETAB,ESX', '*VGET,SY1,ELEM,1,ETAB,ESY', '*VGET,SXY1,ELEM,1,ETAB,ESXY',
        f'LL={layer}',
        '*VMASK,ESTAT',
        '*VWRITE,LL,EID(1),SX1(1),SY1(1),SXY1(1)',
        '(F4.0,F9.0,3E15.6)']
strength_macro = strength_macro + [
    '*CFCLOS',
    '! Doi chieu: PRESOL lop 1 va lop 2 cua 3 phan tu dau tien moi TYPE 1, 3, 5',
    'ALLSEL'] + POST_HDR + ['/OUTPUT,ben_kiem_tra_PRESOL,txt']
for element_type in (1, 3, 5):
    strength_macro = strength_macro + [
        f'ESEL,S,TYPE,,{element_type}', '*GET,E0,ELEM,0,NUM,MIN', 'ESEL,S,ELEM,,E0,E0+2',
        'LAYER,1', 'PRESOL,S,COMP', 'LAYER,2', 'PRESOL,S,COMP']
strength_macro = strength_macro + ['/OUTPUT', 'ALLSEL', 'FINISH']
with open(os.path.join(D_SO, 'do_ben_SOLSH190.mac'), 'w') as output_file:
    output_file.write('\n'.join(strength_macro) + '\n')
print(f'Tinh ben: {len(section_layer_count)} section, toi da {max_layer_count} lop -> do_ben_SOLSH190.mac')
