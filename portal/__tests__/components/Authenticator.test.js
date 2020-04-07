import { mount, shallow } from "enzyme";
import Authenticator from "../../src/components/Authenticator";
import React from "react";
import { act } from "react-dom/test-utils";

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

    it("sends auth state changes to handleAuthStateChange handler", () => {
      const authState = "signedIn";
      const authData = { attributes: { email: "barbara@email.com" } };
      const handleAuthStateChange = jest.fn();
      const props = {
        handleAuthStateChange,
      };
      const wrapper = render(props);
      wrapper.simulate("stateChange", authState, authData);

      expect(handleAuthStateChange).toBeCalledWith(authState, authData);
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

    it("sends auth state changes to handleAuthStateChange handler", () => {
      const newAuthState = "signIn";
      const handleAuthStateChange = jest.fn();
      const props = {
        authState,
        authData,
        handleAuthStateChange,
      };
      const wrapper = render(props);
      wrapper.simulate("stateChange", newAuthState, null);

      expect(handleAuthStateChange).toBeCalledWith(newAuthState, null);
    });
  });
});
