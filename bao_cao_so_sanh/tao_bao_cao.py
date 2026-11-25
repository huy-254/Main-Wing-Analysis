# -*- coding: utf-8 -*-
"""
tao_bao_cao.py - Sinh bao cao Word so sanh MATLAB - APDL SOLSH190.
Doc ket_qua_so_sanh.json (so_sanh.py) va cac hinh trong thu muc nay.
Chay (can python-docx):  python tao_bao_cao.py
"""
import os, json
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'Bao_cao_so_sanh_canh_chinh_MATLAB_SOLSH190.docx')
D = json.load(open(os.path.join(HERE, 'ket_qua_so_sanh.json'), encoding='utf-8'))
ROWS = D['rows']
BEN = json.load(open(os.path.join(HERE, 'ket_qua_ben.json'), encoding='utf-8'))   # so_sanh_ben.py
BEN_ROW = {}
for ben_row in BEN['table']:
    BEN_ROW[ben_row['name']] = ben_row

T_UD = 0.3/1810/0.63*1000      # mm
TW = 2*T_UD

# ================================================================ dinh dang
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)
TEXT_W = 21.0 - 4.4

def set_font(style, name='Times New Roman', size=12, bold=None, color=None):
    style.font.name = name
    style.font.size = Pt(size)
    if bold is not None: style.font.bold = bold
    if color: style.font.color.rgb = RGBColor.from_string(color)
    rpr = style.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), name)

st = doc.styles
set_font(st['Normal'], size=12)
st['Normal'].paragraph_format.space_after = Pt(6)
st['Normal'].paragraph_format.line_spacing = 1.2
for lvl, size, before in ((1, 15, 18), (2, 13, 12), (3, 12, 10)):
    s = st[f'Heading {lvl}']
    set_font(s, size=size, bold=True, color='1F3864')
    s.font.italic = False
    pf = s.paragraph_format
    pf.space_before, pf.space_after, pf.keep_with_next = Pt(before), Pt(6), True
set_font(st['Title'], size=20, bold=True, color='1F3864')
for nm in ('List Bullet', 'List Number', 'Caption'):
    set_font(st[nm], size=12 if nm != 'Caption' else 10.5)
st['Caption'].font.italic = True
st['Caption'].font.color.rgb = RGBColor(0x40, 0x40, 0x40)


def P(text='', bold_prefix=None, style=None, align=None, italic=False, size=None):
    p = doc.add_paragraph(style=style)
    if bold_prefix:
        r = p.add_run(bold_prefix); r.bold = True
    if text:
        r = p.add_run(text); r.italic = italic
        if size: r.font.size = Pt(size)
    if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == 'j' or align is None: p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def B(text, bold_prefix=None):
    p = P(text, bold_prefix, style='List Bullet')
    return p


def H(text, lvl):
    return doc.add_heading(text, level=lvl)


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement('w:shd')
    sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexcolor)
    tcPr.append(sh)


FIG_N = [0]; TAB_N = [0]


def caption(kind, text):
    if kind == 'Bảng':
        TAB_N[0] += 1; n = TAB_N[0]
    else:
        FIG_N[0] += 1; n = FIG_N[0]
    p = doc.add_paragraph(style='Caption')
    r = p.add_run(f'{kind} {n}. '); r.bold = True
    p.add_run(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if kind == 'Bảng': p.paragraph_format.keep_with_next = True
    return n


def table(headers, rows, widths, cap=None, size=10, align_num=True, bold_last=False):
    if cap: caption('Bảng', cap)
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ''
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(size)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        shade(c, 'DCE6F2')
    for ri, row in enumerate(rows):
        for i, v in enumerate(row):
            c = t.rows[ri + 1].cells[i]; c.text = ''
            r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
            if bold_last and ri == len(rows) - 1: r.bold = True
            isnum = align_num and i > 0 and str(v).replace('.', '').replace(',', '').replace('−', '').replace('+', '').replace('%', '').replace(' ', '').isdigit()
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT if isnum else WD_ALIGN_PARAGRAPH.LEFT
    for row in t.rows:
        tr = row._tr.get_or_add_trPr()
        cs = OxmlElement('w:cantSplit'); tr.append(cs)
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
            for p in row.cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(1); p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.keep_with_next = row is not t.rows[-1]
    hdr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); hdr.append(th)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def fig(path, width_cm, cap):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    return caption('Hình', cap)


def f(x, n=3):
    s = f'{x:.{n}f}'
    return s.replace('-', '−')


def pct(a, b):
    if abs(100*(a/b - 1)) < 0.05: return '0.0%'
    return f'{100*(a/b - 1):+.1f}%'.replace('-', '−')


def toc():
    p = doc.add_paragraph()
    r = p.add_run()
    for tag, txt in (('begin', None), (None, 'TOC \\o "1-3" \\h \\z \\u'), ('separate', None), (None, None), ('end', None)):
        if tag:
            fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), tag); r._r.append(fc)
        elif txt:
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = txt; r._r.append(it)
        else:
            t = OxmlElement('w:t'); t.text = 'Mục lục sẽ hiện sau khi cập nhật trường (F9).'; r._r.append(t)


# ================================================================ so lieu
KIND_VN = {'uon dung': 'Uốn đứng', 'xoan': 'Xoắn', 'uon ngang': 'Uốn ngang'}
cnt = {}
for r in ROWS:
    if r['typ'] == 'S':
        cnt[r['kind']] = cnt.get(r['kind'], 0) + 1
    r['name'] = f"{KIND_VN[r['kind']]} {cnt[r['kind']]}"
    r['sym'] = 'Đối xứng' if r['typ'] == 'S' else 'Phản đối xứng'
row_by = lambda k: ROWS[k - 1]
SD = D['static']

MASS = [  # thanh phan: MATLAB, SOLSH190 (kg)
    ('Vỏ (kể cả dải gia cường)', 53.433, 52.426),
    ('Mũ dầm', 39.741, 39.665),
    ('Side cap (mở rộng mũ dầm)', 3.102, 3.101),
    ('Thành dầm (thành + lõi foam)', 16.508, 16.585),
    ('Rib', 3.208, 3.284),
    ('Foam lấp mép sau', 0.0, 0.069),
]
MT = (115.991, 115.131)       # tong khoi luong: MATLAB, SOLSH190 (kg)
MAC_MIN = min(r['mac_MSO'] for r in ROWS)

# Chi so Tsai-Hill lon nhat cua lop soi (vo, dau KV2)
SKIN_M = max(BEN_ROW['vo_tren']['M_KV2'], BEN_ROW['vo_duoi']['M_KV2'])
SKIN_F = max(BEN_ROW['vo_tren']['F_KV2'], BEN_ROW['vo_duoi']['F_KV2'])
WORST = BEN['worst_fem']


def ben_text(value):
    """Chi so Tsai-Hill 2 chu so thap phan; '–' neu chi tiet khong co o vi tri do."""
    if value <= 0:
        return '–'
    return f(value, 2)

