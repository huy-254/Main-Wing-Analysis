# CLAUDE.md — Phân tích cánh chính UAV (composite)

Chi tiết đầy đủ nằm trong `README.md` (luồng tính, bảng biến, thông số). File này chỉ ghi những gì cần nhớ khi làm việc.

## Bối cảnh
- Cánh chính composite của UAV twin boom, mô hình **dầm tương đương** (MATLAB), kiểm chứng bằng FEM khối nhiều lớp SOLSH190 trong ANSYS APDL (Python sinh file). Phương pháp shell SHELL181 đã bị bỏ (24/11/2026) vì shell chỉ offset theo pháp tuyến, không dựng được mũ dầm/thành dầm thẳng đứng.
- Folder này là **bản sao được tạo trước khi cắt bỏ phần cánh ghép nối với thân và booms** (xem `readme.txt`). Là nguồn gốc để tạo project đuôi ngang (`../2. phan tich duoi ngang`).
- Folder có git riêng (`.git`). Đổi code lõi (xếp lớp, `coupled_beam`, `TimoshenkoBeam`...) thì cân nhắc phần tương ứng bên đuôi ngang, nhưng **không tự sửa folder khác** khi chưa được yêu cầu.

## Quy trình chuẩn
1. `main_CW` (MATLAB) → tần số riêng, dạng dao động, độ võng tĩnh, `equivalent_beam_full_wing.txt`.
2. `py -3 gen_apdl_for_wing_SOLSH190.py` → `APDL_for_wing_SOLSH190.inp` (ghi cả thư mục project và `E:\luan an\ve lai UAV - ANSYS\APDL canh chinh SOLSH190`).
3. Lệnh xem kết quả trong ANSYS: `lenh_hien_thi_trong_APDL.txt`.
4. So sánh và báo cáo (`bao_cao_so_sanh/`): `xuat_ket_qua_MATLAB.m` → `so_sanh.py` (hình + `ket_qua_so_sanh.json`) → `tao_bao_cao.py` (Word). Người dùng có thể sửa tay file Word: trước khi sinh lại, so với bản do script sinh để không mất phần sửa tay. Dùng từ "thành dầm" (không dùng "bụng dầm").

## Quy ước cứng
- Đơn vị MATLAB: SI (m, N, kg). File `.dat` airfoil (NACA 4421): mm, dây cung 800 mm.
- Vị trí theo dây cung (x_E, xc...) tính theo **phần dây cung từ mép trước**.
- Trục: y dọc sải (nửa cánh 0 → 8.0 m, dây cung 0.8 m đến y = 1.75 rồi thuôn còn 0.4 m), x dọc dây cung, z đứng. Bậc tự do mỗi nút `[w, w', φ, u, u']`.
- `cross_section_analysis_CW.m` và file vật liệu là **script dùng chung workspace** với `main_CW.m`. Đặt tên biến mới cẩn thận, không ghi đè `n`, `ii`, `scale`, `stack`.
- Xếp lớp viết dạng chuỗi với `par`; tên biến vật liệu đúng mẫu `<thuộc tính>_<vật liệu>` (`E1_UD`, `t_core`).
- Vòng lặp mặt cắt chạy từ đầu cánh về gốc vì nội lực tích lũy từ phía ngoài.
- Liên kết với thân tại y = ±`fix_loc` = 0.265 m. `F_react`, `M_react` bị `coupled_beam.m` trừ ra khỏi `F_shear`, `M_t` vì FEM toàn cánh tự sinh phản lực.
- Tải khí động `aerodynamic_load.txt` `[y (m)  F (N)]`; trong `main_CW.m` chia 2 (nửa cánh) và nhân `1.3*3.8`.
- Cánh có vùng cánh giữa (y ≤ 3.75 m) và cánh ngoài, khác nhau về lõi, mũ mở rộng, cờ gia cường `reinf` (đuôi ngang đã bỏ cờ này).

## Đồng bộ MATLAB ↔ APDL
Khi đổi xếp lớp/hình học trong MATLAB thì phải sửa tương ứng trong `gen_apdl_for_wing_SOLSH190.py`, và ngược lại.

## Bài học / lỗi đã gặp
- Foam từng bị gán nhầm vật liệu trong ANSYS (phát hiện ở đuôi ngang). Sau khi sinh APDL, đối chiếu khối lượng theo TYPE với MATLAB.
- `README.md` còn nhắc `PVD_Foam.m`, `ply_3D.m`, `laminate_3D.m`; file thực tế là `PVC_Foam.m`, `ply3D.m`, `laminate3D.m`.

## Việc không làm
- Không xóa các file `.inp`, `output.dat`, `Output*/` (kết quả các lần chạy trước) khi chưa hỏi.
- Không sửa file `.inp` sinh tự động bằng tay; sửa script Python rồi sinh lại.
- Không commit/push nếu chưa được yêu cầu. `.gitignore` đã loại `*.asv` và `main_CW copy.m`.

## Ngôn ngữ
Trả lời và viết comment/tài liệu bằng tiếng Việt (tên file, biến giữ nguyên như hiện có, không dấu).
