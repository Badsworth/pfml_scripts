import tracker from "../../src/services/tracker";

describe("tracker", () => {
  describe("initialize", () => {
    it("sets New Relic config", () => {
      tracker.initialize();

      expect(window.NREUM).toMatchSnapshot();
    });
  });

  // Tests below are generated! If you add another tracker method, add its name
  // here and in the mocked newrelic object below
  const newrelicMethods = [
    // Mappings of tracker.METHOD_NAME to newrelic.METHOD_NAME
    { trackerMethod: "noticeError", newrelicMethod: "noticeError" },
    {
      trackerMethod: "startPageView",
      newrelicMethod: "setCurrentRouteName",
    },
    { trackerMethod: "trackEvent", newrelicMethod: "addPageAction" },
  ];

  describe("when newrelic is defined", () => {
    beforeEach(() => {
      // Mock chained methods
      const interaction = {
        end: jest.fn(),
        save: jest.fn(),
        setName: jest.fn(),
      };
      interaction.end.mockReturnValue(interaction);
      interaction.save.mockReturnValue(interaction);
      interaction.setName.mockReturnValue(interaction);

      // Our app relies on `newrelic` being exposed as a global variable,
      // which is set when the New Relic JS snippet loads.
      global.newrelic = {
        addPageAction: jest.fn(),
        interaction: jest.fn().mockReturnValue(interaction),
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

    it("trackFetchRequest tracks interaction with the given URL", () => {
      tracker.trackFetchRequest("https://example.com");

      expect(newrelic.interaction().end).toHaveBeenCalledTimes(1);
      expect(newrelic.interaction().setName).toHaveBeenCalledWith(
        "fetch: example.com"
      );
      expect(newrelic.interaction().save).toHaveBeenCalledTimes(1);
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

    it("trackFetchRequest does not call newRelic.interaction", () => {
      const callTracker = () =>
        tracker.trackFetchRequest("https://example.com");

      expect(callTracker).not.toThrow();
    });
  });
});
