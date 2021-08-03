## How to view LST Reports

After running a Load & Stress test for any given purpose, Flood Element, the tool used, will automatically show each step of the test, which matching average time to complete that step and error rate.

If you have access to a Flood account, you'll be able to find the most recent run under the "Floods" menu. Click on it's title and you'll see the results.

If you ran LST through a Github Action, using one of the given presets, you'll get a link to view the results along with a summary of the run after the GH Action completes.

## How to interpret LST Reports

First thing to consider before starting looking at the results is that they're always relative to previous runs, so if you do not have some context on how long a step usually takes, or if the step usually has 0.5% error rate due to a very rare situation, you might interpret the recent results differently.

Simple comparisons to make are "how long it takes to run a particular step" and "how much % error rate does it have".

The more time it takes, less performant it is.

With increase of error rate, we would need further investigation on a case-by-case basis, but there are some common causes such as:

- Some feature is not working as it should;
- A feature was changed or recently updated, requiring the LST code to be updated accordingly;
- The dataset we're using to run LST is no longer "valid/available" in that environment;
- The environment is not up to date compared to "performance".
- Requests are timing out due to very high traffic, meaning that the feature cannot perform against such high stress;

## A concrete example

Use this link to view one of our recent runs targetting Employer Response after Claim Submissions in the Performance environment:
https://app.flood.io/1p1jMhHYXnnTeIVDPYIKSr2x7mI

This is a graphical representation of our LST example run:
![part1-end707](https://user-images.githubusercontent.com/9201063/109800116-b7d03d80-7c14-11eb-8c3d-4b35d274d036.JPG)
Check out the labels below the graph to understand which line refers to which parameter.

We can see a very clear good starting point leading up to a higher and higher response time, which led up to an error spike. Let's analyse the results below.

Just below the graph, we can see all the steps that ran during this LST:
![part2-end707](https://user-images.githubusercontent.com/9201063/109800117-b868d400-7c14-11eb-8aff-b7bf282a36e7.JPG)

We can see from these images that we have a particular step in this Claim Submission LST that has an <b>100% error rate</b>, it's called "PortalClaimSubmit: <b>Point of Contact fills employer response</b>", and the <b>response time is 3 minutes</b>.

Based on this alone, we can tell that something must not be working as it should. Could be the feature or the underlying test itself. An 100% error rate would not show up if this was due to high traffic.

The 3 minute response time seems to be very high compared to other steps, but in this particular example, it just means that our LST code made "several attempts / retries" on that step before considering it an error.

We also see that all other steps regarding claim submission are working very well, with 0% error rate and low response times, which means that in this run we detected that Employer Response in the Performance environment is not working properly, and that it is likely to be one of the following:

- Employer Response is not working as it should;
- Employer Response was changed or recently updated, requiring the LST code to be updated accordingly;
- The dataset we're using to run LST is no longer "valid/available" in performance;

But it is possible that there might be other reasons.

## TL;DR

- More error rate is bad.
- More response time is bad.
- Always compare results to previous runs.
  Example: You might think 17 seconds is too long to register / login but turns out that it's been like that for 6 months so it might be normal.
- Some errors are being worked on, are not a high priority or affect a very small ammount of users or with little impact on user experience.
- A 1.5% error rate during an high traffic LST run can be normal, but it is always good to check the logs and confirm we can rule out those "low priority" errors for now.
