# -*- coding: utf-8 -*-
"""
so_sanh_ben.py - So sanh chi so pha huy Tsai-Hill (nghich dao he so an toan) giua MATLAB va APDL SOLSH190 (canh chinh).

Dau vao:
  ../ket_qua_MATLAB_so_sanh.mat                    (xuat_ket_qua_MATLAB.m: f_TH_fiber, f_TH_core, gioi han ben)
  ../upper_point.dat, ../lower_point.dat           (bien dang NACA 4421, de tach mat tren / mat duoi)
  E:\\...\\APDL canh chinh SOLSH190\\APDL_for_wing_SOLSH190.inp   (nut, phan tu, section)
  E:\\...\\APDL canh chinh SOLSH190\\ben_ung_suat_lop.txt         (do_ben_SOLSH190.mac: ung suat tung lop)

Cach tinh phia SOLSH190:
  Moi phan tu, moi lop: ung suat S1 (doc soi), S2 (ngang soi), S12 (cat) o giua chieu day lop, tai tam phan tu.
  Chi so Tsai-Hill giong THstrength.m:
    f = sqrt((S1/X)^2 - S1*S2/X^2 + (S2/Y)^2 + (S12/S)^2)
    X = ben keo doc neu S1 > 0, ben nen doc neu S1 <= 0; Y tuong tu theo S2; S = ben cat.
  Lop carbon dung gioi han ben UD, lop foam dung gioi han ben foam (cung gia tri voi MATLAB).
  Gom theo chi tiet (TYPE, tren/duoi, dam truoc/sau) va theo tram |y| (luoi y cua MATLAB, buoc 0.02 m),
  lay gia tri lon nhat. Foam thanh dam va foam mep sau (SOLID185) khong tinh.
  TYPE 2 (vo vung dam): |y| <= 3.75 cung xep lop voi vo thuong -> gom vao vo;
                        |y| > 3.75 la dai gia cuong (1woven/3UD/1woven) nhu skin_reinf cua MATLAB.

Dau ra (thu muc nay): ben_Tsai_Hill.png, ket_qua_ben.json
"""
import os
import json
import numpy as np
import scipy.io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(THIS_FOLDER)
SOLSH190_FOLDER = r'E:\luan an\ve lai UAV - ANSYS\APDL canh chinh SOLSH190'

FRONT_SPAR_POSITION = 0.22125
REAR_SPAR_POSITION = 0.710625
DIVIDING_POSITION = (FRONT_SPAR_POSITION + REAR_SPAR_POSITION) / 2   # phan day cung tu mep truoc
Y_KV1 = 1.75
Y_KV2 = 3.75
Y_CLAMP = 0.265              # vi tri ngam (MATLAB fix_loc; APDL ngam tai 0.26)
Y_ROOT = 0.30                # tram "goc" dung trong bang (ngay ngoai vung ngam)
FOAM_MATERIAL = 2            # so hieu vat lieu foam trong input APDL

plt.rcParams.update({
    'font.size': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.color': '#e5e4df',
    'grid.linewidth': 0.6,
    'legend.frameon': False,
})


def chord(y_abs):
    """Day cung (m) theo |y| (mang), nhu main_CW.m."""
    return np.where(y_abs < Y_KV1, 0.8, 0.8 * (1 - (y_abs - Y_KV1) / 6.25) + 0.4 * (y_abs - Y_KV1) / 6.25)


def leading_edge_x(y_abs):
    """Toa do x cua mep truoc (m) theo |y| (mang)."""
    return np.where(y_abs < Y_KV1, 0.8, -0.08 * (y_abs - Y_KV1) / 6.25 + 0.8)


def load_airfoil(file_name):
    """Mot mat bien dang: mang (n, 2) [x/c, z/c] tang theo x (giong gen_apdl_for_wing_SOLSH190.py)."""
    data = np.loadtxt(os.path.join(PROJECT_FOLDER, file_name))[:, [0, -1]]
    data = data[np.argsort(data[:, 0])]
    return data / data[:, 0].max()


upper_surface = load_airfoil('upper_point.dat')
lower_surface = load_airfoil('lower_point.dat')


def mean_line(position):
    """z/c cua duong giua hai mat bien dang tai vi tri position (phan day cung)."""
    position = np.clip(position, 0.0, 1.0)
    z_up = np.interp(np.sqrt(position), np.sqrt(upper_surface[:, 0]), upper_surface[:, 1])
    z_low = np.interp(np.sqrt(position), np.sqrt(lower_surface[:, 0]), lower_surface[:, 1])
    return (z_up + z_low) / 2


