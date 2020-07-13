#
# Makefile to build Pydantic models for FINEOS APIs.
#
# This is only needed if the API has changed. The output files should be committed to version control.
#

MODELS = customer_api.py

models: $(MODELS)

clean:
	rm $(MODELS)

%.py: %.cleaned.yaml
	poetry run datamodel-codegen --input $< --output $@
	poetry run black $@

# Fix some issues in the OpenAPI file.
%.cleaned.yaml: %.yaml
	perl -pe "s/format: string//; s/format: money/format: decimal/; s/format: date-time/format: date/" $< >$@

# This is difficult to automate as both an oauth2 session and valid userid header are needed.
customer_api.yaml:
	$(error Please fetch https://dt1-api.masspfml.fineos.com/customer-services/openapi.yaml manually)
