Trigger Cypress Action
======================

This custom Github Action is designed to trigger the E2E test suite from deployment workflows. It avoids overlapping test runs by checking to see if a test workflow is already running before triggering one. When the triggered or detected run completes, the result will be reported by this action.
