// =====================================================================
//  NIMBUS-9¾  BROOM  --  manned eVTOL, 1 rider   [STICK EDITION]
//  No body. No belly. No mercy. Just a thin broom HANDLE and BRISTLES,
//  exactly like the reference -- and it still actually flies.
//
//  How a bare stick lifts 120 kg (악으로 깡으로 / by sheer spite):
//  the handle IS the duct. A linear array of high-RPM micro ducted fans
//  lives INSIDE the shaft and exhausts straight down through flush
//  ventral louvres; the bristle root holds the rear lift cluster. Brutal
//  disc loading, but the silhouette stays a broomstick. Fan x-stations
//  are the exact layout from nimbus_fc/core/params.py.
//  Units: mm. (SI -> mm = x1000).  cutaway=true reveals the in-shaft fans.
// =====================================================================
include <lib/common.scad>

S       = 1000;          // metres -> mm
LEN     = 2.4 * S;       // 2400 mm overall
cutaway = false;

WOOD    = [0.40, 0.26, 0.13];
WOOD_HI = [0.50, 0.34, 0.17];
LEAF    = [0.80, 0.62, 0.24];
STRAND  = [0.58, 0.43, 0.17];

// fan stations [x(m), y(m), spin]; 8 fans inline in the shaft (params.py)
FAN_LAYOUT = [
    [ 0.90,  0.22,  1], [ 0.90, -0.22, -1],
    [ 0.30,  0.24, -1], [ 0.30, -0.24,  1],
    [-0.30,  0.24,  1], [-0.30, -0.24, -1],
    [-0.90,  0.26, -1], [-0.90, -0.26,  1],
];

// shaft radius at body-x (thin: Ø60 at the collar tapering to Ø30 tip)
SHAFT_X0 = -0.20 * S;     // collar end
SHAFT_X1 =  1.25 * S;     // grip tip
function shaft_r(x) =
    let (u = (x - SHAFT_X0) / (SHAFT_X1 - SHAFT_X0))
    30 - 15 * max(0, min(1, u));

// ----- the bare broom handle (the whole airframe) ----------------------
module handle() {
    color(WOOD)
        translate([SHAFT_X0, 0, 0]) rotate([0, 90, 0])
            cylinder(h = SHAFT_X1 - SHAFT_X0, r1 = 30, r2 = 15, $fn = 40);
    color(COL_BRASS) translate([SHAFT_X1, 0, 0]) sphere(r = 15);     // pommel
    // brass ferrules / binding rings -- the only adornment
    for (x = [1.05, 0.62, 0.20] * S)
        color(COL_BRASS)
            translate([x, 0, 0]) rotate([0, 90, 0])
                cylinder(h = 14, r = shaft_r(x) + 2, center = true, $fn = 32);
    // ventral exhaust louvres (where the lift leaves) + dorsal intake gills
    for (f = FAN_LAYOUT) {
        x = f[0] * S; r = shaft_r(x);
        color([0.12,0.09,0.05])                       // exhaust slot, underside
            translate([x, 0, -r + 3]) scale([1, 1.5, 1]) cylinder(h = 8, r = r*0.7, center = true, $fn = 24);
        color([0.18,0.13,0.07])                       // intake gill, topside
            translate([x, 0,  r - 4]) rotate([0,0,90])
                cube([r*0.9, 6, 5], center = true);
    }
}

// ----- in-shaft lift fans + cooling (only drawn in cutaway) ------------
module lift_fans() {
    for (f = FAN_LAYOUT) {
        x = f[0] * S; r = shaft_r(x);
        translate([x, 0, r - 6])                       // fan sits in the bore
            rotate([180, 0, 0])                        // exhaust downward
                mirror([0, f[2] > 0 ? 0 : 1, 0])
                    ducted_fan(duct_d = 2 * r - 6, duct_h = 1.6 * r, blades = 5);
    }
    // main-lift ducted fan, sized + placed to fit ENTIRELY inside the bristle
    // flare at its widest (mid-leaf). The flare frontal area is the disc-area
    // ceiling -- the honest physical price of keeping a broom silhouette.
    color(COL_CARBON)
        translate([-0.62 * S, 0, 0.11 * S]) rotate([0, -14, 0])
            translate([0, 0, -0.15 * S])
                ducted_fan(duct_d = 0.34 * S, duct_h = 100, blades = 7);
    // heat pipes: thin copper rods spreading motor heat down the 2.4 m shaft
    for (a = [40, 140, 220, 320])
        color([0.72, 0.45, 0.20])
            rotate([a, 0, 0])
                translate([SHAFT_X0, 9, 0])
                    rotate([0, 90, 0])
                        cylinder(h = SHAFT_X1 - SHAFT_X0 - 40, r = 2.4, $fn = 12);
    // SERIES-HYBRID range extender, all inside the slim shaft (challenge 4):
    //   SAF fuel bladder (forward) -> micro-turbine genset (aft) -> exhaust
    //   ejector that mixes cool bypass air and vents through the bristle root.
    color([0.86, 0.66, 0.22, 0.65])                       // sustainable-fuel bladder
        translate([0.18 * S, 0, 2]) rotate([0, 90, 0])
            cylinder(h = 0.66 * S, r1 = 13, r2 = 16, $fn = 28);
    color([0.58, 0.58, 0.64])                             // micro-turbine genset
        translate([-0.07 * S, 0, 2]) rotate([0, 90, 0])
            cylinder(h = 0.20 * S, r = 17, $fn = 28);
    color([0.32, 0.32, 0.34])                             // exhaust ejector to bristles
        translate([-0.25 * S, 0, 2]) rotate([0, -90, 0])
            cylinder(h = 0.10 * S, r1 = 15, r2 = 22, $fn = 24);
}

