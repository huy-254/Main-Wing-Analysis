function FOS = TWstrength_3D_chen2020(E1_layer, E2_layer, theta_layer, G12_layer, ...
    G23_layer, nju12_layer, nju23_layer, Y1_tens_layer, Y2_tens_layer, ...
    Y1_compr_layer, Y2_compr_layer, Y12_layer, Y23_layer, Y31_layer, strain_xy)
%% Tsai-Wu criterion for failure test of composite laminate
n = length(theta_layer);
FOS = zeros(n,1);
for i=1:n
    c = cos(theta_layer(i));
    s = sin(theta_layer(i));
    E1 = E1_layer(i);
    E2 = E2_layer(i);
    G12 = G12_layer(i);
    G23 = G23_layer(i);
    nju12 = nju12_layer(i);
    nju23 = nju23_layer(i);
    % S_12 matrix (Gibson eq. 2.25)
    S11 = 1/E1;
    S12 = -nju12/E1;
    S22 = 1/E2;
    S23 = -nju23/E2;
    S44 = 1/G23;
    S66 = 1/G12;
    S = [S11 S12 S12 0 0 0;
        S12 S22 S23 0 0 0;
        S12 S23 S22 0 0 0;
        0 0 0 S44 0 0;
        0 0 0 0 S66 0;
        0 0 0 0 0 S66];
    % Q_12 matrix
    % Q = inv(S);
    T = [c^2 s^2 0 0 0 2*c*s;
        s^2 c^2 0 0 0 -2*c*s;
        0 0 1 0 0 0;
        0 0 0 c s 0;
        0 0 0 -s c 0;
       -c*s c*s 0 0 0 c^2-s^2];
    % strain_12
    strain_xy(3) = strain_xy(3)/2;
    strain_12 = T*strain_xy; % Gibson eq. 2.33
    strain_12(3) = strain_12(3)*2;
    % sigma_12 in the layer
    sigma_12 = S\strain_12;
    % f1, f2, f3, f11, f12, ...
    f1 = 1/Y1_tens_layer(i) - 1/Y1_compr_layer(i); % Daniel 6.32, 6.33, 6.35
    f2 = 1/Y2_tens_layer(i) - 1/Y2_compr_layer(i);
    f3 = 1/Y2_tens_layer(i) - 1/Y2_compr_layer(i);
    f11 = 1/(Y1_tens_layer(i)*Y1_compr_layer(i));
    f22 = 1/(Y2_tens_layer(i)*Y2_compr_layer(i));
    f33 = 1/(Y2_tens_layer(i)*Y2_compr_layer(i));
    f44 = 1/(Y23_layer(i)^2);
    f55 = 1/(Y31_layer(i)^2);
    f66 = 1/(Y12_layer(i)^2);
    f12 = -sqrt(f11*f22)/2; % Daniel 6.40
    f31 = f12;
    f23 = f22 - f44/2;
    if (sigma_12(1) > 0)
        f12 = 1/(2*Y1_tens_layer(i))*(1/Y2_compr_layer(i) - 1/Y2_tens_layer(i));
    else
        f12 = -1/4/Y1_compr_layer(i)/Y1_tens_layer(i);
    end
    a = f11*sigma_12(1)^2 + f22*sigma_12(2)^2 + f33*sigma_12(3)^2 + ...
        f44*sigma_12(4)^2 + f55*sigma_12(5)^2 + f66*sigma_12(6)^2 + ...
        2*f12*sigma_12(1)*sigma_12(2) + 2*f23*sigma_12(2)*sigma_12(3) + ...
        2*f31*sigma_12(3)*sigma_12(1);
    b = f1*sigma_12(1) + f2*sigma_12(2) + f3*sigma_12(3);
    % Factor of safety
    % Tsai-Wu equation (Daniel eq. 6.59)
    FOS(i) = (-b + sqrt(b^2 + 4*a))/(2*a);
end