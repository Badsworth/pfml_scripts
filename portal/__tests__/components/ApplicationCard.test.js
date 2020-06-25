import ApplicationCard from "../../src/components/ApplicationCard";
import Claim from "../../src/models/Claim";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCard", () => {
  it("renders a card for the given application", () => {
    const wrapper = shallow(
      <ApplicationCard
        claim={new Claim({ application_id: "mock-claim-id" })}
        number={2}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });
});
