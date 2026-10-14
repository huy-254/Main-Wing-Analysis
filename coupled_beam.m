%% Mo hinh dam cho toan bo canh (doi xung qua y = 0)
% Cac dac trung mat cat duoc tinh cho nua canh phai (y = 0..y_tip),
% sau do lay doi xung sang nua canh trai (y = -y_tip..0).
% Nut trung tam (y = 0) co chi so n_half trong luoi toan canh.
n_half = length(y_coord);
mirror = @(p) [fliplr(p(2:end)) p]; % [trai | phai], dung chung nut y = 0

y_full = [-fliplr(y_coord(2:end)) y_coord];
c_full = mirror(c_length(:)');
x_LE_full = mirror(x_coord(:)');
x_E_full = mirror(x_E(:)');
xc_full = mirror(xc_airfoil(:)');
EI_full = mirror(EI(:)');
GJ_full = mirror(GJ(:)');
m_full = mirror(m_airfoil(:)');
Im_full = mirror(Im(:)');

elementLength = dy;
numberElements = length(y_full)-1;
GDof = 3*(numberElements+1);

% Gia tri trung binh tren phan tu
avg = @(p) (p(2:end)+p(1:end-1))/2;
EI_elem = avg(EI_full);
GJ_elem = avg(GJ_full);
m_elem = avg(m_full);
Im_elem = avg(Im_full);
e = (avg(xc_full)-avg(x_E_full)).*avg(c_full); % do lech tam (m), theo day cung tung phan tu

%stiffess matrix and mass matrix
[stiffness,mass]=...
    BernoulliBeam(GDof, numberElements, elementLength, EI_elem, m_elem, GJ_elem, Im_elem, e);

%boundary conditions and solution
% Lien ket voi than tai y = +-fix_loc: khoa vong w va goc xoan phi
node_fix_R = n_half + round(fix_loc/dy);
node_fix_L = n_half - round(fix_loc/dy);
prescribedDof = [3*node_fix_L-2:3*node_fix_L 3*node_fix_R-2:3*node_fix_R];
activeDof = setdiff((1:GDof)',prescribedDof);
[V,Df] = eig(stiffness(activeDof,activeDof),...
    mass(activeDof,activeDof));
Df = diag(sqrt(Df));
[Df,ii] = sort(Df);
Df = Df/2/pi;
V_all = zeros(GDof,length(Df));
V_all(activeDof,:) = V(:,ii);

% Tach mode doi xung / phan doi xung
% Khi hai nua canh tach roi (vd. ngam ca 3 bac tu do tai +-fix_loc), moi tan so
% xuat hien 2 lan; eig tra ve to hop tuy y (vd. chi 1 ben dao dong). Chieu
% khong gian cua moi cum tan so trung nhau len phan doi xung va phan doi xung.
% Phep phan chieu y -> -y: w(-y) = w(y), theta(-y) = -theta(y), phi(-y) = phi(y)
mode_type = strings(1,modeNumber_f);
k = 1;
while k <= modeNumber_f
    j = k;
    while j < length(Df) && Df(j+1)-Df(k) < 1e-3*Df(k)
        j = j+1;
    end
    W = V_all(:,k:j);
    W_mir = zeros(size(W));
    for d = 1:3 % phan chieu: dao thu tu nut, doi dau theta
        W_mir(d:3:end,:) = flipud(W(d:3:end,:))*(1-2*(d==2));
    end
    if j > k % cum tan so trung nhau: tao co so doi xung / phan doi xung
        [Us,Ss,~] = svd((W+W_mir)/2,'econ');
        [Ua,Sa,~] = svd((W-W_mir)/2,'econ');
        s = diag(Ss); a = diag(Sa); tol = 1e-3*max([s; a]);
        W = [Us(:,s>tol) Ua(:,a>tol)];
        types = [repmat("doi xung",1,sum(s>tol)) repmat("phan doi xung",1,sum(a>tol))];
        f_new = zeros(1,size(W,2));
        for c = 1:size(W,2) % chuan hoa theo ma tran khoi luong, tan so theo thuong Rayleigh
            W(:,c) = W(:,c)/sqrt(W(:,c)'*mass*W(:,c));
            f_new(c) = sqrt(W(:,c)'*stiffness*W(:,c))/2/pi;
        end
        [f_new,order] = sort(f_new);
        V_all(:,k:j) = W(:,order);
        Df(k:j) = f_new;
        types = types(order);
    else
        if norm(W-W_mir) < norm(W+W_mir)
            types = "doi xung";
        else
            types = "phan doi xung";
        end
    end
    mode_type(k:j) = types(1:j-k+1);
    k = j+1;
end
mode_type = mode_type(1:modeNumber_f);
Vf = V_all(:,1:modeNumber_f);

% Force matrix
% Bo phan luc lien ket ra khoi F_shear, M_t: o mo hinh toan canh phan luc
% do cac goi tai +-fix_loc tu sinh ra.
idx_fix = round(fix_loc/dy);
F_shear_ext = F_shear;
F_shear_ext(1:idx_fix) = F_shear_ext(1:idx_fix)-F_react;
M_t_ext = M_t;
M_t_ext(1:idx_fix) = M_t_ext(1:idx_fix)-M_react;

F0=[0 F_shear_ext(1:end-1)-F_shear_ext(2:end) 0];
F_mat  = (F0(1:end-1)+F0(2:end))/2; % tai nut nua canh phai

M0=[0 M_t_ext(1:end-1)-M_t_ext(2:end) 0];
Mt_mat  = (M0(1:end-1)+M0(2:end))/2;

% Doi xung sang toan canh; nut y = 0 nhan tai tu ca hai nua canh
F_full = mirror(F_mat);
F_full(n_half) = 2*F_mat(1);
Mt_full = mirror(Mt_mat);
Mt_full(n_half) = 2*Mt_mat(1);

force_mat = zeros(GDof,1);
force_mat(1:3:end) = F_full';
force_mat(3:3:end) = Mt_full';
deflection = zeros(GDof,1);
deflection(activeDof) = (stiffness(activeDof,activeDof))\force_mat(activeDof);
