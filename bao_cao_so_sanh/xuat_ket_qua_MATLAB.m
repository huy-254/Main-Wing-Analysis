%% xuat_ket_qua_MATLAB.m - Xuat ket qua mo hinh dam MATLAB de so sanh voi APDL
% Chay tu thu muc goc project:  matlab -batch "run('bao_cao_so_sanh/xuat_ket_qua_MATLAB.m')"
% Khong sua main_CW.m / cross_section_analysis_CW.m. Ket qua ghi vao thu muc goc project:
%   ket_qua_MATLAB_so_sanh.mat : tan so, vector rieng, do vong (tai thiet ke va 100 N dau mut),
%                                khoi luong theo thanh phan
%   ket_qua_MATLAB_so_sanh.txt : tom tat dang van ban
cd(fileparts(fileparts(mfilename('fullpath'))))   % thu muc goc project
main_CW

%% 0. Xuat hinh dang dao dong 3D ma main_CW da ve (title 'Mode shape so k') -> hinh_mode_MATLAB/MATLAB_modeXX.png
% Giu goc nhin view(-55,30) cua main_CW; nen trang. Dung de ghep voi hinh ANSYS (so_sanh.py).
img_dir = fullfile('bao_cao_so_sanh', 'hinh_mode_MATLAB');
if ~exist(img_dir, 'dir'), mkdir(img_dir); end
for f_h = findobj('Type', 'figure')'
    ax_h = findobj(f_h, 'Type', 'axes');
    if isempty(ax_h), continue, end
    t_h = ax_h(1).Title.String;
    if iscell(t_h), t_h = t_h{1}; end
    tok = regexp(t_h, 'Mode shape so (\d+)', 'tokens');
    if isempty(tok), continue, end
    set(f_h, 'Position', [100 100 1100 800], 'Color', 'w');
    title(ax_h(1), '');   % tieu de ghi lai khi ghep hinh (so_sanh.py), bo di de khong lan vao vung cat
    exportgraphics(f_h, fullfile(img_dir, sprintf('MATLAB_mode%02d.png', str2double(tok{1}{1}))), ...
        'Resolution', 150, 'BackgroundColor', 'white');
end
close all

%% 0b. Chi so pha huy Tsai-Hill (tinh trong cross_section_analysis_CW.m, vong mat cat cua main_CW)
% Phai lay TRUOC muc 1 vi muc 1 goi lai cross_section_analysis_CW va ghi de cac mang f_*.
% Moi hang: mot mat cat y_coord (nua phai, 0 -> 8 m). Moi cot: mot chi tiet.
% f_TH_fiber: lon nhat theo cac lop soi (carbon); f_TH_core: lop loi foam (0 neu chi tiet khong co loi).
% Vi tri lop loi trong xep lop MATLAB: vo lop 4 (y < 1.75) hoac lop 3 (y >= 1.75),
% thanh dam truoc lop 11, thanh dam sau lop 7, rib lop 5. Dai gia cuong (chi co khi y > 3.75) khong co loi.
ben_names = {'vo_tren', 'vo_duoi', 'dai_gia_cuong_tren', 'dai_gia_cuong_duoi', ...
    'mu_dam_truoc_tren', 'mu_dam_truoc_duoi', 'mu_dam_sau_tren', 'mu_dam_sau_duoi', ...
    'side_cap_truoc_tren', 'side_cap_truoc_duoi', 'side_cap_sau_tren', 'side_cap_sau_duoi', ...
    'thanh_dam_truoc_tren', 'thanh_dam_truoc_duoi', 'thanh_dam_sau_tren', 'thanh_dam_sau_duoi', ...
    'rib_mep_truoc', 'rib_mep_sau'};
ben_arrays = {f_u_skin, f_l_skin, f_u_skin_reinf, f_l_skin_reinf, ...
    f_u_cap_1, f_l_cap_1, f_u_cap_2, f_l_cap_2, ...
    f_u_side_cap_1, f_l_side_cap_1, f_u_side_cap_2, f_l_side_cap_2, ...
    f_u_spar_1, f_l_spar_1, f_u_spar_2, f_l_spar_2, ...
    f_front_rib, f_rear_rib};
core_column = [3 3 0 0 0 0 0 0 0 0 0 0 11 11 7 7 5 5];   % vo: doi thanh 4 khi y < 1.75 (ben duoi)
f_TH_fiber = zeros(n, numel(ben_arrays));
f_TH_core = zeros(n, numel(ben_arrays));
for k = 1:numel(ben_arrays)
    for ii = 1:n
        layer_values = ben_arrays{k}(ii,:);
        core_layer = core_column(k);
        if k <= 2 && y_coord(ii) < 1.75
            core_layer = 4;                % KV1: 1woven/1UD/F10/1UD/1woven
        end
        is_core = false(size(layer_values));
        if core_layer > 0
            is_core(core_layer) = true;
            f_TH_core(ii,k) = layer_values(core_layer);
        end
        f_TH_fiber(ii,k) = max(layer_values(~is_core));
    end
end
y_half = y_coord;
% Gioi han ben (Pa): [keo doc, nen doc, keo ngang, nen ngang, cat]
strength_UD = [sL_tens_UD sL_compr_UD sT_tens_UD sT_compr_UD sLT_UD];
strength_core = [sL_tens_core sL_compr_core sT_tens_core sT_compr_core sLT_core];

