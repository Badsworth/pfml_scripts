import { mount, shallow } from "enzyme";
import Authenticator from "../../src/components/Authenticator";
import { Hub } from "aws-amplify";
import React from "react";
import { act } from "react-dom/test-utils";
import customAmplifyErrorMessageKey from "../../src/utils/customAmplifyErrorMessageKey";

jest.mock("../../src/utils/customAmplifyErrorMessageKey");

const render = (props = {}, mountComponent = false) => {
  const App = <h1>App</h1>;

  const component = <Authenticator {...props}>{App}</Authenticator>;

  return mountComponent ? mount(component) : shallow(component);
};

describe("Authenticator", () => {
  describe("when a user is NOT authenticated", () => {
    it("shows the auth page instead of the app", () => {
      const wrapper = render();

      expect(wrapper.html()).toMatchInlineSnapshot(
        `"<h1>You must sign in</h1>"`
      );
    });

    it("sends auth state changes to onStateChange handler", () => {
      const authState = "signedIn";
      const authData = { attributes: { email: "barbara@email.com" } };
      const onStateChange = jest.fn();
      const props = {
        onStateChange,
      };
      const wrapper = render(props);
      wrapper.simulate("stateChange", authState, authData);

      expect(onStateChange).toBeCalledWith(authState, authData);
    });
  });

  describe("when Amplify's errorMessage map is triggered", () => {
    it("displays an Alert", () => {
      const wrapper = render();

      expect(wrapper.find("Alert")).toHaveLength(0);

      const errorHandler = wrapper.prop("errorMessage");
      errorHandler("Mock error message");

      expect(wrapper.find("Alert")).toMatchInlineSnapshot(`
        <Alert
          heading="Please fix the following errors"
          role="alert"
        >
          Mock error message
        </Alert>
      `);
    });

    it("replaces the 'Email verified' success alert", () => {
      const wrapper = render({ authState: "signedUp" });

      const errorHandler = wrapper.prop("errorMessage");
      errorHandler("Mock error message");

      expect(wrapper.find("Alert")).toHaveLength(1);
      expect(wrapper.find("Alert")).toMatchInlineSnapshot(`
        <Alert
          heading="Please fix the following errors"
          role="alert"
        >
          Mock error message
        </Alert>
      `);
    });

    it("focuses the Alert", async () => {
      expect.hasAssertions();

      // Mount the component so useEffect is called
      const wrapper = render({}, true);

      await act(async () => {
        const errorHandler = wrapper.children().first().prop("errorMessage");
        errorHandler("Mock error message");

        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));

        wrapper.update();
      });

      const alert = wrapper.find("Alert").getDOMNode();
      expect(document.activeElement).toBe(alert);
    });

    it("renders the customized Amplify error message", () => {
      customAmplifyErrorMessageKey.mockReturnValueOnce(
        "errors.auth.passwordRequired"
      );
      const wrapper = render();

      const errorHandler = wrapper.prop("errorMessage");
      errorHandler(
        "customAmplifyErrorMessageKey is mocked so this string doesn't matter"
      );

      expect(wrapper.find("Alert").text()).toMatchInlineSnapshot(
        `"Enter your password"`
      );
    });

    it("falls back to the original Amplify error message", () => {
      customAmplifyErrorMessageKey.mockReturnValueOnce(undefined);
      const wrapper = render();

      const errorHandler = wrapper.prop("errorMessage");
      errorHandler("Original Amplify error message");

      expect(wrapper.find("Alert").text()).toBe(
        "Original Amplify error message"
      );
    });
  });

  describe("when the forgotPassword auth event occurs", () => {
    const forgotPasswordEvent = {
      payload: {
        event: "forgotPassword",
      },
    };

    it("removes any displayed error alerts", () => {
      // Mock Hub.listen() to just save the callback so we can call it ourselves
      let forgotPasswordCallback;
      jest.spyOn(Hub, "listen").mockImplementationOnce((channel, callback) => {
        forgotPasswordCallback = callback;
      });

      customAmplifyErrorMessageKey.mockReturnValueOnce(
        "errors.auth.passwordRequired"
      );

      const wrapper = render({}, true);
      const authenticator = wrapper.childAt(0);
      const errorHandler = authenticator.prop("errorMessage");

      act(() => {
        // Trigger an amplify error alert
        errorHandler(
          "customAmplifyErrorMessageKey is mocked so this string doesn't matter"
        );
      });
      wrapper.update();
      expect(wrapper.find("Alert")).toHaveLength(1);

      act(() => {
        // Trigger a forgotPassword event to clear the error
        forgotPasswordCallback(forgotPasswordEvent);
      });
      wrapper.update();
      expect(wrapper.find("Alert")).toHaveLength(0);
    });
  });

  describe("when the authState changes", () => {
    it("clears any previously displayed Amplify errors", () => {
      const newAuthState = "signIn";
      const wrapper = render();

      // Set the error
      const errorHandler = wrapper.prop("errorMessage");
      errorHandler("Mock error message");

      expect(wrapper.find("Alert")).toHaveLength(1);

      // Change the state and hide the error
      wrapper.simulate("stateChange", newAuthState, null);

      expect(wrapper.find("Alert")).toHaveLength(0);
    });
  });

  describe("when the authState is 'signedUp'", () => {
    it("displays a Success alert indicating the email was verified", () => {
      const wrapper = render({ authState: "signedUp" });

      expect(wrapper.find("Alert")).toMatchSnapshot();
    });
  });

  describe("when a user IS authenticated", () => {
    const authState = "signedIn";
    const authData = { attributes: { email: "barbara@email.com" } };

    it("shows the app instead of auth pages", () => {
      const props = {
        authState,
        authData,
      };
      const wrapper = render(props);
      expect(wrapper.html()).toMatchInlineSnapshot(`"<h1>App</h1>"`);
    });

    it("sends auth state changes to onStateChange handler", () => {
      const newAuthState = "signIn";
      const onStateChange = jest.fn();
      const props = {
        authState,
        authData,
        onStateChange,
      };
      const wrapper = render(props);
      wrapper.simulate("stateChange", newAuthState, null);

      expect(onStateChange).toBeCalledWith(newAuthState, null);
    });
  });
});
