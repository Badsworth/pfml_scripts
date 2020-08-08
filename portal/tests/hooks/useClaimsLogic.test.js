import {
  createClaimMock,
  getClaimsMock,
  submitClaimMock,
  updateClaimMock,
} from "../../src/api/ClaimsApi";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
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

// TODO add tests for api returning errors and warnings
describe("useClaimsLogic", () => {
  const applicationId = "mock-application-id";
  const user = new User({ user_id: "mock-user-id" });
  let appErrorsLogic, claimsLogic, portalFlow;

  beforeEach(() => {
    // remove error logs
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
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

    it("only makes one api request at a time", async () => {
      await act(async () => {
        // call loadClaims twice in parallel
        await Promise.all([claimsLogic.load(), claimsLogic.load()]);
      });

      const claims = claimsLogic.claims.items;
      expect(claims[0]).toBeInstanceOf(Claim);
      expect(getClaimsMock).toHaveBeenCalledTimes(1);
    });

    describe("when request errors", () => {
      it("catches the error", async () => {
        getClaimsMock.mockImplementationOnce(() => {
          describe("forceReload parameter", () => {
            it("forces a reload even after claims have been loaded", async () => {
              await act(async () => {
                await claimsLogic.load();
                await claimsLogic.load(true);
              });

              expect(getClaimsMock).toHaveBeenCalledTimes(2);
            });
          });

          throw new Error();
        });

        await act(async () => {
          await claimsLogic.load();
        });

        expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
      });
    });
  });

  describe("createClaim", () => {
    it("sends API request", async () => {
      await act(async () => {
        await claimsLogic.create();
      });

      expect(createClaimMock).toHaveBeenCalled();
    });

    describe("when the request succeeds", () => {
      let claim;

      beforeEach(async () => {
        claim = new Claim({ application_id: "12345" });

        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        // This mock is needed for the workaround of calling loadClaims
        // after creating a claim in createClaims
        // TODO: Remove this once the workaround is removed: https://lwd.atlassian.net/browse/CP-701
        getClaimsMock.mockResolvedValueOnce({
          claims: new ClaimCollection([
            new Claim({ application_id: "mock-application-id-1" }),
            new Claim({ application_id: "mock-application-id-2" }),
            claim,
          ]),
          success: true,
        });

        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await claimsLogic.create();
        });
      });

      it("clears errors", () => {
        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });

      it("stores the new claim", () => {
        expect(claimsLogic.claims.items).toContain(claim);
      });

      it("routes to claim checklist page", () => {
        expect(mockRouter.push).toHaveBeenCalledWith(
          expect.stringContaining(
            `${routes.claims.checklist}?claim_id=${claim.application_id}`
          )
        );
      });
    });

    describe("when the request is unsuccessful", () => {
      beforeEach(async () => {
        createClaimMock.mockResolvedValueOnce({
          claim: null,
          success: false,
        });

        await act(async () => {
          await claimsLogic.create();
        });
      });

      it("doesn't change the route", () => {
        expect(mockRouter.push).not.toHaveBeenCalled();
      });

      it("doesn't store a claim", () => {
        expect(claimsLogic.claims).toBeNull();
      });
    });

    describe("when the request throws an error", () => {
      beforeEach(async () => {
        createClaimMock.mockRejectedValueOnce(new Error());
        await act(async () => {
          await claimsLogic.create();
        });
      });

      it("catches the error", () => {
        expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
      });

      it("doesn't change the route", () => {
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("when claims have previously been loaded", () => {
      let claim;

      beforeEach(async () => {
        await act(async () => {
          await claimsLogic.load();
        });

        claim = new Claim({ application_id: "12345" });
        createClaimMock.mockResolvedValueOnce({
          claim,
          success: true,
        });

        // This mock is needed for the workaround of calling loadClaims
        // after creating a claim in createClaims
        // TODO: Remove this once the workaround is removed: https://lwd.atlassian.net/browse/CP-701
        getClaimsMock.mockResolvedValueOnce({
          claims: new ClaimCollection([
            new Claim({ application_id: "mock-application-id-1" }),
            new Claim({ application_id: "mock-application-id-2" }),
            claim,
          ]),
          success: true,
        });

        await act(async () => {
          await claimsLogic.create();
        });
      });

      it("stores the new claim", () => {
        expect(claimsLogic.claims.items).toContain(claim);
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

      describe("when request errors", () => {
        it("catches the error", async () => {
          updateClaimMock.mockImplementationOnce(() => {
            throw new Error();
          });

          const patchData = {
            first_name: "Bud",
          };

          await act(async () => {
            await claimsLogic.update(applicationId, patchData);
          });

          expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
        });
      });
    });

    describe("submitClaim", () => {
      it("asynchronously submits claim", async () => {
        await act(async () => {
          await claimsLogic.submit(applicationId);
        });

        expect(submitClaimMock).toHaveBeenCalledWith(applicationId);
      });

      describe("when request errors", () => {
        it("catches the error", async () => {
          submitClaimMock.mockImplementationOnce(() => {
            throw new Error();
          });

          await act(async () => {
            await claimsLogic.submit(applicationId);
          });

          expect(appErrorsLogic.appErrors.items[0].type).toEqual("Error");
          expect(mockRouter.push).not.toHaveBeenCalled();
        });
      });
    });
  });
});