%% 1. Khoi luong theo thanh phan (lap lai vong mat cat, lay cac so hang cua m_airfoil)
% Cac so hang giong cross_section_analysis_CW.m dong 324-337 (kg/m)
cmp_names = {'vo', 'mu_dam', 'side_cap', 'bung_dam', 'rib'};
m_cmp = zeros(n, 5);
for ii = n:-1:1
    scale = c_length(ii);
    if y_coord(ii) <= 3.75
        core_thickness_skin = .01; core_thickness_rib = .01;
        core_thickness_spar_1 = 0.029; core_thickness_spar_2 = 0.0138;
        d_side_cap_1 = 0.015/scale; d_side_cap_2 = 0.012/scale; reinf = 0;
    else
        core_thickness_skin = .005; core_thickness_rib = .005;
        core_thickness_spar_1 = 0.015; core_thickness_spar_2 = 0.0138;
        d_side_cap_1 = 0.012/scale; d_side_cap_2 = 0.012/scale; reinf = 1;
        d_reinf_1 = .050/scale; d_reinf_2 = .047/scale;
    end
    rib_spacing = rib_spacing_3(ii);
    cross_section_analysis_CW;
    sk = sum(rho_skin.*t_layer_skin)*(sum(elem_length_u)+sum(elem_length_l));
    if reinf == 1
        sk = sk - sum(rho_skin.*t_layer_skin)/sum(t_layer_skin)*t_skin*(2*d_reinf_1+2*d_reinf_2)*scale + ...
            sum(rho_skin_reinf.*t_layer_skin_reinf)/sum(t_layer_skin_reinf)*t_skin_reinf*(2*d_reinf_1+2*d_reinf_2)*scale;
    end
    cap = sum(rho_cap_1_u.*t_layer_cap_1_u)*d_cap_1 + sum(rho_cap_1_l.*t_layer_cap_1_l)*d_cap_1 + ...
        sum(rho_cap_2_u.*t_layer_cap_2_u)*d_cap_2 + sum(rho_cap_2_l.*t_layer_cap_2_l)*d_cap_2;
    sc = sum(rho_side_cap_1.*t_layer_side_cap_1)*d_side_cap_1*2 + sum(rho_side_cap_2.*t_layer_side_cap_2)*d_side_cap_2*2;
    wb = sum(rho_spar_1.*t_layer_spar_1)*h_foam_1 + sum(rho_spar_2.*t_layer_spar_2)*h_foam_2;
    rb = sum(rho_rib.*t_layer_rib)*(h_spar_1+h_spar_2)/2*(x_spar_2-x_spar_1)*scale*n_rib;
    m_cmp(ii,:) = [sk cap sc wb rb]*scale;
end
m_cmp_full = [flipud(m_cmp(2:end,:)); m_cmp];        % toan canh, trung nut y = 0
mass_cmp = sum(m_cmp_full*dy, 1);                    % cung quy tac tong nhu sum(m_full*dy)
mass_tot = sum(m_full*dy);

%% 2. Tinh: tai thiet ke (deflection cua coupled_beam) va 100 N tai dau mut phai
xi_mid = (0.22125 + 0.710625)/2;                     % hop luc 100 N chia deu 2 bung dam
F_tip = zeros(GDof,1);
F_tip(5*numel(y_full)-4) = 100;                      % w cua nut y = +8
F_tip(5*numel(y_full)-2) = 100*(x_E_full(end) - xi_mid)*c_full(end);   % phi > 0: mep truoc len
defl_tip = zeros(GDof,1);
defl_tip(activeDof) = stiffness(activeDof,activeDof)\F_tip(activeDof);
defl_design = deflection;

%% 3. Ghi ket qua
xi_spar = [0.22125 0.710625];
save('ket_qua_MATLAB_so_sanh.mat', 'y_full', 'c_full', 'x_LE_full', 'x_E_full', 'xc_full', ...
    'Df', 'Vf', 'mode_type', 'mode_kind', 'mode_energy', 'defl_design', 'defl_tip', ...
    'mass_cmp', 'cmp_names', 'mass_tot', 'm_full', 'xi_spar', 'EI_full', 'GJ_full', 'EI_z_full', 'dy', 'fix_loc', ...
    'ben_names', 'f_TH_fiber', 'f_TH_core', 'y_half', 'strength_UD', 'strength_core');
fid = fopen('ket_qua_MATLAB_so_sanh.txt', 'w');
fprintf(fid, 'Ket qua mo hinh dam MATLAB (main_CW + coupled_beam, Bernoulli), %s\n', datestr(now));
fprintf(fid, 'Tong khoi luong: %.3f kg\n', mass_tot);
for k = 1:5, fprintf(fid, '  %-10s %8.3f kg\n', cmp_names{k}, mass_cmp(k)); end
fprintf(fid, 'Tan so rieng (Hz)\n');
for k = 1:numel(Df(1:modeNumber_f))
    fprintf(fid, '  Mode %2d  f = %9.4f Hz  %-14s %-10s  [uon dung %3.0f%%, xoan %3.0f%%, uon ngang %3.0f%%]\n', ...
        k, Df(k), mode_type(k), mode_kind(k), 100*mode_energy(:,k));
end
w_d = defl_design(1:5:end); w_t = defl_tip(1:5:end);
fprintf(fid, 'Do vong w tai truc dan hoi (mm): y | tai thiet ke | 100 N dau mut\n');
for yy = [1 2 3 4 5 6 7 8]
    [~, j] = min(abs(y_full - yy));
    fprintf(fid, '  y = %5.2f  %10.3f  %10.3f\n', y_full(j), 1e3*w_d(j), 1e3*w_t(j));
end
fclose(fid);
type('ket_qua_MATLAB_so_sanh.txt')
