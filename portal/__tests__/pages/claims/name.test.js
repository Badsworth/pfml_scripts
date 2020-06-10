import Claim from "../../../src/models/Claim";
import { Name } from "../../../src/pages/claims/name";
import React from "react";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Name", () => {
  let appLogic, claim, wrapper;
  const claim_id = "12345";

  beforeEach(() => {
    claim = new Claim({
      application_id: claim_id,
      first_name: "Aquib",
      middle_name: "cricketer",
      last_name: "Khan",
    });
    appLogic = useAppLogic();

    wrapper = shallow(
      <Name claim={claim} appLogic={appLogic} query={{ claim_id }} />
    );
  });

  it("renders the empty page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page prefilled with user information", () => {
    claim = new Claim({
      application_id: claim_id,
      first_name: "Aquib",
      middle_name: "cricketer",
      last_name: "Khan",
    });
    appLogic = useAppLogic();
    wrapper = shallow(
      <Name claim={claim} appLogic={appLogic} query={{ claim_id }} />
    );
    expect(wrapper).toMatchSnapshot();
  });

  describe("when the form is successfully submitted", () => {
    it("calls updateClaim", async () => {
      expect.assertions();

      await wrapper.find("QuestionPage").simulate("save");
      // formState is undefined since we are not mounting the component
      expect(appLogic.updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        undefined
      );
    });
  });
});
