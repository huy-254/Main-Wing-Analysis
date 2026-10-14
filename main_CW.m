clear ;
close all;
clc;

% chua tinh den khoi luong cac bo phan khac
m_tail = 0;
m_elev = 0;
m_vert_tail = 0;
m_boom = 0;
F_tail = 0;
F_ground = 0;
d_tail = 6;
xc_boom = 3;

fix_loc = 265e-3;

% Thong so vat lieu
material_2D
PVC_Foam

% Thong so hinh hoc
dy = 0.02;
y_coord = 0:dy:8.0;
n = length(y_coord);
c_length = zeros(n,1);
x_coord = zeros(n,1); % x_cooord of leading edge
for i=1:n
   if y_coord(i)<1.75
       c_length(i) = 0.8;
       x_coord(i) = 0.8;
   else
       c_length(i) = 0.8*(1-(y_coord(i)-1.750)/6.250) + 0.4*(y_coord(i)-1.750)/6.250;
       x_coord(i) = -0.08*(y_coord(i)-1.750)/6.250 + 0.8;
   end
end

boom_attach_loc = 1560e-3;
index_boom = round(boom_attach_loc/dy)+1;
n_load = 1;


% compute ribs spacing (full wing)
ribs_coord = [0, 375, 880, 1560, 2645, 3650, 3830, 4220, 4670, 5405, 5845, 6260, 6745, 7700, 7950];
% convert coordinates to meters and sort ascending
y_rib = ribs_coord/1000;
rib_size = length(y_rib);
rib_spacing_3 = zeros(n,1);
for ii=n:-1:1
    scale = c_length(ii); 
        if y_coord(ii)>y_rib(rib_size)
            rib_spacing_3(ii) = (y_rib(rib_size) - y_rib(rib_size-1))/scale;
        else
            for jj = rib_size:-1:2
                if y_coord(ii)<= y_rib(jj)
                    rib_spacing_3(ii) = (y_rib(jj) - y_rib(jj-1))/scale;
                end 
            end     
        end
end

%% Wing configuration
% % vi tri dam truoc va dam sau
% for i = 1:length(y_coord)
%     if y_coord(i) < 1.75
%         x_spar_1(i) = x_coord(i) - 0.2*c_length(i) - 0.020/2;
%     else
%         x_spar_1(i) = x_coord(i) - 0.2*c_length(i) - 0.034/2;
%     end
% end
% x_spar_2 = x_coord - 0.75*c_length + 0.017/2;
% 
% % Plot hinh dang canh
% plot(y_coord, x_coord, 'b-', 'LineWidth', 2);
% x_trailing_edge = x_coord - c_length;
% hold on;
% plot(y_coord, x_trailing_edge, 'b-', 'LineWidth', 2);
% plot(y_coord, x_spar_1, 'r--', 'LineWidth', 1.5);
% plot(y_coord, x_spar_2, 'r--', 'LineWidth', 1.5);
% xlabel('X Coordinate');
% ylabel('Y Coordinate');
% title('Cross-Sectional Shape of the Wing');
% grid on;
% axis equal;

%% loading airfoil
load upper_point.dat % load upper points
load lower_point.dat % load lower points
% chuyen sang met
upper_point = upper_point/upper_point(1,1);
lower_point = lower_point/lower_point(end,1);
figure
plot(upper_point(:,1), upper_point(:,2))
hold on
plot(lower_point(:,1), lower_point(:,2))

% Tai khi dong
load aerodynamic_load.txt;
aerodynamic_data = aerodynamic_load;
aerodynamic_data(:,2) = aerodynamic_data(:,2)/2*1.3*3.8;

F_dist = zeros(n,1);
for ii = 1:length(aerodynamic_data(:,1))
   if ii == 1
       F_dist(1:round(aerodynamic_data(ii,1)/dy)) = aerodynamic_data(ii,2)/aerodynamic_data(ii,1);
   else
       F_dist(round(abs(aerodynamic_data(ii-1,1))/dy):round(abs(aerodynamic_data(ii,1))/dy)) =...
           aerodynamic_data(ii,2)/abs(aerodynamic_data(ii,1)-aerodynamic_data(ii-1,1));
   end
end

y_point = aerodynamic_data(:,1);
F_point = aerodynamic_data(:,2);

