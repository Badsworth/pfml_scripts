#
# Makefile to build Pydantic models for FINEOS APIs.
#
# This is only needed if the API has changed. The output files should be committed to version control.
#

MODELS = customer_api/spec.py group_client_api/spec.py

models: $(MODELS)

clean:
	rm -f $(MODELS) */*.cleaned.json

customer_api.yaml:
	$(error Please fetch https://documentation.fineos.com/support/documentation/ manually)

# Fix some issues in the OpenAPI file.
%.cleaned.json: %.json
	poetry run python preprocess-fineos-models-spec.py $< > $@

%.py: %.cleaned.json
	poetry run datamodel-codegen --field-constraints --input $< --output $@
	poetry run black $@
