# -*- coding: utf-8 -*-
"""
so_sanh.py - So sanh ket qua MATLAB (dam tuong duong) - APDL SOLSH190.

Dau vao:
  ../ket_qua_MATLAB_so_sanh.mat                               (tao boi xuat_ket_qua_MATLAB.m)
  E:\\...\\APDL canh chinh SOLSH190\\sup_SOLSH190_*.txt        (tao boi post_sup_SOLSH190.mac)

Moi mo hinh duoc rut gon ve 3 dai luong tai thanh dam theo tung tram y:
  UZ_truoc, UZ_sau = do vong trung binh cac nut thanh dam truoc / sau
  UX               = chuyen vi theo day cung (trung binh cac nut hai thanh dam)
Voi MATLAB: UZ_truoc = w + phi*(x_E - 0.22125)*c, UZ_sau = w + phi*(x_E - 0.710625)*c, UX = u.

Dau ra (thu muc nay): cac hinh *.png va ket_qua_so_sanh.json.
Dau ra (thu muc E: cua mo hinh SOLSH190): macro hinh_mode_SOLSH190.inp de ANSYS chup anh dang dao dong 3D.

Ghi chu cho nguoi quen MATLAB:
  - Chi so trong Python bat dau tu 0:  a[0] la phan tu dau tien, a[0::5] tuong duong a(1:5:end) cua MATLAB.
  - dict (vi du results['SOLSH190']) giong struct cua MATLAB, nhung truy cap bang ten trong ngoac vuong.
  - list (vi du [1, 2, 3]) giong cell array mot chieu.
"""
import os
import re
import json
import numpy as np
import scipy.io
import matplotlib
matplotlib.use('Agg')                 # ve hinh ra file, khong mo cua so
import matplotlib.pyplot as plt
import matplotlib.image


# =============================================================================
# Thong so chung
# =============================================================================
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_FOLDER = os.path.dirname(THIS_FOLDER)
SOLSH190_FOLDER = r'E:\luan an\ve lai UAV - ANSYS\APDL canh chinh SOLSH190'

FRONT_SPAR_POSITION = 0.22125         # vi tri dam truoc, phan day cung tinh tu mep truoc
REAR_SPAR_POSITION = 0.710625         # vi tri dam sau

# Luoi y chung cho ca 2 mo hinh: -8 m den 8 m, buoc 0.05 m (giong -8:0.05:8 trong MATLAB)
Y_GRID = np.round(np.arange(-8.0, 8.0001, 0.05), 6)

MODELS = ['MATLAB', 'SOLSH190']
LINE_COLOR = {'MATLAB': '#2a78d6', 'SOLSH190': '#1baf7a'}
LINE_STYLE = {'MATLAB': '-', 'SOLSH190': ':'}
LINE_MARKER = {'MATLAB': None, 'SOLSH190': 'o'}

plt.rcParams.update({
    'font.size': 9,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.color': '#e5e4df',
    'grid.linewidth': 0.6,
    'axes.edgecolor': '#888',
    'legend.frameon': False,
    'figure.dpi': 110,
})


def leading_edge_x(y):
    """Toa do x cua mep truoc (m) tai vi tri sai y. y co the la mot so hoac mot mang."""
    distance = np.abs(y)
    return np.where(distance < 1.75, 0.8, 0.8 - 0.08 * (distance - 1.75) / 6.25)


def chord_length(y):
    """Do dai day cung (m): 0.8 m den |y| = 1.75 m, sau do thuon tuyen tinh con 0.4 m o dau mut."""
    distance = np.abs(y)
    ratio = (distance - 1.75) / 6.25
    return np.where(distance < 1.75, 0.8, 0.8 * (1 - ratio) + 0.4 * ratio)


# =============================================================================
# 1. Doc ket qua APDL
# =============================================================================
def read_apdl_model(input_file):
    """Doc file .inp cua APDL: toa do nut va danh sach phan tu theo TYPE.
    Tra ve:
      node_xyz[so nut] = (x, y, z)
      elements_by_type[TYPE] = list cac phan tu, moi phan tu la list so nut
    """
    node_xyz = {}
    elements_by_type = {}
    current_type = None
    for line in open(input_file, encoding='ascii', errors='replace'):
        if line.startswith('N,'):
            parts = line.split(',')
            node_number = int(parts[1])
            node_xyz[node_number] = (float(parts[2]), float(parts[3]), float(parts[4]))
        elif line.startswith('TYPE,'):
            current_type = int(line.split(',')[1])
        elif line.startswith('E,'):
            parts = line.split(',')
            element_nodes = []
            for value in parts[1:]:
                element_nodes.append(int(value))
            if current_type not in elements_by_type:
                elements_by_type[current_type] = []
            elements_by_type[current_type].append(element_nodes)
        elif line.startswith('/SOLU'):
            break
    return node_xyz, elements_by_type


