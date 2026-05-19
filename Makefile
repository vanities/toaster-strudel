# strudel-skills · local dev
#
# Quick start:  make play
# Stop server:  make stop

PORT ?= 4747
PIDFILE := .server.pid
URL := http://localhost:$(PORT)/player/

.PHONY: help play serve open stop list status

help:
	@echo "strudel-skills"
	@echo ""
	@echo "  make play     start server and open the player in your browser"
	@echo "  make serve    start the static server (background, port $(PORT))"
	@echo "  make open     open the player URL ($(URL))"
	@echo "  make stop     stop the background server"
	@echo "  make status   show whether the server is running"
	@echo "  make list     list available tracks"

play: serve open

serve:
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "server already running (pid `cat $(PIDFILE)`, port $(PORT))"; \
	else \
		uv run python -m http.server $(PORT) > .server.log 2>&1 & echo $$! > $(PIDFILE); \
		sleep 0.4; \
		echo "serving on $(URL) (pid `cat $(PIDFILE)`)"; \
	fi

open:
	@open $(URL)

stop:
	@if [ -f $(PIDFILE) ]; then \
		kill `cat $(PIDFILE)` 2>/dev/null && echo "stopped pid `cat $(PIDFILE)`" || echo "process already gone"; \
		rm -f $(PIDFILE); \
	else \
		echo "no server running"; \
	fi

status:
	@if [ -f $(PIDFILE) ] && kill -0 `cat $(PIDFILE)` 2>/dev/null; then \
		echo "running · pid `cat $(PIDFILE)` · $(URL)"; \
	else \
		echo "stopped"; \
	fi

list:
	@ls -1 tracks/*.strudel | sed 's|tracks/||; s|\.strudel||'