# ================================================================ trang bia
P('BÁO CÁO KỸ THUẬT', align='c', size=13).runs[0].bold = True
doc.add_paragraph('So sánh mô hình dầm tương đương (MATLAB) với mô hình phần tử hữu hạn APDL-SOLSH190 cho cánh chính composite UAV twin boom', style='Title').alignment = WD_ALIGN_PARAGRAPH.CENTER
P('Phân tích tĩnh, khối lượng, tần số riêng, dạng dao động (MAC) và chỉ số phá hủy Tsai–Hill', align='c', italic=True)
P('Ngày lập: 24/11/2026', align='c')
P('Phần mềm: MATLAB R2023b; ANSYS Mechanical APDL 2023 R1; Python 3.13', align='c', size=11)
P()
P('Tóm tắt. ', None).runs[0].bold = True
doc.paragraphs[-1].runs[0].text = ''
P(f'Báo cáo kiểm chứng mô hình dầm tương đương (MATLAB, dầm Euler–Bernoulli 5 bậc tự do/nút) của cánh chính '
  f'composite bằng mô hình phần tử hữu hạn khối nhiều lớp SOLSH190 trong ANSYS APDL. '
  f'Mô hình SOLSH190 khớp MATLAB về khối lượng ({pct(MT[1], MT[0])}), độ võng đầu mút ({pct(SD["design"]["8"]["SOLSH190"][0], SD["design"]["8"]["MATLAB"][0])} với tải thiết kế), '
  f'tần số uốn đứng 1 ({pct(row_by(1)["f_SO"], row_by(1)["f_M"])}) và xoắn 1 ({pct(row_by(11)["f_SO"], row_by(11)["f_M"])}). '
  f'Các mode uốn ngang và mode bậc cao của MATLAB cao hơn SOLSH190 (uốn ngang 3: {pct(row_by(17)["f_SO"], row_by(17)["f_M"])}), phù hợp với giới hạn của dầm Euler–Bernoulli. '
  f'Tất cả 20 mode MATLAB đều ghép được cặp với MAC ≥ {int(MAC_MIN*100)/100:.2f}. '
  f'Chỉ số phá hủy Tsai–Hill dưới tải thiết kế của vỏ, mũ dầm, side cap và dải gia cường gần trùng nhau dọc sải. '
  f'Cả hai mô hình cho chỉ số lớn nhất ở vỏ ngay sau ranh giới KV1/KV2 (y ≈ 1.75 m) và đều vượt 1: '
  f'MATLAB {SKIN_M:.2f}, SOLSH190 {SKIN_F:.2f} (hệ số an toàn {1/SKIN_M:.2f} và {1/SKIN_F:.2f}). '
  f'Ở thành dầm trước MATLAB cho chỉ số cao hơn nhiều vì lấy ứng suất tại cao độ mặt ngoài mũ dầm.')
doc.add_page_break()
P('MỤC LỤC', align='c').runs[0].bold = True
toc()
doc.add_page_break()

# ================================================================ 1
H('1. Mục đích và phạm vi', 1)
H('1.1. Kết cấu cánh chính', 2)
P('Cánh chính là cánh liền của UAV twin boom, profile NACA 4421, sải toàn cánh 16 m. '
  'Dây cung 0.8 m không đổi tới |y| = 1.75 m rồi thuôn tuyến tính còn 0.4 m ở đầu mút; mép trước dịch từ x = 0.80 m về 0.72 m. '
  'Kết cấu hộp hai dầm: dầm trước tại 22.125% và dầm sau tại 71.0625% dây cung (tính từ mép trước). Mỗi dầm gồm thành dầm '
  'sandwich (thành woven / lõi PVC foam / thành woven), mũ dầm trên và dưới (woven + UD), side cap mở rộng mũ dầm về phía giữa hộp. '
  'Vỏ sandwich (woven/foam/woven), cánh ngoài (|y| > 3.75 m) có dải vỏ gia cường 1woven/3UD/1woven chạy trên vùng mũ dầm + side cap. '
  'Cánh có 29 rib sandwich (14 vị trí mỗi bên, và một rib tại y = 0). Ba vùng xếp lớp theo sải: KV1 (|y| < 1.75 m), KV2 (1.75–3.75 m) và cánh ngoài.')
H('1.2. Điều kiện biên và mục tiêu kiểm chứng', 2)
P('Cánh liên kết với thân tại y = ±0.26 m. MATLAB khai báo fix_loc = 0.265 m nhưng với bước lưới dy = 0.02 m nút bị ngàm thực tế là y = ±0.26 m, '
  'trùng vị trí ngàm của mô hình APDL. Ở cả hai mô hình, ngàm được mô hình bằng cách khóa mọi bậc tự do tại hai trạm ngàm (MATLAB: nút dầm; SOLSH190: mọi nút của mặt cắt); '
  'phần cánh giữa hai trạm ngàm vẫn nằm trong mô hình.')
P('Mục tiêu là kiểm chứng mô hình dầm tương đương MATLAB (độ cứng EI, GJ, EI_z, khối lượng, độ lệch tâm khối lượng – tâm cắt) bằng mô hình FEM toàn cánh, '
  'thông qua năm đại lượng: khối lượng theo thành phần, độ võng tĩnh theo sải, tần số riêng, dạng dao động (chỉ số MAC) '
  'và chỉ số phá hủy Tsai–Hill (nghịch đảo hệ số an toàn) dưới tải thiết kế.')
P('Mô hình FEM dùng phần tử khối – vỏ SOLSH190: chiều dày thật được dựng trong hình học. Mỗi "tầng" xếp lớp (woven ngoài, lõi, woven trong, mũ dầm A, B) '
  'là một lớp phần tử khối 8 nút offset từ OML vào trong; thành dầm, foam và rib là khối nằm đúng vào khoảng trống còn lại, nối bằng chung nút, không chồng lấn.')

# ================================================================ 2
H('2. Dữ liệu đầu vào chung', 1)
table(['Thông số', 'Giá trị', 'Ghi chú'], [
    ['Profile', 'NACA 4421', 'upper/lower_point.dat (mm, dây cung 800 mm)'],
    ['Sải toàn cánh / nửa cánh', '16.0 m / 8.0 m', 'trục y dọc sải, x hướng về trước, z hướng lên'],
    ['Dây cung', '0.80 m → 0.40 m', 'không đổi tới |y| = 1.75 m, thuôn tuyến tính tới |y| = 8 m'],
    ['Tọa độ mép trước x_LE', '0.80 m → 0.72 m', 'dịch tuyến tính từ |y| = 1.75 m'],
    ['Vị trí dầm trước / dầm sau', '0.22125c / 0.710625c', 'tâm thành dầm, tính từ mép trước'],
    ['Vùng xếp lớp', 'KV1 < 1.75 m; KV2 ≤ 3.75 m; cánh ngoài', 'cánh ngoài có dải vỏ gia cường'],
    ['Vị trí rib (mm, đối xứng)', '0, 375, 880, 1560, 2645, 3650, 3830, 4220, 4670, 5405, 5845, 6260, 6745, 7700, 7950', '29 rib toàn cánh'],
    ['Vị trí ngàm', 'y = ±0.26 m', 'MATLAB fix_loc = 0.265 m → nút 0.26 m'],
    ['Tải khí động (toàn cánh, tại |y|)', '1200 N tại 0.863; 1.52; 2.63; 3.632; 5.8325; 7.30 m; 2400 N tại 4.2075 m', 'aerodynamic_load.txt'],
    ['Hệ số tải', '× 1.3 × 3.8 / 2 = 2.47', 'chia 2 cho mỗi nửa cánh; tổng 23 712 N/nửa cánh'],
    ['Phân phối tải theo dây cung', '80% dầm trước, 20% dầm sau', 'như M_t trong cross_section_analysis_CW.m'],
    ['Trọng lượng bản thân', '1 g, hướng −z', 'n_load = 1'],
    ['Tải kiểm tra', '100 N tại y = +8 m', 'chia đều cho các nút hai thành dầm'],
], [4.2, 5.6, 6.8], 'Hình học, điều kiện biên và tải')