def find_web_nodes_by_station(node_xyz, elements_by_type, web_types):
    """Gom cac nut thanh dam theo tram y, tach thanh nut dam truoc va nut dam sau.
    Tra ve: y_stations (mang), front_nodes (list cac mang nut), rear_nodes (list cac mang nut).
    """
    web_nodes = set()
    for element_type in web_types:
        for element_nodes in elements_by_type[element_type]:
            for node in element_nodes:
                web_nodes.add(node)

    # Duong chia giua hai dam: x = x_mep_truoc - 0.466*c (giua 0.22125c va 0.710625c)
    front_by_y = {}
    rear_by_y = {}
    for node in sorted(web_nodes):
        x, y, z = node_xyz[node]
        y_key = round(y, 6)
        if y_key not in front_by_y:
            front_by_y[y_key] = []
            rear_by_y[y_key] = []
        dividing_x = leading_edge_x(y) - 0.466 * chord_length(y)
        if x > dividing_x:
            front_by_y[y_key].append(node)
        else:
            rear_by_y[y_key].append(node)

    y_stations = np.array(sorted(front_by_y.keys()))
    front_nodes = []
    rear_nodes = []
    for y_key in y_stations:
        front_nodes.append(np.array(front_by_y[y_key]))
        rear_nodes.append(np.array(rear_by_y[y_key]))
    return y_stations, front_nodes, rear_nodes


def read_prnsol_file(file_name):
    """Doc file ket qua cua lenh PRNSOL,U,COMP. Tra ve displacement[so nut] = (UX, UZ).
    Cac so am co the dinh lien nhau (vi du '0.35E-002-0.13E-001') nen phai tach bang bieu thuc chinh quy.
    """
    number_pattern = re.compile(r'[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?')
    displacement = {}
    for line in open(file_name):
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            values = number_pattern.findall(parts[1])
            if len(values) == 4:                       # UX, UY, UZ, USUM
                node = int(parts[0])
                displacement[node] = (float(values[0]), float(values[2]))
    return displacement


def reduce_to_stations(file_name, stations):
    """Doc mot file PRNSOL va rut gon ve ma tran 3 x so_tram: hang 1 UZ_truoc, hang 2 UZ_sau, hang 3 UX."""
    displacement = read_prnsol_file(file_name)
    y_stations, front_nodes, rear_nodes = stations
    number_of_stations = len(y_stations)
    uz_front = np.zeros(number_of_stations)
    uz_rear = np.zeros(number_of_stations)
    ux = np.zeros(number_of_stations)
    for i in range(number_of_stations):
        uz_front_values = []
        for node in front_nodes[i]:
            uz_front_values.append(displacement[node][1])
        uz_rear_values = []
        for node in rear_nodes[i]:
            uz_rear_values.append(displacement[node][1])
        ux_values = []
        for node in np.concatenate([front_nodes[i], rear_nodes[i]]):
            ux_values.append(displacement[node][0])
        uz_front[i] = np.mean(uz_front_values)
        uz_rear[i] = np.mean(uz_rear_values)
        ux[i] = np.mean(ux_values)
    return np.vstack([uz_front, uz_rear, ux])


def read_frequencies(file_name):
    """Doc tan so tu file ket qua cua lenh SET,LIST."""
    frequencies = []
    for line in open(file_name):
        parts = line.split()
        if len(parts) >= 5 and parts[0].isdigit():
            frequencies.append(float(parts[1]))
    return np.array(frequencies)


# Ten file ket qua cua tung mo hinh APDL
APDL_FILES = {
    'SOLSH190': {
        'folder': SOLSH190_FOLDER,
        'input': 'APDL_for_wing_SOLSH190.inp',
        'web_types': [5, 6, 7],
        'mode': 'sup_SOLSH190_m24_mode{}.txt',         # {} duoc thay bang so thu tu mode
        'frequency': 'sup_SOLSH190_freq24.txt',
        'design': 'sup_SOLSH190_static_design.txt',
        'tip': 'sup_SOLSH190_static_tip.txt',
    },
}

# results[mo hinh] chua: y, f (tan so), modes (list ma tran 3 x so_tram), design, tip, nnode, nelem
results = {}
for model_name in APDL_FILES:
    files = APDL_FILES[model_name]
    folder = files['folder']
    node_xyz, elements_by_type = read_apdl_model(os.path.join(folder, files['input']))
    stations = find_web_nodes_by_station(node_xyz, elements_by_type, files['web_types'])
    frequencies = read_frequencies(os.path.join(folder, files['frequency']))

    modes = []
    for mode_number in range(1, len(frequencies) + 1):
        mode_file = os.path.join(folder, files['mode'].format(mode_number))
        modes.append(reduce_to_stations(mode_file, stations))

    number_of_elements = 0
    for element_type in elements_by_type:
        number_of_elements = number_of_elements + len(elements_by_type[element_type])

    results[model_name] = {
        'y': stations[0],
        'f': frequencies,
        'modes': modes,
        'design': reduce_to_stations(os.path.join(folder, files['design']), stations),
        'tip': reduce_to_stations(os.path.join(folder, files['tip']), stations),
        'nnode': len(node_xyz),
        'nelem': number_of_elements,
    }
    print(model_name, 'so tram', len(stations[0]), 'so mode', len(frequencies))


