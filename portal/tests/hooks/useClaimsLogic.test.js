import { BadRequestError, NotFoundError } from "../../src/errors";
import Claim, { ClaimStatus } from "../../src/models/Claim";
import { MockClaimBuilder, testHook } from "../test-utils";
import {
  completeClaimMock,
  createClaimMock,
  getClaimMock,
  getClaimMockApplicationId,
  getClaimsMock,
  submitClaimMock,
  submitPaymentPreferenceMock,
  updateClaimMock,
} from "../../src/api/ClaimsApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import ClaimCollection from "../../src/models/ClaimCollection";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useClaimsLogic from "../../src/hooks/useClaimsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/ClaimsApi");
jest.mock("../../src/services/tracker");

describe("useClaimsLogic", () => {
  let appErrorsLogic, applicationId, claimsLogic, portalFlow, user;

  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      claimsLogic = useClaimsLogic({ appErrorsLogic, user, portalFlow });
    });
  }

  beforeEach(() => {
    applicationId = "mock-application-id";
    mockRouter.pathname = routes.dashboard;
    user = new User({ user_id: "mock-user-id" });
  });

  afterEach(() => {
    appErrorsLogic = null;
    claimsLogic = null;
    portalFlow = null;
  });

  it("sets initial claims data to empty collection", () => {
    renderHook();

    expect(claimsLogic.claims).toBeInstanceOf(ClaimCollection);
    expect(claimsLogic.claims.items).toHaveLength(0);
  });

  describe("hasLoadedClaimAndWarnings", () => {
    beforeEach(() => {
      // Make sure the ID we're loading matches what the API will return to us so caching works as
      applicationId = getClaimMockApplicationId;

      renderHook();
    });

    it("returns true when a claim and its warnings are loaded", async () => {
      expect(claimsLogic.hasLoadedClaimAndWarnings(applicationId)).toBe(false);

      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      expect(claimsLogic.hasLoadedClaimAndWarnings(applicationId)).toBe(true);
    });
  });

  describe("load", () => {
    beforeEach(() => {
      // Make sure the ID we're loading matches what the API will return to us so caching works as
      applicationId = getClaimMockApplicationId;

      renderHook();
    });

    it("asynchronously fetches a claim and adds it to claims collection", async () => {
      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      const claims = claimsLogic.claims.items;

      expect(claims).toHaveLength(1);
      expect(claims[0]).toBeInstanceOf(Claim);
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
        await claimsLogic.loadAll();
        await claimsLogic.load(applicationId);
      });

      expect(getClaimMock).toHaveBeenCalledTimes(1);
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await claimsLogic.load(applicationId);
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    describe("when request is unsuccessful", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("throws an error if user has not been loaded", async () => {
        user = null;
        renderHook();
        await expect(claimsLogic.load).rejects.toThrow(/Cannot load claim/);
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

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "BadRequestError"
        );
      });
    });
  });

  describe("loadAll", () => {
    beforeEach(() => {
      renderHook();
    });

    it("asynchronously fetches all claims and adds to claims collection", async () => {
      await act(async () => {
        await claimsLogic.loadAll();
      });

      expect(claimsLogic.claims.items[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalled();
    });

    it("only makes api request if all claims have not been loaded", async () => {
      await act(async () => {
        // load a single application so that the claims collection is not empty
        await claimsLogic.load(getClaimMockApplicationId);
        // this should make an API request since ALL claims haven't been loaded yet
        await claimsLogic.loadAll();
        // but this shouldn't, since we've already loaded all claims
        await claimsLogic.loadAll();
      });

      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await claimsLogic.loadAll();
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    describe("when request is unsuccessful", () => {
      beforeEach(() => {
        jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
      });

      it("throws an error if user has not been loaded", async () => {
        user = null;
        renderHook();
        await expect(claimsLogic.loadAll).rejects.toThrow(/Cannot load claims/);
      });

      it("catches exceptions thrown from the API module", async () => {
        getClaimsMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.loadAll();
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "BadRequestError"
        );
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });

  describe("create", () => {
    beforeEach(() => {
      mockRouter.pathname = routes.applications.start;
      renderHook();
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
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await claimsLogic.create();
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
    });

    it("catches exceptions thrown from the API module", async () => {
      jest.spyOn(console, "error").mockImplementationOnce(jest.fn());

      createClaimMock.mockImplementationOnce(() => {
        throw new BadRequestError();
      });

      await act(async () => {
        await claimsLogic.create();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toEqual("BadRequestError");
      expect(mockRouter.push).not.toHaveBeenCalled();
    });

    it("adds the claim to a new collection when claims weren't loaded yet", async () => {
      const claim = new Claim({ application_id: "12345" });
      createClaimMock.mockResolvedValueOnce({
        claim,
        success: true,
      });

      await act(async () => {
        await claimsLogic.create();
      });

      expect(claimsLogic.claims.items).toContain(claim);
    });

    describe("when claims have previously been loaded", () => {
      let claim, existingClaims;

      beforeEach(async () => {
        existingClaims = new ClaimCollection([
          new Claim({ application_id: "1" }),
          new Claim({ application_id: "2" }),
        ]);

        getClaimsMock.mockImplementationOnce(() => {
          return {
            success: true,
            claims: existingClaims,
          };
        });

        claim = new Claim({ application_id: "12345" });

        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        await act(async () => {
          await claimsLogic.loadAll();
          await claimsLogic.create();
        });
      });

      it("stores the new claim", () => {
        expect(claimsLogic.claims.items).toContain(claim);
      });

      it("doesn't affect existing claims", () => {
        expect.assertions(existingClaims.items.length);
        existingClaims.items.forEach((existingClaim) => {
          expect(claimsLogic.claims.items).toContain(existingClaim);
        });
      });
    });
  });

  describe("when claims have been loaded or a new claim was created", () => {
    describe("complete", () => {
      beforeEach(async () => {
        mockRouter.pathname = routes.applications.review;
        renderHook();
        const claim = new Claim({ application_id: applicationId });
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

        const claim = claimsLogic.claims.getItem(applicationId);

        expect(completeClaimMock).toHaveBeenCalledWith(applicationId);
        expect(claim.status).toBe(ClaimStatus.completed);
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
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

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "BadRequestError"
        );
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("update", () => {
      const patchData = {
        first_name: "Bud",
        last_name: null,
      };

      beforeEach(() => {
        const claim = new Claim({ application_id: applicationId });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });
      });

      it("updates claim and redirects to nextPage when successful", async () => {
        mockRouter.pathname = routes.applications.ssn;

        renderHook();

        await act(async () => {
          await claimsLogic.create();
        });

        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        const claim = claimsLogic.claims.getItem(applicationId);

        expect(claim).toBeInstanceOf(Claim);
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
        renderHook();

        await act(async () => {
          await claimsLogic.create();

          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });

      describe("when request is unsuccessful", () => {
        beforeEach(() => {
          jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
        });

        it("updates the local claim and warningsList if response only included warnings", async () => {
          mockRouter.pathname = routes.applications.name;
          const claimResponse = new MockClaimBuilder()
            .id(applicationId)
            .create();
          const last_name = "Updated from API";

          renderHook();

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

          const claim = claimsLogic.claims.getItem(applicationId);

          expect(claim.last_name).toBe(last_name);
          expect(claimsLogic.warningsLists[applicationId]).toEqual([
            { field: "first_name", type: "required" },
          ]);
        });

        it("does not update the local claim if response included any errors", async () => {
          mockRouter.pathname = routes.applications.name;
          const claimResponse = new MockClaimBuilder()
            .id(applicationId)
            .create();
          const last_name = "Name in API";

          renderHook();

          await act(async () => {
            await claimsLogic.create();
          });

          updateClaimMock.mockResolvedValueOnce({
            claim: { ...claimResponse, last_name },
            errors: [{ rule: "disallow_foo" }],
            warnings: [],
            // Responses with errors receive a 400 status
            success: false,
          });

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          const claim = claimsLogic.claims.getItem(applicationId);

          expect(claim.last_name).toBeNull();
        });

        it("reports warnings for fields on the Name page", async () => {
          mockRouter.pathname = routes.applications.name;

          renderHook();

          await act(async () => {
            await claimsLogic.create();
          });

          updateClaimMock.mockResolvedValueOnce({
            claim: new MockClaimBuilder().id(applicationId).create(),
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

          const errors = appErrorsLogic.appErrors.items;
          const errorFields = errors.map((error) => error.field);

          expect(errors).toHaveLength(2);
          expect(errorFields).toContain("first_name");
          expect(errorFields).toContain("last_name");
        });

        it("reports warnings for applicable rules on the Intermittent Leave page", async () => {
          mockRouter.pathname = routes.applications.leavePeriodIntermittent;
          renderHook();

          await act(async () => {
            await claimsLogic.create();
          });

          updateClaimMock.mockResolvedValueOnce({
            claim: new MockClaimBuilder().id(applicationId).create(),
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

          const errors = appErrorsLogic.appErrors.items;

          expect(errors).toHaveLength(1);
          expect(errors[0].rule).toBe("disallow_hybrid_intermittent_leave");
        });

        it("catches exceptions thrown from the API module", async () => {
          mockRouter.pathname = routes.applications.name;
          renderHook();

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

          expect(appErrorsLogic.appErrors.items[0].name).toEqual(
            "BadRequestError"
          );
          expect(mockRouter.push).not.toHaveBeenCalled();
        });
      });
    });

    describe("submit", () => {
      beforeEach(async () => {
        mockRouter.pathname = routes.applications.review;
        renderHook(routes.applications);

        const claim = new Claim({ application_id: applicationId });
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

        const claim = claimsLogic.claims.getItem(applicationId);

        expect(submitClaimMock).toHaveBeenCalledWith(applicationId);
        expect(claim.status).toBe(ClaimStatus.submitted);
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
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

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "BadRequestError"
        );
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("submitPaymentPreference", () => {
      const paymentData = {
        payment_preference: new MockClaimBuilder().directDeposit().create()
          .payment_preference,
      };

      beforeEach(async () => {
        mockRouter.pathname = routes.applications.paymentMethod;
        renderHook(routes.applications);

        const claim = new Claim({ application_id: applicationId });
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

        const claim = claimsLogic.claims.getItem(applicationId);

        expect(submitPaymentPreferenceMock).toHaveBeenCalledWith(
          applicationId,
          paymentData
        );
        expect(claim.has_submitted_payment_preference).toBe(true);
      });

      it("clears prior errors", async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await claimsLogic.submitPaymentPreference(applicationId);
        });

        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
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

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          "BadRequestError"
        );
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });
});
