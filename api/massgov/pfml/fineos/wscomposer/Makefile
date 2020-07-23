#
# Makefile to fetch XML Schema Definition (XSD) files for Web Services Composer APIs.
#
# This is only needed if the API has changed. The output files should be committed to version control.
#

WSCOMPOSER_URL := https://idt-claims-webapp.masspfml.fineos.com/wscomposer/webservice?userid=CONTENT
CURL := curl --fail
TIDY := tidy -xml -indent -wrap 120

TARGETS = EmployeeRegisterService.Request.xsd \
       EmployeeRegisterService.Response.xsd \
       ReadEmployer.Request.xsd \
       ReadEmployer.Response.xsd

update: $(TARGETS)

clean:
	rm $(TARGETS)

%.Request.xsd:
	@echo " ==> $@"
	$(CURL) "$(WSCOMPOSER_URL)&config=$*&Request-XSD" | $(TIDY) >$@

%.Response.xsd:
	@echo " ==> $@"
	$(CURL) "$(WSCOMPOSER_URL)&config=$*&Response-XSD" | $(TIDY) >$@
