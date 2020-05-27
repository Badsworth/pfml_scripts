import tracker from "../../src/services/tracker";

describe("tracker", () => {
  // Tests below are generated! If you add another tracker method, add its name
  // here and in the mocked newrelic object below
  const newrelicMethods = [
    // Mappings of tracker.METHOD_NAME to newrelic.METHOD_NAME
    { trackerMethod: "noticeError", newrelicMethod: "noticeError" },
    {
      trackerMethod: "setCurrentRouteName",
      newrelicMethod: "setCurrentRouteName",
    },
    { trackerMethod: "trackEvent", newrelicMethod: "addPageAction" },
  ];

  describe("when newrelic is defined", () => {
    beforeEach(() => {
      // Our app relies on `newrelic` being exposed as a global variable,
      // which is set when the New Relic JS snippet loads.
      global.newrelic = {
        addPageAction: jest.fn(),
        noticeError: jest.fn(),
        setCurrentRouteName: jest.fn(),
      };
    });

    newrelicMethods.forEach(({ trackerMethod, newrelicMethod }) => {
      it(`${trackerMethod}: calls newrelic.${newrelicMethod}`, () => {
        tracker[trackerMethod]();

        expect(newrelic[newrelicMethod]).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("when newrelic is undefined", () => {
    beforeEach(() => {
      global.newrelic = undefined;
    });

    newrelicMethods.forEach(({ trackerMethod, newrelicMethod }) => {
      it(`${trackerMethod}: does not call newrelic.${newrelicMethod}`, () => {
        // Call the method from inside another function so we can test
        // that it doesn't throw an error
        const callTracker = () => tracker[trackerMethod]();

        expect(callTracker).not.toThrow();
      });
    });
  });
});
