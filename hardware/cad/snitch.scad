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

module snitch(beat = 16) {
    snitch_shell();
    // the real, flapping wings
    for (s = [-1, 1])
        translate([0, s * (R + 4), R * 0.15])
            rotate([0, 0, s * 90])
                mirror([0, s > 0 ? 0 : 1, 0])
                    animatronic_wing(span = R * 1.9, chord = R * 0.9,
                                     beat = s * beat);
    // the secret, if you cut it open
    if (cutaway) swarm_core(R, n = 4, fan_d = 16);
}

snitch(beat = beat);
