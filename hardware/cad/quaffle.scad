// =====================================================================
//  QUAFFLE  --  ball/params.py quaffle(): radius 0.18 m, mass 0.5 kg
//  True scale: 180 mm shell radius (a touch bigger than a basketball).
//  The friendly one: soft, grippy, easy to catch. Quad-panel seams +
//  finger grooves so a player can actually hold it. No wings.
// =====================================================================
include <lib/common.scad>

R = 180;
cutaway = false;

module quaffle() {
    color(COL_RED) difference() {
        sphere(r = R);
        sphere(r = R - 6);                       // grippy foam wall
        vent_pattern(R, rings = 7, dimple = 7, depth = 4);
        // four longitudinal grip seams (like a leather quaffle)
        for (i = [0 : 3])
            rotate([0, 0, i * 90])
                rotate([90, 0, 0])
                    translate([0, 0, -R]) cylinder(h = R*2, r = 4);
        if (cutaway) translate([0, -R, 0]) cube([R*2, R*2, R*2], center = true);
    }
    // recessed grab handle ring (capacitive catch sensor lives here)
    color(COL_LEATHER) rotate_extrude() translate([R - 3, 0]) circle(r = 5);
    if (cutaway) swarm_core(R, n = 4, fan_d = 48);
}

quaffle();