# ================================================================ 3
H('3. Phương pháp mô hình APDL-SOLSH190', 1)
P('Mô hình được sinh bằng gen_apdl_for_wing_SOLSH190.py theo cùng cách làm với đuôi ngang (gen_apdl_for_DN_v2.py). Các tầng composite dùng SOLSH190 '
  '(khối – vỏ 8 nút, xếp lớp bằng SECTYPE,SHELL); foam thành dầm và foam lấp mép sau dùng SOLID185 với KEYOPT(2) = 2 (biến dạng tăng cường, tránh khóa cắt). '
  'Mọi nút và phần tử được ghi trực tiếp; tất cả liên kết bằng chung nút (không có MPC, CP, CE hay contact).')
H('3.1. Dựng lớp với chiều dày thật (offset từ mặt ngoài)', 2)
B('Bước B1: chia điểm trên OML của mặt cắt theo dây cung (cột k = 0 ở mép trước đến k = M = 54 ở mép sau). Vị trí cột tính lại cho từng trạm vì dây cung thuôn, '
  'trong khi bề rộng mũ dầm, side cap, dải gia cường là kích thước tuyệt đối (m).')
B('Bước B2: tại mỗi điểm OML, offset vào trong theo chiều dày cộng dồn của các tầng, tạo 7 mức nút: 0 = OML; 1 = sau woven ngoài; 2 = sau lõi; 3 = mặt trong vỏ (sau woven trong); '
  '4 = sau tầng A; 5, 6 = sau hai phần tử của tầng B (A chỉ có ở mũ dầm/side cap, B chỉ có ở mũ dầm). Như vậy mặt trong vỏ, mặt trong mũ dầm nằm đúng vị trí hình học thật.')
H('3.2. Phân tầng xếp lớp và lưới có cấu trúc', 2)
B('Vỏ = 3 tầng: woven ngoài / lõi / woven trong. Lõi là F10 (KV2), F5 (cánh ngoài), 1U/F10/1U (KV1) hoặc 3U ở dải gia cường. Mỗi tầng là đúng một lớp phần tử theo chiều dày.')
B('Mũ dầm = tầng A + tầng B: tầng A là các lớp đầu của mũ dầm, có cùng số lớp với side cap (10 hoặc 6 lớp); tầng B là phần còn lại, '
  'được chia đều theo số lớp thành N_CAP_B = 2 phần tử theo chiều dày, nên mũ dầm có 3 phần tử theo chiều dày. '
  'Side cap chỉ có tầng A. Tách như vậy để mũ dầm và side cap là các khối chữ nhật dùng chung nút.')
B('Lưới có cấu trúc: mọi trạm dùng chung một topology cột (55 cột theo dây cung, đường bao kín 109 điểm), nên hai trạm liên tiếp nối trực tiếp thành phần tử khối 8 nút. '
  'Phân loại đoạn theo dây cung (_seg_kind): cap, side, skin_reinf, skin; chiều dày tại một cột lấy theo vùng "mạnh" nhất của hai đoạn kề (RANK: skin < skin_reinf < side < cap).')
H('3.3. Hướng offset, chuyển tiếp chiều dày, xử lý mép sau', 2)
B('Hướng offset: các cột thuộc mũ dầm + side cap offset theo phương thẳng đứng (xuống ở mặt trên, lên ở mặt dưới) để mũ dầm là khối chữ nhật và thành dầm thẳng đứng; '
  'các cột còn lại (kể cả dải gia cường) offset theo pháp tuyến OML, tiếp tuyến tính bằng sai phân trung tâm.')
B('Chuyển tiếp chiều dày: phần tử nằm giữa hai cột có chiều dày khác nhau có hình dạng vát; xếp lớp của nó được co về chiều dày trung bình thật của 4 góc (fit_lam: giảm foam trước, hết foam mới co đều các lớp còn lại). '
  'SOLSH190 tự co giãn chiều dày các lớp SECDATA theo chiều dày thực của phần tử.')
B('Mép sau: ở x/c > 0.5, nếu tổng chiều dày vỏ vượt 0.8 × nửa chiều dày profile thì giảm lõi trước (tối thiểu 20%), chưa đủ thì co đều cả ba tầng. '
  'Khe giữa mặt trong vỏ trên và vỏ dưới từ cột phải co trở ra mép sau được lấp bằng foam SOLID185 (TYPE 9, 0.07 kg).')
H('3.4. Thành dầm và rib dạng khối, nối chung nút', 2)
B('Thành dầm: nằm giữa mặt trong mũ dầm dưới (mức 6, cột M+k) và mặt trong mũ dầm trên (mức 6, cột M−k); chia N_H = 8 hàng theo chiều cao. '
  'Theo bề rộng có N_FOAM_X + 2 = 5 cột phần tử: cột đầu và cuối là thành woven (SOLSH190, TYPE 5/6), 3 cột giữa là foam SOLID185 (TYPE 7). '
  'Thành dầm bắt đầu đúng ở mặt trong mũ dầm nên không chồng lấn, không tính trùng.')
B('Rib: khối dày t_rib theo phương y, chiếm khoảng [y_r − t/2, y_r + t/2] (hai mặt rib là hai trạm lưới). Lưới chính của rib nằm giữa mặt sau dầm trước và mặt trước dầm sau, '
  'dùng chung nút với thành dầm. Thêm các dải phần tử chạy dọc mặt trong vỏ (mức 4–5 và 5–6 ngang tầng B của mũ dầm; mức 3–4 giữa hai side cap) để lấp góc mũ dầm/side cap, dùng các nút "ảo" nội suy chiều dày tầng A, B giữa hai side cap. '
  'Xếp lớp rib xếp theo phương y; khi rib bị chia thành nhiều phần tử theo y, cut_lam cắt đúng phần lớp nằm trong mỗi phần tử.')
B('Hướng phần tử: nếu thể tích âm, script đảo vòng nút nhưng giữ nguyên mặt dưới/mặt trên, nên chiều xếp lớp không đổi.')
H('3.5. Lưới dọc sải, section, hệ tọa độ, chiều xếp lớp', 2)
B('Dọc sải: bước lớn nhất 0.04 m, trạm bắt buộc tại y = 0, ±0.26, ±1.75, ±3.75, ±8, mọi vị trí tải khí động và hai mặt của mỗi rib → 451 trạm.')
B('Tổng: 283 133 nút, 219 648 phần tử, 30 section; 845 823 phương trình. Theo TYPE: vỏ thường 102 600; vỏ vùng dầm/dải gia cường 43 200; mũ dầm 27 000; side cap 1 800; '
  'lớp woven thành dầm trước/sau 7 200 mỗi loại; foam thành dầm 21 600; rib 8 280; foam mép sau 768.')
B('Chiều xếp lớp: lớp 1 của SECDATA nằm ở mặt I-J-K-L của phần tử; script đặt mặt này ở phía OML (mức l) và mặt M-N-O-P ở phía trong (mức l+1), nên các lớp xếp từ ngoài vào trong đúng thứ tự trong xếp lớp.')
B('Hệ tọa độ: LOCAL,11 quay 90° quanh z để trục x cục bộ song song với trục y tổng thể; vỏ, mũ dầm và thành dầm dùng ESYS,11 nên góc 0° của lớp là phương dọc sải, ±45° là lớp woven. '
  'Rib dùng ESYS,0.')