# =============================================================================
# 1. Doc MATLAB
# =============================================================================
matlab_data = scipy.io.loadmat(os.path.join(PROJECT_FOLDER, 'ket_qua_MATLAB_so_sanh.mat'))
matlab_y = matlab_data['y_half'].ravel()
matlab_fiber = matlab_data['f_TH_fiber']
matlab_core = matlab_data['f_TH_core']
matlab_names = []
for name in matlab_data['ben_names'].ravel():
    matlab_names.append(str(np.squeeze(name)))
strength_UD = matlab_data['strength_UD'].ravel().astype(float)     # [keo doc, nen doc, keo ngang, nen ngang, cat] (Pa)
strength_core = matlab_data['strength_core'].ravel().astype(float) # MATLAB luu so nguyen int32: phai doi sang so thuc, tranh tran so khi binh phuong


def matlab_column(name):
    """Chi so cot cua mot chi tiet trong f_TH_fiber / f_TH_core."""
    return matlab_names.index(name)


# =============================================================================
# 2. Doc mo hinh APDL: nut, section (vat lieu tung lop), phan tu (TYPE, section, nut)
# =============================================================================
node_numbers = []
node_coordinates = []
section_materials = {}         # so section -> list vat lieu cua tung lop
element_type_list = []
element_section_list = []
element_node_list = []
current_section_id = None
current_type = None
current_secnum = 0
for line in open(os.path.join(SOLSH190_FOLDER, 'APDL_for_wing_SOLSH190.inp'), encoding='ascii', errors='replace'):
    if line.startswith('N,'):
        parts = line.split(',')
        node_numbers.append(int(parts[1]))
        node_coordinates.append((float(parts[2]), float(parts[3]), float(parts[4])))
    elif line.startswith('SECTYPE,'):
        current_section_id = int(line.split(',')[1])
        section_materials[current_section_id] = []
    elif line.startswith('SECDATA,'):
        section_materials[current_section_id].append(int(line.split(',')[2]))
    elif line.startswith('TYPE,'):
        current_type = int(line.split(',')[1])
    elif line.startswith('SECNUM,'):
        current_secnum = int(line.split(',')[1])
    elif line.startswith('MAT,'):
        current_secnum = 0
    elif line.startswith('E,'):
        nodes = []
        for value in line.split(',')[1:]:
            nodes.append(int(value))
        element_type_list.append(current_type)       # ANSYS danh so phan tu lien tiep tu 1 theo thu tu dong E
        element_section_list.append(current_secnum)
        element_node_list.append(nodes)
    elif line.startswith('/SOLU'):
        break
number_of_elements = len(element_type_list)
print('So phan tu', number_of_elements, 'so section', len(section_materials))

# Toa do nut theo so nut (mang, chi so = so nut)
all_coordinates = np.zeros((max(node_numbers) + 1, 3))
all_coordinates[np.array(node_numbers)] = np.array(node_coordinates)

# Mang theo so phan tu (chi so 0 bo trong de chi so = so phan tu)
element_type = np.zeros(number_of_elements + 1, dtype=int)
element_type[1:] = element_type_list
element_section = np.zeros(number_of_elements + 1, dtype=int)
element_section[1:] = element_section_list
element_nodes = np.zeros((number_of_elements + 1, 8), dtype=int)
element_nodes[1:] = np.array(element_node_list)
centroid = all_coordinates[element_nodes].mean(axis=1)        # (so phan tu + 1, 3)
centroid_abs_y = np.abs(centroid[:, 1])

# Vat lieu cua tung (section, lop): -1 neu section khong co lop do
max_layers = 0
for section_number in section_materials:
    max_layers = max(max_layers, len(section_materials[section_number]))
material_table = -np.ones((max(section_materials) + 1, max_layers + 1), dtype=int)
for section_number in section_materials:
    for layer_index in range(len(section_materials[section_number])):
        material_table[section_number, layer_index + 1] = section_materials[section_number][layer_index]

