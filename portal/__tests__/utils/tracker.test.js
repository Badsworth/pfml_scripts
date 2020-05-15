import tracker from "../../src/services/tracker";

describe("tracker", () => {
  // Tests below are generated! If you add another tracker method, add its name
  // here and in the mocked newrelic object below
  const newrelicMethods = ["noticeError", "setCurrentRouteName"];

  describe("when newrelic is defined", () => {
    beforeEach(() => {
      // Our app relies on `newrelic` being exposed as a global variable,
      // which is set when the New Relic JS snippet loads.
      global.newrelic = {
        noticeError: jest.fn(),
        setCurrentRouteName: jest.fn(),
      };
    });

    newrelicMethods.forEach((methodName) => {
      it(`${methodName}: calls the newrelic method`, () => {
        tracker[methodName]();

        expect(newrelic[methodName]).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("when newrelic is undefined", () => {
    beforeEach(() => {
      global.newrelic = undefined;
    });

    newrelicMethods.forEach((methodName) => {
      it(`${methodName}: does not call the newrelic method`, () => {
        // Call the method from inside another function so we can test
        // that it doesn't throw an error
        const callTracker = () => tracker[methodName]();

        expect(callTracker).not.toThrow();
      });
    });
  });
});
