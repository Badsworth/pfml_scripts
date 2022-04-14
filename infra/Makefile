SHELL = /bin/bash -o pipefail
INFRA_PATHS := ./pfml-aws ./monitoring ./bi

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

