// =====================================================================
//  NIMBUS-9¾  shared CAD library
//  Everything is in MILLIMETRES. Reusable bits that show up on more
//  than one airframe live here: the ducted fan, the "looks like a ball,
//  is actually a vented swarm shell" shell, and an animatronic wing.
// =====================================================================

// ----- global render quality -----------------------------------------
$fn = $preview ? 48 : 96;

// gold / black / leather palette so the renders read as the props they are
COL_GOLD    = [0.83, 0.69, 0.22];
COL_BRASS   = [0.72, 0.55, 0.20];
COL_BLACK   = [0.12, 0.12, 0.13];
COL_LEATHER = [0.36, 0.22, 0.11];
COL_CARBON  = [0.18, 0.18, 0.20];
COL_RED     = [0.62, 0.13, 0.13];
COL_GLASS   = [0.55, 0.75, 0.85];

// ---------------------------------------------------------------------
//  ducted_fan(): the only thrust source we ever expose. A shrouded ring
//  with a hub + blades so NO open prop ever touches a finger. Used 8x on
//  the broom and (in miniature) as the hidden swarm rotor on the balls.
// ---------------------------------------------------------------------
module ducted_fan(duct_d = 90, duct_h = 34, blades = 5, hub_frac = 0.34) {
    wall = duct_d * 0.06;
    ro = duct_d / 2;
    ri = ro - wall;
    hub_r = ro * hub_frac;
    color(COL_CARBON) difference() {
        cylinder(h = duct_h, r = ro);
        translate([0, 0, -1]) cylinder(h = duct_h + 2, r = ri);
        // inlet bellmouth
        translate([0, 0, duct_h]) rotate_extrude()
            translate([ri, 0]) circle(r = wall * 0.9);
    }
    // hub
    color(COL_BLACK)
        translate([0, 0, duct_h * 0.5])
            cylinder(h = duct_h * 0.5, r = hub_r, center = true);
    // blades
    color([0.30, 0.30, 0.33])
        for (i = [0 : blades - 1])
            rotate([0, 0, i * 360 / blades])
                translate([hub_r * 0.7, 0, duct_h * 0.5])
                    rotate([0, 0, 28])
                        cube([ri - hub_r * 0.7, wall * 1.1, duct_h * 0.55],
                             center = true);
}

// ---------------------------------------------------------------------
//  vent_pattern(): golf-ball dimples drilled over a sphere of radius r.
//  Far away = a texture; up close = the ports the inner swarm breathes
//  and sees through. Returns a UNION of little spheres to subtract.
// ---------------------------------------------------------------------
module vent_pattern(r, rings = 7, dimple = 4, depth = 2.2) {
    for (a = [-80 : 160 / (rings - 1) : 80]) {
        ringr = r * cos(a);
        z = r * sin(a);
        n = max(4, round(rings * cos(a) * 2));
        for (i = [0 : n - 1])
            rotate([0, 0, i * 360 / n + a * 1.7])
                translate([ringr, 0, z])
                    sphere(r = dimple);
    }
}

// ---------------------------------------------------------------------
//  swarm_core(): the secret. A small cluster of micro ducted fans on a
//  gimbal frame -- the real lift. The Potterheads never see this; the
//  shell does. Shown here so the BOM has something to point at.
// ---------------------------------------------------------------------
module swarm_core(r, n = 4, fan_d = 22) {
    color([0.25, 0.26, 0.30]) sphere(r = r * 0.30);     // avionics ball
    for (i = [0 : n - 1])
        rotate([0, 0, i * 360 / n])
            translate([r * 0.42, 0, 0])
                rotate([0, 18, 0])
                    scale(fan_d / 90)
                        ducted_fan(duct_d = 90, duct_h = 30, blades = 4);
}

// ---------------------------------------------------------------------
//  animatronic_wing(): the lie, made beautiful. A thin filigree wing on
//  a hub that a coreless gearmotor flaps. Aerodynamically does ~nothing;
//  it exists so the crowd sees WINGS, not rotors. `beat` in degrees.
// ---------------------------------------------------------------------
module animatronic_wing(span = 70, chord = 34, beat = 18) {
    rotate([beat, 0, 0]) {
        // leading-edge spar
        color(COL_BRASS) rotate([0, 90, 0]) cylinder(h = span, r = 1.4);
        // membrane: thin tapered feathered vane
        color([0.95, 0.86, 0.55, 0.92])
            for (i = [0 : 11]) {
                f = i / 11;
                translate([span * f, 0, 0])
                    rotate([0, 0, -14 * f])
                        translate([0, -chord * (1 - f * 0.55) / 2, 0])
                            cube([span / 14, chord * (1 - f * 0.55), 0.5]);
            }
        // hub gear
        color(COL_GOLD) rotate([0, 90, 0]) cylinder(h = 6, r = 5);
    }
}
