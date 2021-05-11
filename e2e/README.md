PFML End to End Testing
=======================

Here you will find the end-to-end testing code for this project. Testing efforts on this project have been broken into three groups:

* **[End to End](#end-to-end-tests)** - Tests application functionality from a user (employee, CSR) perspective across multiple components using [Cypress](https://www.cypress.io/). This test type is browser based, and runs nightly in CI to ensure continuity of functionality.
* **[Data Generation](#data-generation)** - Generates ad-hoc data to be used for manual testing and training activities (Employers, Employees, and Claims).
* **[Load and Stress](#load-and-stress-testing)** - Tests performance of the system by simulating a large amount of user activity on multiple points in the application. Load and stress tests are scheduled activities that will run against a production-like environment.

End-to-End Tests
----------------

End to End tests are Cypress based, and operate by driving a real browser through the Claimant Portal and Claims Processing System.

### Running E2E Tests Locally

Tests can be executed locally (against one of the cloud environments) by following these steps:

#### Initial Setup:
* Create your `.env` file with the values [described here](#Setting-up-End-to-End-Configuration).
* Run `npm install` in this directory.

#### Running Cypress:

<u>**E2E Team**</u>

* Run `npm run cypress:open`
* A window will pop open showing the various tests available for running.
* Click the test you want to run, and a browser window will open with the test running in it.

<u>**Portal Team**</u>

The test suite can run against your local portal enviornment.

* To run all tests use `npm run cypress:open:local`
* To run a subset of Portal-based tests as a Portal smoke test run `npm run cypress:open:local:portal` instead
* A window will pop open showing the various tests available for running.
* Depending on what feature you're working on will determine the test of most interest. See Below ⬇️

#### Information about Scenario Test:
* [BHAP1](https://lwd.atlassian.net/browse/ETS-8) - continuous leave bonding claim
* [BHAP8](https://lwd.atlassian.net/browse/ETS-33) - reduced leave bonding claim
* [BHAP9](https://lwd.atlassian.net/browse/ETS-34) - intermittent leave bonding claim
* [BGBM1](https://lwd.atlassian.net/browse/ETS-6) - continous leave bonding claim (Only ID)

### Writing/Editing E2E Tests

We have two different styles of Cypress tests:

* End-to-End - Follows a single claim from initial creation on the Portal to Fineos and back. This type of test truly goes "end to end", but it is very fragile, due to the number of different systems it covers at once.
* Feature Tests - Exercises a single feature of the application in the most minimal way possible.  These tests still span multiple applications, but will often start or end at the PFML API.  An example of a feature test is "Financial eligiblity should not be met if an employee has made less than $5000 in the past year." We prefer these tests when possible, as they are less brittle.

<details>
  <summary>Tips for writing effective tests</summary>

* When implementing step definitions, you can use "helper" code in the form of custom Cypress commands, and our system of "actions". Using helpers for repetitive technical steps is good, since it allows us to reuse and improve the execution over time. But make sure your helpers are specifying technical steps rather than business or human process. Business process belongs in the step definition rather than tucked away in a helper.
  * Good helper examples
    * Selecting a particular fieldset based on legend label.
    * Closing a popup window
    * Selecting a particular form element based on label text.
    * Filling a particular type of form element with a value.
  * Bad helper examples:
    * Approving or denying a particular document
    * Filling out a page of a form
* Avoid "flake" in tests without using `cy.wait()`. This is a whole topic in itself, so we'll just refer to [Cypress' documentation](https://docs.cypress.io/guides/core-concepts/retry-ability.html) here. As a rule of thumb, we shouldn't be using `cy.wait()` unless there isn't any other way to do it.

</details>


Data Generation
---------------

The End-to-End team regularly conducts data generation activities to support testing activities for other teams.  We have developed a suite of data generation tools to make this process easy(ier).  Generally, the types of data we generate are:

* **Employers/Employees**: May be generated in virtually any amount or mix.  We have complete control over the employer's withholding, employer exemption status and employee's wages. We do not currently support customization of most other aspects of employer/employee generation.
* **Claims**: May be generated in limited quantities and programatically submitted to the API. We have control over most of the aspects of claim generation, including which employee we pick, what ER is submitted, what documents are generated (or missing), and specific properties like address and payment details. Generally, we can submit claims to an environment at a rate of ~300/hr, which means that ~2400 claims is about the maximum amount we can submit in a given day.

### Requesting data from the E2E team:

If you would like to request data from the End-to-End team, please fill out [this form](https://docs.google.com/spreadsheets/d/11oR5o4macQO1LsHMlYCuylXlWiHtDpH2oypwYfJmgoE/edit#gid=1227817983) and submit it to an E2E team member such as Rob (rob@lastcallmedia.com) or Lili (lili@lastcallmedia.com).

### Technical process of generating data

The process is documented in [our docs folder](./docs/data.md).


Load and Stress Testing
-----------------------

The process is documented in [our docs folder](./docs/LST.md).

General Testing Methodology/Philosophy
----------------------

### Focus on the user journey

As we proceed through E2E testing workflows, we always want to try to take the perspective of the user.  To that end, we prefer to select HTML elements based on their display values wherever possible.  For example, if I'm writing a login workflow, I'd prefer to put my e-mail address into a field labelled "E-mail address" rather than an input matching `#input2`. Tests written this way are both easier to understand and come closer to matching the way actual users will interact with the application. This will not be a hard-and-fast rule, but we'd like to avoid hard-coding CSS selectors as much as we can.

### Only consider inputs and outputs

When writing tests, we will be aiming to focus on input (e.g. entering a particular type of application), and output (e.g. seeing that application appear in the claims processing system).  What happens in between these two steps is immaterial to us - if the input is accepted, and the output matches what we expect it to be, our test is doing its job. As a concrete example of this, if we wanted to check that adjustments are working in the API, the way we'd actually test that in an End to End test would be to enter an application that should receive an adjustment, then visit the CPS to ensure that the adjustment was applied.

### Limit tests to critical business functionality

End-to-end functionality is expensive to test, but valuable to have. In any of our testing efforts, we should focus on capturing the inputs and outputs that will bring the most business value for the least amount of effort.  With that in mind, end to end tests should only be written to validate primary business value, not to test for regressions.

Setting up End-to-End Configuration
-----------------------------------

Configuration for all E2E testing components is in [`config.json`](./config.json) and a `.env` file you can create in this directory.

Must be in your `.env file:`
```
# Your username to log into the portal. Easiest if this is consistent between environments.
E2E_PORTAL_USERNAME=XXX
# Your password to log into the portal. Easiest if this is consistent between environments.
E2E_PORTAL_PASSWORD=XXX
# The Fineos "CONTENT" user's password:
E2E_FINEOS_PASSWORD=XXX
```
