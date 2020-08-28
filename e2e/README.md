PFML End to End Testing
=======================

Here you will find the [Cypress](https://www.cypress.io/) tests for PFML. In this project, we have two different "styles" of test:

* End to End tests - Testing a single, known business case as it progresses through the various parts of the application. The inputs for these tests are always known in advance. These tests are designed to be run on a scheduled basis.
* Business Simulation tests - Testing designed to exercise business processes using generated, semi-random inputs. These tests are designed to be run on an as-needed basis, and may produce a variable amount of inputs.

In general, the two test types will follow the same paths (eg: we might submit a medical leave claim through the claimant portal in both), but the inputs will be very different.

Running Tests
-------------

Before you start, copy the `.env.example` in this directory to `.env`, and make sure it's filled out.

To run the tests:

```bash
npm install
npm run cypress:open
```

The Cypress UI will open, and you will have a choice of tests to run. Choose the test you wish to run, and Cypress will
begin running.

Architecture
------------

To promote the reuse of automation routines, test code should be composable from modular parts.  To promote this reuse, we've introduced a couple of data structures:

* ["Page Objects"](./src/pages), which encapsulate the logic for dealing with a single page or a handful of similar pages. This is where the majority of our selectors will live, and page classes will have Object Oriented methods pertaining to their usage (Eg: The login page will have `fill()` and `submit()` methods that do exactly what you'd expect).
* ["Flows"](./src/flows.ts), which orchestrate a journey across multiple pages. A single flow will only operate within the scope of a single application, however, due to limitations with Cypress and crossing domain boundaries.  Typically, a flow will take an input of a known shape (eg: an application), and invoke many page objects.

Once a flow is written, it may be used in both end to end and business simulation tests, although it's unlikely we'll want to have all of our end to end workflows as business simulation tests, and vice versa.

Methodology/Philosophy
----------------------

### Focus on the user journey

As we proceed through E2E testing workflows, we always want to try to take the perspective of the user.  To that end, we prefer to select HTML elements based on their display values wherever possible.  ie: If I'm writing a login workflow, I'd prefer to put my e-mail address into a field labelled "E-mail address" rather than an input matching `#input2`. Tests written this way are both easier to understand and come closer to matching the way actual users will interact with the application. Obviously this will not a hard-and-fast rule, but we'd like to avoid hard-coding CSS selectors as much as we can.

### Only consider inputs and outputs

When writing tests, we will be aiming to focus on input (eg: entering a particular type of application), and output (eg: Seeing that application appear in the claims processing system).  What happens in between these two steps is immaterial to us - if the input is accepted, and the output matches what we expect it to be, our test is doing its job. As a concrete example of this, if we wanted that adjustments are working in the API, the way we'd actually test that in an End to End test is to enter an application that should receive an adjustment, then visit the CPS to ensure that the adjustment was applied.

### Limit tests to critical business functionality

End-to-end tests are expensive. They are the slowest to run, easiest to break, and most difficult to write of any of the different types of tests available. We write them because they cover a lot of functionality at once, and because they are the closest thing we can get to proving the value of an application in the real world. With that in mind, end to end tests should only be written to validate primary business value, not to test for regressions.

Business Simulation
-------------------

#### Generating Mock Employee Data

Before running the bizSim - you may need to generate mock employee data in order to populate the employee pool.  The script provided will create a JSON file with however many employees you specify.  All files that are generated will be placed here: [./data/simulation/users](./data/simulation/users)

To generate mock employee data:

```
# Generates mock data for <number> of employees
npm run sim:generateUsers -- <number>

# eg.
npm run sim:generateUsers -- 500
```

The file name will contain a timestamp and the number of employees generated
```
yyyy-mm-ddThh:mm:ss--n-users.json
````

---

#### Running the Business Simulation

The business simulation code is kept in [./src/simulation](./src/simulation). Business simulation is run through a NodeJS CLI script that submits generated applications directly to the API. The simulation is broken down into scenarios, each of which has a given probability of running.

##### Adding the employee pool info:

In order to run the bizSim you will need to add the file name of the generated employee pool file.  You must use a ```-u``` or ```-users``` flag to import employee pool data.

eg.
```
-u ./data/simulation/users/2020-08-20T00:31:46.322Z--10-users.json
```

To run the business simulation, we've created a couple handy commands:
```
# Run Pilot 3 simulation with default settings.
npm run sim:pilot3 -- -u <filname>

# Run HAP1 scenario from Pilot 3 simulation.
npm run sim:pilot3 -u <filname> -s HAP1

# Run HAP1 scenario from Pilot 3 20 times.
npm run sim:pilot3 -u <filname> -s HAP1 -n 20
```
If you want to run the simulation w/o submitting the application to the API (for testing) then use ```-r``` or ```-dryrun``` flags.

eg.
```
npm run sim:pilot3 -- -u <filname> -s HAP1 -r
```

