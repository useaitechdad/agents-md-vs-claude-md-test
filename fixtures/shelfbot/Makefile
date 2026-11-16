TODAY ?= 2028-03-10

.PHONY: check run

# Tests need the vendored helpers on the path and a fixed clock.
check:
	PYTHONPATH=vendor:. SHELFBOT_TODAY=$(TODAY) python3 -m unittest discover -s tests -t .

run:
	PYTHONPATH=vendor:. python3 -m shelfbot $(ARGS)
