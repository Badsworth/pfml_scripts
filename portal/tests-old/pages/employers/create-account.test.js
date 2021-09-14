import CreateAccount from "../../../src/pages/employers/create-account";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("CreateAccount", () => {
  let appLogic, changeField, submitForm, wrapper;

  beforeEach(() => {
    appLogic = useAppLogic();
    act(() => {
      wrapper = shallow(<CreateAccount appLogic={appLogic} />);
    });
    ({ changeField, submitForm } = simulateEvents(wrapper));
  });
  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  it("displays the form fields", () => {
    expect(wrapper.find("InputText").length).toEqual(2);
    expect(wrapper.find("InputPassword").length).toEqual(1);
  });

  it("calls createAccount upon form submission", async () => {
    const email = "email@test.com";
    const password = "TestP@ssw0rd!";
    const ein = "123456789";

    changeField("email_address", email);
    changeField("password", password);
    changeField("user_leave_administrator.employer_fein", ein);
    await submitForm();
    expect(appLogic.auth.createEmployerAccount).toHaveBeenCalledWith(
      email,
      password,
      ein
    );
  });
});