H('3.6. Hình mặt cắt minh họa', 2)
P('Hình do chính script sinh (vẽ các phần tử có một mặt nằm trên trạm, phía +y). Màu theo TYPE.')
fig(os.path.join(PROJ, 'wing_SOLSH190_section_y1005.png'), 14.5, 'SOLSH190 – mặt cắt tại y = 1.005 m (KV1): toàn mặt cắt, chi tiết dầm trước/sau, mép trước, mép sau')
fig(os.path.join(PROJ, 'wing_SOLSH190_section_y5997.png'), 14.5, 'SOLSH190 – mặt cắt tại y = 5.997 m (cánh ngoài, có dải gia cường)')
fig(os.path.join(PROJ, 'wing_SOLSH190_section_y0369.png'), 14.5, 'SOLSH190 – mặt rib y = 0.369 m (mặt trước của rib y = 375 mm)')
H('3.7. Quy mô mô hình và tài nguyên tính toán', 2)
table(['Hạng mục', 'APDL-SOLSH190'], [
    ['Loại phần tử', 'SOLSH190 8 nút (composite) + SOLID185 (foam, KEYOPT 2 = 2)'],
    ['Biểu diễn chiều dày', 'trong hình học: mỗi tầng xếp lớp là một lớp phần tử, offset thật từ OML'],
    ['Mũ dầm, side cap', 'khối riêng (tầng A, B) chung nút với vỏ'],
    ['Thành dầm', 'thành woven + foam khối, giữa hai mặt trong mũ dầm, không chồng lấn'],
    ['Liên kết', 'chung nút; không vật liệu giả'],
    ['Mép sau', 'giảm chiều dày vỏ + foam lấp (SOLID185)'],
    ['Ngàm y = ±0.26 m', 'mọi nút của hai trạm ngàm (FIX_MODE = all)'],
    ['Nút / phần tử / section', '283 133 / 219 648 / 30'],
    ['Số phương trình', '845 823'],
    ['Bộ nhớ solver in-core', '6.4 GB'],
    ['Thời gian (12 nhân)', 'cả lượt chạy (input gốc: tĩnh + modal 12; bổ sung: 2 tĩnh + modal 24): 5.7 phút'],
    ['Khối lượng (kg)', f'{MT[1]:.3f} ({pct(MT[1], MT[0])} so với MATLAB)'],
    ['Ưu điểm', 'hình học thật, không chồng lấn/tính trùng; biểu diễn được thành dầm dày, mép sau, rib; ứng suất theo chiều dày, ứng suất pháp tuyến'],
    ['Nhược điểm', 'lưới lớn; nhiều cảnh báo tỷ lệ cạnh; cần script phức tạp (offset, chuyển tiếp, nút ảo)'],
], [4.2, 12.4], 'Tóm tắt mô hình APDL-SOLSH190', size=9.5, align_num=False)

# ================================================================ 4
H('4. Kiểm tra chất lượng mô hình', 1)
H('4.1. Hình học và Jacobian', 2)
P('Script tính định thức Jacobian tại 8 góc của mọi phần tử khối (tích hỗn hợp ba cạnh tại mỗi góc) và dừng nếu có giá trị ≤ 0; '
  'input hiện tại vượt qua kiểm tra (mọi Jacobian góc > 0). Thể tích tính bằng 5 tứ diện.')
H('4.2. Lỗi và cảnh báo của ANSYS', 2)
table(['Lỗi', 'Cảnh báo hình dạng', 'Ghi chú'], [
    ['0', '122 508 / 219 648 (55.8%) tỷ lệ cạnh > 20; trung vị 71, lớn nhất 435', 'Theo TYPE: vỏ thường 70 208/102 600 (lớn nhất 435); vỏ vùng dầm 35 076/43 200 (≤ 80); mũ dầm 9 920/27 000 (≤ 38); side cap 428/1 800; lớp woven thành dầm sau 6 400/7 200 (≤ 25); foam mép sau 476/768 (≤ 86); lớp woven thành dầm trước, foam thành dầm, rib: 0.'],
], [1.2, 5.6, 9.8], 'Lỗi và cảnh báo của ANSYS (APDL-SOLSH190)', size=9.5)
P('Tỷ lệ cạnh cao là hệ quả trực tiếp của việc mỗi tầng woven 0.53 mm là một lớp phần tử trong khi kích thước trong mặt phẳng là 20–40 mm. '
  'SOLSH190 là phần tử khối – vỏ được thiết kế cho kết cấu mỏng (dùng giả thiết biến dạng cắt ngang như shell, không bị khóa cắt khi phần tử mỏng), '
  'nên các cảnh báo này không làm sai kết quả tĩnh và dao động; mọi phần tử có tỷ lệ cạnh > 150 (548 phần tử, lớn nhất 435) nằm ở x/c ≈ 0.987, nơi vỏ bị co mỏng sát mép sau. '
  'ANSYS còn gợi ý KEYOPT(2) = 3 cho SOLID185 (chỉ là gợi ý, không phải cảnh báo).')
H('4.3. Khối lượng theo TYPE so với tính toán', 2)
table(['TYPE', 'Nội dung', 'ANSYS (kg)'], [
    ['1', 'Vỏ thường (3 tầng)', '42.654'],
    ['2', 'Vỏ vùng dầm / dải gia cường', '9.772'],
    ['3', 'Mũ dầm (tầng A, B)', '39.665'],
    ['4', 'Side cap', '3.101'],
    ['5', 'Lớp woven thành dầm trước', '9.624'],
    ['6', 'Lớp woven thành dầm sau', '4.713'],
    ['7', 'Foam thành dầm', '2.249'],
    ['8', 'Rib', '3.284'],
    ['9', 'Foam lấp mép sau', '0.069'],
    ['', 'Tổng (IRLF,−1)', '115.131'],
], [1.6, 7.0, 3.0], 'Khối lượng theo TYPE do ANSYS tính (PRECISE MASS SUMMARY)', size=9.5, bold_last=True)
P('Khối lượng theo TYPE của ANSYS trùng với giá trị script Python tính trước khi ghi input (115.131 kg), '
  'chứng tỏ vật liệu và section được gán đúng cho từng TYPE (đây là phép kiểm tra đã phát hiện lỗi gán nhầm foam ở đuôi ngang trước đây).')

# ================================================================ 5
H('5. Điều kiện biên, tải và phân tích', 1)
table(['Hạng mục', 'MATLAB', 'APDL-SOLSH190'], [
    ['Ngàm', 'khóa 5 bậc tự do tại nút y = ±0.26 m', 'D,ALL,ALL mọi nút của mặt cắt tại y = ±0.26 m (FIX_MODE = all)'],
    ['Trọng lượng bản thân', '−n_load·9.81·m(y) trong lực cắt F_shear', 'ACEL,0,0,9.81'],
    ['Tải khí động', 'lực nút từ hiệu F_shear, mômen xoắn từ M_t (80/20 quanh tâm cắt x_E, cánh tay đòn theo tọa độ x thật của điểm đặt lực); đã trừ phản lực F_react, M_react', 'lực nút chia đều cho 54 nút mỗi thành dầm (80/20) tại đúng trạm đặt tải'],
    ['Tải 100 N', 'lực tại nút y = 8 m + mômen 100·(x_E − 0.466)·c', '100 N chia đều 108 nút hai thành dầm (bổ sung)'],
    ['Phân tích tĩnh', 'tuyến tính, K·d = F', 'tuyến tính, sparse direct'],
    ['Phân tích dao động', 'eig(K, M), 20 mode', 'Block Lanczos 12 mode (gốc) + 24 mode (bổ sung)'],
    ['Đại lượng so sánh', 'w, φ, u tại trục đàn hồi → quy về hai thành dầm', 'UX, UZ trung bình nút thành dầm (cả foam)'],
], [3.0, 6.2, 7.4], 'Điều kiện biên, tải và loại phân tích', size=9)
P('Ghi chú về ngàm: ở cả hai mô hình, hai nửa cánh bị tách hoàn toàn tại trạm ngàm, nên mỗi tần số xuất hiện hai lần (cặp đối xứng / phản đối xứng trùng nhau, '
  'ở SOLSH190 chênh nhau không quá 0.003%).')
