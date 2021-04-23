Data Generation - Technical Documentation
========================================

All ad-hoc data generation tasks are done using a Typescript file stored in `src/scripts`.  Each ticket we work on typically gets its own script, which we commit to the repository for historical reference.  A single script might do any or all of the following:

* Generate Employer Data, stored in JSON files and optionally exported to DOR employer files.
* Generate Employee Data, stored in JSON files and optionally exported to DOR employee files.
* Generate Claim Data, stored in JSON files.
* Submit claims to the API, and optionally "post process" those claims by performing adjudication actions in Fineos.

### Concepts used in data generation scripts

* **Data Directory**: A data directory is a directory on the filesystem where we store generated data during generation and submission. It typically ends up with at least an `employees.json` and `employers.json` file in it, and often includes DOR files and `claims.json` as well.
* **Employee/Employer/Claim Pools**: A "pool" is a collection of generated data that can be loaded from and saved to the filesystem in the form of a JSON (or NDJSON, for claims) file.
* **Scenarios**: A scenario is a specification for how a claim will be generated and what kind of employee will be used. It can specify things like the claim's start and end date, type, leave reason, etc. During claim generation, claims from multiple scenarios can be combined into the final claim pool.

### Examples
All data generation scripts use APIs which are defined in `src/generation` and `src/submission`. The best way to explain those APIs is probably to point to examples of specific scripts we've used in the past:

* [E2E test Employer and Employee generation](../src/scripts/2021-04-08-e2e-employees.ts): This script generates 5 employers and 10,000 employees. All employees are assigned to 2 of the employers (the other 3 are just used for LA registration/verification testing). This script generates the JSON files, as well as DOR files, which we then loaded into every environment.
* [PUB payment testing generation & submission](../src/scripts/2021-04-02-payments.ts): This script generates claim data using complex scenarios that were defined for this task (employees/employers are generated externally).  It also defines a claim submission routine, including post-submission adjudication action.
