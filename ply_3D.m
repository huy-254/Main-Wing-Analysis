function [E1c, E2c, G12c, G23c, nju12_c, nju23_c, Y1_tens, Y1_compr, ...
    Y2_tens, Y2_compr, Y3_tens, Y3_compr, Y12, Y23, Y31, rho_c] = ...
    ply_3D(E1f, E2f, G12f, G23f, nju12_f, nju23_f, rho_f, vf, Em, Gm, ...
    sLf_tens, sLm_tens, sLm_compr, sLTm, rho_m,  nju_m, style)
%% Modulus
E1c = E1f*vf + Em*(1-vf); % Gibson eq. 3.23
nju12_c = nju12_f*vf + nju_m*(1-vf); % Gibson eq. 3.41
% Modulus: Halpin-Tsai semiempirical relation
zeta = 1;
eta_E = (E2f - Em)/(E2f + zeta*Em);
E2c = Em*(1 + zeta*eta_E*vf)/(1 - eta_E*vf);
eta_G = (G12f/Gm - 1)/(G12f/Gm + zeta);
G12c = Gm*(1 + zeta*eta_G*vf)/(1 - eta_G*vf);
% Poisson ratio: nju23_c
nju21_c = nju12_c*E2c/E1c;
Km = Em/2/(1 + nju_m)/(1 - 2*nju_m); % Daniel 3.27: Plain strain bulk moduli of matrix
nju21_f = nju12_f*E2f/E1f;
Kf = E1f*E2f/(2*E1f*(1 - nju21_f - nju23_f) - E2f*(1 - 2*nju21_f));
eta_K = (Kf/Km - 1)/(Kf/Km + zeta);
K = Km*(1 + zeta*eta_K*vf)/(1 - eta_K*vf);
nju23_c = 1 - nju21_c - E2c/2/K + E2c*(1-2*nju12_c)/2/E1c;
% G23c: Out-of-plane modulus
G23c = (Gm * (Km * (Gm + G23f) + 2 * G23f * Gm + Km * (G23f - Gm) * vf)) / ...
      (Km * (Gm + G23f) + 2 * G23f * Gm - (Km + 2 * Gm) * (G23f - Gm) * vf); % Daniel 3.40
%% Strength
% Longitudinal tensile strength
eLf_tens = sLf_tens / E1f;
eLm_tens = sLm_tens / Em;
if eLf_tens < eLm_tens % Gibson Fig. 4.9
    Y1_tens = eLf_tens*E1c;
    if vf < (sLm_tens - eLf_tens*Em)/(sLf_tens - eLf_tens*Em) % Gibson Eq. 4.22
        Y1_tens = sLm_tens*(1 - vf); % Gibson Eq. 4.23
    end
else
    Y1_tens = eLm_tens*E1c;
end
% Longitudinal compressive strength
phi = 0.034906;
sLc_compr_ext = 2*vf*sqrt(vf*Em*E1f/3/(1-vf)); % Gibson Eq. 4.29, Daniel Eq. 5.21  
sLc_compr_shear = Gm/(1-vf); % Daniel 5.22
sLc_compr_misalign = sLTm/(sLTm/(Gm/(1-vf))+phi); % Gibson Eq. 4.30
Y1_compr = min([sLc_compr_ext, sLc_compr_misalign, sLc_compr_shear]);
% Transverse strength
if style == 1 % uniform distribution
    d_s_ratio = sqrt(vf*4/pi);
else % layered
    d_s_ratio = 0;
end
F = (d_s_ratio*(Em/E2f - 1)+1)^-1; % concentration factor Gibson Eq. 4.38
Y2_tens = E2c*sLm_tens/Em/F; % Gibson Eq. 4.35
Y2_compr = E2c*sLm_compr/Em/F; % Gibson Eq. 4.35
% Out-of-plane strength
Y3_tens = Y2_tens; % Daniel 5.8 Out-of-plane loading p.115
Y3_compr = Y2_compr;
% Shear strength
F = (d_s_ratio*(Gm/G12f-1)+1)^-1; % Gibson Eq. 4.41
Y12 = G12c*sLTm/Gm/F; % Gibson Eq. 4.35
Y31 = Y12; % Daniel 5.8 Out-of-plane loading p.115
Y23 = Y2_tens;
%% Density
rho_c = rho_f*vf+rho_m*(1-vf);
