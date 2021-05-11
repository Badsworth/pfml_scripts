PORTAL_PATHS := . ../infra/portal ../.github/workflows/portal-deploy.yml
release-notes: refs=origin/deploy/portal/stage..origin/main
release-notes: ## Generate PORTAL release notes for $refs (defaults between stage and test)
	@git log --pretty='format: * %s' $(refs) -- $(PORTAL_PATHS) | \
	sed -E 's;^ \* \[*((API|CP|EDM|EMPLOYER|END|INFRA|PUB|DFMLBI|PSD)-[0-9]+)[] :]*(.*); \* [\1](https://lwd.atlassian.net/browse/\1): \3;' | \
	sed -E 's;\(#([0-9]+)\);([#\1](https://github.com/EOLWD/pfml/pull/\1));'

release-list: refs=origin/deploy/portal/stage..origin/main
release-list: ## Generate comma-separated list of ticket ids for $refs
	@git log --pretty='format: * %s' $(refs) -- $(PORTAL_PATHS) | \
	grep -E '(API|CP|EDM|EMPLOYER|END|INFRA|PUB|DFMLBI|PSD)-[0-9]+' | \
	sed -E 's/.*((API|CP|EDM|EMPLOYER|END|INFRA|PUB|DFMLBI|PSD)-[0-9]+)[] :]*(.*)/\1/g' | tr '\n' ',' | sed 's/,$$//'

PORTAL_RELEASE_BRANCHES := $(addprefix origin/, main deploy/portal/stage deploy/portal/prod deploy/portal/performance deploy/portal/training deploy/portal/uat deploy/portal/breakfix deploy/portal/cps-preview)
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
