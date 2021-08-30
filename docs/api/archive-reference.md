# Archived Features Overview (API)

In accordance with the [archive spec](https://lwd.atlassian.net/wiki/spaces/API/pages/1488847498/Tech+Spec+Process+for+Archiving+Code), this document serves as documentation for archived API features.

## Bank of America Integration

https://github.com/EOLWD/pfml/tree/archive/bank-of-america

DFML initially had plans to issue debit cards through Bank of America.

Code was written to generate mock data files for the integration.

Then the Bank of America work was put on indefinite hold as Bank of America
suspended any new integrations with benefit programs in late 2020.

## Bulk user import

https://github.com/EOLWD/pfml/tree/archive/bulk-user-import

Before Leave Admins could self-register and verify, we had two manual processes for reaching out to leave admins and importing them into the system: one using a Formstack survey, and another was a tool that supported importing Leave Admin users from one or more CSV files stored locally or in S3.

The Formstack importer was related to the leave admin outreach work, and while it did get deployed, it was sidestepped with the bulk imports instead. After self-registration/verification launched, the bulk-imports process was discontinued as well. Bulk import data was duplicated to Sharepoint at `EOL-PFMLPROJECT > Shared Documents > General > Service Desk > POC Loads`.

## MMARs integration

https://github.com/EOLWD/pfml/tree/archive/mmars-integration

Manual/MMARs/payment voucher was the original payment processing approach/integration, but PUB payments is the current payment processing for PFML since late June/early July 2021.
