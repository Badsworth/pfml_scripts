import CustomSignUp from "../../src/components/CustomSignUp";
import React from "react";
import { shallow } from "enzyme";
import theme from "../../src/utils/amplifyTheme";

const render = (props = {}) => {
  return shallow(<CustomSignUp authState="signUp" theme={theme} {...props} />);
};

describe("CustomSignUp", () => {
  describe("when signUpConfig prop has signupFields defined and hideAllDefaults set to true", () => {
    it("renders signUpFields from signUpConfig", () => {
      const signUpFields = [
        {
          label: "Email",
          key: "username",
          placeholder: "",
          required: true,
          type: "email",
          displayOrder: 1,
        },
        {
          label: "Password",
          key: "password",
          placeholder: "",
          required: true,
          type: "password",
          displayOrder: 2,
        },
      ];

      const wrapper = render({
        signUpConfig: { signUpFields, hideAllDefaults: true },
      });

      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("InputText")).toHaveLength(2);
    });
  });

  describe("when signUpConfig prop has no signUpFields defined", () => {
    it("renders default signUpFields", () => {
      const wrapper = render();

      expect(wrapper.find("InputText")).toHaveLength(4);
    });
  });

  describe("when authstate is not signUp", () => {
    it("is not rendered", () => {
      const wrapper = render({ authState: "signIn" });

      expect(wrapper.type()).toBeNull();
    });
  });

  it("calls Auth signUp when user clicks sign up", () => {
    const wrapper = render();
    const signUp = jest.spyOn(wrapper.instance(), "signUp");
    wrapper
      .find({ type: "submit" })
      .simulate("click", { preventDefault: jest.fn() });

    expect(signUp).toHaveBeenCalled();
  });

  it("changes to sign in state when user indicates they already have an account", () => {
    // mocks AuthPiece implementation: https://github.com/aws-amplify/amplify-js/blob/4bd5c7ebef0ad223d4c05a452e696242927a750f/packages/aws-amplify-react/src/Auth/AuthPiece.tsx#L180
    const onStateChange = jest.fn();
    const wrapper = render({ onStateChange });
    // "Sign in" link
    wrapper.find(".usa-button--unstyled").simulate("click");

    expect(onStateChange).toHaveBeenCalledWith("signIn", undefined);
  });
});
