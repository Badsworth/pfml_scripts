.DEFAULT_GOAL := help
PORTAL_PATHS := . ../infra/portal

help: ## Displays this help screen
	@grep -Eh '^[[:print:]]+:.*?##' $(MAKEFILE_LIST) | \
	sort -d | \
	awk -F':.*?## ' '{printf "\033[36m%s\033[0m\t%s\n", $$1, $$2}' | \
	column -t -s "$$(printf '\t')"
	@echo ""

start-release: ## Creates a new release series. Increments the Portal's major version number.
	pushd ../bin/ci && poetry run scripted-releases --app portal start-release $(args) && popd

update-release: ## Updates an in-progress release series. Increments the Portal's RC number.
	pushd ../bin/ci && poetry run scripted-releases --app portal update-release $(args) && popd

finalize-release: ## Marks a release series as approved to go to prod. Enables hotfixes; disables updates.
	pushd ../bin/ci && poetry run scripted-releases --app portal finalize-release $(args) && popd

hotfix: ## Alters a release series that already went to prod. Increments the Portal's minor version number.
	pushd ../bin/ci && poetry run scripted-releases --app portal hotfix $(args) && popd

release-notes: refs=origin/deploy/portal/stage..origin/main
release-notes: ## Generate PORTAL release notes for $refs (defaults between stage and test)
	@git log --pretty='format: * %s' $(refs) -- $(PORTAL_PATHS) | \
	sed -E 's;^ \* \[*([A-Za-z]{2,}-[0-9]+)[] :]*(.*); \* [\1](https://lwd.atlassian.net/browse/\1): \2;' | \
	sed -E 's;\(#([0-9]+)\);([#\1](https://github.com/EOLWD/pfml/pull/\1));'

release-list: refs=origin/deploy/portal/stage..origin/main
release-list: ## Generate comma-separated list of ticket ids for $refs
	@git log --pretty='format: * %s' $(refs) -- $(PORTAL_PATHS) | \
	grep --extended-regexp --only-matching '[A-Za-z]{2,}-[0-9]+' | \
	tr '\n' ',' | sed 's/,$$//'

PORTAL_RELEASE_BRANCHES := $(addprefix origin/, main deploy/portal/stage deploy/portal/prod deploy/portal/performance deploy/portal/training deploy/portal/uat deploy/portal/breakfix deploy/portal/cps-preview deploy/portal/long deploy/portal/trn2 deploy/portal/infra-test)
where-ticket: ## Search release branches for $ticket
	@for b in $(PORTAL_RELEASE_BRANCHES); do echo "## $$b ##"; \
		git --no-pager log --oneline --decorate --grep=$(ticket) $$b; \
		echo ""; \
	done

whats-released: ## List latest commit on release branches
	@for branch in $(PORTAL_RELEASE_BRANCHES); do echo "## $$branch ##"; \
		echo " * Closest tag: $$(git describe --tags --match portal/v* $$branch)"; \
		echo " * Latest commit: $$(git --no-pager log --oneline --decorate --color -n 1 $$branch)"; \
		echo ""; \
	done

whats-released-short: ## List latest version tag on release branches
	@for branch in $(PORTAL_RELEASE_BRANCHES); do \
		echo " * $$branch: $$(git describe --tags --match portal/v* $$branch)"; \
	done