# =============================================================================
# 2. Doc ket qua MATLAB
# =============================================================================
matlab_data = scipy.io.loadmat(os.path.join(PROJECT_FOLDER, 'ket_qua_MATLAB_so_sanh.mat'))
matlab_y = matlab_data['y_full'].ravel()          # ravel(): bien ma tran thanh vector, giong (:) trong MATLAB
matlab_chord = matlab_data['c_full'].ravel()
matlab_x_E = matlab_data['x_E_full'].ravel()


def beam_to_web(beam_vector):
    """Quy vector bac tu do cua dam [w, w', phi, u, u'] ve 3 dai luong tai thanh dam (giong APDL)."""
    w = beam_vector[0::5]
    phi = beam_vector[2::5]
    u = beam_vector[3::5]
    uz_front = w + phi * (matlab_x_E - FRONT_SPAR_POSITION) * matlab_chord
    uz_rear = w + phi * (matlab_x_E - REAR_SPAR_POSITION) * matlab_chord
    return np.vstack([uz_front, uz_rear, u])


matlab_mode_vectors = matlab_data['Vf']
number_of_matlab_modes = matlab_mode_vectors.shape[1]
matlab_modes = []
for k in range(number_of_matlab_modes):
    matlab_modes.append(beam_to_web(matlab_mode_vectors[:, k]))

results['MATLAB'] = {
    'y': matlab_y,
    'f': matlab_data['Df'].ravel()[:number_of_matlab_modes],
    'modes': matlab_modes,
    'design': beam_to_web(matlab_data['defl_design'].ravel()),
    'tip': beam_to_web(matlab_data['defl_tip'].ravel()),
    'energy': matlab_data['mode_energy'],
}


def interpolate_on_grid(model_name, station_values):
    """Noi suy ma tran 3 x so_tram cua mot mo hinh len luoi chung Y_GRID (ket qua: 3 x so diem luoi)."""
    rows_on_grid = []
    for row in station_values:
        rows_on_grid.append(np.interp(Y_GRID, results[model_name]['y'], row))
    return np.vstack(rows_on_grid)


# =============================================================================
# 3. MAC va co so doi xung / phan doi xung
# =============================================================================
def mac(vector_a, vector_b):
    """MAC = (a'b)^2 / ((a'a)(b'b))."""
    a = np.ravel(vector_a)
    b = np.ravel(vector_b)
    return float(np.dot(a, b) ** 2 / (np.dot(a, a) * np.dot(b, b)))


def mirror(grid_values):
    """Phan chieu qua y = 0: dao nguoc thu tu theo y (giong fliplr), UZ va UX giu nguyen dau."""
    return grid_values[:, ::-1]


def symmetric_basis(model_name, tolerance=1e-3):
    """Dua cac mode cua mot mo hinh ve co so doi xung (S) / phan doi xung (A).

    Hai nua canh gan nhu doc lap nen hay co cap mode trung tan so; ANSYS co the tra ve mode tron
    (chi mot nua canh dao dong). Cac mode co tan so chenh nhau < tolerance duoc gom thanh mot cum,
    roi tach phan doi xung (W + W_phan_chieu)/2 va phan doi xung (W - W_phan_chieu)/2 bang SVD.

    Tra ve list cac dict: f (tan so), typ ('S' hoac 'A'), V (ma tran 3 x so diem luoi),
    src (so thu tu cac mode goc trong cum, tinh tu 1).
    """
    frequencies = results[model_name]['f']
    modes_on_grid = []
    for mode in results[model_name]['modes']:
        modes_on_grid.append(interpolate_on_grid(model_name, mode))

    basis = []
    first = 0
    while first < len(frequencies):
        # tim mode cuoi cung cua cum co tan so gan bang tan so mode dau cum
        last = first
        while last + 1 < len(frequencies) and frequencies[last + 1] - frequencies[first] < tolerance * frequencies[first]:
            last = last + 1

        # W: moi cot la mot mode goc (duoi dang vector), W_mirror: cac mode do sau khi phan chieu
        columns = []
        mirrored_columns = []
        for k in range(first, last + 1):
            columns.append(modes_on_grid[k].ravel())
            mirrored_columns.append(mirror(modes_on_grid[k]).ravel())
        W = np.array(columns).T
        W_mirror = np.array(mirrored_columns).T
        threshold = 0.3 * np.linalg.norm(W) / np.sqrt(W.shape[1])

        candidates = []
        for symmetry_type, part in (('S', (W + W_mirror) / 2), ('A', (W - W_mirror) / 2)):
            U, singular_values, _ = np.linalg.svd(part, full_matrices=False)
            for q in range(len(singular_values)):
                if singular_values[q] > threshold:
                    candidates.append((symmetry_type, U[:, q]))
        number_in_cluster = last - first + 1
        candidates = candidates[:number_in_cluster]

        source_modes = list(range(first + 1, last + 2))
        for symmetry_type, vector in candidates:
            # lay tan so cua mode goc giong vector nay nhat (MAC lon nhat)
            mac_with_sources = []
            for q in range(W.shape[1]):
                mac_with_sources.append(mac(vector, W[:, q]))
            closest = int(np.argmax(mac_with_sources))
            basis.append({
                'f': float(frequencies[first + closest]),
                'typ': symmetry_type,
                'V': vector.reshape(3, -1),
                'src': source_modes,
            })
        first = last + 1

    basis.sort(key=get_frequency)
    return basis


