// =====================================================================
//  BLUDGER  --  ball/params.py bludger(): radius 0.15 m, mass 1.2 kg
//  True scale: 150 mm shell radius. Looks like a menacing iron ball;
//  is actually a light foam shell over a swarm core. All threat, no skull.
//  No wings (not canon) -- just black, riveted, and rude.
// =====================================================================
include <lib/common.scad>

R = 150;
cutaway = false;

module bludger() {
    color(COL_BLACK) difference() {
        sphere(r = R);
        sphere(r = R - 8);                       // thick impact-foam wall
        vent_pattern(R, rings = 8, dimple = 6, depth = 4);
        if (cutaway) translate([0, -R, 0]) cube([R*2, R*2, R*2], center = true);
    }
    // two riveted equator bands -> "wrought iron" read
    for (tilt = [0, 90])
        rotate([tilt, 0, 0])
            color(COL_CARBON) rotate_extrude() translate([R - 1, 0]) square([3, 14], center = true);
    // rivets
    for (tilt = [0, 90])
        rotate([tilt, 0, 0])
            for (i = [0 : 17])
                rotate([0, 0, i * 20])
                    color([0.4,0.4,0.42]) translate([R, 0, 0]) sphere(r = 3.5);
    if (cutaway) swarm_core(R, n = 4, fan_d = 40);
}

bludger();
