# NIMBUS-9¾ broom -- convenience targets.
# Python is the only hard dependency; `make rust` adds the compiled core.

.PHONY: rust test bench scenarios clean

# Build the hard-real-time control core (Rust cdylib).
rust:
	cd rust/nimbus_core && cargo build --release

# Run the test suite (backend-parity tests auto-skip if the core isn't built).
test:
	python -m pytest -q

# Latency / jitter benchmark: Python vs Rust control core.
bench: rust
	python tools/bench.py

# Run every scenario on the Rust core.
scenarios: rust
	python scenarios/run.py all --backend rust

clean:
	cd rust/nimbus_core && cargo clean
	rm -rf scenarios/out __pycache__ */__pycache__ .pytest_cache
