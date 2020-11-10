import CreateAccount from "../../../src/pages/employers/create-account";
import React from "react";
import { Trans } from "react-i18next";
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
    expect(wrapper.find(Trans)).toMatchSnapshot();
  });

  it("calls createAccount upon form submission", () => {
    const email = "email@test.com";
    const password = "TestP@ssw0rd!";
    const ein = "123456789";

    changeField("username", email);
    changeField("password", password);
    changeField("ein", ein);
    submitForm();
    expect(appLogic.auth.createEmployerAccount).toHaveBeenCalledWith(
      email,
      password,
      ein
    );
  });
});