# Ten chi tiet cua tung phan tu (trung voi ten ben MATLAB)
element_chord = chord(centroid_abs_y)
element_position = (leading_edge_x(centroid_abs_y) - centroid[:, 0]) / element_chord   # phan day cung tu mep truoc
is_upper = centroid[:, 2] > mean_line(element_position) * element_chord
is_front = element_position < DIVIDING_POSITION
group_of_element = np.empty(number_of_elements + 1, dtype=object)
for element_number in range(1, number_of_elements + 1):
    kind = element_type[element_number]
    if is_upper[element_number]:
        side = 'tren'
    else:
        side = 'duoi'
    if is_front[element_number]:
        spar = 'truoc'
    else:
        spar = 'sau'
    if kind == 1:
        name = 'vo_' + side
    elif kind == 2:
        if centroid_abs_y[element_number] <= Y_KV2:
            name = 'vo_' + side
        else:
            name = 'dai_gia_cuong_' + side
    elif kind == 3:
        name = 'mu_dam_' + spar + '_' + side
    elif kind == 4:
        name = 'side_cap_' + spar + '_' + side
    elif kind == 5:
        name = 'thanh_dam_truoc_' + side
    elif kind == 6:
        name = 'thanh_dam_sau_' + side
    elif kind == 8:
        name = 'rib'
    else:
        name = None
    group_of_element[element_number] = name


# =============================================================================
# 3. Doc ung suat tung lop va tinh Tsai-Hill (tinh tren ca mang)
# =============================================================================
def tsai_hill(s1, s2, s12, strength):
    """Chi so Tsai-Hill (giong THstrength.m) cho cac mang ung suat s1, s2, s12 (Pa).
    strength: mang (so dong, 5) hoac (5,) [keo doc, nen doc, keo ngang, nen ngang, cat]."""
    strength = np.atleast_2d(strength)
    longitudinal_strength = np.where(s1 > 0, strength[:, 0], strength[:, 1])
    transverse_strength = np.where(s2 > 0, strength[:, 2], strength[:, 3])
    value = (s1 / longitudinal_strength) ** 2 - s1 * s2 / longitudinal_strength ** 2 \
        + (s2 / transverse_strength) ** 2 + (s12 / strength[:, 4]) ** 2
    return np.sqrt(np.maximum(value, 0.0))


stress_table = np.loadtxt(os.path.join(SOLSH190_FOLDER, 'ben_ung_suat_lop.txt'))
layer_numbers = stress_table[:, 0].astype(int)
element_numbers = stress_table[:, 1].astype(int)
row_material = material_table[element_section[element_numbers], layer_numbers]
valid = row_material > 0
print('So dong ung suat', len(stress_table), ', dong hop le', int(valid.sum()))
layer_numbers = layer_numbers[valid]
element_numbers = element_numbers[valid]
row_material = row_material[valid]
stress_values = stress_table[valid, 2:5]
row_is_foam = row_material == FOAM_MATERIAL
row_strength = np.where(row_is_foam[:, None], strength_core[None, :], strength_UD[None, :])
row_f = tsai_hill(stress_values[:, 0], stress_values[:, 1], stress_values[:, 2], row_strength)
row_group = group_of_element[element_numbers]
row_abs_y = centroid_abs_y[element_numbers]

# Luoi FEM theo sai (buoc ~0.04 m, thua hon buoc 0.02 m cua MATLAB): moi cot phan tu la mot tram fem_y.
# Duong bao FEM ve tren chinh cac tram nay; gia tri FEM tai mot tram y bat ky lay o tram fem_y gan nhat.
fem_y = np.unique(np.round(centroid_abs_y[1:], 4))
row_station = np.searchsorted(fem_y, np.round(row_abs_y, 4))

# Gia tri lon nhat theo (nhom, vat lieu) va theo tram fem_y
fem_envelope = {}
fem_worst = {}
group_names = sorted(set(name for name in row_group if name is not None))
for name in group_names:
    for material, material_mask in (('soi', ~row_is_foam), ('foam', row_is_foam)):
        mask = (row_group == name) & material_mask
        if not mask.any():
            continue
        envelope = np.full(len(fem_y), np.nan)          # nan: chi tiet khong co phan tu tai tram nay
        np.fmax.at(envelope, row_station[mask], row_f[mask])
        fem_envelope[(name, material)] = envelope
        # Lon nhat ngoai vung ngam (|y| >= Y_ROOT): bo tap trung ung suat sat mat cat ngam
        outside = mask & (row_abs_y >= Y_ROOT)
        index = np.flatnonzero(outside)[np.argmax(row_f[outside])]
        fem_worst[(name, material)] = (float(row_f[index]), float(row_abs_y[index]),
                                       int(element_numbers[index]), int(layer_numbers[index]))
print('So cap (phan tu, lop) da tinh:', int(valid.sum()))


def fem_curve(name, material='soi'):
    """Duong bao FEM tren luoi fem_y (nan o tram khong co phan tu)."""
    return fem_envelope.get((name, material), np.full(len(fem_y), np.nan))


