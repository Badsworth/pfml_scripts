import Claim, { ClaimStatus } from "../../src/models/Claim";
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
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useClaimsLogic from "../../src/hooks/useClaimsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("../../src/api/ClaimsApi");

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
    user = new User({ user_id: "mock-user-id" });
    renderHook();
  });

  afterEach(() => {
    appErrorsLogic = null;
    claimsLogic = null;
    portalFlow = null;
  });

  it("returns claims with null value", () => {
    expect(claimsLogic.claims).toBeNull();
  });

  describe("load", () => {
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
    it("sends API request", async () => {
      await act(async () => {
        await claimsLogic.create();
      });

      expect(createClaimMock).toHaveBeenCalled();
    });

    it("routes to claim checklist page when the request succeeds", async () => {
      mockRouter.pathname = routes.claims.start;

      act(() => {
        appErrorsLogic.setAppErrors(new AppErrorInfoCollection([]));
      });

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
    beforeEach(() => {
      testHook(() => {
        appErrorsLogic = useAppErrorsLogic();
        portalFlow = usePortalFlow({ user });
        claimsLogic = useClaimsLogic({ user, appErrorsLogic, portalFlow });
      });

      act(() => {
        claimsLogic.setClaims(
          new ClaimCollection([new Claim({ application_id: applicationId })])
        );
      });
    });

    describe("complete", () => {
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
        mockRouter.pathname = routes.claims.review;

        act(() => {
          appErrorsLogic.setAppErrors(new AppErrorInfoCollection([]));
        });

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
        await act(async () => {
          await claimsLogic.update(applicationId, patchData);
        });

        const claim = claimsLogic.claims.get(applicationId);

        expect(claim).toBeInstanceOf(Claim);
        expect(claim).toEqual(expect.objectContaining(patchData));
        expect(updateClaimMock).toHaveBeenCalled();
        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(`?claim_id=${claim.application_id}`)
        );
      });

      it("clears prior errors", async () => {
        act(() => {
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

        it("reports all relevant warnings in the response", async () => {
          updateClaimMock.mockResolvedValueOnce({
            errors: [],
            warnings: [
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

          expect(errors).toHaveLength(1);
          expect(errors[0].field).toEqual("last_name");
        });

        it("catches exceptions thrown from the API module", async () => {
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
        mockRouter.pathname = routes.claims.review;

        act(() => {
          appErrorsLogic.setAppErrors(new AppErrorInfoCollection([]));
        });

        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.claims.checklist}?claim_id=${applicationId}`
          )
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
