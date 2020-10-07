import { MockClaimBuilder, renderWithAppLogic, testHook } from "../test-utils";
import ApplicationCard from "../../src/components/ApplicationCard";
import Applications from "../../src/pages/applications";
import Claim from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";
import React from "react";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAppLogic from "../../src/hooks/useAppLogic";

jest.mock("@aws-amplify/auth");

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
      render();
    });

    it("renders the empty page state", () => {
      // Dive to get the child component of the withClaim higher order component
      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when applications have been started or submitted", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([
        new MockClaimBuilder().create(),
        new MockClaimBuilder().submitted().create(),
      ]);
      jest
        .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
        .mockImplementation(() => true);
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

    it("renders list of started and completed applications", () => {
      expect(wrapper.find(ApplicationCard)).toHaveLength(2);
    });
  });

  describe("when applications have been completed", () => {
    beforeEach(() => {
      appLogic.claims.claims = new ClaimCollection([
        new MockClaimBuilder().completed().create(),
      ]);
      render();
    });

    it("visually hides the page title", () => {
      expect(wrapper.find("Title").prop("hidden")).toBe(true);
    });

    it("renders a heading for the completed applications", () => {
      expect(wrapper.find("Heading")).toMatchInlineSnapshot(`
        <Heading
          level="2"
          size="1"
        >
          Submitted applications
        </Heading>
      `);
    });

    it("renders list of completed applications", () => {
      expect(wrapper.find(ApplicationCard)).toHaveLength(1);
    });
  });

  describe("when in progress and completed applications both exist", () => {
    let completedClaim, startedClaim, submittedClaim;

    beforeEach(() => {
      startedClaim = new MockClaimBuilder().create();
      submittedClaim = new MockClaimBuilder().submitted().create();
      completedClaim = new MockClaimBuilder().completed().create();
      appLogic.claims.claims = new ClaimCollection([
        startedClaim,
        submittedClaim,
        completedClaim,
      ]);
      render();
    });

    it("increments the submitted ApplicationCard numbers by the number of in progress claims", () => {
      expect(wrapper.find(ApplicationCard).last().prop("number")).toBe(3);
    });

    it("separates completed claims into 'Submitted' section", () => {
      const sections = wrapper.findWhere((el) => {
        // using "ComponentWithUser" here because the "withClaimDocuments" HOC uses the
        // "withUser" HOC, which returns a "ComponentWithUser"
        return ["Heading", "ComponentWithUser"].includes(el.name());
      });

      expect(sections.get(1).props.claim).toEqual(startedClaim);
      expect(sections.get(2).props.claim).toEqual(submittedClaim);
      expect(sections.get(4).props.claim).toEqual(completedClaim);
    });
  });

  describe("when multiple claims exist", () => {
    const claim1 = new MockClaimBuilder().submitted().create();
    claim1.application_id = "claim1";
    const claim2 = new MockClaimBuilder().submitted().create();
    claim2.application_id = "claim2";

    beforeEach(() => {
      act(() => {
        const newClaims = [new Claim(claim1), new Claim(claim2)];

        appLogic.claims.claims = new ClaimCollection(newClaims);
      });
    });

    it("should only load documents for each claim once", async () => {
      const spy = jest
        .spyOn(appLogic.documents, "load")
        .mockImplementation(() => jest.fn());

      await act(async () => {
        jest
          .spyOn(appLogic.users, "requireUserConsentToDataAgreement")
          .mockImplementation(() => {});
        await mount(<Applications appLogic={appLogic} />);
      });

      expect(spy).toHaveBeenCalledTimes(2);
    });
  });
});
