import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  testHook,
} from "../../test-utils";

import Applications from "../../../src/pages/applications/index";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import React from "react";
import User from "../../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { mount } from "enzyme";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("@aws-amplify/auth");

describe("Applications", () => {
  let appLogic, wrapper;

  function render() {
    ({ wrapper } = renderWithAppLogic(Applications, {
      props: { appLogic },
    }));
  }

  beforeEach(() => {
    mockRouter.pathname = routes.applications.index;

    testHook(() => {
      appLogic = useAppLogic();
      appLogic.users.user = new User({ consented_to_data_sharing: true });
      appLogic.benefitsApplications.hasLoadedAll = true;
    });

    jest.spyOn(appLogic.benefitsApplications, "loadAll").mockResolvedValue();
  });

  describe("when no claims exist", () => {
    it("redirects to getReady", () => {
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([]);
      const goToSpy = jest.spyOn(appLogic.portalFlow, "goTo");
      render();

      expect(goToSpy).toHaveBeenCalledWith("/applications/get-ready");
    });
  });

  describe("when applications have been started or submitted", () => {
    beforeEach(() => {
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([
          new MockBenefitsApplicationBuilder().create(),
          new MockBenefitsApplicationBuilder().submitted().create(),
        ]);
      jest
        .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
        .mockImplementation(() => true);
      render();
    });

    it("renders a heading for the started applications", () => {
      expect(wrapper.find("Heading").first()).toMatchInlineSnapshot(`
        <Heading
          level="2"
        >
          In-progress applications
        </Heading>
      `);
    });

    it("renders list of started and completed applications", () => {
      expect(wrapper.find("ApplicationCard")).toHaveLength(2);
    });
  });

  describe("when applications have been completed", () => {
    beforeEach(() => {
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([
          new MockBenefitsApplicationBuilder().completed().create(),
        ]);
      render();
    });

    it("renders a heading for the completed applications", () => {
      expect(wrapper.find("Heading").first()).toMatchInlineSnapshot(`
        <Heading
          level="2"
        >
          Submitted applications
        </Heading>
      `);
    });

    it("renders list of completed applications", () => {
      expect(wrapper.find("ApplicationCard").dive()).toHaveLength(1);
    });
  });

  describe("when in progress and completed applications both exist", () => {
    let completedClaim, startedClaim, submittedClaim;

    beforeEach(() => {
      startedClaim = new MockBenefitsApplicationBuilder().create();
      submittedClaim = new MockBenefitsApplicationBuilder()
        .submitted()
        .create();
      completedClaim = new MockBenefitsApplicationBuilder()
        .completed()
        .create();
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([
          startedClaim,
          submittedClaim,
          completedClaim,
        ]);
      render();
    });

    it("increments the submitted ApplicationCard numbers by the number of in progress claims", () => {
      expect(wrapper.find("ApplicationCard").last().prop("number")).toBe(3);
    });

    it("separates completed claims into 'Submitted' section", () => {
      expect(wrapper.find("ApplicationCard").get(0).props.claim).toEqual(
        startedClaim
      );
      expect(wrapper.find("ApplicationCard").get(1).props.claim).toEqual(
        submittedClaim
      );
      expect(wrapper.find("ApplicationCard").get(2).props.claim).toEqual(
        completedClaim
      );
    });
  });

  describe("when multiple claims exist", () => {
    const claim1 = new MockBenefitsApplicationBuilder().submitted().create();
    claim1.application_id = "claim1";
    const claim2 = new MockBenefitsApplicationBuilder().submitted().create();
    claim2.application_id = "claim2";

    beforeEach(() => {
      act(() => {
        const newClaims = [
          new BenefitsApplication(claim1),
          new BenefitsApplication(claim2),
        ];

        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection(newClaims);
      });
    });

    it("should only load documents for each claim once", async () => {
      const spy = jest
        .spyOn(appLogic.documents, "loadAll")
        .mockImplementation(() => jest.fn());

      await act(async () => {
        jest
          .spyOn(appLogic.users, "requireUserConsentToDataAgreement")
          .mockImplementation(() => {});
        jest
          .spyOn(appLogic.users, "requireUserRole")
          .mockImplementation(() => {});
        await mount(<Applications appLogic={appLogic} />);
      });

      expect(spy).toHaveBeenCalledTimes(2);
    });

    it("renders application card when feature flags are enabled", () => {
      process.env.featureFlags = {
        claimantShowStatusPage: true,
      };

      expect(wrapper.find("ApplicationCard")).toMatchSnapshot();
    });
  });
});
