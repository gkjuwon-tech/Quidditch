// =====================================================================
//  GOLDEN SNITCH  --  ball/params.py snitch(): radius 0.04 m, mass 0.05 kg
//  True scale: 40 mm shell radius (≈ a walnut). The ONE canon ball with
//  wings, so it gets real flapping ones on coreless gearmotors. The wings
//  are theatre; lift comes from the hidden inner swarm. Don't tell anyone.
// =====================================================================
include <lib/common.scad>

R = 40;          // shell radius (matches snitch radius 0.04 m)
beat = $t * 0;   // set to e.g. 22*sin(360*$t) when animating an export

cutaway = false; // true -> slice the shell to reveal the swarm core

module snitch_shell() {
    color(COL_GOLD) difference() {
        sphere(r = R);
        sphere(r = R - 2.2);                 // hollow it (1.0 mm? thin gold-clad foam)
        vent_pattern(R, rings = 9, dimple = 2.4, depth = 1.8);
        // equator filigree groove
        rotate_extrude() translate([R - 0.4, 0]) circle(r = 1.2);
        if (cutaway) translate([0, -R, 0]) cube([R * 2, R * 2, R * 2], center = true);
    }
    // wing mounts: two brass nacelles at the equator
    for (s = [-1, 1])
        color(COL_BRASS)
            translate([0, s * (R - 1), 0])
                rotate([s * 90, 0, 0])
                    cylinder(h = 7, r = 5.5);
}

// The energy fix, hidden under the gold. The dimple VENTS (the ones the shell
// already has) double as a 5.8 GHz rectenna -- so the harvester adds ~0 form:
// it is the shell. Inside: a supercap ring (peak buffer for the jukes) and the
// harvester PMIC. Only ever visible in cutaway; the silhouette is unchanged.
module snitch_power_core() {
    // rectenna liner: a thin conductive shell just under the gold skin, the
    // "antenna side" of the dimple pattern that catches the beamed power
    color([0.86, 0.74, 0.30, 0.55])
        difference() {
            sphere(r = R - 2.4);
            sphere(r = R - 3.0);
            translate([0, -R, 0]) cube([R * 2, R * 2, R * 2], center = true);
        }
    // graphene supercap ring (SNT-17) -- the peak buffer that fires the jukes
    color([0.20, 0.21, 0.24])
        rotate_extrude() translate([R * 0.52, 0]) circle(r = R * 0.10);
    // harvester PMIC + tri-source bus puck (SNT-16/18), under the swarm
    color([0.10, 0.35, 0.18])
        translate([0, 0, -R * 0.18])
            cylinder(h = R * 0.10, r = R * 0.22, center = true);
}

module snitch(beat = 16) {
    snitch_shell();
    // the real, flapping wings
    for (s = [-1, 1])
        translate([0, s * (R + 4), R * 0.15])
            rotate([0, 0, s * 90])
                mirror([0, s > 0 ? 0 : 1, 0])
                    animatronic_wing(span = R * 1.9, chord = R * 0.9,
                                     beat = s * beat);
    // the secrets, if you cut it open: the lift swarm AND the power harvester
    if (cutaway) {
        snitch_power_core();
        swarm_core(R, n = 4, fan_d = 16);
    }
}

snitch(beat = beat);
