# strudel-skills · local dev
#
# First run:    make install   (installs the web app deps)
# Quick start:  make play       (backend API + React app at :5273)
# Stop backend: make stop

PORT ?= 4747
PIDFILE := .server.pid
WEB_URL := http://localhost:5273/

.PHONY: help install play serve web stop status list

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
