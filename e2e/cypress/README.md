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

To work around this problem, we've introduced a helper, `cy.dependsOnPreviousPass();`. Calling this function will immediately fail the test if a dependent test fails.

Eg:

```typescript
describe("Denial Notifications", () => {

  const submit = it("Submits a claim", () => {
    // submit a claim.
  });

  it("Checks for a notification", () => {
    cy.dependsOnPreviousPass([submit]);
    // Check for a notification.
  })
})
```
This code will exit properly if the initial submission fails, failing the notifications check. Note that it will still use retries, meaning that if either test function fails, it will first try that function again before exiting, and if it's able to succeed, it will allow progression onto the next step.

Hanging Test
----------------------------
Hanging test are test/specs that "hang" or get stuck during a run.  Runs typically take slightly over 10 mins and when a run starts to exceed 20 mins - it's probably a hanger (_term I like to use to refer to a hanging test_) causing the delay.  

These hangers usually occur with tests that are "unstable" and below is how we can debug and suppress errors that cause a test to hang.  

- As mentioned hangers are usually in the "unstable" folder so first update the workflow [e2e-cypress.yml](e2e-cypress.yml) to run only the unstable tests.

- Make sure to turn on cypress debugging in Github Actions by adding this `env ` variable:

```yml
DEBUG: "cypress:*"
```
- Run as many tests needed (via your branch) to try and recreate a test to hang. As an example twenty runs (across different lower envs) may spawn two hangers. They seem to happen 10 to 20 percent of the time. 

- Once a test has hung, download the log information (from [Github Actions](https://github.com/EOLWD/pfml/runs/3087590445?check_suite_focus=true)) and start digging through the logs towards the end whenever the test stopped ... _Note: change the file extension to `.log` for easier searching and filtering._

<h3>Things to look for in the logs ...</h3>

The easiest and most common errors that cause hangers are _**Fineos page errors**_.  They can come in different flavors and we've identified 2 specific errors that get suppressed in the code. See example page error log below:

  ```log
  021-07-15T18:15:58.5182207Z [32;1mcypress:proxy:http:request-middleware [0mproxying request { req: { method: [32m'GET'[39m, proxiedUrl: [32m'https://perf-claims-webapp.masspfml.fineos.com/outofdatedataerror.jsp?errorid=bf9dc982-52f2-430c-bb07-bfdd56cdbd64&vsid=86922'[39m, headers: { host: [32m'perf-claims-webapp.masspfml.fineos.com'[39m, connection: [32m'keep-alive'[39m, [32m'upgrade-insecure-requests'[39m: [32m'1'[39m, [32m'user-agent'[39m: [32m'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Cypress/6.9.1 Chrome/87.0.4280.141 Electron/11.3.0 Safari/537.36'[39m, accept: [32m'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'[39m, [32m'sec-fetch-site'[39m: [32m'same-origin'[39m, [32m'sec-fetch-mode'[39m: [32m'navigate'[39m, [32m'sec-fetch-dest'[39m: [32m'document'[39m, referer: [32m'https://perf-claims-webapp.masspfml.fineos.com/outofdatedataerror.jsp?errorid=bf9dc982-52f2-430c-bb07-bfdd56cdbd64&vsid=86922'[39m, [32m'accept-encoding'[39m: [32m'gzip, deflate, br'[39m, [32m'accept-language'[39m: [32m'en-US'[39m, cookie: [32m'JSESSIONID=WFuWqo12lpwyMhu9QnMmay5qoaDlVX6nHcIWVVB_.ip-10-100-7-171; AWSALB=eiVIkgyrd56yE/FgP15WxP45XIEkVsTJ/vtQZC0+H4/CI2v7CKI2uxZhMvLnnkFimxoCbWR8mlzFaojx5jNq2JKk5d+2UrggcShTwqoxxcpQ2klsrzMllOz7uUWF; AWSALBCORS=eiVIkgyrd56yE/FgP15WxP45XIEkVsTJ/vtQZC0+H4/CI2v7CKI2uxZhMvLnnkFimxoCbWR8mlzFaojx5jNq2JKk5d+2UrggcShTwqoxxcpQ2klsrzMllOz7uUWF; __cypress.unload=true'[39m } } } [32m+100ms[0m
```
If you're able to locate a new Fineos page error that caused a hanger, then it can be added below.  

[fineos.ts](fineos.ts)
```typescript
  // Fineos error pages have been found to cause test crashes when rendered. This is very hard to debug, as Cypress
  // crashes with no warning and removes the entire run history, so when a Fineos error page is detected, we instead
  // throw an error.
  cy.intercept(/\/(util\/errorpage\.jsp|outofdatedataerror\.jsp)/, (req) => {
    req.reply(
      "A fatal Fineos error was thrown at this point. We've blocked the rendering of this page to prevent test crashes"
    );
  });
  ```
  
  Also we there are `uncaught:expection` errors that may cause hangers and can be added as well:
  ```typescript
    cy.on("uncaught:exception", (e) => {
    if (
      e.message.match(
        /(#.(CaseOwnershipSummaryPanelElement|CaseParticipantsSummaryPanelElement)|panelsdrilldown|startHeartbeatMonitorForPage)/
      )
    ) {
      return false;
    }
    if (
      e.message.match(
        /Cannot (set|read) property ('status'|'range') of undefined/
      )
    ) {
      return false;
    }
    return true;
  });
  ```
  Unfortunately we may uncover hangers that either haven't been suppressed (and we can just add them) or don't fall into a page error or `uncaught:exception` category. In this case it is best to save the log and comb through it with another dev to help decipher the failure. 