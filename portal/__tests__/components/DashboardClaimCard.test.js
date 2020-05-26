import Claim from "../../src/models/Claim";
import DashboardClaimCard from "../../src/components/DashboardClaimCard";
import React from "react";
import { shallow } from "enzyme";

describe("DashboardClaimCard", () => {
  it("renders a card for the given claim", () => {
    const wrapper = shallow(
      <DashboardClaimCard
        claim={new Claim({ application_id: "mock-claim-id" })}
        number={2}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
