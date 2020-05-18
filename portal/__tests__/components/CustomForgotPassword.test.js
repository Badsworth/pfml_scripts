import CustomForgotPassword from "../../src/components/CustomForgotPassword";
import React from "react";
import { shallow } from "enzyme";

jest.unmock("aws-amplify-react");

// Allow us to match two snapshots taken in the same test
jest.mock("lodash/uniqueId");

const render = (props = {}) => {
  return shallow(
    <CustomForgotPassword
      authState="forgotPassword"
      theme={{ mockTheme: true }}
      {...props}
    />
  ).dive();
};

describe("CustomForgotPassword", () => {
  describe("when authState is not forgotPassword", () => {
    it("is not rendered", () => {
      const wrapper = render({ authState: "signUp" });

      expect(wrapper.type()).toBeNull();
    });
  });

  describe("when the delivery state is undefined", () => {
    it("renders the Enter Email view", () => {
      const wrapper = render();

      expect(wrapper).toMatchSnapshot();
    });

    it("sends code when submit button is clicked", () => {
      const wrapper = render();
      const spy = jest.spyOn(wrapper.instance(), "send").mockImplementation();

      wrapper.find({ name: "submit" }).simulate("click");

      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  describe("when authData includes a username or when the delivery state is set", () => {
    const delivery = {
      AttributeName: "email",
      DeliveryMedium: "EMAIL",
      Destination: "s***@n***.com",
    };

    it("renders the Create Password view", () => {
      const email = "foo@example.com";

      // Render example where email is already known
      const wrapperAuthData = render({
        authData: {
          username: email,
        },
      });

      // Render example where email is entered by user
      const wrapperDeliveryState = render();
      wrapperDeliveryState.find("[name='username']").simulate("change", {
        target: {
          name: "username",
          value: email,
        },
      });
      wrapperDeliveryState.setState({ delivery });

      expect(wrapperAuthData).toMatchSnapshot();
      expect(wrapperDeliveryState.html()).toEqual(wrapperAuthData.html());
    });
  });

  describe("when the Create Password view is active", () => {
    const delivery = {
      AttributeName: "email",
      DeliveryMedium: "EMAIL",
      Destination: "s***@n***.com",
    };

    it("trims whitespace from the code field", () => {
      const wrapper = render();
      wrapper.setState({ delivery });

      const event = { target: { value: " 123456 " } };
      wrapper.find('InputText[name="code"]').simulate("change", event);

      expect(event.target.value).toBe("123456");
    });

    it("resends code when resend code button is clicked", () => {
      const wrapper = render();
      const spy = jest.spyOn(wrapper.instance(), "send").mockImplementation();

      wrapper.setState({ delivery });

      wrapper.find({ name: "resendCode" }).simulate("click");

      expect(spy).toHaveBeenCalledTimes(1);
    });

    it("submits the form when submit button is clicked", () => {
      const wrapper = render();
      const spy = jest.spyOn(wrapper.instance(), "submit").mockImplementation();

      wrapper.setState({ delivery });

      wrapper.find({ name: "submit" }).simulate("click");

      expect(spy).toHaveBeenCalledTimes(1);
    });
  });

  it("changes to sign in state when user clicks back to sign in", () => {
    const onStateChange = jest.fn();
    const wrapper = render({ onStateChange });
    wrapper.find({ name: "backToSignIn" }).simulate("click");

    expect(onStateChange).toHaveBeenCalledWith("signIn", undefined);
  });
});
