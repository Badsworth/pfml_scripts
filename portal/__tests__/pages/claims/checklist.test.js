import { Checklist } from "../../../src/pages/claims/checklist";
import Claim from "../../../src/models/Claim";
import React from "react";
import { shallow } from "enzyme";

describe("Checklist", () => {
  it("renders component", () => {
    const wrapper = shallow(
      <Checklist
        claim={new Claim({ application_id: "mock-application-id" })}
        appLogic={{}}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
