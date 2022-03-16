SHELL = /bin/bash -o pipefail
INFRA_PATHS := ./pfml-aws ./monitoring

release-notes: refs=origin/deploy/api/stage..origin/main
release-notes: ## Generate INFRA release notes for $refs (defaults between stage and test)
	@git log --pretty='format: * %s' $(refs) -- $(INFRA_PATHS) | \
	sed -E 's;^ \* \[*([A-Za-z]{2,}-[0-9]+)[] :]*(.*); \* [\1](https://lwd.atlassian.net/browse/\1): \2;' | \
	sed -E 's;\(#([0-9]+)\);([#\1](https://github.com/EOLWD/pfml/pull/\1));'

release-list: refs=origin/deploy/api/stage..origin/main
release-list: ## Generate comma-separated list of ticket ids for $refs
	@git log --pretty='format: %s' $(refs) -- $(INFRA_PATHS) | \
	grep --extended-regexp --only-matching '[A-Za-z]{2,}-[0-9]+' | \
	tr '\n' ',' | sed 's/,$$//'

INFRA_RELEASE_BRANCHES := $(addprefix origin/, main deploy/admin-portal/stage deploy/admin-portal/prod deploy/admin-portal/performance deploy/admin-portal/training deploy/admin-portal/uat deploy/admin-portal/breakfix deploy/admin-portal/cps-preview deploy/admin-portal/long deploy/admin-portal/trn2)
whats-released-short: ## List latest version tag on release branches
	@for branch in $(INFRA_RELEASE_BRANCHES); do \
		echo " * $$branch: $$(git describe --tags --match admin-portal/v* $$branch)"; \
	done
