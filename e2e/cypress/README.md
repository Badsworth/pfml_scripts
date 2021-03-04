Cypress Test Suite
==================

This README contains in-depth documentation on our Cypress test suite.

Guidelines
----------

* E2E tests are expensive to run (slow), and fragile.  Any tests we add must meet the following criteria:
  * It tests integrated (not component level) functionality. Component functionality should be tested by the component's own test suite.
  * It covers new functionality that is not tested elsewhere (avoid hitting the same path many times).
  * The functionality it covers is critical for the operation of the business.
* It's OK to check multiple things in a single test. It's often better to add a new assertion to a test that is already exercising the flow you need than to write a whole new test for it. As a concrete example, we check both the employer response submission and the employer response notification e-mail in the same test, because separating these two things would require us to go back through the claim sumission and employer response process multiple times.
* We often share state between `it()` statements in a test.  This is discouraged by Cypress, but necessary here.  Because claim submission and adjudication flows are so slow, we often chain them before several `it()` blocks, and reuse the claim for multiple assertions. We share the submitted claim state using `cy.stash()`, a custom system built for retaining state between steps. When writing tests that cross multiple domains, test state (aliased data) is lost. `cy.stash()` works by writing our state data to the filesystem. `cy.stash()` should only be used at the top level of a test (never in helpers/action code).  Here are the common things we might stash:
  * Full Claims (under `claim`), which give us access to stuff like employer_fein, first_name, last_name, etc.
  * API Claim Submission Response (under `submission`), which gives us access to stuff like fineos_absence_id and application_id.
  * Credentials, (under `credentials`) wherever we need to create new ones in one block, then reuse them in another.
* Avoid `cy.wait()` with explicit wait times at all costs. Explicit wait times are extremely fragile and prevent our tests from getting faster as the system gets faster (ie: if claim submission or e-mail happens to speed up). This is a whole topic in itself, so we'll just refer to [Cypress' documentation](https://docs.cypress.io/guides/core-concepts/retry-ability.html) here.  There are a few cases where `cy.wait()` is necessary in our test suite, and they're mostly to resolve issues with Fineos DOM instability (and constrained to wait times of under 1 second).

Retries and dependent tests
----------------------------

Our test suite uses a Cypress feature called test retries. With retries, a failing test step will trigger Cypress to retry that particular step to see if it passes. Retries are useful for dealing with flakiness (eg: when the test hits an endpoint that occasionally times out), although they also mask inconsistency.

The important thing to know about retries is that they only operate on a per-test level, not per-suite.  So if you have a structure like this:
```typescript
describe("Denial Notifications", () => {

    it("Submits a claim", () => {
        // submit a claim.
    });

    it("Checks for a notification", () => {
        // Check for a notification.
    })
})
```
When this test is executed, if the claim submission step fails, it will be retried, and **regardless of whether it succeeds, the notification step will be run**. Since notification is usually a time consuming process that requires the claim to be submitted, this will lead to us spending a lot of time trying (then later, retrying) notifications we know for certain will never arrive (because the claim submission failed).

To work around this problem, we've introduced a helper, `bailIfThisTestFails()`. Calling this function will exit the suite if a particular test fails, skipping the rest of the tests entirely. Using this helper allows us to designate particular test functions as _required_ for the rest of the suite to pass.

Eg:

```typescript
describe("Denial Notifications", () => {

  it("Submits a claim", () => {
    bailIfThisTestFails();
    // submit a claim.
  });

  it("Checks for a notification", () => {
    // Check for a notification.
  })
})
```
This code will exit properly if the initial submission fails, skipping the notifications check. Note that it will still use retries, meaning that if either test function fails, it will first try that function again before exiting, and if it's able to succeed, it will allow progression onto the next step.
