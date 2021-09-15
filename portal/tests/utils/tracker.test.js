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
        setAttribute: jest.fn(),
        setName: jest.fn(),
      };
      interaction.end.mockReturnValue(interaction);
      interaction.save.mockReturnValue(interaction);
      interaction.setAttribute.mockReturnValue(interaction);
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

    it("markFetchRequestEnd ends the interaction", () => {
      tracker.trackFetchRequest("https://example.com");

      expect(newrelic.interaction().end).toHaveBeenCalledTimes(1);
    });

    it("trackFetchRequest tracks interaction with the given URL and environment", () => {
      tracker.trackFetchRequest("https://example.com");

      expect(newrelic.interaction().end).toHaveBeenCalledTimes(1);
      expect(newrelic.interaction().setName).toHaveBeenCalledWith(
        "fetch: example.com"
      );
      expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
        "environment",
        "mock-build-env"
      );
      expect(newrelic.interaction().save).toHaveBeenCalledTimes(1);
    });

    describe("custom attributes", () => {
      const environment = "automated-test-environment";
      beforeEach(() => {
        process.env.buildEnv = environment;
      });

      it("noticeError sets the build environment as a custom `environment` attribute", () => {
        const error = new Error("some test error");
        tracker.noticeError(error);
        expect(newrelic.noticeError).toHaveBeenCalledWith(
          error,
          expect.objectContaining({ environment })
        );
      });

      it("noticeError sets additional custom attributes", () => {
        const customAttributes = {
          numberAttribute: 1,
          stringAttribute: "test value",
        };
        const error = new Error("some test error");
        tracker.noticeError(error, customAttributes);
        expect(newrelic.noticeError).toHaveBeenCalledWith(
          error,
          expect.objectContaining({
            environment,
            ...customAttributes,
          })
        );
      });

      it("trackEvent sets the build environment as a custom `environment` attribute", () => {
        tracker.trackEvent("TestEvent");
        expect(newrelic.addPageAction).toHaveBeenCalledWith(
          "TestEvent",
          expect.objectContaining({ environment })
        );
      });

      it("trackEvent sets additional custom attributes", () => {
        const customAttributes = {
          numberAttribute: 1,
          stringAttribute: "test value",
        };
        tracker.trackEvent("TestEvent", customAttributes);
        expect(newrelic.addPageAction).toHaveBeenCalledWith(
          "TestEvent",
          expect.objectContaining({
            environment,
            ...customAttributes,
          })
        );
      });
    });

    describe("custom page attributes", () => {
      const numberAttribute = 1;
      const stringAttribute = "test value";
      let customAttributes;
      beforeEach(() => {
        customAttributes = { numberAttribute, stringAttribute };
      });

      it("startPageView sets custom attributes on browser interaction events", () => {
        tracker.startPageView("/page-1", customAttributes);
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "numberAttribute",
          numberAttribute
        );
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "stringAttribute",
          stringAttribute
        );
      });

      it("startPageView sets custom attributes on later trackFetchRequest events", () => {
        tracker.startPageView("/page-2", customAttributes);

        newrelic.interaction().setAttribute.mockClear();
        tracker.trackFetchRequest("/test-api-call");
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "numberAttribute",
          numberAttribute
        );
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "stringAttribute",
          stringAttribute
        );
      });

      it("startPageView sets custom attributes on later noticeError calls", () => {
        tracker.startPageView("/page-2", customAttributes);

        const error = new Error("some test error");
        tracker.noticeError(error);
        expect(newrelic.noticeError).toHaveBeenCalledWith(
          error,
          expect.objectContaining(customAttributes)
        );

        const extraAttributes = { extraAttribute: "extra attribute value" };
        newrelic.noticeError.mockClear();
        tracker.noticeError(error, extraAttributes);
        expect(newrelic.noticeError).toHaveBeenCalledWith(
          error,
          expect.objectContaining({
            ...customAttributes,
            ...extraAttributes,
          })
        );
      });

      it("startPageView sets custom attributes on later trackEvent calls", () => {
        tracker.startPageView("/page-2", customAttributes);

        tracker.trackEvent("TestEvent");
        expect(newrelic.addPageAction).toHaveBeenCalledWith(
          "TestEvent",
          expect.objectContaining(customAttributes)
        );

        const extraAttributes = { extraAttribute: "extra attribute value" };
        newrelic.addPageAction.mockClear();
        tracker.trackEvent("TestEvent", extraAttributes);
        expect(newrelic.addPageAction).toHaveBeenCalledWith(
          "TestEvent",
          expect.objectContaining({
            ...customAttributes,
            ...extraAttributes,
          })
        );
      });

      it("startPageView sets custom attributes on later trackFetchRequest calls", () => {
        tracker.startPageView("/page-2", customAttributes);

        newrelic.interaction().setAttribute.mockClear();
        tracker.trackFetchRequest("/test-api-call");
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "numberAttribute",
          numberAttribute
        );
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "stringAttribute",
          stringAttribute
        );
      });

      it("startPageView clears custom attributes from previous startPageView calls", () => {
        const customAttributes1 = { numberAttribute };
        const customAttributes2 = { stringAttribute };
        tracker.startPageView("/page-3", customAttributes1);

        newrelic.interaction().setAttribute.mockClear();
        tracker.startPageView("/page-4", customAttributes2);
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledTimes(1);
        expect(newrelic.interaction().setAttribute).not.toHaveBeenCalledWith(
          "numberAttribute",
          numberAttribute
        );
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "stringAttribute",
          stringAttribute
        );

        newrelic.interaction().setAttribute.mockClear();
        tracker.trackFetchRequest("/test-api-call");
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledTimes(3); // includes the environment setAttribute()
        expect(newrelic.interaction().setAttribute).not.toHaveBeenCalledWith(
          "numberAttribute",
          numberAttribute
        );
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledWith(
          "stringAttribute",
          stringAttribute
        );

        newrelic.interaction().setAttribute.mockClear();
        tracker.startPageView("/page-5");
        expect(newrelic.interaction().setAttribute).not.toHaveBeenCalled();

        tracker.trackFetchRequest("/test-api-call");
        expect(newrelic.interaction().setAttribute).toHaveBeenCalledTimes(2); // just the environment setAttribute()
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

    it("trackFetchRequest does not call newRelic.interaction", () => {
      const callTracker = () =>
        tracker.trackFetchRequest("https://example.com");

      expect(callTracker).not.toThrow();
    });
  });
});