// ----- slim saddle + fold-out footpegs (no bulk) -----------------------
module saddle() {
    color([0.14,0.09,0.05])
        translate([0.34 * S, 0, 26]) scale([2.0, 0.85, 0.42]) sphere(r = 40);
    for (s = [-1, 1]) {
        color(COL_BRASS) translate([0.34*S, s*28, 30]) sphere(r = 5);
        color(WOOD) translate([0.44*S, s*60, -6]) rotate([0,0,s*8])
            cube([120, 22, 8], center = true);
    }
}

// ----- brass binding collar + compass at the bristle root --------------
module collar_and_gauge() {
    color(COL_BRASS)
        translate([-0.20 * S, 0, 0]) rotate([0, 90, 0])
            cylinder(h = 54, r = 38, center = true, $fn = 36);
    translate([-0.20 * S, 0, 34]) {
        color(COL_BRASS) cylinder(h = 11, r = 25, center = true, $fn = 36);
        color(COL_GLASS) translate([0,0,6]) cylinder(h = 3, r = 20, center = true, $fn = 36);
    }
    for (a = [30, 165, 285])
        rotate([a, 0, 0]) color(COL_BRASS)
            translate([-0.20*S, 0, 30]) cylinder(h = 6, r = 7, center = true, $fn = 20);
}

// ----- the bristle leaf: a dense 3-D brush of feathered strands --------
//  Every strand runs from the brass binding to a tip on an almond (leaf)
//  surface: width 0 at the collar, max mid-leaf, back to 0 at the tail
//  tip -> the canon Nimbus leaf, but a VOLUME of bristles, not a paddle.
module bristle_leaf() {
    root = [-0.235 * S, 0, 2];
    L    = 1.07 * S;
    Wy   = 0.34 * S;     // half-width at the widest point
    Wz   = 0.13 * S;     // half-thickness (flattened brush)
    bow  = 0.16 * S;     // upward arch toward the tail
    n    = 880;
    translate(root) {
        for (i = [0 : n - 1]) {
            t   = 0.04 + 0.96 * pow((i % 30) / 29, 0.9);
            a   = i * 137.5;
            hw  = pow(sin(180 * t), 0.5);
            sh  = (i % 5) / 4;
            color([0.55 + sh*0.22, 0.40 + sh*0.18, 0.14])
                hull() {
                    sphere(r = 4, $fn = 8);
                    translate([-t * L, cos(a) * hw * Wy,
                               sin(a) * hw * Wz + bow * sin(160 * t)])
                        sphere(r = 0.8, $fn = 6);
                }
        }
        // a few long hero flyaways converging past the tip
        color([0.5, 0.37, 0.14])
            for (i = [0 : 11])
                hull() {
                    sphere(r = 3, $fn = 8);
                    translate([-L * 1.05, (i - 5.5) * 1.6, bow * 0.7]) sphere(r = 0.4, $fn = 6);
                }
    }
}

module broom() {
    collar_and_gauge();
    bristle_leaf();
    saddle();
    if (cutaway) {
        // keep only the far half of the shaft so the bore opens to the camera
        intersection() {
            handle();
            translate([SHAFT_X0 - 50, -400, -400]) cube([LEN + 100, 400, 800]);
        }
        lift_fans();      // in-shaft EDFs + hybrid genset/tank + main lift + heat pipes
    } else {
        handle();
    }
}

broom();