def get_frequency(mode):
    return mode['f']


def kind_of_mode(V):
    """Phan loai so bo mot mode APDL theo do lon cac thanh phan tren nua canh phai (y > 0.3 m)."""
    right_half = Y_GRID > 0.3
    bending = ((V[0] + V[1]) / 2)[right_half]
    twisting = ((V[0] - V[1]) / 2)[right_half]
    lateral = V[2][right_half]
    # he so 6: quy doi chuyen vi do xoan (nho) ve cung co do voi hai thanh phan con lai
    energy = np.array([np.sum(bending ** 2), np.sum(twisting ** 2) * 6, np.sum(lateral ** 2)])
    names = ['uon dung', 'xoan', 'uon ngang']
    return names[int(np.argmax(energy))]


basis = {}
for model_name in MODELS:
    basis[model_name] = symmetric_basis(model_name)
    summary = []
    for mode in basis[model_name][:14]:
        summary.append((round(mode['f'], 3), mode['typ']))
    print(model_name, summary)

# MATLAB: loai mode lay theo ty le dong nang ma coupled_beam.m da tinh
kind_names = ['uon dung', 'xoan', 'uon ngang']
for mode in basis['MATLAB']:
    original_index = mode['src'][0] - 1
    mode['kind'] = kind_names[int(np.argmax(results['MATLAB']['energy'][:, original_index]))]
for mode in basis['SOLSH190']:
    mode['kind'] = kind_of_mode(mode['V'])


# =============================================================================
# 4. Ghep cap mode MATLAB voi mode APDL
# =============================================================================
def match_modes(reference_modes, other_modes):
    """Moi mode cua reference_modes duoc ghep voi mode cung kieu doi xung cua other_modes co MAC lon nhat.
    Moi mode cua other_modes chi duoc dung mot lan; chi chap nhan khi MAC > 0.5.
    Tra ve list cac cap (MAC, chi so trong other_modes hoac None).
    """
    used = set()
    matches = []
    for reference in reference_modes:
        best_mac = 0.0
        best_index = None
        for index in range(len(other_modes)):
            other = other_modes[index]
            if other['typ'] != reference['typ'] or index in used:
                continue
            value = mac(reference['V'], other['V'])
            if value > best_mac:
                best_mac = value
                best_index = index
        if best_index is not None and best_mac > 0.5:
            used.add(best_index)
            matches.append((best_mac, best_index))
        else:
            matches.append((best_mac, None))
    return matches


reference_modes = basis['MATLAB'][:20]
matches_solsh = match_modes(reference_modes, basis['SOLSH190'])

# Moi dong cua bang ghep cap. Ten khoa giu nguyen vi tao_bao_cao.py doc chung:
#   k: so thu tu mode MATLAB; f_M, f_SO: tan so MATLAB / SOLSH190
#   mac_MSO: MAC giua MATLAB va SOLSH190; i_SO: chi so mode trong basis['SOLSH190']
rows = []
for k in range(len(reference_modes)):
    reference = reference_modes[k]
    row = {'k': k + 1, 'kind': reference['kind'], 'typ': reference['typ'], 'f_M': reference['f']}
    match_mac, match_index = matches_solsh[k]
    if match_index is None:
        row['f_SO'] = None
    else:
        row['f_SO'] = basis['SOLSH190'][match_index]['f']
    row['mac_MSO'] = match_mac
    row['i_SO'] = match_index
    rows.append(row)
    print(row)


# =============================================================================
# 5. Hinh ma tran MAC
# =============================================================================
def mac_matrix(modes_a, modes_b):
    matrix = np.zeros((len(modes_a), len(modes_b)))
    for i in range(len(modes_a)):
        for j in range(len(modes_b)):
            matrix[i, j] = mac(modes_a[i]['V'], modes_b[j]['V'])
    return matrix


def diagonal_column_order(matrix):
    """Thu tu cot de cac o MAC lon nam tren duong cheo.
    Xet cac o theo MAC giam dan; o (i, j) duoc chon neu hang i va cot j chua duoc dung.
    Cot duoc chon cho hang i dat o vi tri i; cac cot khong duoc chon noi vao cuoi.
    """
    sorted_positions = np.argsort(-matrix, axis=None)
    row_indices, column_indices = np.unravel_index(sorted_positions, matrix.shape)
    column_of_row = {}
    used_columns = set()
    for i, j in zip(row_indices, column_indices):
        if i not in column_of_row and j not in used_columns:
            column_of_row[i] = j
            used_columns.add(j)

    order = []
    for i in range(matrix.shape[0]):
        if i in column_of_row:
            order.append(column_of_row[i])
    for j in range(matrix.shape[1]):
        if j not in used_columns:
            order.append(j)
    return order


