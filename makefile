
.DEFAULT_GOAL:=help

.PHONY: help clean build-dev build run

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

clean: ## Removes build assets
	rm -rf build dist

build-dev: ## Builds for development (slower)
	python setup.py py2app -A

build: clean ## Builds for release (faster)
	python setup.py py2app

run: ## Runs the app
	./dist/StatusPage\ Monitor.app/Contents/MacOS/StatusPage\ Monitor