%................................................................
function[stiffness,mass]=...
    BernoulliBeam(GDof,numberElements,LElem,EI,rhoA,GIp,Im,e)
mass=zeros(GDof);
stiffness=zeros(GDof);
% calculation of the system stiffness matrix and mass
for j=1:numberElements
    % elementDof:element degrees of freedom(Dof)
    elementDof=(j*3-2:(j+1)*3);
    % length of element
    
    k1=EI(j)/(LElem)^3*[12 6*LElem -12 6*LElem;
        6*LElem 4*LElem^2 -6*LElem 2*LElem^2;
        -12 -6*LElem 12 -6*LElem;
        6*LElem 2*LElem^2 -6*LElem 4*LElem^2];
    k2=GIp(j)/LElem*[1 -1; -1 1];
    
    
    m1=rhoA(j)*LElem/420*[156 22*LElem 54 -13*LElem;
        22*LElem 4*LElem^2 13*LElem -3*LElem^2;
        54 13*LElem 156 -22*LElem;
        -13*LElem -3*LElem^2 -22*LElem 4*LElem^2];
    m2=Im(j)*LElem*[1/3 1/6; 1/6 1/3];
    m3=-rhoA(j)*e(j)*LElem*[7/20 3/20;
        1/20*LElem 1/30*LElem;
        3/20 7/20;
        -1/30*LElem -1/20*LElem];
    
    % stiffnes and mass matrices
    stiffness(elementDof([1 2 4 5]),elementDof([1 2 4 5]))=...
        stiffness(elementDof([1 2 4 5]),elementDof([1 2 4 5]))+k1;
    stiffness(elementDof([3 6]),elementDof([3 6]))=...
        stiffness(elementDof([3 6]),elementDof([3 6]))+k2;
    mass(elementDof([1 2 4 5]),elementDof([1 2 4 5]))=...
        mass(elementDof([1 2 4 5]),elementDof([1 2 4 5]))+m1;    
    mass(elementDof([3 6]),elementDof([3 6]))=...
        mass(elementDof([3 6]),elementDof([3 6]))+m2;
    mass(elementDof([1 2 4 5]),elementDof([3 6]))=...
        mass(elementDof([1 2 4 5]),elementDof([3 6]))+m3;    
    mass(elementDof([3 6]),elementDof([1 2 4 5]))=...
        mass(elementDof([3 6]),elementDof([1 2 4 5]))+m3';
end