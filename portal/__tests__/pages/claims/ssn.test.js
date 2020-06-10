import { mount, shallow } from "enzyme";
import Claim from "../../../src/models/Claim";
import ClaimsApi from "../../../src/api/ClaimsApi";
import React from "react";
import { Ssn } from "../../../src/pages/claims/ssn";
import User from "../../../src/models/User";
import routes from "../../../src/routes";

const claim_id = "12345";

const render = (customProps = {}, mountComponent) => {
  const claimsApi = new ClaimsApi({ user: new User() });

  jest
    .spyOn(claimsApi, "updateClaim")
    .mockImplementation((application_id, patchData) => {
      const claim = new Claim(patchData);
      return {
        success: true,
        status: 200,
        apiErrors: [],
        claim,
      };
    });

  const props = Object.assign(
    {
      claim: new Claim({
        application_id: claim_id,
        employee_ssn: "123-123-1234",
      }),
      claimsApi,
      updateClaim: jest.fn(),
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

  it("redirects to leaveReason", () => {
    const { props, wrapper } = render();

    expect(wrapper.find("QuestionPage").prop("nextPage")).toEqual(
      `${routes.claims.leaveReason}?claim_id=${props.query.claim_id}`
    );
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

      expect(props.claimsApi.updateClaim).toHaveBeenCalledTimes(1);
      expect(props.updateClaim).toHaveBeenCalledWith(expect.any(Claim));
    });
  });
});
