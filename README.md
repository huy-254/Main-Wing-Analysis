# Phân tích kết cấu cánh chính UAV (composite)

Bộ script MATLAB tính kết cấu cánh chính composite của UAV theo mô hình **dầm tương đương**:

1. Với từng mặt cắt dọc sải cánh: tính đặc trưng mặt cắt (khối lượng, EI, GJ, mômen quán tính khối lượng Im, tâm cứng x_E, trọng tâm xc), nội lực và hệ số an toàn (HSAT) của từng chi tiết.
2. Ghép các mặt cắt thành dầm uốn–xoắn liên kết cho **toàn bộ cánh** (đối xứng qua y = 0), giải FEM để lấy tần số riêng, dạng dao động và độ võng tĩnh.

> Thư mục này là **bản sao** được tạo trước khi cắt bỏ phần cánh ghép nối với thân và booms (xem `readme.txt`).

## Chạy chương trình

Mở MATLAB, chuyển thư mục làm việc về thư mục này rồi chạy:

```matlab
main_CW
```

Kết quả: một figure 3D cho mỗi dạng dao động (mặc định 3 dạng, `modeNumber_f` trong `main_CW.m`), tiêu đề ghi tần số riêng (Hz). Các biến kết quả nằm trong workspace (xem [Biến kết quả chính](#biến-kết-quả-chính)).

## Luồng tính toán

```
main_CW.m
├── material_2D.m        tính chất lớp sợi carbon UD / woven (gọi ply.m, laminate.m, THstrength.m)
├── HM80.m               tính chất lõi foam PVC
├── hình học cánh, vị trí sườn, airfoil, tải khí động
├── vòng lặp ii = n → 1 (đầu cánh → gốc cánh)
│   └── cross_section_analysis_CW.m      (script, dùng chung workspace)
│       ├── laminate.m                   ma trận A, D của tấm lớp
│       ├── shear_center.m, shear_flow.m dòng cắt, tâm cứng, GJ (mặt cắt 3 ngăn)
│       ├── THstrength.m                 HSAT theo Tsai-Hill
│       └── vonMises.m, eq_strain.m
└── coupled_beam.m                       dầm uốn–xoắn toàn cánh
    └── BernoulliBeam.m                  ma trận độ cứng & khối lượng
```

Vòng lặp chạy **từ đầu cánh về gốc** vì lực cắt `F_shear(ii)` và mômen xoắn `M_t(ii)` tại mặt cắt `ii` được tích lũy từ tải của các mặt cắt phía ngoài (`ii+1:end`).

## Mô tả các file

### Script chính

| File | Vai trò |
|---|---|
| `main_CW.m` | Điểm vào. Khai báo hình học cánh, vị trí sườn, tải, bề dày lõi theo vùng; lặp qua các mặt cắt; gọi `coupled_beam` và vẽ dạng dao động. |
| `cross_section_analysis_CW.m` | **Script** (không phải hàm) chạy cho mặt cắt `ii`: định nghĩa xếp lớp của vỏ, dầm trước/sau, mũ dầm, mũ mở rộng, sườn; tính khối lượng & trọng tâm, EI, nội lực, ứng suất/biến dạng, HSAT, ổn định vỏ và sườn, tâm cứng, GJ, Im. |
| `coupled_beam.m` | Lấy đối xứng dữ liệu nửa cánh phải sang toàn cánh, lắp ráp FEM, đặt liên kết tại y = ±`fix_loc`, giải trị riêng và bài toán tĩnh. |

### Hàm

| File | Vai trò |
|---|---|
| `BernoulliBeam.m` | Ma trận độ cứng và khối lượng của phần tử dầm Euler-Bernoulli uốn + xoắn, có số hạng liên kết quán tính uốn–xoắn qua độ lệch tâm `e`. Mỗi nút có 3 bậc tự do: `[w, w', φ]`. |
| `laminate.m` | Ma trận A, D của tấm composite nhiều lớp (Gibson ch. 7). |
| `ply.m` | Tính chất lớp UD từ sợi + nền (cơ học vi mô, Gibson). |
| `THstrength.m` | Hệ số an toàn theo tiêu chuẩn Tsai-Hill cho từng lớp. |
| `shear_center.m` | Vị trí tâm cứng của mặt cắt kín 3 ngăn. |
| `shear_flow.m` | Dòng cắt 3 ngăn và độ cứng xoắn GJ (Megson eq. 23.10, 23.12). |
| `vonMises.m`, `eq_strain.m` | Ứng suất von Mises và biến dạng tương đương. |

### Vật liệu

| File | Nội dung | Được dùng? |
|---|---|---|
| `material_2D.m` | Sợi AS4 + epoxy 3501-6 → lớp UD (`*_UD`) và woven (`*_woven`) | Có |
| `HM80.m` | Lõi foam PVC (`*_core`) | Có |
| `RC200.m` | Sợi T700s + nền F201-10 | Không (phương án thay thế) |
| `material_3D.m`, `ply_3D.m`, `laminate_3D.m`, `TWstrength_3D_chen2020.m` | Phiên bản 3D + tiêu chuẩn Tsai-Wu | Không (chưa gắn vào luồng chính) |

Xếp lớp trong `cross_section_analysis_CW.m` được viết dạng chuỗi, ví dụ `'[par_UD*ones(1,2) par_core par_UD*ones(1,2)]'`, rồi thay `par` bằng `E1`, `E2`, `G12`, `rho`, `t`... Vì vậy tên biến vật liệu phải theo đúng mẫu `<thuộc tính>_<vật liệu>` (ví dụ `E1_UD`, `t_core`).

### Dữ liệu đầu vào

| File | Nội dung |
|---|---|
| `upper_point.dat`, `lower_point.dat` | Tọa độ airfoil mặt trên/dưới `[x z]` (mm, dây cung 800 mm); được chuẩn hóa về dây cung = 1 trong `main_CW.m`. |
| `aerodynamic_load.txt` | Tải khí động dạng `[y (m)  F (N)]` theo từng đoạn sải cánh. Trong `main_CW.m` tải được chia 2 (nửa cánh) và nhân `1.3*3.8`. |

### Kết quả lưu sẵn

`output.dat`, `Output/` và `Output2/` chứa HSAT, ứng suất, biến dạng của các chi tiết theo tọa độ sải cánh từ **các lần chạy trước**. Mã hiện tại không ghi các file này — kết quả mới chỉ nằm trong workspace.

## Thông số cần chỉnh thường gặp (trong `main_CW.m`)

| Biến | Ý nghĩa | Giá trị hiện tại |
|---|---|---|
| `dy`, `y_coord` | Bước lưới và tọa độ nửa sải cánh (m) | 0.02; 0 → 8.0 |
| `c_length`, `x_LE` | Dây cung và tọa độ mép trước theo y | 0.8 m đến y = 1.75, thuôn còn 0.4 m ở đầu cánh |
| `ribs_coord` | Vị trí sườn (mm) | 15 sườn |
| `fix_loc` | Vị trí liên kết với thân, đối xứng ±y (m) | 0.265 |
| `x_spar_1`, `x_spar_2` | Vị trí dầm trước/sau (phần dây cung) | 0.221; 0.711 |
| `core_thickness_*`, `d_side_cap_*`, `reinf`, `d_reinf_*` | Bề dày lõi, bề rộng mũ mở rộng, gia cường vỏ — khác nhau giữa cánh giữa (y ≤ 3.75 m) và cánh ngoài | xem vòng lặp |
| `n_load` | Hệ số tải cho trọng lượng bản thân | 1 |
| `modeNumber_f` | Số dạng dao động cần lấy | 3 |

Phân vùng xếp lớp vỏ theo y nằm ở đầu `cross_section_analysis_CW.m`: KV1 (y < 1.75), KV2 (y ≤ 3.75), cánh ngoài.

## Biến kết quả chính

Theo nửa cánh phải, chỉ số `ii` ứng với `y_coord(ii)`:

| Biến | Ý nghĩa |
|---|---|
| `m_airfoil` | Khối lượng trên đơn vị dài (kg/m) |
| `EI`, `GJ` | Độ cứng uốn, độ cứng xoắn |
| `Im` | Mômen quán tính khối lượng xoắn |
| `x_E`, `xc_airfoil` | Tâm cứng, trọng tâm (phần dây cung tính từ mép trước) |
| `F_shear`, `M_b`, `M_t` | Lực cắt, mômen uốn, mômen xoắn |
| `f_u_skin`, `f_l_spar_1`, `f_u_cap_1`, `f_rib`, ... | HSAT Tsai-Hill theo lớp, kích thước `n × 100` (cột = số thứ tự lớp) |

Theo toàn cánh (`coupled_beam.m`), nút trung tâm y = 0 có chỉ số `n_half`:

| Biến | Ý nghĩa |
|---|---|
| `y_full`, `c_full`, `x_E_full`, ... | Dữ liệu đã lấy đối xứng |
| `Df` | Tần số riêng (Hz), tăng dần |
| `Vf` | Dạng dao động; nút `i` có `w = Vf(3i-2)`, `w' = Vf(3i-1)`, `φ = Vf(3i)` |
| `deflection` | Chuyển vị tĩnh dưới tải, cùng cách đánh chỉ số |

## Lưu ý

- `cross_section_analysis_CW.m` và các file vật liệu là **script**, dùng chung workspace với `main_CW.m`. Đặt tên biến mới cẩn thận để không ghi đè biến đang dùng (ví dụ `n`, `ii`, `scale`, `stack`).
- `F_react`, `M_react` được tính khi vòng lặp đi qua vị trí `fix_loc`; `coupled_beam.m` trừ chúng ra khỏi `F_shear`, `M_t` vì trong mô hình toàn cánh phản lực do gối tại ±`fix_loc` tự sinh ra.
- Các file `*.asv` là bản autosave của MATLAB, có thể bỏ qua.

## Tài liệu tham khảo dùng trong mã

- R. F. Gibson, *Principles of Composite Material Mechanics* — cơ học vi mô, tấm lớp.
- I. M. Daniel, O. Ishai, *Engineering Mechanics of Composite Materials* — số liệu vật liệu (Table A.3).
- T. H. G. Megson, *Aircraft Structures for Engineering Students* — dòng cắt, tâm cứng, dầm thuôn (ch. 20, 23).
- Chizhov — ứng suất trung bình (eq. 2.24).
