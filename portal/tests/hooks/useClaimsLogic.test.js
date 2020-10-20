import Claim, { ClaimStatus } from "../../src/models/Claim";
import { MockClaimBuilder, testHook } from "../test-utils";
import {
  completeClaimMock,
  createClaimMock,
  getClaimsMock,
  submitClaimMock,
  updateClaimMock,
} from "../../src/api/ClaimsApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { BadRequestError } from "../../src/errors";
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
  const applicationId = "mock-application-id";
  let appErrorsLogic, claimsLogic, portalFlow, user;

  function renderHook() {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
      portalFlow = usePortalFlow();
      claimsLogic = useClaimsLogic({ appErrorsLogic, user, portalFlow });
    });
  }

  beforeEach(() => {
    mockRouter.pathname = routes.home;
    user = new User({ user_id: "mock-user-id" });
  });

  afterEach(() => {
    appErrorsLogic = null;
    claimsLogic = null;
    portalFlow = null;
  });

  it("returns claims with null value", () => {
    renderHook();

    expect(claimsLogic.claims).toBeNull();
  });

  describe("load", () => {
    beforeEach(() => {
      renderHook();
    });

    it("asynchronously fetches all claims and adds to claims collection", async () => {
      await act(async () => {
        await claimsLogic.load();
      });

      expect(claimsLogic.claims.items[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalled();
    });

    it("only makes api request if claims have not been loaded", async () => {
      await act(async () => {
        await claimsLogic.load();
        await claimsLogic.load();
      });

      const claims = claimsLogic.claims.items;
      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });

    it("clears prior errors", async () => {
      act(() => {
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
      });

      await act(async () => {
        await claimsLogic.load();
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
        await expect(claimsLogic.load).rejects.toThrow(/Cannot load claims/);
      });

      it("catches exceptions thrown from the API module", async () => {
        getClaimsMock.mockImplementationOnce(() => {
          throw new BadRequestError();
        });

        await act(async () => {
          await claimsLogic.load();
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
      mockRouter.pathname = routes.claims.start;
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
        expect.stringContaining(`${routes.claims.checklist}?claim_id=mock`)
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

    describe("when claims have not been previously loaded", () => {
      let claim;

      beforeEach(async () => {
        claim = new Claim({ application_id: "12345" });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        getClaimsMock.mockImplementationOnce(() => {
          return {
            success: true,
            claims: new ClaimCollection([claim]),
          };
        });

        await act(async () => {
          await claimsLogic.create();
        });
      });

      it("calls claimsApi.getClaims", () => {
        expect(getClaimsMock).toHaveBeenCalledTimes(1);
      });

      it("updates claimsLogic.claims with the new claim", () => {
        expect(claimsLogic.claims.items).toContain(claim);
      });
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
          await claimsLogic.load();
          getClaimsMock.mockClear(); // to clear the getClaimsMock calls
          await claimsLogic.create();
        });
      });

      it("should not call claimsApi.getClaims", () => {
        expect(getClaimsMock).not.toHaveBeenCalled();
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
      beforeEach(() => {
        mockRouter.pathname = routes.claims.review;
        renderHook();

        act(() => {
          claimsLogic.setClaims(
            new ClaimCollection([new Claim({ application_id: applicationId })])
          );
        });
      });

      it("completes the claim", async () => {
        await act(async () => {
          await claimsLogic.complete(applicationId);
        });

        const claim = claimsLogic.claims.get(applicationId);

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
            `${routes.claims.success}?claim_id=${applicationId}`
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

      it("updates claim and redirects to nextPage when successful", async () => {
        mockRouter.pathname = routes.claims.name;

        renderHook();

        act(() => {
          claimsLogic.setClaims(
            new ClaimCollection([new Claim({ application_id: applicationId })])
          );
        });

        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        const claim = claimsLogic.claims.get(applicationId);

        expect(claim).toBeInstanceOf(Claim);
        expect(claim).toEqual(expect.objectContaining(patchData));
        expect(updateClaimMock).toHaveBeenCalled();
        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.claims.address}?claim_id=${claim.application_id}`
          )
        );
      });

      it("clears prior errors", async () => {
        mockRouter.pathname = routes.claims.name;
        renderHook();

        act(() => {
          claimsLogic.setClaims(
            new ClaimCollection([new Claim({ application_id: applicationId })])
          );

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

        it("updates the local claim if response only included warnings", async () => {
          mockRouter.pathname = routes.claims.name;
          const claimResponse = new MockClaimBuilder()
            .id(applicationId)
            .create();
          const last_name = "Updated from API";

          renderHook();

          act(() => {
            claimsLogic.setClaims(
              new ClaimCollection([
                new Claim({ application_id: applicationId }),
              ])
            );
          });

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

          const claim = claimsLogic.claims.get(applicationId);

          expect(claim.last_name).toBe(last_name);
        });

        it("does not update the local claim if response included any errors", async () => {
          mockRouter.pathname = routes.claims.name;
          const claimResponse = new MockClaimBuilder()
            .id(applicationId)
            .create();
          const last_name = "Name in API";

          renderHook();

          act(() => {
            claimsLogic.setClaims(
              new ClaimCollection([
                new Claim({ application_id: applicationId }),
              ])
            );
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

          const claim = claimsLogic.claims.get(applicationId);

          expect(claim.last_name).toBeNull();
        });

        it("reports warnings for fields on the Name page", async () => {
          mockRouter.pathname = routes.claims.name;

          renderHook();

          act(() => {
            claimsLogic.setClaims(
              new ClaimCollection([
                new Claim({ application_id: applicationId }),
              ])
            );
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
          mockRouter.pathname = routes.claims.leavePeriodIntermittent;
          renderHook();

          act(() => {
            claimsLogic.setClaims(
              new ClaimCollection([
                new Claim({ application_id: applicationId }),
              ])
            );
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
          mockRouter.pathname = routes.claims.name;
          renderHook();

          act(() => {
            claimsLogic.setClaims(
              new ClaimCollection([
                new Claim({ application_id: applicationId }),
              ])
            );
          });

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
      beforeEach(() => {
        mockRouter.pathname = routes.claims.review;
        renderHook(routes.claims);

        act(() => {
          claimsLogic.setClaims(
            new ClaimCollection([new Claim({ application_id: applicationId })])
          );
        });
      });

      it("submits the claim", async () => {
        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        const claim = claimsLogic.claims.get(applicationId);

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
            `${routes.claims.checklist}?claim_id=${applicationId}`
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
  });
});
