/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2406                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      k;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -2 0 0 0 0];

// U=1.54, I=5% → k = 1.5 (U I)^2 ≈ 0.0089  (HVAC-style intensity inlet)
internalField   uniform 0.0089;

boundaryField
{
    tileInlet
    {
        type            turbulentIntensityKineticEnergyInlet;
        intensity       0.05;
        value           uniform 0.0089;
    }
    returnOutlet
    {
        type            inletOutlet;
        inletValue      uniform 0.0089;
        value           uniform 0.0089;
    }
    "(floorRack|floorHot|ceiling|rackCanopy|front|back|sideCold|sideHot|floor_.*|ceil_.*|rackTop.*|rackSide.*)"
    {
        type            kqRWallFunction;
        value           uniform 0.0089;
    }
}


// ************************************************************************* //
