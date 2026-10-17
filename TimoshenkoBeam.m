%................................................................
function [stiffness,mass] = ...
    TimoshenkoBeam(GDof,numberElements,LElem,EI,rhoA,GIp,Im,e,kGA,rhoI)
% Dam Timoshenko uon - xoan (cung cach dung voi BernoulliBeam)
%   Bac tu do moi nut: [w theta phi] (do vong, goc xoay uon, goc xoan)
%   EI, rhoA, GIp, Im, e : nhu BernoulliBeam (gia tri tren tung phan tu)
%   kGA  : do cung cat ngang hieu dung kappa*G*A (N), Inf -> bo qua bien dang cat
%   rhoI : quan tinh xoay cua mat cat quanh truc uon (kg.m), = sum(rho*z^2*dA)
%
%   Phan tu dung ham dang "chinh xac" cua dam Timoshenko (Friedman & Kosmatka,
%   1993): khong bi khoa cat (shear locking), cho chuyen vi tinh chinh xac tai nut.
%   Voi kGA = Inf va rhoI = 0, ma tran trung khop BernoulliBeam.
%   Ky hieu Phi = 12*EI/(kGA*L^2).

if nargin < 9 || isempty(kGA)
    kGA = Inf(size(EI));
end
if nargin < 10 || isempty(rhoI)
    rhoI = zeros(size(EI));
end
if isscalar(kGA),  kGA  = kGA*ones(size(EI));  end
if isscalar(rhoI), rhoI = rhoI*ones(size(EI)); end

mass = zeros(GDof);
stiffness = zeros(GDof);
L = LElem;
for j = 1:numberElements
    % elementDof: element degrees of freedom (Dof)
    elementDof = (j*3-2:(j+1)*3);
    p = 12*EI(j)/(kGA(j)*L^2);   % Phi = 0 khi kGA = Inf

    % Do cung uon + cat
    k1 = EI(j)/((1+p)*L^3)*[12      6*L          -12     6*L;
                            6*L     (4+p)*L^2    -6*L    (2-p)*L^2;
                            -12     -6*L         12      -6*L;
                            6*L     (2-p)*L^2    -6*L    (4+p)*L^2];
    % Do cung xoan
    k2 = GIp(j)/L*[1 -1; -1 1];

    % Khoi luong tinh tien (rhoA)
    a1 = 70*p^2 + 147*p + 78;
    a2 = (35*p^2 + 77*p + 44)*L/4;
    a3 = 35*p^2 + 63*p + 27;
    a4 = (35*p^2 + 63*p + 26)*L/4;
    a5 = (7*p^2 + 14*p + 8)*L^2/4;
    a6 = (7*p^2 + 14*p + 6)*L^2/4;
    m1 = rhoA(j)*L/(210*(1+p)^2)*[a1   a2   a3  -a4;
                                  a2   a5   a4  -a6;
                                  a3   a4   a1  -a2;
                                 -a4  -a6  -a2   a5];
    % Quan tinh xoay cua mat cat (rhoI)
    b1 = (15*p - 3)*L;
    b2 = (10*p^2 + 5*p + 4)*L^2;
    b3 = (5*p^2 - 5*p - 1)*L^2;
    m1 = m1 + rhoI(j)/(30*(1+p)^2*L)*[ 36  -b1  -36  -b1;
                                      -b1   b2   b1   b3;
                                      -36   b1   36   b1;
                                      -b1   b3   b1   b2];
    % Quan tinh xoan
    m2 = Im(j)*L*[1/3 1/6; 1/6 1/3];
    % Lien ket quan tinh uon - xoan (do lech tam e), tich phan N_w^T * N_phi
    m3 = -rhoA(j)*e(j)*L/(1+p)*[(20*p+21)/60       (10*p+9)/60;
                                (5*p+6)*L/120      (5*p+4)*L/120;
                                (10*p+9)/60        (20*p+21)/60;
                                -(5*p+4)*L/120     -(5*p+6)*L/120];

    % stiffness and mass matrices
    stiffness(elementDof([1 2 4 5]),elementDof([1 2 4 5])) = ...
        stiffness(elementDof([1 2 4 5]),elementDof([1 2 4 5])) + k1;
    stiffness(elementDof([3 6]),elementDof([3 6])) = ...
        stiffness(elementDof([3 6]),elementDof([3 6])) + k2;
    mass(elementDof([1 2 4 5]),elementDof([1 2 4 5])) = ...
        mass(elementDof([1 2 4 5]),elementDof([1 2 4 5])) + m1;
    mass(elementDof([3 6]),elementDof([3 6])) = ...
        mass(elementDof([3 6]),elementDof([3 6])) + m2;
    mass(elementDof([1 2 4 5]),elementDof([3 6])) = ...
        mass(elementDof([1 2 4 5]),elementDof([3 6])) + m3;
    mass(elementDof([3 6]),elementDof([1 2 4 5])) = ...
        mass(elementDof([3 6]),elementDof([1 2 4 5])) + m3';
end