P('Mômen xoắn khí động trong MATLAB: cánh tay đòn của mỗi lực khí động phía ngoài mặt cắt được tính bằng tọa độ x thật của điểm đặt lực, '
  'tức dùng mép trước và dây cung tại chính vị trí lực, giống như lực được đặt trong mô hình SOLSH190. Bản trước dùng dây cung của mặt cắt đang xét cho mọi lực phía ngoài, '
  'nên mômen xoắn khí động tại ngàm lớn hơn khoảng 1.5 lần và góc xoắn đầu mút dưới tải thiết kế là −0.306° (nay −0.192°).')
P('Quy đổi kết quả dầm về điểm so sánh: độ võng tại thành dầm trước UZ_f = w + φ·(x_E − 0.22125)·c, tại thành dầm sau UZ_r = w + φ·(x_E − 0.710625)·c, '
  'chuyển vị theo dây cung UX = u (φ > 0 khi mép trước đi lên). Ở mô hình APDL lấy trung bình UZ của mọi nút thành dầm ở mỗi trạm và trung bình UX của hai thành dầm. '
  'Độ võng trình bày là trung bình hai thành dầm, góc xoắn = (UZ_f − UZ_r)/((0.710625 − 0.22125)·c).')

# ================================================================ 6
H('6. Kết quả so sánh MATLAB – APDL-SOLSH190', 1)
H('6.1. Khối lượng', 2)
rows = [[n, f(a), f(c), pct(c, a) if a else '–'] for n, a, c in MASS]
rows.append(['Tổng', f(MT[0]), f(MT[1]), pct(MT[1], MT[0])])
table(['Thành phần', 'MATLAB (kg)', 'SOLSH190 (kg)', 'SOLSH190 / MATLAB'], rows,
      [5.6, 3.0, 3.0, 3.4], 'Khối lượng toàn cánh theo thành phần', size=9.5, bold_last=True)
P('SOLSH190 tách theo TYPE (mục 4.3). MATLAB tách bằng cách lặp lại đúng các số hạng của m_airfoil (dòng 324–337 của cross_section_analysis_CW.m); tổng các thành phần trùng tổng 115.991 kg.')
H('6.2. Độ võng tĩnh theo vị trí dọc sải', 2)
for case, ttl in (('design', 'tải thiết kế (khí động × 2.47, trừ trọng lượng 1g)'), ('tip', 'lực 100 N tại đầu mút y = +8 m')):
    rr = []
    for yy in ('1', '2', '3', '4', '5', '6', '7', '8'):
        v = SD[case][yy]
        nd = 2 if case == 'design' else 3
        rr.append([f'{yy}.0', f(v['MATLAB'][0], nd), f(v['SOLSH190'][0], nd), pct(v['SOLSH190'][0], v['MATLAB'][0])])
    table(['y (m)', 'MATLAB (mm)', 'SOLSH190 (mm)', 'SOLSH190 / MATLAB'], rr,
          [2.0, 3.2, 3.2, 3.6], f'Độ võng trung bình hai thành dầm – {ttl}', size=9.5)
fig(os.path.join(HERE, 'static_design.png'), 16.0, 'Độ võng và góc xoắn theo sải – tải thiết kế')
fig(os.path.join(HERE, 'static_tip.png'), 16.0, 'Độ võng và góc xoắn theo sải – lực 100 N đầu mút')
P('Kiểm tra chéo: độ võng tải thiết kế SOLSH190 tại 13 vị trí trong wing_SOLSH190_results.txt trùng kết quả giải lại trong lượt bổ sung. '
  'Góc xoắn đầu mút dưới 100 N: MATLAB −0.0102°, SOLSH190 −0.0111°; dưới tải thiết kế: −0.192° và −0.190°.')
H('6.3. Tần số riêng', 2)
rr = []
for r in ROWS:
    rr.append([str(r['k']), r['name'], r['sym'], f(r['f_M']), f(r['f_SO']), pct(r['f_SO'], r['f_M'])])
table(['#', 'Dạng dao động', 'Kiểu', 'MATLAB (Hz)', 'SOLSH190 (Hz)', 'SOLSH190 / MATLAB'], rr,
      [0.9, 3.0, 3.0, 2.8, 2.8, 3.2], 'Tần số riêng theo cặp mode đã ghép (thứ tự theo MATLAB)', size=9)
P('Cột "Kiểu" là kiểu đối xứng qua y = 0 sau khi đưa về cơ sở đối xứng / phản đối xứng (mục 6.4). Dạng dao động lấy theo tỷ lệ động năng của MATLAB '
  '(nhóm bậc tự do chiếm ưu thế: uốn đứng w, w′; xoắn φ; uốn ngang u, u′). Mode MATLAB bậc 11–12 (xoắn 1) có 81% động năng xoắn và 19% uốn đứng.')
fig(os.path.join(HERE, 'tan_so.png'), 16.0, 'Tần số riêng của 20 mode MATLAB và mode SOLSH190 ghép tương ứng')
H('6.4. Dạng dao động và MAC', 2)
P('Véc-tơ dạng dao động. Mỗi mode của mỗi mô hình được quy về ba hàm theo sải: UZ_f(y), UZ_r(y), UX(y) (mục 5), nội suy tuyến tính lên lưới chung y = −8 … 8 m bước 0.05 m (321 điểm), '
  'rồi ghép thành véc-tơ φ = [UZ_f; UZ_r; UX] dài 963 phần tử. Cả hai nửa cánh đều có mặt trong véc-tơ.')
P('Cơ sở đối xứng: Khi hai tần số liền nhau chênh dưới 0.1%, solver trả về tổ hợp tùy ý của hai mode (ví dụ chỉ một nửa cánh dao động). '
  'Với mỗi cụm như vậy, véc-tơ được chiếu lên phần đối xứng (φ + Rφ)/2 và phản đối xứng (φ − Rφ)/2, với R là phép phản chiếu y → −y (UZ, UX giữ dấu), '
  'rồi lấy cơ sở trực chuẩn bằng SVD; tần số gán cho véc-tơ mới là tần số của mode gốc gần nó nhất. Cách làm giống phần tách mode trong coupled_beam.m.')
P('Ghép cặp: với mỗi mode MATLAB (20 mode), chọn mode SOLSH190 cùng kiểu đối xứng có MAC lớn nhất, chưa được ghép trước đó, và chỉ chấp nhận khi MAC > 0.5. '
  'Kết quả: cả 20 mode đều ghép được.')
P('Trong ma trận MAC dưới đây, trục tung là MATLAB với tần số tăng dần từ dưới lên; các cột SOLSH190 '
  'được sắp lại sao cho mode ghép với hàng thứ i nằm ở cột thứ i (ghép theo MAC giảm dần, mỗi mode dùng một lần), '
  'các mode không ghép được bỏ khỏi hình. Vì vậy các ô MAC cao nằm trên đường chéo, còn nhãn tần số trên trục hoành không nhất thiết tăng đơn điệu.')
rr = [[str(r['k']), r['name'], r['sym'], f(r['mac_MSO'])] for r in ROWS]
table(['#', 'Dạng dao động', 'Kiểu', 'MAC MATLAB–SOLSH190'], rr,
      [1.0, 4.0, 3.6, 4.2], 'Chỉ số MAC của các cặp mode', size=9.5)
