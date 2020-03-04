/* eslint-disable import/first */
jest.mock("aws-amplify");

import { mount, shallow } from "enzyme";
import { App } from "../../src/pages/_app";
import { Auth } from "aws-amplify";
import React from "react";
import { act } from "react-dom/test-utils";

function render(customProps = {}, mountComponent = false) {
  const props = Object.assign(
    {
      Component: () => <div />,
      pageProps: {}
    },
    customProps
  );

  const component = <App {...props} />;

  return {
    props,
    wrapper: mountComponent ? mount(component) : shallow(component)
  };
}

describe("App", () => {
  describe("when a user is authenticated", () => {
    it("renders the site header with the authenticated user's info", async () => {
      Auth.currentAuthenticatedUser.mockResolvedValueOnce({
        attributes: {
          email: "mocked-header-user@example.com"
        }
      });

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      // We need to wait a hot second for async authentication and state update
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        wrapper.update();
      });

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toMatchInlineSnapshot(`
      Object {
        "username": "mocked-header-user@example.com",
      }
    `);
    });
  });

  describe("when currentAuthenticatedUser throws an error", () => {
    beforeAll(() => {
      // Don't show a scary error in our log when it's expected
      jest.spyOn(console, "error").mockImplementation(() => null);
    });

    afterAll(() => {
      console.error.mockRestore();
    });

    it("renders the site header without a user", async () => {
      Auth.currentAuthenticatedUser.mockRejectedValueOnce(
        Error("Mocked rejection")
      );

      // We need to mount the component so that useEffect is called
      const mountComponent = true;
      const { wrapper } = render({}, mountComponent);

      // We need to wait a hot second for async authentication and state update
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 0));
        wrapper.update();
      });

      const header = wrapper.find("Header");

      expect(header.exists()).toBe(true);
      expect(header.prop("user")).toEqual({});
    });
  });

  it("renders the passed in Component with the given pageProps", () => {
    const TestComponent = () => <div>Hello world</div>;

    const { wrapper } = render({
      Component: TestComponent,
      pageProps: {
        title: "Test page"
      }
    });

    const component = wrapper.find("TestComponent");

    expect(component).toMatchInlineSnapshot(`
      <TestComponent
        title="Test page"
      />
    `);
  });
});
