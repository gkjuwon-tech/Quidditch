# NIMBUS-9¾ hardware full-stack
# Source of truth: cad/*.scad, bom/*.csv, firmware/*, analysis/*.
# Build artifacts (renders/, drawings/, build/) are regenerated from these.

OPENSCAD ?= openscad
PY       ?= python3
SIZE     ?= 1400x900

.PHONY: all bom cad pdf check clean help

help:
	@echo "make check  - flight+thermal budget and HAL self-test"
	@echo "make cad    - render every model to PNG views (build/views, renders/)"
	@echo "make pdf    - assemble the drawing package (drawings/) + BOM rollup"
	@echo "make all    - check + cad + pdf"
	@echo "make clean  - remove build/ (keeps committed renders/ drawings/)"

all: check cad pdf

# ---- engineering: prove it flies, doesn't melt, flies a match, and that
#      waving the broom actually commands flight through the real software ----
check:
	@$(PY) analysis/flight_thermal.py
	@echo
	@$(PY) analysis/endurance_match.py
	@echo
	@$(PY) analysis/snitch_endurance.py
	@echo
	@$(PY) analysis/altitude_ceiling.py
	@echo
	@$(PY) firmware/hal.py
	@echo
	@$(PY) firmware/rider_input.py

# ---- CAD: render all views (needs openscad; uses xvfb if headless) ------
cad:
	@bash scripts/render.sh $(SIZE)

# ---- drawings + BOM rollup (needs matplotlib) ---------------------------
pdf: cad
	@$(PY) scripts/make_pdf.py

# bom rollup alone (no rendering)
bom:
	@$(PY) scripts/make_pdf.py

clean:
	@rm -rf build
	@echo "cleaned build/ (renders/ and drawings/ are committed deliverables)"