fig(os.path.join(HERE, 'mac_MATLAB_SOLSH190.png'), 12.5, 'Ma trận MAC MATLAB – SOLSH190 (số ghi trên ô khi MAC ≥ 0.5)')
P('Hình so sánh từng cặp mode. Mỗi hình gồm cặp đối xứng (hàng trên) và phản đối xứng (hàng dưới) của một dạng dao động; ba cột là độ võng trung bình w, góc xoắn và chuyển vị uốn ngang u theo sải. '
  'Mode SOLSH190 được nhân với hệ số bình phương tối thiểu để cùng dấu và cùng biên độ với mode MATLAB, sau đó cả hai chia cho biên độ lớn nhất của véc-tơ MATLAB.')
P('Mỗi dạng dao động được minh họa thêm bằng hình 3D (màu theo độ lớn chuyển vị |U|, cùng góc nhìn từ phía sau-trái). Hình MATLAB là hình main_CW vẽ từ (w, φ, u) của dầm trên bề mặt phẳng mép trước – mép sau. '
  'Hình SOLSH190 được ANSYS chụp ở chế độ batch từ file .rst (PLNSOL,U,SUM, nền trắng, /VIEW tương đương view(−55°, 30°) của MATLAB). '
  'Với cặp mode trùng tần số (ví dụ SOLSH190 mode 1 và 2), hình là tổ hợp tuyến tính của hai mode gốc (lệnh LCDEF/LCFACT/LCOPER) đúng bằng véc-tơ đối xứng hoặc phản đối xứng dùng để tính MAC, '
  'và dấu được chọn cùng chiều với mode MATLAB. Biên độ hiển thị do từng chương trình tự chọn nên chỉ so sánh hình dạng, không so sánh độ lớn.')
for i, fn in enumerate(D['mode_figs']):
    r = ROWS[2*i]
    if i < len(D.get('mode_img_figs', [])):
        fig(os.path.join(HERE, D['mode_img_figs'][i]), 16.0, f'{r["name"]} – hình dạng dao động 3D: MATLAB (trên), SOLSH190 (dưới); trái đối xứng, phải phản đối xứng')
    fig(os.path.join(HERE, fn), 16.0, f'{r["name"]} (mode MATLAB {r["k"]}–{r["k"]+1}): MATLAB {r["f_M"]:.2f} Hz, SOLSH190 {r["f_SO"]:.2f} Hz')

H('6.5. Chỉ số phá hủy Tsai–Hill', 2)
P('MATLAB: cross_section_analysis_CW.m tính biến dạng của từng chi tiết từ ứng suất uốn và dòng cắt tại mặt cắt, rồi chỉ số Tsai–Hill của từng lớp '
  '(THstrength.m). SOLSH190: giải lại bài toán tĩnh dưới tải thiết kế, cùng điều kiện ngàm, với KEYOPT(8) = 1 để lưu ứng suất mọi lớp (macro do_ben_SOLSH190.mac, khoảng 2 phút với 12 nhân). '
  'Ứng suất S1 (dọc sợi), S2 (ngang sợi), S12 (cắt) lấy ở giữa chiều dày lớp, tại tâm phần tử, trong hệ trục lớp (RSYS,LSYS); '
  'giá trị ETABLE đã được đối chiếu với PRESOL (trung bình 8 nút) ở một số phần tử. Chỉ số Tsai–Hill tính bằng cùng công thức và cùng giới hạn bền với MATLAB '
  f'(lớp UD: kéo/nén dọc {BEN["strength_UD_MPa"][0]:.0f}/{BEN["strength_UD_MPa"][1]:.0f} MPa, kéo/nén ngang {BEN["strength_UD_MPa"][2]:.1f}/{BEN["strength_UD_MPa"][3]:.1f} MPa, '
  f'cắt {BEN["strength_UD_MPa"][4]:.1f} MPa; foam: {BEN["strength_core_MPa"][0]:.1f} MPa, cắt {BEN["strength_core_MPa"][4]:.2f} MPa). '
  'Hệ số an toàn bằng nghịch đảo chỉ số: 1/f.')
P('Cách gom kết quả SOLSH190: lấy giá trị lớn nhất trên các phần tử cùng chi tiết tại mỗi cột phần tử theo sải (bước khoảng 0.04 m, gộp hai nửa cánh). '
  'Mặt trên / mặt dưới tách theo đường trung bình của profile, dầm trước / dầm sau tách tại 0.466c. '
  'Phần tử TYPE 2 (vỏ vùng dầm) ở cánh giữa có cùng xếp lớp với vỏ nên được gộp vào vỏ; ở cánh ngoài (|y| > 3.75 m) là dải gia cường. '
  'Foam thành dầm và foam lấp mép sau (SOLID185) không tính. Đoạn |y| < 0.265 m nằm giữa hai mặt cắt ngàm nên không so sánh.')
rr = []
for t in BEN['table']:
    rr.append([t['label'], ben_text(t['M_root']) if t['M_root'] > 0 else '–', ben_text(t['F_root']) if t['M_root'] > 0 else '–',
               ben_text(t['M_y1']) if t['M_y1'] > 0 else '–', ben_text(t['F_y1']) if t['M_y1'] > 0 else '–',
               ben_text(t['M_KV2']), f"{ben_text(t['F_KV2'])} ({t['F_KV2_y']:.2f})" if t['F_KV2'] > 0 else '–',
               ben_text(t['M_ngoai']), f"{ben_text(t['F_ngoai'])} ({t['F_ngoai_y']:.2f})"])
table(['Chi tiết', f'M y={BEN["y_root"]:.1f}', f'SO y={BEN["y_root"]:.1f}', 'M y=1.0', 'SO y=1.0',
       'M lớn nhất KV2', 'SO lớn nhất KV2 (y)', 'M lớn nhất cánh ngoài', 'SO lớn nhất cánh ngoài (y)'], rr,
      [3.5, 1.3, 1.3, 1.3, 1.3, 1.6, 2.1, 1.7, 2.5],
      'Chỉ số Tsai–Hill lớn nhất theo các lớp sợi (M: MATLAB, SO: SOLSH190). Số trong ngoặc là vị trí |y| (m) của giá trị lớn nhất SOLSH190; '
      'giá trị lớn nhất MATLAB luôn ở đầu vùng (y = 1.76 m và 3.76 m)', size=8)
O = BEN['other']
table(['Chi tiết', 'MATLAB', 'SOLSH190', 'Vị trí SOLSH190'], [
    ['Rib, lớp sợi', f(O['rib_soi']['M']), f(O['rib_soi']['F']), f"|y| = {O['rib_soi']['F_y']:.3f} m"],
    ['Lõi foam của vỏ', f(O['vo_loi_foam']['M']), f(O['vo_loi_foam']['F']), f"|y| = {O['vo_loi_foam']['F_y']:.2f} m"],
    ['Lõi foam của rib', f(O['rib_loi_foam']['M']), f(O['rib_loi_foam']['F']), f"|y| = {O['rib_loi_foam']['F_y']:.3f} m"],
], [5.0, 2.6, 2.6, 3.4], f'Chỉ số Tsai–Hill lớn nhất của rib và các lớp lõi foam (|y| ≥ {BEN["y_root"]:.1f} m)', size=9.5)
fig(os.path.join(HERE, 'ben_Tsai_Hill.png'), 16.0, 'Chỉ số Tsai–Hill lớn nhất theo các lớp sợi dọc sải – MATLAB và SOLSH190 (mặt trên: nét liền, mặt dưới: nét đứt)')