def mode_labels(modes):
    labels = []
    for mode in modes:
        labels.append(f"{mode['f']:.1f}{mode['typ']}")
    return labels


def plot_mac(modes_a, modes_b, name_a, name_b, file_name):
    matrix = mac_matrix(modes_a, modes_b)
    order = diagonal_column_order(matrix)
    order = order[:len(modes_a)]                        # bo cac cot (mode) khong ghep duoc
    reordered_modes_b = []
    for j in order:
        reordered_modes_b.append(modes_b[j])
    matrix = matrix[:, order]

    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    image = ax.imshow(matrix, cmap='Blues', vmin=0, vmax=1, origin='lower')   # origin='lower': tan so nho o duoi
    ax.set_xticks(range(len(reordered_modes_b)))
    ax.set_xticklabels(mode_labels(reordered_modes_b), rotation=90, fontsize=7)
    ax.set_yticks(range(len(modes_a)))
    ax.set_yticklabels(mode_labels(modes_a), fontsize=7)
    ax.set_xlabel(f'{name_b}: tần số (Hz) + kiểu (S/A), sắp theo mode ghép')
    ax.set_ylabel(f'{name_a}: tần số (Hz) + kiểu')
    ax.grid(False)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if matrix[i, j] >= 0.5:
                if matrix[i, j] > 0.7:
                    text_color = 'white'
                else:
                    text_color = '#0b0b0b'
                ax.text(j, i, f'{matrix[i, j]:.2f}', ha='center', va='center', fontsize=5.5, color=text_color)
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03, label='MAC')
    ax.set_title(f'Ma trận MAC: {name_a} – {name_b}', fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(THIS_FOLDER, file_name), dpi=180)
    plt.close(fig)


plot_mac(basis['MATLAB'][:20], basis['SOLSH190'][:24], 'MATLAB', 'SOLSH190', 'mac_MATLAB_SOLSH190.png')


# =============================================================================
# 6. Hinh duong cong dang dao dong tung cap (w, goc xoan, u theo sai)
# =============================================================================
def split_components(V, scale=1.0):
    """Tu ma tran 3 x so diem luoi tinh: do vong trung binh w, goc xoan (rad, > 0 khi mep truoc di len), u."""
    chord = chord_length(Y_GRID)
    w = (V[0] + V[1]) / 2
    twist = (V[0] - V[1]) / ((REAR_SPAR_POSITION - FRONT_SPAR_POSITION) * chord)
    return scale * w, scale * twist, scale * V[2]


def least_squares_factor(vector, reference):
    """He so a sao cho a*vector gan reference nhat (cung dau, cung bien do)."""
    return np.dot(vector.ravel(), reference.ravel()) / np.dot(vector.ravel(), vector.ravel())


component_titles = ['w – uốn đứng', 'góc xoắn (chuẩn hóa)', 'u – uốn ngang']
fig_modes = []
for k in range(0, len(rows), 2):                       # moi hinh: mot cap mode doi xung / phan doi xung
    pair = rows[k:k + 2]
    fig, axes = plt.subplots(len(pair), 3, figsize=(10, 2.6 * len(pair)), squeeze=False)
    for row_number in range(len(pair)):
        row = pair[row_number]
        reference_V = reference_modes[row['k'] - 1]['V']
        normalize = 1 / np.max(np.abs(reference_V))
        if row['typ'] == 'S':
            symmetry_text = 'đối xứng'
        else:
            symmetry_text = 'phản đối xứng'

        for model_name, index in (('MATLAB', row['k'] - 1), ('SOLSH190', row['i_SO'])):
            if index is None:
                continue
            if model_name == 'MATLAB':
                V = reference_V
            else:
                V = basis[model_name][index]['V']
            scale = least_squares_factor(V, reference_V) * normalize
            components = split_components(V, scale)
            if model_name == 'MATLAB':
                line_width = 1.6
            else:
                line_width = 1.3
            for column in range(3):
                ax = axes[row_number][column]
                ax.plot(Y_GRID, components[column], color=LINE_COLOR[model_name], lw=line_width,
                        ls=LINE_STYLE[model_name], marker=LINE_MARKER[model_name], markevery=16, ms=4,
                        label=model_name)
                ax.set_title(f"Mode {row['k']} ({symmetry_text}) - {component_titles[column]}", fontsize=8)
                ax.set_xlabel('y (m)')
        axes[row_number][0].legend(fontsize=7, loc='best')
    fig.tight_layout()
    file_name = f"mode_pair_{k // 2 + 1:02d}.png"
    fig.savefig(os.path.join(THIS_FOLDER, file_name), dpi=170)
    plt.close(fig)
    fig_modes.append(file_name)


