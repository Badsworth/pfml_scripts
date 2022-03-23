.DEFAULT_GOAL := help
ADMIN_PORTAL_PATHS := . ../infra/admin-portal

help: ## Displays this help screen
	@grep -Eh '^[[:print:]]+:.*?##' $(MAKEFILE_LIST) | \
	sort -d | \
	awk -F':.*?## ' '{printf "\033[36m%s\033[0m\t%s\n", $$1, $$2}' | \
	column -t -s "$$(printf '\t')"
	@echo ""

format: ## Format code
	npm run format

start-release: ## Creates a new release series. Increments the Portal's major version number.
	pushd ../bin/ci && poetry run scripted-releases --app admin-portal start-release $(args) && popd

update-release: ## Updates an in-progress release series. Increments the Portal's RC number.
	pushd ../bin/ci && poetry run scripted-releases --app admin-portal update-release $(args) && popd

finalize-release: ## Marks a release series as approved to go to prod. Enables hotfixes; disables updates.
	pushd ../bin/ci && poetry run scripted-releases --app admin-portal finalize-release $(args) && popd

hotfix: ## Alters a release series that already went to prod. Increments the Portal's minor version number.
	pushd ../bin/ci && poetry run scripted-releases --app admin-portal hotfix $(args) && popd

release-notes: refs=origin/deploy/admin-portal/stage..origin/main
release-notes: ## Generate ADMIN_PORTAL release notes for $refs (defaults between stage and test)
	@git log --pretty='format: * %s' $(refs) -- $(ADMIN_PORTAL_PATHS) | \
	sed -E 's;^ \* \[*([A-Za-z]{2,}-[0-9]+)[] :]*(.*); \* [\1](https://lwd.atlassian.net/browse/\1): \2;' | \
	sed -E 's;\(#([0-9]+)\);([#\1](https://github.com/EOLWD/pfml/pull/\1));'

release-list: refs=origin/deploy/admin-portal/stage..origin/main
release-list: ## Generate comma-separated list of ticket ids for $refs
	@git log --pretty='format: * %s' $(refs) -- $(ADMIN_PORTAL_PATHS) | \
	grep --extended-regexp --only-matching '[A-Za-z]{2,}-[0-9]+' | \
	tr '\n' ',' | sed 's/,$$//'

# There is currently no deploy/admin-portal/infra-test branch.
# ADMIN_PORTAL_RELEASE_BRANCHES := $(addprefix origin/, main deploy/admin-portal/stage deploy/admin-portal/prod deploy/admin-portal/performance deploy/admin-portal/training deploy/admin-portal/uat deploy/admin-portal/breakfix deploy/admin-portal/cps-preview deploy/admin-portal/long deploy/admin-portal/trn2 deploy/admin-portal/infra-test)
ADMIN_PORTAL_RELEASE_BRANCHES := $(addprefix origin/, main deploy/admin-portal/stage deploy/admin-portal/prod deploy/admin-portal/performance deploy/admin-portal/training deploy/admin-portal/uat deploy/admin-portal/breakfix deploy/admin-portal/cps-preview deploy/admin-portal/long deploy/admin-portal/trn2)
where-ticket: ## Search release branches for $ticket
	@for b in $(ADMIN_PORTAL_RELEASE_BRANCHES); do echo "## $$b ##"; \
		git --no-pager log --oneline --decorate --grep=$(ticket) $$b; \
		echo ""; \
	done

whats-released: ## List latest commit on release branches
	@for branch in $(ADMIN_PORTAL_RELEASE_BRANCHES); do echo "## $$branch ##"; \
		echo " * Closest tag: $$(git describe --tags --match admin-portal/v* $$branch)"; \
		echo " * Latest commit: $$(git --no-pager log --oneline --decorate --color -n 1 $$branch)"; \
		echo ""; \
	done

whats-released-short: ## List latest version tag on release branches
	@for branch in $(ADMIN_PORTAL_RELEASE_BRANCHES); do \
		echo " * $$branch: $$(git describe --tags --match admin-portal/v* $$branch)"; \
	done
