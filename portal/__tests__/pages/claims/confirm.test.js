import Claim from "../../../src/models/Claim";
import { Confirm } from "../../../src/pages/claims/confirm";
import React from "react";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Confirm", () => {
  let claim, wrapper;
  const application_id = "34567";

  beforeEach(() => {
    const appLogic = useAppLogic();
    claim = new Claim({ application_id });
    wrapper = shallow(<Confirm claim={claim} appLogic={appLogic} />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });
});
