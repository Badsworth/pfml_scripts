import {
  createClaimMock,
  getClaimsMock,
  submitClaimMock,
  updateClaimMock,
} from "../../src/api/ClaimsApi";
import Claim from "../../src/models/Claim";
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
jest.mock("../../src/hooks/useAppErrorsLogic");

// TODO add tests for api returning errors and warnings
describe("useClaimsLogic", () => {
  const applicationId = "mock-application-id";
  const user = new User({ user_id: "mock-user-id" });
  let appErrorsLogic, claimsLogic, portalFlow;

  beforeEach(() => {
    testHook(() => {
      appErrorsLogic = useAppErrorsLogic();
      portalFlow = usePortalFlow({ user });
      claimsLogic = useClaimsLogic({ appErrorsLogic, user, portalFlow });
    });
  });

  afterEach(() => {
    appErrorsLogic = null;
    claimsLogic = null;
    portalFlow = null;
  });

  it("returns claims with null value", () => {
    expect(claimsLogic.claims).toBeNull();
  });

  describe("loadClaims", () => {
    it("asynchronously fetches all claims and adds to claims collection", async () => {
      await act(async () => {
        await claimsLogic.loadClaims();
      });

      const claims = claimsLogic.claims;

      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalled();
    });

    it("only makes api request if claims have not been loaded", async () => {
      await act(async () => {
        await claimsLogic.loadClaims();
      });

      await claimsLogic.loadClaims();
      const claims = claimsLogic.claims;
      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });

    describe("when request errors", () => {
      it("catches the error", async () => {
        getClaimsMock.mockImplementationOnce(() => {
          throw new Error();
        });

        await act(async () => {
          await claimsLogic.loadClaims();
        });

        expect(appErrorsLogic.catchError).toHaveBeenCalled();
      });
    });
  });

  describe("createClaim", () => {
    it("sends API request", async () => {
      await act(async () => {
        await claimsLogic.createClaim();
      });

      expect(createClaimMock).toHaveBeenCalled();
    });

    describe("when the request succeeds", () => {
      let claim;

      beforeEach(() => {
        claim = new Claim({ application_id: "12345" });

        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });
      });

      it("stores the new claim", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(claimsLogic.claims.items).toContain(claim);
      });

      it("routes to claim checklist page", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.claims.checklist}?claim_id=${claim.application_id}`
          )
        );
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(() => {
        createClaimMock.mockResolvedValueOnce({
          claim: null,
          success: false,
        });
      });

      it("doesn't change the route", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(mockRouter.push).not.toHaveBeenCalled();
      });

      it("doesn't store a claim", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(claimsLogic.claims).toBeNull();
      });
    });

    describe("when the request throws an error", () => {
      beforeEach(() => {
        createClaimMock.mockRejectedValueOnce(new Error());
      });

      it("catches the error", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(appErrorsLogic.catchError).toHaveBeenCalled();
      });

      it("doesn't change the route", async () => {
        await act(async () => {
          await claimsLogic.createClaim();
        });

        expect(mockRouter.push).not.toHaveBeenCalled();
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

    describe("updateClaim", () => {
      it("updates claim with formState and redirects to nextPage", async () => {
        const patchData = {
          first_name: "Bud",
        };

        await act(async () => {
          await claimsLogic.updateClaim(applicationId, patchData);
        });

        const claim = claimsLogic.claims.get(applicationId);

        expect(claim).toBeInstanceOf(Claim);
        expect(claim).toEqual(expect.objectContaining(patchData));
        expect(updateClaimMock).toHaveBeenCalled();
        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(`?claim_id=${claim.application_id}`)
        );
      });

      describe("when request errors", () => {
        it("catches the error", async () => {
          updateClaimMock.mockImplementationOnce(() => {
            throw new Error();
          });

          const patchData = {
            first_name: "Bud",
          };

          await act(async () => {
            await claimsLogic.updateClaim(applicationId, patchData);
          });

          expect(appErrorsLogic.catchError).toHaveBeenCalled();
        });
      });
    });

    describe("submitClaim", () => {
      it("submits claim with formState and redirects to success page", async () => {
        const formState = {
          application_id: applicationId,
          first_name: "Bud",
        };

        await act(async () => {
          await claimsLogic.submitClaim(formState);
        });

        const claim = claimsLogic.claims.get(applicationId);

        expect(claim).toEqual(expect.objectContaining(formState));
        expect(submitClaimMock).toHaveBeenCalled();
        expect(mockRouter.push).toHaveBeenCalled();
      });

      describe("when request errors", () => {
        it("catches the error", async () => {
          submitClaimMock.mockImplementationOnce(() => {
            throw new Error();
          });

          const formState = {
            application_id: applicationId,
            first_name: "Bud",
          };

          await act(async () => {
            await claimsLogic.submitClaim(formState);
          });

          expect(appErrorsLogic.catchError).toHaveBeenCalled();
          expect(mockRouter.push).not.toHaveBeenCalled();
        });
      });
    });
  });
});