% Khoi tao cac mang chua HSAT
f_u_skin = zeros(n,100);
f_l_skin = zeros(n,100);
f_u_skin_reinf = zeros(n,100);
f_l_skin_reinf = zeros(n,100);
f_u_spar_1 = zeros(n,100);
f_u_spar_2 = zeros(n,100);
f_l_spar_1 = zeros(n,100);
f_l_spar_2 = zeros(n,100);
f_u_cap_1 = zeros(n,100);
f_u_cap_2 = zeros(n,100);
f_l_cap_1 = zeros(n,100);
f_l_cap_2 = zeros(n,100);
f_rib = zeros(n,100);
f_front_rib = zeros(n,100);
f_rear_rib = zeros(n,100);
f_u_side_cap_1 = zeros(n,100);
f_l_side_cap_1 = zeros(n,100);
f_u_side_cap_2 = zeros(n,100);
f_l_side_cap_2 = zeros(n,100);
spar_1_up_0 = zeros(n,1);
spar_1_low_0 = zeros(n,1);
spar_2_up_0 = zeros(n,1);
spar_2_low_0 = zeros(n,1);
x_spar_1_0 = zeros(n,1);
x_spar_2_0 = zeros(n,1);

% phan canh giao voi than va boom
w_fuselage = 650e-3;
w_boom = 175e-3;

% cross section analysis
for ii=n:-1:1
    scale = c_length(ii);
    x_spar_1 = 0.22125;
    x_spar_2 = 0.710625;
    if y_coord(ii)<=3.75 % centered wing
        core_thickness_skin = .01; 
        core_thickness_rib = .01;
        core_thickness_spar_1 = 0.029;
        core_thickness_spar_2 = 0.0138;
        d_side_cap_1 = 0.015/scale; 
        d_side_cap_2 = 0.012/scale; 
        reinf = 0; % No skin reinforcement
        
    else % Side wing
        core_thickness_skin = .005; % foam 5
        core_thickness_rib = .005; % foam 5
        core_thickness_spar_1 = 0.015;
        core_thickness_spar_2 = 0.0138;
        d_side_cap_1 = 0.012/scale; % front side cap width (fraction of chord length)
        d_side_cap_2 = 0.012/scale; % aft side cap width (fraction of chord length)
        reinf = 1; % skin reinforcement
        d_reinf_1 = .050;
        d_reinf_2 = .047;
    end
    rib_spacing = rib_spacing_3(ii);
    cross_section_analysis_CW;
end


% FEM analysis
modeNumber_f = 6;
coupled_beam

% In tan so cac mode doi xung dau tien (bo qua mode phan doi xung)
id_sym = find(mode_type == "doi xung");
id_sym = id_sym(1:min(floor(modeNumber_f/2), numel(id_sym)));
fprintf('Tan so cac mode doi xung:\n');
for kk = 1:numel(id_sym)
    fprintf('  Mode %d (mode so %d): %.3f Hz\n', kk, id_sym(kk), Df(id_sym(kk)));
end
fprintf('\n');
fprintf('Tong khoi luong canh: %.3f kg\n', sum(m_full*dy));

% Ve mode shape
% Moi mat cat (day cung) xoay quanh truc dan hoi (tam cung x_E) mot goc phi
% va tinh tien theo phuong z mot doan w. Truc x huong ve phia truoc, mep sau
% nam tai x_LE - c. Khoang cach co dau tu truc dan hoi den mep truoc / mep sau:
%   d_LE = x_E*c,  d_TE = -(1-x_E)*c
% Toa do sau bien dang (phi > 0: mep truoc di xuong, mep sau di len):
%   x = x_EA + d*cos(phi),  z = w - d*sin(phi)
% Vector rieng co bien do tuy y nen nhan ca vector voi 1 he so ty le chung
% (giu nguyen ty le w/phi cua mode) sao cho max|w| <= w_plot_max va
% max|phi| <= phi_plot_max.
w_plot_max = 0.1*max(y_full);  % do vong lon nhat khi ve (m)
phi_plot_max = 30*pi/180;      % goc xoan lon nhat khi ve (rad)