# =============================================================================
# 7. Hinh do vong tinh va goc xoan theo sai
# =============================================================================
def plot_static(case, file_name, title):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for model_name in MODELS:
        values = results[model_name][case]
        y = results[model_name]['y']
        right_half = y >= 0
        marker_step = max(1, right_half.sum() // 12)

        deflection_mm = (values[0] + values[1]) / 2 * 1000
        chord = chord_length(y)
        twist_degree = np.degrees((values[0] - values[1]) / ((REAR_SPAR_POSITION - FRONT_SPAR_POSITION) * chord))

        axes[0].plot(y[right_half], deflection_mm[right_half], color=LINE_COLOR[model_name],
                     ls=LINE_STYLE[model_name], marker=LINE_MARKER[model_name],
                     markevery=marker_step, ms=4, lw=1.6, label=model_name)
        axes[1].plot(y[right_half], twist_degree[right_half], color=LINE_COLOR[model_name],
                     ls=LINE_STYLE[model_name], marker=LINE_MARKER[model_name],
                     markevery=marker_step, ms=4, lw=1.6, label=model_name)
    axes[0].set_ylabel('Độ võng trung bình hai thành dầm (mm)')
    axes[1].set_ylabel('Góc xoắn (độ), > 0: mép trước đi lên')
    for ax in axes:
        ax.set_xlabel('y (m)')
        ax.legend(fontsize=8)
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(THIS_FOLDER, file_name), dpi=180)
    plt.close(fig)


plot_static('design', 'static_design.png', 'Tải thiết kế (khí động × 1.3 × 3.8 / 2, trừ trọng lượng 1g) – nửa cánh phải')
plot_static('tip', 'static_tip.png', 'Lực 100 N tại đầu mút y = +8 m (chia đều hai thành dầm) – nửa cánh phải')


# =============================================================================
# 8. Hinh cot tan so
# =============================================================================
fig, ax = plt.subplots(figsize=(9, 3.6))
bar_positions = np.arange(len(rows))
bar_width = 0.38
bar_hatch = {'MATLAB': None, 'SOLSH190': '....'}
bar_offset = {'MATLAB': -0.5, 'SOLSH190': 0.5}
frequency_key = {'MATLAB': 'f_M', 'SOLSH190': 'f_SO'}
for model_name in MODELS:
    values = []
    for row in rows:
        if row[frequency_key[model_name]] is None:
            values.append(np.nan)
        else:
            values.append(row[frequency_key[model_name]])
    ax.bar(bar_positions + bar_offset[model_name] * bar_width, values, bar_width - 0.03,
           color=LINE_COLOR[model_name], label=model_name, hatch=bar_hatch[model_name], edgecolor='white', lw=0)
tick_labels = []
for row in rows:
    tick_labels.append(f"{row['k']}\n{row['typ']}")
ax.set_xticks(bar_positions)
ax.set_xticklabels(tick_labels, fontsize=7)
ax.set_xlabel('Mode MATLAB (S đối xứng / A phản đối xứng)')
ax.set_ylabel('Tần số (Hz)')
ax.legend(fontsize=8)
ax.set_title('Tần số riêng của các mode đã ghép cặp theo MAC', fontsize=10)
fig.tight_layout()
fig.savefig(os.path.join(THIS_FOLDER, 'tan_so.png'), dpi=180)
plt.close(fig)


# =============================================================================
# 9. Hinh dang dao dong 3D (anh MATLAB + anh chup tu ANSYS)
# =============================================================================
# Buoc 1 (o day): ghi macro APDL hinh_mode_<mo hinh>.inp vao thu muc cua moi mo hinh.
# Buoc 2: chay ANSYS batch trong thu muc mo hinh:
#   ANSYS231.exe -b -np 4 -j hinh_mode_<mo hinh> -i hinh_mode_<mo hinh>.inp -o hinh_mode_<mo hinh>.out
#   -> hinh_mode_<mo hinh>000.png ... 019.png; chuyen cac anh nay vao thu muc con hinh_mode\
# Buoc 3: chay lai so_sanh.py -> ghep thanh mode_img_01..10.png (chi ghep khi da co du anh).
RESULT_FILE = {'SOLSH190': (SOLSH190_FOLDER, 'wing_SOLSH190_sup')}

# Mode goc (chua dua ve co so S/A) tren luoi chung, dang vector
raw_modes_on_grid = {}
for model_name in MODELS:
    raw_modes_on_grid[model_name] = []
    for mode in results[model_name]['modes']:
        raw_modes_on_grid[model_name].append(interpolate_on_grid(model_name, mode).ravel())


