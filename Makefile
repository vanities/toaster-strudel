# strudel-skills · local dev
#
# First run:    make install   (installs the web app deps)
# Quick start:  make play       (backend API + React app at :5273)
# Stop backend: make stop

PORT ?= 4747
PIDFILE := .server.pid
WEB_URL := http://localhost:5273/
PC ?= pc

.PHONY: help install play serve web stop status list arrangements analyze sections-pc midi

help:
	@echo "strudel-skills"
	@echo ""
	@echo "  make install  install the web app deps (pnpm -C web install)"
	@echo "  make play     start the backend API + the React app ($(WEB_URL))"
	@echo "  make serve    start just the backend API (background, port $(PORT))"
	@echo "  make web      start just the React dev server (foreground, opens browser)"
	@echo "  make stop     stop the background backend"
	@echo "  make status   show whether the backend is running"
	@echo "  make list     list available tracks"
	@echo "  make arrangements  (re)build each track's whole-arc arrange.strudel from its sections"
	@echo ""
	@echo "  make analyze      re-run reference analysis (after adding songs) → cards + skills"
	@echo "  make midi         re-run MIDI-exact DNA (after adding .mid to midi-sourced/) → cards + skills"
	@echo "  make sections-pc  (optional) refresh allin1 section labels on the GPU box ($(PC))"

install:
	@pnpm -C web install

play: serve web

serve:
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "backend already running (pid `cat $(PIDFILE)`, port $(PORT))"; \
	else \
		PORT=$(PORT) node tools/server.mjs > .server.log 2>&1 & echo $$! > $(PIDFILE); \
		sleep 0.4; \
		echo "backend API on :$(PORT) (pid `cat $(PIDFILE)`)"; \
	fi

web:
	@echo "starting React app — $(WEB_URL)"
	@cd web && pnpm dev --open

stop:
	@if [ -f $(PIDFILE) ]; then \
		kill `cat $(PIDFILE)` 2>/dev/null && echo "stopped pid `cat $(PIDFILE)`" || echo "process already gone"; \
		rm -f $(PIDFILE); \
	else \
		echo "no backend running"; \
	fi

status:
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "backend running · pid `cat $(PIDFILE)` · :$(PORT) · app at $(WEB_URL)"; \
	else \
		echo "stopped"; \
	fi

list:
	@ls -1 tracks/*.strudel | sed 's|tracks/||; s|\.strudel||'

# Stitch each track's section files (NN.strudel) into one whole-arc
# arrange.strudel, so the player's "arc" toggle (🎼) and strudel.cc can play the
# full intended arrangement as a single continuous pattern. Re-run after editing
# sections. Pass ids to rebuild specific tracks:  make arrangements ARGS="v2-gen/crank-glade"
arrangements:
	@node tools/build-arrangements.mjs $(ARGS)

# ── reference-analysis pipeline ───────────────────────────────────────────────
# Add songs: edit tools/build-manifest.py (EXACT paths or BY_NAME terms), then:
#   make analyze        — local: manifest → stems+transcribe → BTC chords → sections → index → skills
#   make sections-pc    — optional GPU step: allin1 functional section labels (run before analyze to include)
analyze:
	python3 tools/build-manifest.py
	tools/.venv-transcribe/bin/python tools/transcribe.py --manifest tools/reference-manifest.json --out references/analysis --device cpu
	tools/.venv-btc/bin/python tools/augment_chords.py --out references/analysis
	@if [ -f tools/allin1-results.json ]; then \
		tools/.venv-transcribe/bin/python tools/augment_sections.py tools/allin1-results.json; \
	else \
		echo "(no tools/allin1-results.json — run 'make sections-pc' for functional section labels)"; \
	fi
	python3 tools/build-index.py
	python3 tools/distill-skills.py

# ── MIDI-exact DNA ────────────────────────────────────────────────────────────
# The note-level counterpart to `analyze`, for sequenced/chiptune VGM where a real
# MIDI exists (exact tempo/voices/harmony — no demucs/Basic-Pitch guessing). Drop
# a .mid into the vault's 02_SOURCES/Music/midi-sourced/<skill>/ (see
# tools/research-midi.md for sourcing), then:
#   make midi           — manifest → MIDI DNA cards → distill the MIDI block into skills
midi:
	python3 tools/build-midi-manifest.py
	tools/.venv-transcribe/bin/python tools/midi_dna.py --manifest tools/midi-manifest.json --out references/analysis
	python3 tools/distill-skills.py

sections-pc:
	python3 tools/build-manifest.py
	rsync -a --files-from=tools/xfer-list.txt "$$HOME/git/work/me/game/references/audio/" $(PC):~/refs/audio/
	scp -q tools/pc-manifest.json tools/allin1_batch.py $(PC):~/git/work/me/toaster-strudel/tools/
	ssh $(PC) 'cd ~/git/work/me/toaster-strudel && ~/venv-allin1/bin/python tools/allin1_batch.py'
	scp -q $(PC):~/allin1-results.json tools/allin1-results.json
	@echo "→ now run 'make analyze' to fold the section labels into cards + skills"
