# NIMBUS-9¾ broom -- convenience targets.
# Python is the only hard dependency; `make rust` adds the compiled core.

.PHONY: rust embedded test bench scenarios clean

# Build the hard-real-time control core (Rust cdylib) for the host.
rust:
	cd rust/nimbus_core && cargo build --release

# Cross-compile the SAME core, no_std, for a real flight MCU (Cortex-M4F).
# Produces libnimbus_core.a to link into firmware (placement-init, no heap).
embedded:
	rustup target add thumbv7em-none-eabihf
	cd rust/nimbus_core && cargo build --release \
		--target thumbv7em-none-eabihf --no-default-features --features poc-panic
	@echo "built: rust/nimbus_core/target/thumbv7em-none-eabihf/release/libnimbus_core.a"

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
