import Claim, { ClaimStatus } from "../../src/models/Claim";
import ApplicationCard from "../../src/components/ApplicationCard";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCard", () => {
  it("renders a card for the given application", () => {
    const wrapper = shallow(
      <ApplicationCard
        claim={
          new Claim({
            application_id: "mock-claim-id",
            status: ClaimStatus.started,
          })
        }
        number={2}
      />
    );

    expect(wrapper).toMatchSnapshot();
  });

  describe("when the claim status is Submitted", () => {
    it("includes a link to edit the claim", () => {
      const wrapper = shallow(
        <ApplicationCard
          claim={
            new Claim({
              application_id: "mock-claim-id",
              status: ClaimStatus.submitted,
            })
          }
          number={2}
        />
      );

      expect(wrapper.find("ButtonLink")).toHaveLength(1);
    });
  });

  describe("when the claim status is Completed", () => {
    it("does not include a link to edit the claim", () => {
      const wrapper = shallow(
        <ApplicationCard
          claim={
            new Claim({
              application_id: "mock-claim-id",
              status: ClaimStatus.completed,
            })
          }
          number={2}
        />
      );

      expect(wrapper.find("ButtonLink")).toHaveLength(0);
    });
  });
});