def combination_of_raw_modes(model_name, mode, target):
    """He so to hop cac mode goc (mode['src']) tao ra vector S/A mode['V'], doi dau de cung chieu voi target.
    Tra ve list cac cap (so thu tu mode goc, he so).
    """
    columns = []
    for source in mode['src']:
        columns.append(raw_modes_on_grid[model_name][source - 1])
    W = np.array(columns).T
    coefficients = np.linalg.lstsq(W, mode['V'].ravel(), rcond=None)[0]     # giai W*c = V, giong W\V cua MATLAB
    if np.dot(W @ coefficients, target) < 0:                                 # @ la nhan ma tran
        coefficients = -coefficients
    coefficients = coefficients / np.max(np.abs(coefficients))
    combination = []
    for source, coefficient in zip(mode['src'], coefficients):
        if abs(coefficient) > 1e-3:
            combination.append((source, float(coefficient)))
    return combination


# Ke hoach anh: moi dong MATLAB mot anh cho moi mo hinh
img_plan = []
for row in rows:
    reference = reference_modes[row['k'] - 1]
    # mode MATLAB goc giong vector S/A nhat (de lay dung anh ma main_CW da ve)
    matlab_mode = reference['src'][0]
    best_mac = -1.0
    for source in reference['src']:
        value = mac(raw_modes_on_grid['MATLAB'][source - 1], reference['V'])
        if value > best_mac:
            best_mac = value
            matlab_mode = source
    target = raw_modes_on_grid['MATLAB'][matlab_mode - 1]

    item = {'k': row['k'], 'typ': row['typ'], 'kind': row['kind'], 'matlab_mode': matlab_mode, 'f_M': row['f_M']}
    if row['i_SO'] is None:
        item['SOLSH190'] = None
    else:
        item['SOLSH190'] = combination_of_raw_modes('SOLSH190', basis['SOLSH190'][row['i_SO']], target)
    img_plan.append(item)

# Ghi macro APDL
for model_name in RESULT_FILE:
    folder, result_name = RESULT_FILE[model_name]
    lines = [
        '/BATCH',
        f'! hinh_mode_{model_name}.inp - chup hinh dang dao dong (sinh boi bao_cao_so_sanh/so_sanh.py, khong sua tay)',
        '/POST1',
        f'FILE,{result_name},rst',
        'SET,FIRST',                                  # SET nap luoi tu file .rst vao database
        '/RGB,INDEX,100,100,100,0',                   # nen trang
        '/RGB,INDEX,0,0,0,15',                        # chu den
        '/SHOW,PNG',
        '/GFILE,1600',
        'PNGR,COMP,1,-1',
        '/VUP,1,Z',
        '/VIEW,1,-0.709,-0.497,0.5',                  # giong view(-55,30) cua MATLAB
        '/AUTO,1',
        '/TRIAD,OFF',
        '/PLOPTS,INFO,0',
        '/PLOPTS,LOGO,0',
        '/PLOPTS,DATE,0',
        '/PLOPTS,WP,0',
        '/EDGE,1,1',                                  # chi ve canh bien
        '/GLINE,1,-1',                                # khong ve luoi phan tu
        '/CONT,1,9',                                  # 9 dai mau
    ]
    for item in img_plan:
        combination = item[model_name]
        lines.append('LCZERO')
        lines.append('LCDEF,ERASE')
        load_case = 0
        for source, coefficient in combination:
            load_case = load_case + 1
            lines.append(f'LCDEF,{load_case},1,{source}')
            lines.append(f'LCFACT,{load_case},{coefficient:.6f}')
        lines.append('LCASE,1')
        for load_case in range(2, len(combination) + 1):
            lines.append(f'LCOPER,ADD,{load_case}')
        lines.append(f"/TITLE,{model_name} - MATLAB mode {item['k']}")
        lines.append('PLNSOL,U,SUM,0')
    lines.append('/SHOW,CLOSE')
    lines.append('FINISH')
    with open(os.path.join(folder, f'hinh_mode_{model_name}.inp'), 'w') as macro_file:
        macro_file.write('\n'.join(lines) + '\n')


def image_path(model_name, item, image_index):
    if model_name == 'MATLAB':
        return os.path.join(THIS_FOLDER, 'hinh_mode_MATLAB', f"MATLAB_mode{item['matlab_mode']:02d}.png")
    return os.path.join(SOLSH190_FOLDER, 'hinh_mode', f'hinh_mode_SOLSH190{image_index:03d}.png')


def trim_to_colored_area(image, padding=12):
    """Cat anh sat vung co mau (bo nen trang va chu den/xam)."""
    rgb = image[:, :, :3].astype(float)
    if rgb.max() > 1.5:
        rgb = rgb / 255
    saturation = rgb.max(axis=2) - rgb.min(axis=2)
    colored_rows, colored_columns = np.where(saturation > 0.15)
    top = max(colored_rows.min() - padding, 0)
    bottom = colored_rows.max() + padding
    left = max(colored_columns.min() - padding, 0)
    right = colored_columns.max() + padding
    return image[top:bottom, left:right]


KIND_IN_VIETNAMESE = {'uon dung': 'Uốn đứng', 'xoan': 'Xoắn', 'uon ngang': 'Uốn ngang'}

all_images_exist = True
last_item = img_plan[-1]
for model_name in MODELS:
    if not os.path.exists(image_path(model_name, last_item, len(img_plan) - 1)):
        all_images_exist = False

