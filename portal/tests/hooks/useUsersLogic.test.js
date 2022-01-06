import * as MFAService from "../../src/services/mfa";
import User, { RoleDescription, UserRole } from "../../src/models/User";
import { act, renderHook } from "@testing-library/react-hooks";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { NetworkError } from "../../src/errors";
import UsersApi from "../../src/api/UsersApi";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";
import useUsersLogic from "../../src/hooks/useUsersLogic";

jest.mock("../../src/api/UsersApi");
jest.mock("../../src/services/mfa", () => ({
  setMFAPreference: jest.fn(),
  updateMFAPhoneNumber: jest.fn(),
}));
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

  function setup() {
    renderHook(() => {
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
    isLoggedIn = true;
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
  });

  describe("updateUser", () => {
    const user_id = "mock-user-id";
    const patchData = { path: "data" };

    beforeEach(() => {
      setup();
    });

    it("updates user to the api", async () => {
      await act(async () => {
        await usersLogic.updateUser(user_id, patchData);
      });

      expect(usersApi.updateUser).toHaveBeenCalledWith(user_id, patchData);
    });

    it("sets user state", async () => {
      await act(async () => {
        await usersLogic.updateUser(user_id, patchData);
      });

      expect(usersLogic.user).toBeInstanceOf(User);
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

    describe("when mfa_delivery_preference is updated", () => {
      const patchData = { mfa_delivery_preference: "SMS" };
      it("sets MFA preferences and updates user", async () => {
        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });

        expect(MFAService.setMFAPreference).toHaveBeenCalledWith("SMS");
        expect(usersApi.updateUser).toHaveBeenCalledWith(user_id, patchData);
      });

      it("does not update user if MFA service fails to update", async () => {
        MFAService.setMFAPreference.mockImplementation(() =>
          Promise.reject(new Error())
        );
        usersApi.updateUser.mockClear();
        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });

        expect(usersApi.updateUser).not.toHaveBeenCalled();
      });
    });

    describe("when mfa_phone_number is updated", () => {
      const patchData = {
        mfa_phone_number: {
          int_code: "1",
          phone_type: "Cell",
          phone_number: "555-555-5555",
        },
      };

      it("sets MFA phone number and updates user", async () => {
        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });

        expect(MFAService.updateMFAPhoneNumber).toHaveBeenCalledWith(
          "555-555-5555"
        );
        expect(usersApi.updateUser).toHaveBeenCalledWith(user_id, patchData);
      });

      it("does not update user if MFA service fails to update", async () => {
        MFAService.updateMFAPhoneNumber.mockImplementation(() =>
          Promise.reject(new Error())
        );
        usersApi.updateUser.mockClear();
        await act(async () => {
          await usersLogic.updateUser(user_id, patchData);
        });

        expect(usersApi.updateUser).not.toHaveBeenCalled();
      });
    });
  });

  describe("loadUser", () => {
    beforeEach(() => {
      setup();
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
      setup();
      await expect(usersLogic.loadUser).rejects.toThrow(/Cannot load user/);
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
        setup();

        expect(usersLogic.requireUserConsentToDataAgreement).toThrow(
          /User not loaded/
        );
      });
    });

    describe("when user consented to data sharing", () => {
      beforeEach(async () => {
        setup();
        await preloadUser(new User({ consented_to_data_sharing: true }));
      });

      it("doesn't redirect to the consent page", () => {
        usersLogic.requireUserConsentToDataAgreement();

        expect(goToSpy).not.toHaveBeenCalled();
      });
    });

    describe("when user didn't consent to data sharing", () => {
      it("redirects to consent page if user isn't already there", async () => {
        setup();
        await preloadUser(new User({ consented_to_data_sharing: false }));

        usersLogic.requireUserConsentToDataAgreement();

        expect(goToSpy).toHaveBeenCalledWith("/user/consent-to-data-sharing");
      });

      it("doesn't redirect if route is already set to consent page", async () => {
        mockRouter.pathname = "/user/consent-to-data-sharing";

        setup();
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
        setup();

        usersLogic.requireUserRole();

        expect(goToSpy).not.toHaveBeenCalled();
      });
    });

    describe("when user has roles", () => {
      it("redirects to Employers welcome if user has Employer role", async () => {
        mockRouter.pathname = routes.applications.index;

        setup();
        await preloadUser(
          new User({ roles: employerRole, consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith(
          "/employers/welcome",
          {},
          { redirect: true }
        );
      });

      it("does not redirect if user has Employer role and currently in Employer Portal", async () => {
        mockRouter.pathname = routes.employers.welcome;

        setup();
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

        setup();
        await preloadUser(
          new User({ roles: multipleRoles, consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith(
          "/employers/welcome",
          {},
          { redirect: true }
        );
      });

      it("redirects to Claims index if user does not have a role", async () => {
        mockRouter.pathname = routes.employers.welcome;

        setup();
        await preloadUser(
          new User({ roles: [], consented_to_data_sharing: true })
        );

        usersLogic.requireUserRole();

        expect(goToSpy).toHaveBeenCalledWith(
          "/applications",
          {},
          { redirect: true }
        );
      });
    });
  });

  describe("convertUser", () => {
    const user_id = "mock-user-id";
    const postData = { employer_fein: "12-3456789" };

    beforeEach(async () => {
      setup();

      await act(async () => {
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