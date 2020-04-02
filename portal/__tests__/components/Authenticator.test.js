import { mount, shallow } from "enzyme";
import Authenticator from "../../src/components/Authenticator";
import React from "react";

const render = (props, mountComponent = false) => {
  const App = <h1>App</h1>;

  const component = <Authenticator {...props}>{App}</Authenticator>;

  return mountComponent ? mount(component) : shallow(component);
};

describe("Authenticator", () => {
  describe("when a user is NOT authenticated", () => {
    it("shows the auth page instead of the app", async () => {
      const page = render({}, true);
      expect(page.html()).toMatchInlineSnapshot(`"<h1>You must sign in</h1>"`);
    });

    it("sends auth state changes to handleAuthStateChange handler", async () => {
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

  describe("when a user IS authenticated", () => {
    const authState = "signedIn";
    const authData = { attributes: { email: "barbara@email.com" } };

    it("shows the app instead of auth pages", async () => {
      const props = {
        authState,
        authData,
      };
      const page = render(props, true);
      expect(page.html()).toMatchInlineSnapshot(`"<h1>App</h1>"`);
    });

    it("sends auth state changes to handleAuthStateChange handler", async () => {
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
