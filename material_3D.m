%% AS4 Carbon fiber (Daniel Table A.3)
E1f_carb = 235e9;
E2f_carb = 15e9;
G12f_carb = 27e9;
G23f_carb = 7e9;
nju12f_carb = 0.2;
nju23f_carb = 0.4;
sLf_tens_carb = 3.7e9;
rho_f_carb = 1810; % Table A1. Daniel and Ishai 394
vf_carb = 0.63;
style = 1;

%% Epoxy (3501-6) (Daniel Table A.3)
Em_epx = 4.3e9;
Gm_epx = 1.6e9;
nju_epx = 0.35;
sLm_tens_epx = 69e6;
sLm_compr_epx = 200e6;
sLTm_epx = 100e6;
rho_m = 1270;

%% Composite woven lamina Style 282 (AS4 carbon) 
% Ply
style_282 = 1; % uniform distribution (1); layered distribution (0)
[E1_UD, E2_UD, G12_UD, G23_UD, nju12_UD, nju23_UD, Y1_tens_UD, Y1_compr_UD, ...
    Y2_tens_UD, Y2_compr_UD, Y3_tens_UD, Y3_compr_UD, Y12_UD, Y23_UD, Y31_UD, rho_UD] = ...
    ply_3D(E1f_carb, E2f_carb, G12f_carb, G23f_carb, nju12f_carb, nju23f_carb, ...
    rho_f_carb, 0.63, Em_epx, Gm_epx, sLf_tens_carb, sLm_tens_epx,...
    sLm_compr_epx, sLTm_epx, rho_m, nju_epx, style_282);
m_UD = 0.3; % mass of fiber per m^2 in each ply
Vf_UD = m_UD/rho_f_carb; % volume of fiber per m^2
V_UD = Vf_UD/vf_carb; % total volume of the ply per m^2
t_UD = V_UD; % ply thickness

% Woven lamina moduli
E1_layer = [E1_UD E1_UD]; 
E2_layer = [E2_UD E2_UD];
G12_layer = [G12_UD G12_UD];
G23_layer = [G23_UD G23_UD];
theta_layer = [0 pi/2];
t_layer = [t_UD t_UD];
nju12_layer = [nju12_UD nju12_UD];
nju23_layer = [nju23_UD nju23_UD];

[A_lam, D_lam]= laminate_3D(E1_layer, E2_layer, theta_layer, t_layer, ...
    G12_layer, G23_layer, nju12_layer, nju23_layer);
Q_lam = A_lam/sum(t_layer);
S_lam = inv(Q_lam);
E1_woven = 1/S_lam(1,1);
E2_woven = 1/S_lam(2,2);
E3_woven = 1/S_lam(3,3);
G12_woven = 1/S_lam(6,6);
G23_woven = 1/S_lam(4,4);
G13_woven = 1/S_lam(5,5);
nju12_woven = -S_lam(2,1)/S_lam(1,1);
nju23_woven = -S_lam(3,2)/S_lam(2,2);
nju13_woven = -S_lam(3,1)/S_lam(1,1);
t_woven = sum(t_layer);

% Failure contants
Y1_tens_layer = Y1_tens_UD*ones(1,2);
Y1_compr_layer = Y1_compr_UD*ones(1,2);
Y2_tens_layer = Y2_tens_UD*ones(1,2);
Y2_compr_layer = Y2_compr_UD*ones(1,2);
Y3_tens_layer = Y3_tens_UD*ones(1,2);
Y3_compr_layer = Y3_compr_UD*ones(1,2);
Y12_layer = Y12_UD*ones(1,2);
Y23_layer = Y23_UD*ones(1,2);
Y31_layer = Y31_UD*ones(1,2);

%% Chen 2020
% Longitudinal Tensile strength
stress = [1;0;0;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y1_tens_wov = max(fos);

% Transverse Tensile strength
stress = [0;1;0;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y2_tens_wov = max(fos);

% Out-of-plane tensile strength
stress = [0;0;1;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y3_tens_wov = max(fos);

% Longitudinal compressive strength
stress = [-1;0;0;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y1_compr_wov = max(fos);

% Transverse compressive strength
stress = [0;-1;0;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y2_compr_wov = max(fos);

% Out-of-plane compressive strength
stress = [0;0;-1;0;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y3_compr_wov = max(fos);

% In-plane Shear  strength
stress = [0;0;0;0;0;1];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y6_wov = max(fos);

% Out-of-plane Shear strength
stress = [0;0;0;1;0;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y4_wov = max(fos);

% Out-of-plane Shear  strength
stress = [0;0;0;0;1;0];
strain_xy = Q_lam\stress;
fos = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, G23_layer, ...
    nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy);
Y5_wov = max(fos);