mode_img_figs = []
if all_images_exist:
    count_by_kind = {}
    for k in range(0, len(rows), 2):
        pair = img_plan[k:k + 2]
        kind = pair[0]['kind']
        count_by_kind[kind] = count_by_kind.get(kind, 0) + 1

        fig, axes = plt.subplots(len(MODELS), 2, figsize=(14, 5.8), squeeze=False)
        for column in range(len(pair)):                # cot trai: doi xung, cot phai: phan doi xung
            item = pair[column]
            row = rows[item['k'] - 1]
            if item['typ'] == 'S':
                symmetry_text = 'đối xứng'
            else:
                symmetry_text = 'phản đối xứng'

            for row_number in range(len(MODELS)):        # hang: MATLAB, SOLSH190
                model_name = MODELS[row_number]
                ax = axes[row_number][column]
                ax.axis('off')
                image = matplotlib.image.imread(image_path(model_name, item, item['k'] - 1))
                if model_name == 'MATLAB':
                    image = image[:, :int(image.shape[1] * 0.86)]     # bo thang mau cua MATLAB
                else:
                    image = image[60:-60, 60:-60]                     # bo khung va so cua so (mau xanh) cua ANSYS
                ax.imshow(trim_to_colored_area(image))

                if model_name == 'MATLAB':
                    title = f"MATLAB – mode {item['matlab_mode']} ({symmetry_text}), f = {item['f_M']:.2f} Hz"
                else:
                    tag = 'SO'
                    source_numbers = []
                    for source, coefficient in item[model_name]:
                        source_numbers.append(str(source))
                    source_text = '+'.join(source_numbers)
                    frequency = row['f_' + tag]
                    difference = f"{100 * (frequency / item['f_M'] - 1):+.1f}".replace('-', '−')
                    title = (f"{model_name} – mode {source_text}, f = {frequency:.2f} Hz   "
                             f"(Δf = {difference}%, MAC = {row['mac_M' + tag]:.3f})")
                ax.set_title(title, fontsize=10)

        fig.suptitle(f"{KIND_IN_VIETNAMESE[kind]} {count_by_kind[kind]}: mode MATLAB {pair[0]['k']}–{pair[-1]['k']} "
                     f"(trái: đối xứng, phải: phản đối xứng; màu = |U|, nhìn từ phía sau-trái giống view(−55°, 30°))",
                     fontsize=11, fontweight='bold')
        fig.tight_layout(rect=(0, 0, 1, 0.96))
        file_name = f"mode_img_{k // 2 + 1:02d}.png"
        fig.savefig(os.path.join(THIS_FOLDER, file_name), dpi=130)
        plt.close(fig)
        mode_img_figs.append(file_name)
    print('da ghep', len(mode_img_figs), 'hinh mode 3D')
else:
    print('chua co du anh mode 3D: chay hinh_mode_SOLSH190.inp bang ANSYS roi chay lai')


# =============================================================================
# 10. Ghi bang so lieu ra ket_qua_so_sanh.json (tao_bao_cao.py doc file nay)
# =============================================================================
def deflection_at(model_name, case, y_position):
    """Do vong (mm) tai y_position: trung binh hai thanh dam, thanh dam truoc, thanh dam sau."""
    values = results[model_name][case]
    y = results[model_name]['y']
    average = np.interp(y_position, y, (values[0] + values[1]) / 2 * 1000)
    front = np.interp(y_position, y, values[0] * 1000)
    rear = np.interp(y_position, y, values[1] * 1000)
    return float(average), float(front), float(rear)


static = {}
for case in ['design', 'tip']:
    static[case] = {}
    for y_position in [1, 2, 3, 4, 5, 6, 7, 8]:
        static[case][str(y_position)] = {}
        for model_name in MODELS:
            static[case][str(y_position)][model_name] = deflection_at(model_name, case, y_position)

frequency_lists = {}
basis_summary = {}
mesh_summary = {}
for model_name in MODELS:
    frequency_lists[model_name] = [float(value) for value in results[model_name]['f']]
    basis_summary[model_name] = []
    for mode in basis[model_name]:
        basis_summary[model_name].append({'f': mode['f'], 'typ': mode['typ'], 'kind': mode['kind'], 'src': mode['src']})
    mesh_summary[model_name] = {
        'nnode': results[model_name].get('nnode'),    # get(): tra ve None neu khong co khoa (MATLAB khong co luoi)
        'nelem': results[model_name].get('nelem'),
        'nst': len(results[model_name]['y']),
    }

output = {
    'rows': rows,
    'static': static,
    'freqs': frequency_lists,
    'basis': basis_summary,
    'mesh': mesh_summary,
    'mode_figs': fig_modes,
    'mode_img_figs': mode_img_figs,
    'img_plan': img_plan,
}
with open(os.path.join(THIS_FOLDER, 'ket_qua_so_sanh.json'), 'w') as json_file:
    json.dump(output, json_file, indent=1, default=float)
print('xong')
