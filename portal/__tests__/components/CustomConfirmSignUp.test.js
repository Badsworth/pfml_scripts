import CustomConfirmSignUp from "../../src/components/CustomConfirmSignUp";
import React from "react";
import { shallow } from "enzyme";
import theme from "../../src/utils/amplifyTheme";

const render = (props = {}) => {
  return shallow(
    <CustomConfirmSignUp
      authState="confirmSignUp"
      theme={theme}
      authData={{
        user: { username: "user_name@test.com" },
      }}
      {...props}
    />
  );
};

describe("CustomConfirmSignUp", () => {
  it("renders the page", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  describe("when authstate is not confirmSignUp", () => {
    it("is not rendered", () => {
      const wrapper = render({ authState: "signUp" });

      expect(wrapper.type()).toBeNull();
    });
  });

  it("resends link when user clicks resend link", () => {
    const wrapper = render();
    const resend = jest
      .spyOn(wrapper.instance(), "resend")
      .mockImplementation();
    wrapper
      .find({ name: "resendCode" })
      .simulate("click", { preventDefault: jest.fn() });

    expect(resend).toHaveBeenCalled();
  });

  it("changes to sign in state when user clicks back to sign in", () => {
    // mocks AuthPiece implementation: https://github.com/aws-amplify/amplify-js/blob/4bd5c7ebef0ad223d4c05a452e696242927a750f/packages/aws-amplify-react/src/Auth/AuthPiece.tsx#L180
    const onStateChange = jest.fn();
    const wrapper = render({ onStateChange });
    wrapper.find({ name: "backToSignIn" }).simulate("click");

    expect(onStateChange).toHaveBeenCalledWith("signIn", undefined);
  });

  it("submits code", () => {
    const wrapper = render();
    const confirm = jest
      .spyOn(wrapper.instance(), "confirm")
      .mockImplementation();
    wrapper
      .find({ name: "submit" })
      .simulate("click", { preventDefault: jest.fn() });

    expect(confirm).toHaveBeenCalled();
  });
});
