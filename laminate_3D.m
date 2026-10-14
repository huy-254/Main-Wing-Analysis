function [A_lam, D_lam] = laminate_3D(E1_layer, E2_layer, theta_layer, ...
    t_layer, G12_layer, G23_layer, nju12_layer, nju23_layer)
n = length(theta_layer);
A_lam = zeros(6,6);
D_lam = zeros(6,6);
z = zeros(1,n+1);
for i=1:n+1
    if i == 1
        z(i) = -sum(t_layer)/2;
    else
        z(i) = z(i-1) + t_layer(i-1);
    end
end
for i=1:n
   c = cos(theta_layer(i));
   s = sin(theta_layer(i));
   T = [c^2 s^2 0 0 0 2*c*s;
        s^2 c^2 0 0 0 -2*c*s;
        0 0 1 0 0 0;
        0 0 0 c s 0;
        0 0 0 -s c 0;
       -c*s c*s 0 0 0 c^2-s^2];
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
   S_bar = T\S*T;
   Q_bar = inv(S_bar);  
   for m = 1:6
       for n = 1:6
           A_lam(m,n) = A_lam(m,n) + Q_bar(m,n)*(z(i+1) - z(i));
           D_lam(m,n) = D_lam(m,n) + Q_bar(m,n)*(z(i+1)^3 - z(i)^3)/3;
       end
   end
end

