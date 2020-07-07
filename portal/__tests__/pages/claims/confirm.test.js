import Claim from "../../../src/models/Claim";
import { Confirm } from "../../../src/pages/claims/confirm";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import { simulateEvents } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Confirm", () => {
  let appLogic, claim, submitForm, wrapper;
  const application_id = "34567";

  beforeEach(() => {
    appLogic = useAppLogic();
    claim = new Claim({ application_id });
    act(() => {
      wrapper = shallow(<Confirm claim={claim} appLogic={appLogic} />);
    });
    ({ submitForm } = simulateEvents(wrapper));
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  describe("when user clicks agree and submit", () => {
    it("calls submitApplication", () => {
      submitForm();
      expect(appLogic.submitClaim).toHaveBeenCalledWith(claim.application_id);
    });
  });
});