# ================================================================ 7
H('7. Nhận xét', 1)
H('7.1. Uốn đứng', 2)
ud = [r for r in ROWS if r['kind'] == 'uon dung' and r['typ'] == 'S']
P('Tần số uốn đứng (mode đối xứng): ' + '; '.join(f"{r['name']}: MATLAB {r['f_M']:.2f} Hz, SOLSH190 {pct(r['f_SO'], r['f_M'])}" for r in ud) + '.')
B(f'SOLSH190 khớp MATLAB ở uốn đứng 1 ({pct(row_by(1)["f_SO"], row_by(1)["f_M"])}) và ở độ võng đầu mút: '
  f'{pct(SD["tip"]["8"]["SOLSH190"][0], SD["tip"]["8"]["MATLAB"][0])} (100 N) và {pct(SD["design"]["8"]["SOLSH190"][0], SD["design"]["8"]["MATLAB"][0])} (tải thiết kế). '
  'Độ cứng EI và phân bố khối lượng của mô hình dầm vì vậy được kiểm chứng tốt.')
B('Gần gốc (y = 1–2 m) SOLSH190 võng ít hơn MATLAB 1–3%, giá trị tuyệt đối rất nhỏ (≈ 0.3 mm tại y = 1 m dưới tải thiết kế). '
  'Khi ngàm toàn bộ mặt cắt, vỏ tại trạm ngàm không còn biến dạng tự do như khi chỉ ngàm vùng thành dầm (khi đó SOLSH190 võng hơn MATLAB 6–7% ở y = 1 m).')
B(f'Chênh lệch tần số thay đổi theo bậc mode ({pct(row_by(1)["f_SO"], row_by(1)["f_M"])} ở uốn đứng 1 → {pct(row_by(15)["f_SO"], row_by(15)["f_M"])} ở uốn đứng 5): FEM càng mềm hơn dầm ở mode bậc cao, đúng xu hướng của dầm Euler–Bernoulli: bỏ qua biến dạng cắt và quán tính xoay nên càng cứng ở mode bậc cao, khi bước sóng ngắn lại so với chiều cao hộp. '
  'Có thể kiểm tra bằng TimoshenkoBeam.m (đã có sẵn trong coupled_beam.m nhưng đang tắt).')
H('7.2. Xoắn', 2)
B(f"Xoắn 1: MATLAB {row_by(11)['f_M']:.2f} Hz, SOLSH190 {row_by(11)['f_SO']:.2f}/{row_by(12)['f_SO']:.2f} Hz ({pct(row_by(11)['f_SO'], row_by(11)['f_M'])}). "
  f"Xoắn 2: MATLAB {row_by(19)['f_M']:.2f} Hz, SOLSH190 {pct(row_by(19)['f_SO'], row_by(19)['f_M'])}.")
B(f'SOLSH190 xác nhận GJ của MATLAB (tính từ dòng chảy cắt hộp ba ô, đã sửa theo đường dòng cắt) và mômen quán tính khối lượng I_m: '
  f'chênh lệch ≤ {max(abs(100*(r["f_SO"]/r["f_M"]-1)) for r in ROWS if r["kind"] == "xoan"):.1f}% ở cả hai mode xoắn, MAC ≥ {int(min(r["mac_MSO"] for r in ROWS if r["kind"] == "xoan")*100)/100:.2f}.')
B('Góc xoắn đầu mút dưới tải thiết kế khớp MATLAB (−0.192° và −0.190°) sau khi sửa cánh tay đòn mômen xoắn khí động (mục 5); dưới 100 N đầu mút: −0.0102° và −0.0111°. '
  'Ở cánh ngoài (y > 4 m) hai đường góc xoắn gần trùng nhau.')
B('Ở cánh giữa, mô hình FEM có một vùng lồi lên (góc xoắn dương, tới khoảng +0.27° dưới tải thiết kế) quanh y ≈ 2 m, ngay sau chỗ dây cung bắt đầu thuôn (y = 1.75 m) và mũ dầm trước giảm từ 27 xuống 14/11 nhóm lớp; '
  'vùng lồi lên này cũng xuất hiện dưới lực 100 N đầu mút. '
  'Đây là hiệu ứng uốn lệch giữa hai dầm có độ cứng rất khác nhau, mặt cắt không còn cứng tuyệt đối. Mô hình dầm với mặt cắt cứng không thể hiện được hiệu ứng này. '
  'Vì vậy góc xoắn tĩnh ở cánh giữa chỉ dùng để so sánh định tính.')
H('7.3. Uốn ngang', 2)
un = [r for r in ROWS if r['kind'] == 'uon ngang']
P('; '.join(f"{r['name']} ({'S' if r['typ']=='S' else 'A'}): MATLAB {r['f_M']:.2f} Hz, SOLSH190 {pct(r['f_SO'], r['f_M'])}" for r in un) + '.')
B(f'MATLAB cao hơn SOLSH190 và chênh lệch tăng nhanh theo bậc ({pct(row_by(3)["f_M"], row_by(3)["f_SO"])} → {pct(row_by(9)["f_M"], row_by(9)["f_SO"])} → {pct(row_by(17)["f_M"], row_by(17)["f_SO"])}), nhanh hơn nhiều so với các mode uốn đứng cùng dải tần. '
  'Xu hướng này chỉ ra giới hạn của mô hình dầm theo phương uốn ngang.')
B('Theo phương dây cung, "chiều cao" của mặt cắt là cả dây cung (0.4–0.8 m), lớn so với nửa bước sóng của mode bậc cao, nên biến dạng cắt trong mặt phẳng cánh (vỏ ±45° và thành dầm làm việc như tấm chịu cắt) đáng kể. '
  'Dầm Euler–Bernoulli bỏ qua thành phần này nên quá cứng. Nên dùng Timoshenko cho cả phương uốn ngang (kGA theo phương x) khi cần các mode uốn ngang bậc 2 trở lên.')
B(f'Ở SOLSH190, uốn ngang 3 ({row_by(17)["f_SO"]:.2f} Hz) nằm dưới uốn đứng 5 ({row_by(15)["f_SO"]:.2f} Hz), ngược thứ tự của MATLAB; việc ghép cặp theo MAC không bị ảnh hưởng.')
H('7.4. Khối lượng', 2)
B(f'SOLSH190 – MATLAB: {pct(MT[1], MT[0])} (−0.86 kg). Vỏ nhẹ hơn 1.0 kg do vỏ được co mỏng ở mép sau (thay một phần bằng foam 60 kg/m³) và chu vi mặt trong nhỏ hơn OML; '
  'rib nặng hơn 0.08 kg do có thêm dải phần tử lấp góc mũ dầm. Mũ dầm, side cap, thành dầm khớp trong 0.5%. Đây là xác nhận độc lập cho lần sửa lỗi tính trùng thành dầm trong MATLAB.')
H('7.5. Độ bền (chỉ số Tsai–Hill)', 2)
AGREE_NAMES = ['vo_tren', 'vo_duoi', 'mu_dam_truoc_tren', 'mu_dam_truoc_duoi', 'mu_dam_sau_tren', 'mu_dam_sau_duoi',
               'side_cap_truoc_tren', 'side_cap_truoc_duoi', 'side_cap_sau_tren', 'side_cap_sau_duoi']
agree_differences = []
for name in AGREE_NAMES:
    agree_differences.append(100*(BEN_ROW[name]['F_y1']/BEN_ROW[name]['M_y1'] - 1))