# =============================================================================
# 4. Hinh: chi so Tsai-Hill theo sai, lop soi
# =============================================================================
PANELS = [('Vỏ', 'vo'), ('Dải gia cường (cánh ngoài, |y| > 3.75 m)', 'dai_gia_cuong'),
          ('Mũ dầm trước', 'mu_dam_truoc'), ('Mũ dầm sau', 'mu_dam_sau'),
          ('Thành dầm trước', 'thanh_dam_truoc'), ('Thành dầm sau', 'thanh_dam_sau')]
COLOR_MATLAB = '#2a78d6'
COLOR_FEM = '#1baf7a'
fig, axes = plt.subplots(3, 2, figsize=(10, 9.0), sharex=True)
for panel_index in range(len(PANELS)):
    title, base_name = PANELS[panel_index]
    ax = axes.flat[panel_index]
    for side, line_style in (('tren', '-'), ('duoi', '--')):
        name = base_name + '_' + side
        if side == 'tren':
            side_text = 'trên'
        else:
            side_text = 'dưới'
        matlab_values = matlab_fiber[:, matlab_column(name)].copy()
        fem_values = fem_curve(name).copy()
        if base_name == 'dai_gia_cuong':                 # chi co o canh ngoai
            matlab_values[matlab_y <= Y_KV2] = np.nan
        fem_values[fem_y < Y_CLAMP] = np.nan             # vung giua hai mat cat ngam cua APDL
        ax.plot(matlab_y, matlab_values, color=COLOR_MATLAB, ls=line_style, lw=1.5, label=f'MATLAB – {side_text}')
        ax.plot(fem_y, fem_values, color=COLOR_FEM, ls=line_style, lw=1.2, label=f'SOLSH190 – {side_text}')
    ax.axvspan(0, Y_CLAMP, color='#888888', alpha=0.15, lw=0)
    for boundary in (Y_KV1, Y_KV2):
        ax.axvline(boundary, color='#888888', lw=0.7, ls=':')
    ax.axhline(1.0, color='#cf5829', lw=0.8, ls='-.')
    ax.set_xlim(0, 8)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel('Chỉ số Tsai–Hill f')
    if panel_index >= 4:
        ax.set_xlabel('|y| (m)')
    if panel_index == 0:
        ax.legend(fontsize=7, loc='upper right')
fig.suptitle('Chỉ số phá hủy Tsai–Hill lớn nhất theo các lớp sợi – tải thiết kế\n'
             '(vùng xám: trong ngàm; đường chấm: ranh giới KV1/KV2 và cánh giữa/cánh ngoài; đường gạch chấm: f = 1)',
             fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(THIS_FOLDER, 'ben_Tsai_Hill.png'), dpi=170)
plt.close(fig)


# =============================================================================
# 5. Bang so lieu ra ket_qua_ben.json
#    Tram so sanh: Y_ROOT (goc, ngay ngoai ngam), 1.0 m (giua KV1), lon nhat tung vung KV1 / KV2 / canh ngoai
# =============================================================================
TABLE_ROWS = [('Vỏ trên', 'vo_tren'), ('Vỏ dưới', 'vo_duoi'),
              ('Dải gia cường trên', 'dai_gia_cuong_tren'), ('Dải gia cường dưới', 'dai_gia_cuong_duoi'),
              ('Mũ dầm trước trên', 'mu_dam_truoc_tren'), ('Mũ dầm trước dưới', 'mu_dam_truoc_duoi'),
              ('Mũ dầm sau trên', 'mu_dam_sau_tren'), ('Mũ dầm sau dưới', 'mu_dam_sau_duoi'),
              ('Side cap trước trên', 'side_cap_truoc_tren'), ('Side cap trước dưới', 'side_cap_truoc_duoi'),
              ('Side cap sau trên', 'side_cap_sau_tren'), ('Side cap sau dưới', 'side_cap_sau_duoi'),
              ('Thành dầm trước trên', 'thanh_dam_truoc_tren'), ('Thành dầm trước dưới', 'thanh_dam_truoc_duoi'),
              ('Thành dầm sau trên', 'thanh_dam_sau_tren'), ('Thành dầm sau dưới', 'thanh_dam_sau_duoi')]
def zone_masks(y_values):
    """Mat na cac vung theo |y|: KV1 (tu Y_ROOT), KV2, canh ngoai."""
    return {'KV1': (y_values >= Y_ROOT - 1e-9) & (y_values < Y_KV1),
            'KV2': (y_values >= Y_KV1) & (y_values <= Y_KV2 + 1e-9),
            'ngoai': y_values > Y_KV2 + 1e-9}


