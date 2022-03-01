import { BadRequestError, NotFoundError } from "../../src/errors";
import BenefitsApplication, {
  BenefitsApplicationStatus,
} from "../../src/models/BenefitsApplication";
import { act, renderHook } from "@testing-library/react-hooks";
import {
  completeClaimMock,
  createClaimMock,
  getClaimMock,
  getClaimMockApplicationId,
  getClaimsMock,
  importClaimMock,
  submitClaimMock,
  submitPaymentPreferenceMock,
  updateClaimMock,
} from "../../src/api/BenefitsApplicationsApi";
import ApiResourceCollection from "../../src/models/ApiResourceCollection";
import ErrorInfo from "../../src/models/ErrorInfo";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useBenefitsApplicationsLogic from "../../src/hooks/useBenefitsApplicationsLogic";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/BenefitsApplicationsApi");
jest.mock("../../src/services/tracker");

describe("useBenefitsApplicationsLogic", () => {
  let applicationId, claimsLogic, errorsLogic, portalFlow;

  function setup() {
    renderHook(() => {
      portalFlow = usePortalFlow();
      errorsLogic = useErrorsLogic({ portalFlow });
      claimsLogic = useBenefitsApplicationsLogic({
        errorsLogic,
        portalFlow,
      });
    });
  }

  beforeEach(() => {
    applicationId = "mock-application-id";
    mockRouter.pathname = routes.getReady;
  });

  afterEach(() => {
    errorsLogic = null;
    claimsLogic = null;
    portalFlow = null;
  });

  it("sets initial claims data to empty collection", () => {
    setup();

    expect(claimsLogic.benefitsApplications).toBeInstanceOf(
      ApiResourceCollection
    );
    expect(claimsLogic.benefitsApplications.items).toHaveLength(0);
  });

  describe("associate", () => {
    const mockAssociateFormState = {
      absence_case_id: "mock-absence-id",
      tax_identifier: "123-45-6789",
    };

    beforeEach(() => {
      mockRouter.pathname = routes.applications.importClaim;
      setup();
    });

    it("transforms the absence ID to uppercase before sending the request", async () => {
      await act(async () => {
        await claimsLogic.associate(mockAssociateFormState);
      });

      expect(importClaimMock).toHaveBeenCalledWith({
        ...mockAssociateFormState,
        absence_case_id: "MOCK-ABSENCE-ID",
      });
    });

    it("updates state to force a new API request the next time loadPage is called, after an application has been associated successfully", async () => {
      await act(async () => {
        await claimsLogic.loadPage();
      });

      expect(claimsLogic.isLoadingClaims).toBe(false);
      expect(getClaimsMock).toHaveBeenCalledTimes(1);

      await act(async () => {
        await claimsLogic.associate(mockAssociateFormState);
      });

      expect(claimsLogic.isLoadingClaims).toBeUndefined();

      await act(async () => {
        await claimsLogic.loadPage();
      });

      expect(getClaimsMock).toHaveBeenCalledTimes(2);
    });

    it("routes to applications index page when the request succeeds", async () => {
      await act(async () => {
        await claimsLogic.associate(mockAssociateFormState);
      });

      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining(
          `${routes.applications.index}?applicationAssociated=mock-absence-id`
        )
      );
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      importClaimMock.mockImplementationOnce(() => {
        throw new BadRequestError();
      });

      await act(async () => {
        await claimsLogic.associate(mockAssociateFormState);
      });

      expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
    });

    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new ErrorInfo()]);
      });

      await act(async () => {
        await claimsLogic.associate(mockAssociateFormState);
      });

      expect(errorsLogic.errors).toHaveLength(0);
    });
  });

  describe("hasLoadedBenefitsApplicationAndWarnings", () => {
    beforeEach(() => {
      // Make sure the ID we're loading matches what the API will return to us so caching works as
      applicationId = getClaimMockApplicationId;

      setup();
    });

    it("returns true when a claim and its warnings are loaded", async () => {
      expect(
        claimsLogic.hasLoadedBenefitsApplicationAndWarnings(applicationId)
      ).toBe(false);

      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      expect(
        claimsLogic.hasLoadedBenefitsApplicationAndWarnings(applicationId)
      ).toBe(true);
    });
  });

  describe("load", () => {
    beforeEach(() => {
      // Make sure the ID we're loading matches what the API will return to us so caching works as
      applicationId = getClaimMockApplicationId;

      setup();
    });

    it("asynchronously fetches a claim and adds it to claims collection", async () => {
      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      const claims = claimsLogic.benefitsApplications.items;

      expect(claims).toHaveLength(1);
      expect(claims[0]).toBeInstanceOf(BenefitsApplication);
      expect(getClaimMock).toHaveBeenCalledTimes(1);
    });

    it("stores the claim's warnings in warningsLists", async () => {
      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      expect(claimsLogic.warningsLists).toEqual({
        [applicationId]: [],
      });
    });

    it("only makes api request if claim has not been loaded", async () => {
      await act(async () => {
        await claimsLogic.load(applicationId);
        await claimsLogic.load(applicationId);
      });

      expect(getClaimMock).toHaveBeenCalledTimes(1);
    });

    it("makes API request when claim is loaded but its warnings haven't been stored in warningsLists", async () => {
      await act(async () => {
        await claimsLogic.loadPage();
        await claimsLogic.load(applicationId);
      });

      expect(getClaimMock).toHaveBeenCalledTimes(1);
    });

    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new ErrorInfo()]);
      });

      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      expect(errorsLogic.errors).toHaveLength(0);
    });

    describe("when request is unsuccessful", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("redirects to /applications page if claim wasn't found", async () => {
        getClaimMock.mockImplementationOnce(() => {
          throw new NotFoundError();
        });

        await act(async () => {
          await claimsLogic.load(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(routes.applications.index);
      });

      it("catches exceptions thrown from the API module", async () => {
        getClaimMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.load(applicationId);
        });

        expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
      });
    });
  });

  describe("loadPage", () => {
    beforeEach(() => {
      setup();
    });

    it("asynchronously fetches all claims and adds to claims collection", async () => {
      await act(async () => {
        await claimsLogic.loadPage();
      });

      expect(claimsLogic.benefitsApplications.items[0]).toBeInstanceOf(
        BenefitsApplication
      );
      expect(getClaimsMock).toHaveBeenCalled();
    });

    it("only makes api request if all claims have not been loaded", async () => {
      await act(async () => {
        const claim = new BenefitsApplication({
          application_id: getClaimMockApplicationId,
        });
        getClaimsMock.mockImplementationOnce(() => {
          return {
            claim,
            paginationMeta: {
              page_offset: 1,
            },
          };
        });
        // this should make an API request since ALL claims haven't been loaded yet
        await claimsLogic.loadPage();
        // but this shouldn't, since we've already loaded all claims
        await claimsLogic.loadPage();
      });

      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });

    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new ErrorInfo()]);
      });

      await act(async () => {
        await claimsLogic.loadPage();
      });

      expect(errorsLogic.errors).toHaveLength(0);
    });

    it("makes api request when page_offset is changed", async () => {
      await act(async () => {
        const claim = new BenefitsApplication({
          application_id: getClaimMockApplicationId,
        });
        getClaimsMock.mockImplementationOnce(() => {
          return {
            claim,
            paginationMeta: {
              page_offset: 1,
            },
          };
        });

        // makes initial api request
        await claimsLogic.loadPage();
        // does not make this call since page_offset is the same
        await claimsLogic.loadPage();
        // makes api call due to page_offset changing
        await claimsLogic.loadPage(2);
      });

      expect(getClaimsMock).toHaveBeenCalledTimes(2);
    });

    describe("when request is unsuccessful", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("catches exceptions thrown from the API module", async () => {
        getClaimsMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.loadPage();
        });

        expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });

  describe("create", () => {
    beforeEach(() => {
      mockRouter.pathname = routes.applications.start;
      setup();
    });

    it("sends API request", async () => {
      await act(async () => {
        await claimsLogic.create();
      });

      expect(createClaimMock).toHaveBeenCalled();
    });

    it("routes to claim checklist page when the request succeeds", async () => {
      await act(async () => {
        await claimsLogic.create();
      });

      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining(
          `${routes.applications.checklist}?claim_id=mock`
        )
      );
    });

    it("clears prior errors", async () => {
      act(() => {
        errorsLogic.setErrors([new ErrorInfo()]);
      });

      await act(async () => {
        await claimsLogic.create();
      });

      expect(errorsLogic.errors).toHaveLength(0);
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

      createClaimMock.mockImplementationOnce(() => {
        throw new BadRequestError();
      });

      await act(async () => {
        await claimsLogic.create();
      });

      expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
      expect(mockRouter.push).not.toHaveBeenCalled();
    });

    it("updates state to force a new API request when needed", async () => {
      const claim = new BenefitsApplication({ application_id: "12345" });
      createClaimMock.mockResolvedValueOnce({
        claim,
        success: true,
      });
      await act(async () => {
        await claimsLogic.loadPage();
      });
      expect(getClaimsMock).toHaveBeenCalledTimes(1);

      expect(claimsLogic.isLoadingClaims).toBe(false);
      await act(async () => {
        await claimsLogic.create();
      });
      expect(claimsLogic.isLoadingClaims).toBeUndefined();

      await act(async () => {
        await claimsLogic.loadPage();
      });

      expect(getClaimsMock).toHaveBeenCalledTimes(2);
    });

    describe("when claims have previously been loaded", () => {
      let claim, existingClaims;

      beforeEach(async () => {
        existingClaims = new ApiResourceCollection("application_id", [
          new BenefitsApplication({ application_id: "1" }),
          new BenefitsApplication({ application_id: "2" }),
        ]);

        getClaimsMock.mockImplementationOnce(() => {
          return {
            success: true,
            claims: existingClaims,
          };
        });

        claim = new BenefitsApplication({ application_id: "12345" });

        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        await act(async () => {
          await claimsLogic.loadPage();
          await claimsLogic.create();
        });
      });

      it("doesn't affect existing claims", () => {
        expect.assertions(existingClaims.items.length);
        existingClaims.items.forEach((existingClaim) => {
          expect(claimsLogic.benefitsApplications.items).toContain(
            existingClaim
          );
        });
      });
    });
  });

  describe("when claims have been loaded or a new claim was created", () => {
    describe("complete", () => {
      beforeEach(async () => {
        mockRouter.pathname = routes.applications.review;
        setup();
        const claim = new BenefitsApplication({
          application_id: applicationId,
        });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        await act(async () => {
          await claimsLogic.create();
        });

        mockRouter.push.mockClear();
      });

      it("completes the claim", async () => {
        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        const claim = claimsLogic.benefitsApplications.getItem(applicationId);

        expect(completeClaimMock).toHaveBeenCalledWith(applicationId);
        expect(claim.status).toBe(BenefitsApplicationStatus.completed);
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new ErrorInfo()]);
        });

        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });

      it("routes to claim success page when the request succeeds", async () => {
        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.applications.success}?claim_id=${applicationId}`
          )
        );
      });

      it("catches exceptions thrown from the API module", async () => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

        completeClaimMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("update", () => {
      const patchData = {
        first_name: "Bud",
        last_name: null,
      };

      beforeEach(() => {
        const claim = new BenefitsApplication({
          application_id: applicationId,
        });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });
      });

      it("updates claim and redirects to nextPage when successful", async () => {
        mockRouter.pathname = routes.applications.ssn;

        setup();

        await act(async () => {
          await claimsLogic.create();
        });

        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        const claim = claimsLogic.benefitsApplications.getItem(applicationId);

        expect(claim).toBeInstanceOf(BenefitsApplication);
        expect(claim).toEqual(expect.objectContaining(patchData));
        expect(updateClaimMock).toHaveBeenCalled();
        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.applications.checklist}?claim_id=${claim.application_id}`
          )
        );
      });

      it("clears prior errors", async () => {
        mockRouter.pathname = routes.applications.name;
        setup();

        await act(async () => {
          await claimsLogic.create();

          errorsLogic.setErrors([new ErrorInfo()]);
        });

        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });

      describe("when request is unsuccessful", () => {
        beforeEach(() => {
          jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        });

        it("updates the local claim and warningsList if response only included warnings", async () => {
          mockRouter.pathname = routes.applications.name;
          const claimResponse = new MockBenefitsApplicationBuilder()
            .id(applicationId)
            .create();
          const last_name = "Updated from API";

          setup();

          await act(async () => {
            await claimsLogic.create();
          });
          mockRouter.push.mockClear();

          updateClaimMock.mockResolvedValueOnce({
            claim: { ...claimResponse, last_name },
            errors: [],
            warnings: [{ field: "first_name", type: "required" }],
            // Responses with only warnings receive a 200 status
            success: true,
          });

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          const claim = claimsLogic.benefitsApplications.getItem(applicationId);

          expect(claim.last_name).toBe(last_name);
          expect(claimsLogic.warningsLists[applicationId]).toEqual([
            { field: "first_name", type: "required" },
          ]);
        });

        it("reports warnings for fields on the Name page", async () => {
          mockRouter.pathname = routes.applications.name;

          setup();

          await act(async () => {
            await claimsLogic.create();
          });

          updateClaimMock.mockResolvedValueOnce({
            claim: new MockBenefitsApplicationBuilder()
              .id(applicationId)
              .create(),
            errors: [],
            warnings: [
              { field: "first_name", type: "required" },
              { field: "last_name", type: "required" },
              { field: "date_of_birth", type: "required" },
            ],
            // Responses with only warnings receive a 200 status
            success: true,
          });

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          const errors = errorsLogic.errors;
          const errorFields = errors.map((error) => error.field);

          expect(errors).toHaveLength(2);
          expect(errorFields).toContain("first_name");
          expect(errorFields).toContain("last_name");
        });

        it("reports warnings for applicable rules on the Intermittent Leave page", async () => {
          mockRouter.pathname = routes.applications.leavePeriodIntermittent;
          setup();

          await act(async () => {
            await claimsLogic.create();
          });

          updateClaimMock.mockResolvedValueOnce({
            claim: new MockBenefitsApplicationBuilder()
              .id(applicationId)
              .create(),
            errors: [],
            warnings: [
              { rule: "disallow_hybrid_intermittent_leave" },
              { field: "tax_identifier", type: "required" },
            ],
            // Responses with only warnings receive a 200 status
            success: true,
          });

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          const errors = errorsLogic.errors;

          expect(errors).toHaveLength(1);
          expect(errors[0].rule).toBe("disallow_hybrid_intermittent_leave");
        });

        it("catches exceptions thrown from the API module", async () => {
          mockRouter.pathname = routes.applications.name;
          setup();

          await act(async () => {
            await claimsLogic.create();
          });
          mockRouter.push.mockClear();

          updateClaimMock.mockImplementationOnce(() => {
            throw new BadRequestError();
          });

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
          expect(mockRouter.push).not.toHaveBeenCalled();
        });
      });
    });

    describe("submit", () => {
      beforeEach(async () => {
        mockRouter.pathname = routes.applications.review;
        setup(routes.applications);

        const claim = new BenefitsApplication({
          application_id: applicationId,
        });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        await act(async () => {
          await claimsLogic.create();
        });

        mockRouter.push.mockClear();
      });

      it("submits the claim", async () => {
        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        const claim = claimsLogic.benefitsApplications.getItem(applicationId);

        expect(submitClaimMock).toHaveBeenCalledWith(applicationId);
        expect(claim.status).toBe(BenefitsApplicationStatus.submitted);
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new ErrorInfo()]);
        });

        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });

      it("routes to claim checklist page when the request succeeds", async () => {
        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.applications.checklist}?claim_id=${applicationId}`
          )
        );
      });

      it("passes part-one-submitted into the route when the request succeeds", async () => {
        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(`&part-one-submitted=true`)
        );
      });

      it("catches exceptions thrown from the API module", async () => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        submitClaimMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("submitPaymentPreference", () => {
      const paymentData = {
        payment_preference: new MockBenefitsApplicationBuilder()
          .directDeposit()
          .create().payment_preference,
      };

      beforeEach(async () => {
        mockRouter.pathname = routes.applications.paymentMethod;
        setup(routes.applications);

        const claim = new BenefitsApplication({
          application_id: applicationId,
        });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        await act(async () => {
          await claimsLogic.create();
        });

        mockRouter.push.mockClear();
      });

      it("submits the payment preference", async () => {
        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId, paymentData);
        });

        const claim = claimsLogic.benefitsApplications.getItem(applicationId);

        expect(submitPaymentPreferenceMock).toHaveBeenCalledWith(
          applicationId,
          paymentData
        );
        expect(claim.has_submitted_payment_preference).toBe(true);
      });

      it("clears prior errors", async () => {
        act(() => {
          errorsLogic.setErrors([new ErrorInfo()]);
        });

        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId);
        });

        expect(errorsLogic.errors).toHaveLength(0);
      });

      it("routes to claim checklist page when the request succeeds", async () => {
        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.applications.checklist}?claim_id=${applicationId}`
          )
        );
      });

      it("passes payment-pref-submitted into the route when the request succeeds", async () => {
        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId, paymentData);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(`&payment-pref-submitted=true`)
        );
      });

      it("catches exceptions thrown from the API module", async () => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        submitPaymentPreferenceMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId);
        });

        expect(errorsLogic.errors[0].name).toEqual("BadRequestError");
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });
});
