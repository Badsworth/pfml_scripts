import Claim, { ClaimStatus } from "../../src/models/Claim";
import Applications from "../../src/pages/applications";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import User from "../../src/models/User";
import { shallow } from "enzyme";
import { testHook } from "../test-utils";
import useAppLogic from "../../src/hooks/useAppLogic";

describe("Applications", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic({ user: new User() });
    });

    jest.spyOn(appLogic.claims, "load").mockResolvedValue();
  });

  describe("when claims haven't been loaded yet", () => {
    beforeEach(() => {
      appLogic.claims.claims = null;

      wrapper = shallow(<Applications appLogic={appLogic} />);
    });

    it("renders the loading page state", () => {
      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when no claims exist", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([]);

      wrapper = shallow(<Applications appLogic={appLogic} />);
    });

    it("renders the empty page state", () => {
      expect(wrapper).toMatchSnapshot();
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

      wrapper = shallow(<Applications appLogic={appLogic} />);
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

      wrapper = shallow(<Applications appLogic={appLogic} />);
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

      wrapper = shallow(<Applications appLogic={appLogic} />);
    });

    it("increments the submitted ApplicationCard numbers by the number of in progress claims", () => {
      expect(wrapper.find("ApplicationCard").last().prop("number")).toBe(2);
    });
  });
});