MATLAB_ZONES = zone_masks(matlab_y)
FEM_ZONES = zone_masks(fem_y)


def zone_maximum(values, y_values, zone_mask):
    """(gia tri lon nhat, vi tri y) cua values trong vung (bo qua nan)."""
    masked = np.where(zone_mask & ~np.isnan(values), values, -1.0)
    index = int(np.argmax(masked))
    return max(float(masked[index]), 0.0), float(y_values[index])


def value_at(values, y_values, y_target):
    """Gia tri tai tram gan y_target nhat (bo qua nan)."""
    distance = np.where(np.isnan(values), np.inf, np.abs(y_values - y_target))
    return float(values[int(np.argmin(distance))])


table = []
for label, name in TABLE_ROWS:
    matlab_values = matlab_fiber[:, matlab_column(name)]
    fem_values = fem_curve(name)
    row = {'label': label, 'name': name,
           'M_root': value_at(matlab_values, matlab_y, Y_ROOT), 'F_root': value_at(fem_values, fem_y, Y_ROOT),
           'M_y1': value_at(matlab_values, matlab_y, 1.0), 'F_y1': value_at(fem_values, fem_y, 1.0)}
    for zone_name in MATLAB_ZONES:
        row['M_' + zone_name], row['M_' + zone_name + '_y'] = zone_maximum(matlab_values, matlab_y, MATLAB_ZONES[zone_name])
        row['F_' + zone_name], row['F_' + zone_name + '_y'] = zone_maximum(fem_values, fem_y, FEM_ZONES[zone_name])
    table.append(row)
    print(f"{label:22s} goc M {row['M_root']:.3f} F {row['F_root']:.3f} | y=1 M {row['M_y1']:.3f} F {row['F_y1']:.3f} | "
          f"KV1 M {row['M_KV1']:.3f} F {row['F_KV1']:.3f}@{row['F_KV1_y']:.2f} | "
          f"KV2 M {row['M_KV2']:.3f}@{row['M_KV2_y']:.2f} F {row['F_KV2']:.3f}@{row['F_KV2_y']:.2f} | "
          f"ngoai M {row['M_ngoai']:.3f}@{row['M_ngoai_y']:.2f} F {row['F_ngoai']:.3f}@{row['F_ngoai_y']:.2f}")

# Rib va foam: chi lay gia tri lon nhat (ngoai vung ngam)
outside_root = matlab_y >= Y_ROOT - 1e-9


def matlab_max(array, names):
    best = 0.0
    for name in names:
        best = max(best, float(array[outside_root, matlab_column(name)].max()))
    return best


def fem_max(names, material):
    best = (0.0, 0.0)
    for name in names:
        value = fem_worst.get((name, material), (0.0, 0.0))
        if value[0] > best[0]:
            best = value
    return {'F': float(best[0]), 'F_y': float(best[1])}


other = {}
other['rib_soi'] = {'M': matlab_max(matlab_fiber, ['rib_mep_truoc', 'rib_mep_sau'])}
other['rib_soi'].update(fem_max(['rib'], 'soi'))
other['vo_loi_foam'] = {'M': matlab_max(matlab_core, ['vo_tren', 'vo_duoi'])}
other['vo_loi_foam'].update(fem_max(['vo_tren', 'vo_duoi'], 'foam'))
other['rib_loi_foam'] = {'M': matlab_max(matlab_core, ['rib_mep_truoc', 'rib_mep_sau'])}
other['rib_loi_foam'].update(fem_max(['rib'], 'foam'))
print(other)

fiber_items = []
for key in fem_worst:
    if key[1] == 'soi':
        fiber_items.append((key, fem_worst[key]))
worst_overall = max(fiber_items, key=lambda item: item[1][0])
print('Lon nhat SOLSH190 (lop soi, |y| >=', Y_ROOT, '):', worst_overall)
output = {'table': table, 'other': other, 'y_root': Y_ROOT,
          'worst_fem': {'group': worst_overall[0][0], 'material': worst_overall[0][1], 'f': worst_overall[1][0],
                        'abs_y': worst_overall[1][1], 'element': worst_overall[1][2], 'layer': worst_overall[1][3]},
          'strength_UD_MPa': (strength_UD / 1e6).tolist(), 'strength_core_MPa': (strength_core / 1e6).tolist()}
with open(os.path.join(THIS_FOLDER, 'ket_qua_ben.json'), 'w', encoding='utf-8') as json_file:
    json.dump(output, json_file, indent=1, ensure_ascii=False)
print('xong')
