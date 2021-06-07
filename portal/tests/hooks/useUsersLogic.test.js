import { NetworkError, UnauthorizedError } from "../../src/errors";
import User, { RoleDescription, UserRole } from "../../src/models/User";

import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import BenefitsApplication from "../../src/models/BenefitsApplication";
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
  let appErrorsLogic, goToSpy, isLoggedIn, portalFlow, usersApi, usersLogic;

  async function preloadUser(user) {
    await act(async () => {
      usersApi.getCurrentUser.mockResolvedValueOnce({
        success: true,
        user,
      });
      await usersLogic.loadUser();
    });
  }

  function renderHook() {
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      usersLogic = useUsersLogic({ appErrorsLogic, isLoggedIn, portalFlow });

      goToSpy = jest.spyOn(portalFlow, "goTo");
    });
  }

  beforeEach(() => {
    // The mock of UsersApi returns an object with references to a singleton
    // of getCurrentUser and updateUser so this will reference the same
    // jest.fn mocks that are used in the hook.
    usersApi = new UsersApi();
    console.log("USERS API:", usersApi);
    isLoggedIn = true;
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
  });

  describe("updateUser", () => {
    const user_id = "mock-user-id";
    const patchData = { path: "data" };

    beforeEach(async () => {
      await act(async () => {
        renderHook();
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
      const claim = new BenefitsApplication({
        application_id: "mock-claim-id",
      });

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
    beforeEach(() => {
      renderHook();
    });

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

    it("doesn't clear errors if user has been loaded", async () => {
      await act(async () => {
        await usersLogic.loadUser();
        appErrorsLogic.setAppErrors(
          new AppErrorInfoCollection([new AppErrorInfo()])
        );
        await usersLogic.loadUser();
      });

      expect(usersApi.getCurrentUser).toHaveBeenCalledTimes(1);
      expect(appErrorsLogic.appErrors.items).toHaveLength(1);
    });

    it("throws an error if user is not logged in to Cognito", async () => {
      isLoggedIn = false;
      renderHook();
      await expect(usersLogic.loadUser).rejects.toThrow(/Cannot load user/);
    });

    it("redirects to reset password page when api responds with a 401 UnauthorizedError", async () => {
      const goToSpy = jest.spyOn(portalFlow, "goTo");
      usersApi.getCurrentUser.mockRejectedValueOnce(new UnauthorizedError());

      await act(async () => {
        await usersLogic.loadUser();
      });

      expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      expect(goToSpy).toHaveBeenCalledWith("/reset-password", {
        "user-not-found": true,
      });
    });

    it("throws UserNotReceivedError when api resolves with no user", async () => {
      usersApi.getCurrentUser.mockResolvedValueOnce({ user: null });

      await act(async () => {
        await usersLogic.loadUser();
      });

      expect(appErrorsLogic.appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, we were unable to retrieve your account. Please log out and try again. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
      );
    });

    it("throws NetworkError when fetch request fails", async () => {
      usersApi.getCurrentUser.mockRejectedValueOnce(new NetworkError());

      await act(async () => {
        await usersLogic.loadUser();
      });

      expect(appErrorsLogic.appErrors.items[0].name).toBe("NetworkError");
    });
  });

  describe("requireUserConsentToDataAgreement", () => {
    describe("when user is not loaded", () => {
      it("throws error if user not loaded", () => {
        renderHook();

        expect(usersLogic.requireUserConsentToDataAgreement).toThrow(
          /User not loaded/
        );
      });
    });

    describe("when user consented to data sharing", () => {
      beforeEach(async () => {
        renderHook();
        await preloadUser(new User({ consented_to_data_sharing: true }));
      });

      it("doesn't redirect to the consent page", () => {
        usersLogic.requireUserConsentToDataAgreement();

        expect(goToSpy).not.toHaveBeenCalled();
      });
    });

    describe("when user didn't consent to data sharing", () => {
      it("redirects to consent page if user isn't already there", async () => {
        renderHook();
        await preloadUser(new User({ consented_to_data_sharing: false }));

        usersLogic.requireUserConsentToDataAgreement();

        expect(goToSpy).toHaveBeenCalledWith("/user/consent-to-data-sharing");
      });

      it("doesn't redirect if route is already set to consent page", async () => {
        mockRouter.pathname = "/user/consent-to-data-sharing";

        renderHook();
        await preloadUser(new User({ consented_to_data_sharing: false }));

        usersLogic.requireUserConsentToDataAgreement();

        expect(goToSpy).not.toHaveBeenCalled();
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

    describe("when user is currently on Consent to Data Sharing page", () => {
      it("does not redirect to another page", () => {
        mockRouter.pathname = "/user/consent-to-data-sharing";
        renderHook();

        usersLogic.requireUserRole();

        expect(goToSpy).not.toHaveBeenCalled();
      });
    });

    describe("when user has roles", () => {
      it("redirects to Employers welcome if user has Employer role", async () => {
        mockRouter.pathname = routes.applications.index;

        renderHook();
        await preloadUser(
          new User({ roles: employerRole, consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith("/employers/welcome");
      });

      it("does not redirect if user has Employer role and currently in Employer Portal", async () => {
        mockRouter.pathname = routes.employers.welcome;

        renderHook();
        await preloadUser(
          new User({ roles: employerRole, consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).not.toHaveBeenCalled();
      });

      it("redirects to Employers welcome if user has multiple roles, including Employer", async () => {
        mockRouter.pathname = routes.applications.index;

        const userRole = [
          new UserRole({
            role_id: 2,
            role_description: "Random user role",
          }),
        ];
        const multipleRoles = employerRole.concat(userRole);

        renderHook();
        await preloadUser(
          new User({ roles: multipleRoles, consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith("/employers/welcome");
      });

      it("redirects to Claims index if user does not have a role", async () => {
        mockRouter.pathname = routes.employers.welcome;

        renderHook();
        await preloadUser(
          new User({ roles: [], consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith("/applications");
      });
    });
  });

  describe("convertUser", () => {
    const user_id = "mock-user-id";
    const postData = { employer_fein: "12-3456789" };

    beforeEach(async () => {
      await act(async () => {
        renderHook();
        await usersLogic.convertUser(user_id, postData);
      });
    });

    it("converts user role in the api", () => {
      expect(usersApi.convertUser).toHaveBeenCalledWith(user_id, postData);
    });

    it("receives user as employer", () => {
      expect(usersLogic.user).toBeInstanceOf(User);
      expect(usersLogic.user.roles.length).toBeGreaterThan(0);
      expect(usersLogic.user.user_leave_administrators.length).toBeGreaterThan(
        0
      );
      expect(usersLogic.user.roles[0].role_description).toBe(
        RoleDescription.employer
      );
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
          await usersLogic.convertUser(user_id, postData);
        });
      });

      it("clears errors", () => {
        expect(appErrorsLogic.appErrors.items).toHaveLength(0);
      });
    });

    describe("when api errors", () => {
      it("catches error", async () => {
        usersApi.convertUser.mockImplementationOnce(() => {
          throw new NetworkError();
        });

        await act(async () => {
          await usersLogic.convertUser(user_id, postData);
        });

        expect(appErrorsLogic.appErrors.items[0].name).toEqual(
          NetworkError.name
        );
      });
    });
  });
});
