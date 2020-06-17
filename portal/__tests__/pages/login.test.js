import Login from "../../src/pages/login";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("../../src/hooks/useAppLogic");

describe("Login", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
    act(() => {
      wrapper = shallow(<Login appLogic={appLogic} />);
    });
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is submitted", () => {
    it("calls login", async () => {
      expect.assertions();

      const email = "email@test.com";
      const password = "TestP@ssw0rd!";

      act(() => {
        wrapper.find({ name: "username" }).simulate("change", {
          target: {
            name: "username",
            value: email,
          },
        });
        wrapper.find({ name: "password" }).simulate("change", {
          target: {
            name: "password",
            value: password,
          },
        });
        wrapper.find("form").simulate("submit", {
          preventDefault: jest.fn(),
        });
      });

      expect(appLogic.login).toHaveBeenCalledWith(email, password);
    });
  });
});
