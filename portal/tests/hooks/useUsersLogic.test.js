import { NetworkError, UserNotFoundError } from "../../src/errors";
import User, { RoleDescription, UserRole } from "../../src/models/User";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import Claim from "../../src/models/Claim";
import UsersApi from "../../src/api/UsersApi";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";
import useUsersLogic from "../../src/hooks/useUsersLogic";

jest.mock("../../src/api/UsersApi");
jest.mock("next/router");

describe("useUsersLogic", () => {
  let appErrorsLogic, errorSpy, isLoggedIn, portalFlow, usersApi, usersLogic;

  async function preloadUser(user) {
    usersApi.getCurrentUser.mockResolvedValueOnce({
      success: true,
      user,
    });
    await usersLogic.loadUser();
  }

  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic();
      usersLogic = useUsersLogic({ appErrorsLogic, isLoggedIn, portalFlow });
    });
  }

  beforeEach(() => {
    // The mock of UsersApi returns an object with references to a singleton
    // of getCurrentUser and updateUser so this will reference the same
    // jest.fn mocks that are used in the hook.
    usersApi = new UsersApi();
    isLoggedIn = true;
    errorSpy = jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    renderHook();
  });

  describe("updateUser", () => {
    const user_id = "mock-user-id";
    const patchData = { path: "data" };

    beforeEach(async () => {
      await act(async () => {
        await usersLogic.updateUser(user_id, patchData);
      });
    });

    it("updates user to the api", () => {
      expect(usersApi.updateUser).toHaveBeenCalledWith(user_id, patchData);
    });

    it("sets user state", () => {
      expect(usersLogic.user).toBeInstanceOf(User);
    });

    it("goes to next page", () => {
      expect(mockRouter.push).toHaveBeenCalled();
    });

    describe("when errors exist", () => {
      beforeEach(async () => {
        act(() => {
          appErrorsLogic.setAppErrors(
            new AppErrorInfoCollection([new AppErrorInfo()])
          );
        });

        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });
      });

      it("clears errors", () => {
        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });

    describe("when a claim is passed", () => {
      const claim = new Claim({ application_id: "mock-claim-id" });

      it("adds claim to context and a claim_id parameter", async () => {
        const nextPageSpy = jest.spyOn(portalFlow, "goToNextPage");

        await act(async () => {
          await usersLogic.updateUser(user_id, patchData, claim);
        });

        expect(nextPageSpy).toHaveBeenCalledWith(
          { user: usersLogic.user, claim },
          expect.objectContaining({ claim_id: claim.application_id })
        );
      });
    });

    describe("when api errors", () => {
      it("catches error", async () => {
        usersApi.updateUser.mockImplementationOnce(() => {
          throw new NetworkError();
        });

        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          NetworkError.name
        );
      });
    });
  });

  describe("loadUser", () => {
    it("fetches current user from api", async () => {
      await act(async () => {
        await usersLogic.loadUser();
      });
      expect(usersApi.getCurrentUser).toHaveBeenCalled();
    });

    it("sets the current user", async () => {
      await act(async () => {
        await usersLogic.loadUser();
      });
      expect(usersLogic.user).toBeInstanceOf(User);
    });

    it("only makes api request if user has not been loaded", async () => {
      await act(async () => {
        await usersLogic.loadUser();
        await usersLogic.loadUser();
      });

      expect(usersLogic.user).toBeInstanceOf(User);
      expect(usersApi.getCurrentUser).toHaveBeenCalledTimes(1);
    });

    it("throws an error if user is not logged in to Cognito", async () => {
      isLoggedIn = false;
      renderHook();
      await expect(usersLogic.loadUser).rejects.toThrow(/Cannot load user/);
    });

    describe("when api does not return success", () => {
      beforeEach(async () => {
        usersApi.getCurrentUser.mockResolvedValueOnce({ success: false });
        await act(async () => {
          await usersLogic.loadUser();
        });
      });

      it("logs UserNotReceivedError and UserNotFoundError", () => {
        expect(errorSpy).toHaveBeenCalledTimes(2);
      });

      it("sets UserNotFoundError error", () => {
        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          UserNotFoundError.name
        );
      });
    });

    describe("when api throws error", () => {
      it("sets UserNotFoundError", async () => {
        usersApi.getCurrentUser.mockResolvedValueOnce(new NetworkError());

        await act(async () => {
          await usersLogic.loadUser();
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          UserNotFoundError.name
        );
      });
    });
  });

  describe("requireUserConsentToDataAgreement", () => {
    describe("when user is not loaded", () => {
      it("throws error if user not loaded", () => {
        expect(usersLogic.requireUserConsentToDataAgreement).toThrow(
          /User not loaded/
        );
      });
    });

    describe("when user consented to data sharing", () => {
      beforeEach(async () => {
        await preloadUser(new User({ consented_to_data_sharing: true }));
      });

      it("doesn't redirect to the consent page", () => {
        usersLogic.requireUserConsentToDataAgreement();
        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("when user didn't consent to data sharing", () => {
      beforeEach(async () => {
        await preloadUser(new User({ consented_to_data_sharing: false }));
      });

      it("redirects to consent page if user isn't already there", () => {
        usersLogic.requireUserConsentToDataAgreement();
        expect(mockRouter.push).toHaveBeenCalledWith(
          "/user/consent-to-data-sharing"
        );
      });

      it("doesn't redirect if route is already set to consent page", () => {
        mockRouter.pathname = "/user/consent-to-data-sharing";
        usersLogic.requireUserConsentToDataAgreement();

        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });

  describe("requireUserRole", () => {
    const employerRole = [
      new UserRole({
        role_id: 1,
        role_description: RoleDescription.employer,
      }),
    ];

    it("redirects to Employers dashboard if user has Employer role", async () => {
      await preloadUser(
        new User({ roles: employerRole, consented_to_data_sharing: true })
      );
      mockRouter.pathname = routes.claims.dashboard;
      usersLogic.requireUserRole();
      expect(mockRouter.push).toHaveBeenCalledWith("/employers");
    });

    it("does not redirect if user has Employer role and currently in Employer Portal", async () => {
      await preloadUser(
        new User({ roles: employerRole, consented_to_data_sharing: true })
      );
      mockRouter.pathname = routes.employers.dashboard;
      usersLogic.requireUserRole();

      expect(mockRouter.push).not.toHaveBeenCalled();
    });

    it("redirects to Employers dashboard if user has multiple roles, including Employer", async () => {
      const userRole = [
        new UserRole({
          role_id: 2,
          role_description: "Random user role",
        }),
      ];
      const multipleRoles = employerRole.concat(userRole);
      await preloadUser(
        new User({ roles: multipleRoles, consented_to_data_sharing: true })
      );
      mockRouter.pathname = routes.claims.dashboard;
      usersLogic.requireUserRole();

      expect(mockRouter.push).toHaveBeenCalledWith("/employers");
    });

    it("redirects to Claims dashboard if user does not have a role", async () => {
      await preloadUser(
        new User({ roles: [], consented_to_data_sharing: true })
      );
      mockRouter.pathname = routes.employers.dashboard;
      usersLogic.requireUserRole();

      expect(mockRouter.push).toHaveBeenCalledWith("/dashboard");
    });
  });
});
