import { NetworkError, UserNotFoundError } from "../../src/errors";
import Claim from "../../src/models/Claim";
import User from "../../src/models/User";
import UsersApi from "../../src/api/UsersApi";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";
import useUsersLogic from "../../src/hooks/useUsersLogic";

jest.mock("../../src/api/UsersApi");
jest.mock("next/router");

describe("useUsersLogic", () => {
  let appErrorsLogic, errorSpy, portalFlow, usersApi, usersLogic;

  beforeEach(() => {
    // The mock of UsersApi returns an object with references to a singleton
    // of getCurrentUser and updateUser so this will reference the same
    // jest.fn mocks that are used in the hook.
    usersApi = new UsersApi();
    errorSpy = jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    testHook(() => {
      portalFlow = usePortalFlow();
      appErrorsLogic = useAppErrorsLogic();
      usersLogic = useUsersLogic({ appErrorsLogic, portalFlow });
    });
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

        expect(appErrorsLogic.appErrors.items[0].type).toEqual(
          NetworkError.name
        );
      });
    });
  });

  describe("loadUser", () => {
    beforeEach(async () => {
      await act(async () => {
        await usersLogic.loadUser();
      });
    });

    it("fetches current user from api", () => {
      expect(usersApi.getCurrentUser).toHaveBeenCalled();
    });

    it("sets the current user", () => {
      expect(usersLogic.user).toBeInstanceOf(User);
    });

    describe("when api does not return sucess", () => {
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
        expect(appErrorsLogic.appErrors.items[0].type).toEqual(
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

        expect(appErrorsLogic.appErrors.items[0].type).toEqual(
          UserNotFoundError.name
        );
      });
    });
  });
});
