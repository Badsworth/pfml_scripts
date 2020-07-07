import { mount, shallow } from "enzyme";
import Claim from "../../../src/models/Claim";
import React from "react";
import { Ssn } from "../../../src/pages/claims/ssn";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

const claim_id = "12345";

const render = (customProps = {}, mountComponent) => {
  const props = Object.assign(
    {
      claim: new Claim({
        application_id: claim_id,
        employee_ssn: "123-123-1234",
      }),
      // eslint-disable-next-line react-hooks/rules-of-hooks
      appLogic: useAppLogic(),
      query: { claim_id },
    },
    customProps
  );

  const renderFn = mountComponent ? mount : shallow;

  return {
    props,
    wrapper: renderFn(<Ssn {...props} />),
  };
};

describe("Ssn", () => {
  it("renders the form", () => {
    const { wrapper } = render();

    expect(wrapper).toMatchSnapshot();
  });

  it("calls updateFieldFromEvent with user input", () => {
    const { wrapper } = render({}, true);

    const inputData = {
      employee_ssn: "555-55-5555",
    };

    for (const key in inputData) {
      const value = inputData[key];
      const event = { target: { name: key, value } };
      wrapper.find({ name: key, type: "text" }).simulate("change", event);
      expect(wrapper.find({ name: key, type: "text" }).prop("value")).toEqual(
        value
      );
    }
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateUser and updates the state", async () => {
      expect.assertions();
      const { props, wrapper } = render();

      await wrapper.find("QuestionPage").simulate("save");

      expect(props.appLogic.updateClaim).toHaveBeenCalledTimes(1);
    });
  });
});
