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
    object      nut;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      [0 2 -1 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    tileInlet
    {
        type            calculated;
        value           uniform 0;
    }
    returnOutlet
    {
        type            calculated;
        value           uniform 0;
    }
    "(floorRack|floorHot|ceiling|rackCanopy|front|back|sideCold|sideHot|floor_.*|ceil_.*|rackTop.*|rackSide.*)"
    {
        // HVAC validation reference (nutUSpaldingWallFunction)
        type            nutUSpaldingWallFunction;
        value           uniform 0;
    }
}


// ************************************************************************* //