B(f'Vỏ, mũ dầm, side cap và dải gia cường: hai mô hình cho đường chỉ số gần trùng nhau dọc sải; tại y = 1.0 m chênh lệch '
  f'từ {min(agree_differences):+.0f}% đến {max(agree_differences):+.0f}%. '.replace('-', '−') +
  'Chênh lệch lớn nhất là mũ dầm sau trên và side cap sau trên (SOLSH190 cao hơn 16–17%); các chi tiết còn lại trong khoảng ±5%. '
  'Như vậy ứng suất uốn và dòng cắt mà mô hình dầm phân cho các chi tiết này được SOLSH190 xác nhận. '
  f'Sát ngàm (|y| < khoảng 0.5 m), vỏ của SOLSH190 thấp hơn MATLAB (y = {BEN["y_root"]:.1f} m: vỏ trên {f(BEN_ROW["vo_tren"]["F_root"], 2)} so với {f(BEN_ROW["vo_tren"]["M_root"], 2)}) '
  'có thể do toàn bộ mặt cắt ngàm bị khóa nên vỏ gần đó không biến dạng tự do; mũ dầm và side cap dầm trước vẫn khớp.')
B(f'Giá trị lớn nhất của cả hai mô hình nằm ở vỏ ngay sau ranh giới KV1/KV2 (y = 1.75 m), nơi vỏ bỏ hai lớp UD 0° (1woven/1UD/F10/1UD/1woven → 1woven/F10/1woven) '
  f'và mũ dầm trước giảm từ 27 xuống 14/11 nhóm lớp: MATLAB {SKIN_M:.2f} (y = 1.76 m), SOLSH190 {SKIN_F:.2f} (y ≈ 1.8 m). '
  f'Cả hai đều vượt 1, tức hệ số an toàn {1/SKIN_M:.2f} và {1/SKIN_F:.2f} dưới tải thiết kế. '
  f'Ở SOLSH190, lớp quyết định là lớp −45° của woven ngoài vỏ trên (phần tử {WORST["element"]}, lớp {WORST["layer"]}): '
  'ứng suất nén dọc sải của vỏ tạo ứng suất cắt S12 ≈ 66 MPa trong hệ trục lớp, vượt bền cắt 52.6 MPa của lớp UD. '
  'Lưu ý: woven được mô hình bằng hai lớp UD ±45° với bền cắt của UD, nên kết luận này có thể thiên về an toàn so với vải dệt thật; '
  'dù vậy vùng đầu KV2 vẫn là vị trí cần xem lại xếp lớp.')
B('Ngay sau các chỗ đổi xếp lớp (y = 1.75 m và 3.75 m), SOLSH190 cao hơn MATLAB: vỏ đầu KV2 cao hơn 11–14%, và có các đỉnh cục bộ hẹp tại y ≈ 3.75 m '
  '(vỏ tới khoảng 0.9, dải gia cường và mũ dầm trước khoảng 0.8, so với 0.5–0.6 của MATLAB). '
  'Trong FEM, mọi lớp được cắt bỏ tại cùng một mặt cắt nên tải phải phân bố lại giữa mũ dầm, side cap và vỏ trên một đoạn khoảng 0.5 m; '
  'mô hình dầm giả thiết mặt cắt phẳng nên chỉ nhảy bậc. Trên kết cấu thật, các lớp được cắt so le nên đỉnh sẽ thấp hơn.')
B(f'Thành dầm trước: MATLAB cao hơn SOLSH190 nhiều (y = 1.0 m: {f(BEN_ROW["thanh_dam_truoc_tren"]["M_y1"], 2)} so với {f(BEN_ROW["thanh_dam_truoc_tren"]["F_y1"], 2)}). '
  'MATLAB tính ứng suất của thành dầm tại spar_1_up, tức mặt ngoài mũ dầm (sát mặt trong vỏ). Trong SOLSH190, phần thành dầm nằm cạnh mũ dầm là side cap (TYPE 4), '
  f'còn thanh thành dầm (TYPE 5) chỉ chạy giữa mặt trong hai mũ dầm. Ở KV1, mũ dầm trước dày 164 lớp ≈ {164*T_UD:.0f} mm, nên đầu thanh thành dầm gần trục trung hòa hơn nhiều. '
  f'Chỉ số của side cap SOLSH190 khớp với "thành dầm" MATLAB (y = 1.0 m: {f(BEN_ROW["side_cap_truoc_tren"]["F_y1"], 2)} so với {f(BEN_ROW["thanh_dam_truoc_tren"]["M_y1"], 2)}). '
  'Chênh lệch giảm dần ở KV2 và cánh ngoài, nơi mũ dầm mỏng hơn; ở dầm sau (mũ dầm 20–26 lớp, khoảng 5–7 mm) hai mô hình gần nhau hơn. '
  'Nếu muốn đánh giá riêng tấm thành dầm, MATLAB nên lấy ứng suất tại foam_1_up / foam_1_low.')
B(f'Rib: SOLSH190 cho {f(O["rib_soi"]["F"], 2)} (rib y = {O["rib_soi"]["F_y"]:.3f} m), MATLAB {f(O["rib_soi"]["M"], 2)}. '
  'Giá trị lớn nằm ở dải rib dán vào mặt trong vỏ, dải này chịu chung biến dạng của vỏ; mô hình rib trong MATLAB chỉ xét nén ép và cắt của tấm rib nên không có thành phần này. '
  f'Tương tự cho lõi foam của rib ({f(O["rib_loi_foam"]["F"], 2)} so với {f(O["rib_loi_foam"]["M"], 2)}). '
  f'Lõi foam của vỏ gần nhau: {f(O["vo_loi_foam"]["F"], 2)} và {f(O["vo_loi_foam"]["M"], 2)}.')

# ================================================================ 8
H('8. Hạn chế và việc tiếp theo', 1)
for a, b in [
    ('Độ cứng xoắn. ', 'Có thể thêm thí nghiệm số mômen xoắn thuần (cặp lực tại hai thành dầm ở đầu mút) cho MATLAB và SOLSH190 để tách GJ khỏi vị trí tâm cắt.'),
    ('Mô hình dầm. ', 'Dầm Euler–Bernoulli cho sai số tăng dần ở mode bậc cao và uốn ngang. Nên bật TimoshenkoBeam.m và đánh giá lại; xem xét kGA theo phương uốn ngang.'),
    ('Véc-tơ MAC. ', 'Chỉ dùng điểm tại hai thành dầm (UZ trước/sau, UX), nên MAC không nhạy với biến dạng mặt cắt và ít nhạy với mức ghép uốn – xoắn. Có thể bổ sung điểm ở mép trước, mép sau và thành phần UY.'),
    ('Phi tuyến hình học. ', 'Phân tích tĩnh tuyến tính; với độ võng đầu mút ≈ 1.4 m (17.5% nửa sải) dưới tải thiết kế, cần NLGEOM,ON khi đánh giá ứng suất và bền.'),
    ('Lưới SOLSH190. ', 'Chưa khảo sát hội tụ lưới (dy 0.04 → 0.02 m, N_H, N_FOAM_X). Có thể thử KEYOPT(2) = 3 cho SOLID185 theo gợi ý của ANSYS.'),
    ('Độ bền. ', 'Mới so sánh chỉ số Tsai–Hill trong mặt phẳng lớp dưới tải thiết kế, phân tích tuyến tính. Chưa so ổn định (mất ổn định cục bộ vỏ, rib), '
     'lõi foam thành dầm, ứng suất pháp tuyến và cắt liên lớp tại góc mũ dầm – thành dầm; tải đặt bằng lực nút trên thành dầm nên ứng suất SOLSH190 ngay tại điểm đặt lực mang tính cục bộ.'),
    ('Đuôi ngang. ', 'cross_section_analysis_DN.m có cùng lỗi tính trùng thành dầm, chưa sửa.')]:
    B(b, a)

doc.save(OUT)
print('Da ghi', OUT)
