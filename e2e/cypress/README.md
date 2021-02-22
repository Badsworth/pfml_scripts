Cypress Test Suite
==================

This README contains in-depth documentation on our Cypress test suite.

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
