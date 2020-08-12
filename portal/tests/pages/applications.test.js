import Claim, { ClaimStatus } from "../../src/models/Claim";
import { renderWithAppLogic, testHook } from "../test-utils";
import Applications from "../../src/pages/applications";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import User from "../../src/models/User";
import { shallow } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("Applications", () => {
  let appLogic, wrapper;

  function render() {
    // Dive two levels since Applications is wrapped by withClaims and withUser
    ({ wrapper } = renderWithAppLogic(Applications, {
      diveLevels: 2,
      props: { appLogic },
    }));
  }

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
      appLogic.users.user = new User({ consented_to_data_sharing: true });
    });

    jest.spyOn(appLogic.claims, "load").mockResolvedValue();
  });

  describe("when no claims exist", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([]);

      wrapper = shallow(<Applications appLogic={appLogic} />);
    });

    it("renders the empty page state", () => {
      // Dive to get the child component of the withClaim higher order component
      expect(wrapper.dive().dive()).toMatchSnapshot();
    });
  });

  describe("when applications have been started", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([
        new Claim({
          application_id: "mock_claim_id",
          status: ClaimStatus.started,
        }),
      ]);
      render();
    });

    it("visually hides the page title", () => {
      expect(wrapper.find("Title").prop("hidden")).toBe(true);
    });

    it("renders a heading for the started applications", () => {
      expect(wrapper.find("Heading")).toMatchInlineSnapshot(`
        <Heading
          level="2"
          size="1"
        >
          In-progress applications
        </Heading>
      `);
    });

    it("renders list of started applications", () => {
      expect(wrapper.find("ApplicationCard")).toHaveLength(1);
    });
  });

  describe("when applications have been submitted", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([
        new Claim({
          application_id: "mock_claim_id",
          status: ClaimStatus.submitted,
        }),
      ]);
      render();
    });

    it("visually hides the page title", () => {
      expect(wrapper.find("Title").prop("hidden")).toBe(true);
    });

    it("renders a heading for the submitted applications", () => {
      expect(wrapper.find("Heading")).toMatchInlineSnapshot(`
        <Heading
          level="2"
          size="1"
        >
          Submitted applications
        </Heading>
      `);
    });

    it("renders list of submitted applications", () => {
      expect(wrapper.find("ApplicationCard")).toHaveLength(1);
    });
  });

  describe("when in progress and completed applications both exist", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([
        new Claim({
          application_id: "mock_claim_id",
          status: ClaimStatus.started,
        }),
        new Claim({
          application_id: "mock_claim_id",
          status: ClaimStatus.completed,
        }),
      ]);
      render();
    });

    it("increments the submitted ApplicationCard numbers by the number of in progress claims", () => {
      expect(wrapper.find("ApplicationCard").last().prop("number")).toBe(2);
    });
  });
});