x_EA_full = x_LE_full - x_E_full.*c_full; % toa do x cua truc dan hoi
d_LE = x_E_full.*c_full;
d_TE = -(1-x_E_full).*c_full;
% Thang mau 9 dai kieu ANSYS: xanh duong (Min) -> do (Max)
cmap_contour = [0 0 1; 0 .7 1; 0 1 1; 0 1 .7; 0 1 0;...
    .7 1 0; 1 1 0; 1 .7 0; 1 0 0];
for kk = 1:modeNumber_f
    figure
    hold on
    mode_deflec = Vf(:,kk);
    w_mode = mode_deflec(1:3:end)';
    phi_mode = mode_deflec(3:3:end)';
    scale_mode = min(w_plot_max/max(max(abs(w_mode)),eps),...
        phi_plot_max/max(max(abs(phi_mode)),eps));
    w_mode = scale_mode*w_mode;
    phi_mode = scale_mode*phi_mode;

    % Toa do mep truoc, mep sau sau bien dang
    x_LE_def = x_EA_full + d_LE.*cos(phi_mode);
    z_LE_def = w_mode - d_LE.*sin(phi_mode);
    x_TE_def = x_EA_full + d_TE.*cos(phi_mode);
    z_TE_def = w_mode - d_TE.*sin(phi_mode);

    % Hinh dang canh chua bien dang (tham chieu)
    plot3(x_LE_full, y_full, zeros(size(y_full)), '--', 'Color', [.6 .6 .6])
    plot3(x_LE_full-c_full, y_full, zeros(size(y_full)), '--', 'Color', [.6 .6 .6])

    % Be mat canh sau bien dang, to mau theo gia tri tuyet doi cua chuyen vi
    % phuong z tai tung diem (z ban dau = 0, da gom ca anh huong cua goc xoan).
    % Hang 1: mep truoc, hang 2: mep sau; mau noi suy doc theo day cung
    uz_abs = abs([z_LE_def; z_TE_def]);
    surf([x_LE_def; x_TE_def], [y_full; y_full], [z_LE_def; z_TE_def], uz_abs,...
        'FaceColor', 'interp', 'EdgeColor', 'none')
    colormap(cmap_contour)
    w_min = min(uz_abs(:));
    w_max = max(uz_abs(:));
    if w_max - w_min < eps
        w_max = w_min + eps;
    end
    clim([w_min w_max])
    w_ticks = linspace(w_min, w_max, size(cmap_contour,1)+1);
    w_labels = compose('%.3g', w_ticks);
    w_labels{1} = [w_labels{1} ' Min'];
    w_labels{end} = [w_labels{end} ' Max'];
    cb = colorbar('Ticks', w_ticks, 'TickLabels', w_labels);
    cb.Label.String = '|u_z| (m)';

    xlabel('x (m)'); ylabel('y (m)'); zlabel('z (m)')
    title(['Mode shape so ', num2str(kk), ', tan so ', num2str(Df(kk)), 'Hz'], 'FontSize', 18)
    axis equal tight
    axis off
    view(-55,30) % nhin tu phia sau (-x) ra phia truoc
    grid on
end

%% Xuat thong so dam tuong duong cua toan canh ra file txt
% x_E, x_C: tinh theo phan day cung, tu mep truoc ve phia sau
% (toa do x tuyet doi = x_LE - x_E*c)
EA_full = mirror(EA(:)');
beam_data = [y_full; c_full; x_LE_full; EI_full; GJ_full; EA_full;...
    m_full; Im_full; x_E_full; xc_full]';
fid = fopen('equivalent_beam_full_wing.txt', 'w');
fprintf(fid, '%12s %12s %12s %14s %14s %14s %12s %12s %12s %12s\n',...
    'y', 'c', 'x_LE', 'EI', 'GJ', 'EA', 'm', 'Im', 'x_E', 'x_C');
fprintf(fid, '%12s %12s %12s %14s %14s %14s %12s %12s %12s %12s\n',...
    '(m)', '(m)', '(m)', '(N.m^2)', '(N.m^2)', '(N)', '(kg/m)', '(kg.m)', '(-/c)', '(-/c)');
fprintf(fid, '%12.4f %12.4f %12.4f %14.6e %14.6e %14.6e %12.6f %12.6e %12.6f %12.6f\n', beam_data');
fclose(fid);
