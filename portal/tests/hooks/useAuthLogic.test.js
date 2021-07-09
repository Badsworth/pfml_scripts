import { Auth } from "@aws-amplify/auth";
import UsersApi from "../../src/api/UsersApi";
import { act } from "react-dom/test-utils";
import routes from "../../src/routes";
import { testHook } from "../test-utils";
import tracker from "../../src/services/tracker";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useAuthLogic from "../../src/hooks/useAuthLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/api/UsersApi");
jest.mock("../../src/services/tracker");

describe("useAuthLogic", () => {
  let appErrors,
    authData,
    createAccount,
    createEmployerAccount,
    ein,
    forgotPassword,
    isLoggedIn,
    login,
    logout,
    password,
    portalFlow,
    requireLogin,
    resendForgotPasswordCode,
    resendVerifyAccountCode,
    resetPassword,
    setAppErrors,
    username,
    verificationCode,
    verifyAccount;

  beforeEach(() => {
    username = "test@email.com";
    password = "TestP@ssw0rd!";
    ein = "12-3456789";
    verificationCode = "123456";
    testHook(() => {
      portalFlow = usePortalFlow();
      const appErrorsLogic = useAppErrorsLogic({ portalFlow });
      ({ appErrors, setAppErrors } = appErrorsLogic);
      ({
        authData,
        forgotPassword,
        login,
        logout,
        isLoggedIn,
        createAccount,
        createEmployerAccount,
        requireLogin,
        resendVerifyAccountCode,
        resendForgotPasswordCode,
        resetPassword,
        verifyAccount,
      } = useAuthLogic({
        appErrorsLogic,
        portalFlow,
      }));
    });
  });

  describe("forgotPassword", () => {
    it("calls Auth.forgotPassword", async () => {
      await act(async () => {
        await forgotPassword(username);
      });
      expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
    });

    it("routes to next page when successful", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");

      await act(async () => {
        await forgotPassword(username);
      });

      expect(spy).toHaveBeenCalledWith("SEND_CODE");
    });

    it("does not change page when Cognito request fails", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");

      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotFoundException",
          message: "An account with the given email does not exist.",
          name: "UserNotFoundException",
        };
      });

      await act(async () => {
        await forgotPassword(username);
      });

      expect(spy).not.toHaveBeenCalled();
    });

    it("stores username in authData for Reset Password page", async () => {
      await act(async () => {
        await forgotPassword(username);
      });

      expect(authData.resetPasswordUsername).toBe(username);
    });
  });

  describe("resendForgotPasswordCode", () => {
    it("calls forgotPassword with whitespace trimmed from username", async () => {
      await act(async () => {
        await resendForgotPasswordCode(`  ${username} `);
      });
      expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
    });

    it("tracks request", async () => {
      await act(async () => {
        await resendForgotPasswordCode(username);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueType: "required",
      });

      expect(Auth.forgotPassword).not.toHaveBeenCalled();
    });

    it("sets app errors when an account isn't found", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotFoundException",
          message: "An account with the given email does not exist.",
          name: "UserNotFoundException",
        };
      });
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email"`
      );
    });

    it("sets app errors when Auth.forgotPassword throws InvalidParameterException", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "InvalidParameterException",
          message:
            "1 validation error detected: Value at 'email' failed to satisfy constraint",
          name: "InvalidParameterException",
        };
      });
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter all required information"`
      );
    });

    it("sets app errors when Auth.forgotPassword throws NotAuthorizedException due to security reasons", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Request not allowed due to security reasons.",
          name: "NotAuthorizedException",
        };
      });
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the contact center at (833) 344‑7365."`
      );
    });

    it("sets app errors when Auth.forgotPassword throws LimitExceededException due to too many forget password requests", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "LimitExceededException",
          message: "Attempt limit exceeded, please try after some time.",
          name: "LimitExceededException",
        };
      });
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your account is temporarily locked because of too many forget password requests. Wait 15 minutes before trying again."`
      );
    });

    it("sets system error message when Auth.forgotPassword throws unanticipated error", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
      );
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
        throw error;
      });

      await act(async () => {
        await resendForgotPasswordCode(username);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", async () => {
      await act(async () => {
        setAppErrors([{ message: "Pre-existing error" }]);
        await resendForgotPasswordCode(username);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("login", () => {
    it("calls Auth.signIn", async () => {
      await act(async () => {
        await login(username, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("tracks request", async () => {
      await act(async () => {
        await login(username, password);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });

    it("sets isLoggedIn to true", async () => {
      await act(async () => {
        await login(username, password);
      });
      expect(isLoggedIn).toBe(true);
    });

    it("trims whitespace from username", async () => {
      await act(async () => {
        await login(`  ${username} `, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("requires fields to not be empty and tracks the errors", async () => {
      await act(async () => {
        await login();
      });

      expect(appErrors.items).toHaveLength(2);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter your email address",
          "Enter your password",
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "password",
        issueType: "required",
      });

      expect(Auth.signIn).not.toHaveBeenCalled();
    });

    it("sets app errors when username and password are incorrect", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Incorrect username or password",
          name: "NotAuthorizedException",
        };
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email or password"`
      );
    });

    it("sets app errors when Auth.signIn throws InvalidParameterException", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "InvalidParameterException",
          message:
            "Custom auth lambda trigger is not configured for the user pool",
          name: "InvalidParameterException",
        };
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter all required information"`
      );
    });

    it("sets app errors when Auth.signIn throws NotAuthorizedException due to security reasons", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Unable to login because of security reasons.",
          name: "NotAuthorizedException",
        };
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your log in attempt was blocked due to suspicious activity. You will need to reset your password to continue. We’ve also sent you an email to confirm your identity."`
      );
    });

    it("sets app errors when Auth.signIn throws NotAuthorizedException due to incorrect username or password", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Incorrect username or password.",
          name: "NotAuthorizedException",
        };
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email or password"`
      );
    });

    it("sets app errors when Auth.signIn throws NotAuthorizedException due to too many failed login attempts", () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Password attempts exceeded",
          name: "NotAuthorizedException",
        };
      });
      act(() => {
        login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your account is temporarily locked because of too many failed login attempts. Wait 15 minutes before trying again."`
      );
    });

    it("sets app errors and tracks event when Auth.signIn throws NotAuthorizedException with unexpected message", async () => {
      const cognitoError = {
        code: "NotAuthorizedException",
        message:
          "This message wasn't expected by Portal code and is the error from Cognito.",
        name: "NotAuthorizedException",
      };

      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw cognitoError;
      });
      await act(async () => {
        await login(username, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"This message wasn't expected by Portal code and is the error from Cognito."`
      );
      expect(tracker.trackEvent).toHaveBeenLastCalledWith(
        "AuthError",
        expect.objectContaining({ errorMessage: cognitoError.message })
      );
    });

    it("sets app errors when Auth.signIn throws AuthError", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // AWS Auth uses an AuthError class that is private, so we
        // are faking our own version of it for testing purposes
        class AuthError extends Error {
          constructor(...params) {
            super(...params);
            this.name = "AuthError";
          }
        }
        throw new AuthError("Username cannot be empty");
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter all required information"`
      );
    });

    it("sets system error message when Auth.signIn throws unanticipated error", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        throw new Error("Some unknown error");
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
      );
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        throw error;
      });

      await act(async () => {
        await login(username, password);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", async () => {
      await act(async () => {
        setAppErrors([{ message: "Pre-existing error" }]);
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(0);
    });

    it("redirects to the specific page while passing next param", async () => {
      const next = "/applications";
      const spy = jest.spyOn(portalFlow, "goTo");
      await act(async () => {
        await login(username, password, next);
      });
      expect(spy).toHaveBeenCalledWith(next);
      spy.mockRestore();
    });

    it("calls goToPageFor func while no next param", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      await act(async () => {
        await login(username, password);
      });
      expect(spy).toHaveBeenCalledWith("LOG_IN");
      spy.mockRestore();
    });

    it("redirects to verify account page while receiving UserNotConfirmedException error", () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotConfirmedException",
          message: "User is not confirmed.",
          name: "UserNotConfirmedException",
        };
      });
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      act(() => {
        login(username, password);
      });
      expect(spy).toHaveBeenCalledWith("UNCONFIRMED_ACCOUNT");
      spy.mockRestore();
    });

    it("sets app errors when Auth.signIn throws PasswordResetRequiredException", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw { code: "PasswordResetRequiredException" };
      });
      await act(async () => {
        await login(username, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your password must be reset before you can log in again. Click the \\"Forgot your password?\\" link below to reset your password."`
      );
    });
  });

  describe("logout", () => {
    let assign;

    beforeEach(() => {
      assign = jest.fn();
      // Mock window.location.assign since browser navigation isn't available in unit tests
      jest.spyOn(window, "location", "get").mockImplementation(() => {
        return { assign };
      });
    });

    afterEach(() => {
      // To access the window.location getter function itself rather than the return value of the getter function
      // we need to use Object.getOwnPropertyDescriptor.
      // See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getOwnPropertyDescriptor
      Object.getOwnPropertyDescriptor(window, "location").get.mockRestore();
    });

    it("redirects to login while receiving PasswordResetRequiredException error", async () => {
      jest.spyOn(Auth, "signOut").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "PasswordResetRequiredException",
          message: "User is not confirmed.",
          name: "PasswordResetRequiredException",
        };
      });

      await act(async () => {
        await logout();
      });

      expect(window.location.assign).toHaveBeenCalledWith(routes.auth.login);
    });

    describe("when called with no parameters", () => {
      beforeEach(async () => {
        await act(async () => {
          await logout();
        });
      });

      it("calls Auth.signOut", () => {
        expect(Auth.signOut).toHaveBeenCalledTimes(1);
        expect(Auth.signOut).toHaveBeenCalledWith({ global: true });
      });

      it("redirects to home page", () => {
        expect(window.location.assign).toHaveBeenCalledWith(routes.auth.login);
      });
    });

    describe("when called with sessionTimedOut parameter", () => {
      beforeEach(async () => {
        await act(async () => {
          await logout({
            sessionTimedOut: true,
          });
        });
      });

      it("redirects to login page with session timed out query parameter", () => {
        expect(window.location.assign).toHaveBeenCalledWith(
          `${routes.auth.login}?session-timed-out=true`
        );
      });
    });

    it("tracks request", async () => {
      await act(async () => {
        await logout();
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });
  });

  describe("createAccount", () => {
    it("sends request through API module", async () => {
      const usersApi = new UsersApi();

      await act(async () => {
        // Add whitespace to username to also cover trimming
        await createAccount(username + " ", password);
      });

      expect(usersApi.createUser).toHaveBeenCalledWith({
        email_address: username,
        password,
        role: {
          role_description: "Claimant",
        },
      });
    });

    it("sets authData for reference on Verify Account page", async () => {
      await act(async () => {
        await createAccount(username, password);
      });

      expect(authData).toEqual({
        createAccountUsername: username,
        createAccountFlow: "claimant",
      });
    });

    it("routes to Verify Account page when request succeeds", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      await act(async () => {
        await createAccount(username, password);
      });

      expect(spy).toHaveBeenCalledWith("CREATE_ACCOUNT");
    });
  });

  describe("createEmployerAccount", () => {
    it("sends request through API module", async () => {
      const usersApi = new UsersApi();

      await act(async () => {
        // Add whitespace to username to also cover trimming
        await createEmployerAccount(username + " ", password, ein);
      });

      expect(usersApi.createUser).toHaveBeenCalledWith({
        email_address: username,
        password,
        role: {
          role_description: "Employer",
        },
        user_leave_administrator: {
          employer_fein: ein,
        },
      });
    });

    it("sets authData for reference on Verify Account page", async () => {
      await act(async () => {
        await createEmployerAccount(username, password, ein);
      });

      expect(authData).toEqual({
        createAccountUsername: username,
        createAccountFlow: "employer",
      });
    });

    it("routes to Verify Account page when request succeeds", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      await act(async () => {
        await createEmployerAccount(username, password, ein);
      });

      expect(spy).toHaveBeenCalledWith("CREATE_ACCOUNT");
    });
  });

  describe("requireLogin", () => {
    describe("when user is logged in", () => {
      beforeEach(() => {
        Auth.currentUserInfo.mockResolvedValue({
          attributes: {
            email: username,
          },
        });
      });

      it("doesn't redirect to the login page", async () => {
        const spy = jest.spyOn(portalFlow, "goTo");
        await act(async () => {
          await requireLogin();
        });
        expect(spy).not.toHaveBeenCalled();
        spy.mockRestore();
      });

      it("sets isLoggedIn", async () => {
        await act(async () => {
          await requireLogin();
        });
        expect(isLoggedIn).toBe(true);
      });

      it("does check auth status if auth status is already set", async () => {
        await act(async () => {
          await requireLogin();
          await requireLogin();
        });

        expect(isLoggedIn).toBe(true);
        expect(Auth.currentUserInfo).toHaveBeenCalledTimes(1);
      });

      it("can recover and try again if Auth.currentUserInfo throws an error", async () => {
        Auth.currentUserInfo
          .mockReset()
          .mockImplementationOnce(() => {
            throw new Error();
          })
          .mockResolvedValueOnce({
            attributes: {
              email: username,
            },
          });
        await act(async () => {
          try {
            await requireLogin();
          } catch {
            await requireLogin();
          }
        });

        expect(isLoggedIn).toBe(true);
        expect(Auth.currentUserInfo).toHaveBeenCalledTimes(2);
      });
    });

    describe("when user is not logged in", () => {
      let spy;
      beforeEach(() => {
        spy = jest.spyOn(portalFlow, "goTo");
        Auth.currentUserInfo.mockResolvedValueOnce(null);
      });

      afterEach(() => {
        spy.mockRestore();
      });

      it("redirects to login page", async () => {
        await act(async () => {
          await requireLogin();
        });
        expect(spy).toHaveBeenCalledWith(routes.auth.login, { next: "" });
      });

      it("doesn't redirect if route is already set to login page", async () => {
        portalFlow.pathname = routes.auth.login;
        await act(async () => {
          await requireLogin();
        });
        expect(spy).not.toHaveBeenCalled();
      });

      it("redirects to login page with nextUrl", async () => {
        portalFlow.pathWithParams = routes.applications.checklist;
        await act(async () => {
          await requireLogin();
        });
        expect(spy).toHaveBeenCalledWith(routes.auth.login, {
          next: routes.applications.checklist,
        });
      });
    });
  });

  describe("resendVerifyAccountCode", () => {
    it("calls Auth.resendSignUp", () => {
      act(() => {
        resendVerifyAccountCode(username);
      });
      expect(Auth.resendSignUp).toHaveBeenCalledWith(username);
    });

    it("tracks request", async () => {
      await act(async () => {
        await resendVerifyAccountCode(username);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      act(() => {
        resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueType: "required",
      });

      expect(Auth.resendSignUp).not.toHaveBeenCalled();
    });

    it("sets system error message when Auth.resendSignUp throws unanticipated error", () => {
      jest.spyOn(Auth, "resendSignUp").mockImplementationOnce(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
      );
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "resendSignUp").mockImplementationOnce(() => {
        throw error;
      });

      await act(async () => {
        await resendVerifyAccountCode(username);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("resetPassword", () => {
    it("calls Auth.forgotPasswordSubmit", () => {
      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(Auth.forgotPasswordSubmit).toHaveBeenCalledWith(
        username,
        verificationCode,
        password
      );
    });

    it("tracks request", async () => {
      await act(async () => {
        await resetPassword(username, verificationCode, password);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });

    it("routes to login page", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      await act(async () => {
        await resetPassword(username, verificationCode, password);
      });

      expect(spy).toHaveBeenCalledWith("SET_NEW_PASSWORD");
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      act(() => {
        resetPassword();
      });

      expect(appErrors.items).toHaveLength(3);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter the 6 digit code sent to your email",
          "Enter your email address",
          "Enter your password",
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "password",
        issueType: "required",
      });

      expect(Auth.forgotPasswordSubmit).not.toHaveBeenCalled();
    });

    it("sets app errors when CodeMismatchException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "CodeMismatchException",
          message: "Invalid verification code provided, please try again.",
          name: "CodeMismatchException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Invalid verification code. Make sure the code matches the code emailed to you."`
      );
    });

    it("sets app errors when ExpiredCodeException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "ExpiredCodeException",
          message: "Invalid code provided, please request a code again.",
          name: "ExpiredCodeException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, your verification code has expired or has already been used."`
      );
    });

    it("sets app errors when InvalidParameterException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "InvalidParameterException",
          message:
            "1 validation error detected: Value at 'password' failed to satisfy constraint: Member must have length greater than or equal to 6",
          name: "InvalidParameterException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Check the requirements and try again. Ensure all required information is entered and the password meets the requirements."`
      );
    });

    it("sets app errors when InvalidPasswordException is thrown due to non-conforming password", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "InvalidPasswordException",
          message: "InvalidPasswordException was thrown",
          name: "InvalidPasswordException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your password does not meet the requirements. Please check the requirements and try again."`
      );
    });

    it("sets app errors when InvalidPasswordException is thrown due to insecure password", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "InvalidPasswordException",
          message: "Provided password cannot be used for security reasons.",
          name: "InvalidPasswordException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Choose a different password. Avoid commonly used passwords and avoid using the same password on multiple websites."`
      );
    });

    it("sets app errors when UserNotConfirmedException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotConfirmedException",
          message: "UserNotConfirmedException was thrown",
          name: "UserNotConfirmedException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Confirm your account by following the instructions in the verification email sent to your inbox."`
      );
    });

    it("sets app errors when UserNotFoundException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotFoundException",
          message: "UserNotFoundException was thrown",
          name: "UserNotFoundException",
        };
      });

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email"`
      );
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementationOnce(() => {
        throw error;
      });

      await act(async () => {
        await resetPassword(username, verificationCode, password);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        resetPassword(username, verificationCode, password);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("verifyAccount", () => {
    it("calls Auth.confirmSignUp", () => {
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(Auth.confirmSignUp).toHaveBeenCalledWith(
        username,
        verificationCode
      );
    });

    it("tracks request", async () => {
      await act(async () => {
        await verifyAccount(username, verificationCode);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    });

    it("trims whitespace from code", () => {
      act(() => {
        verifyAccount(username, `  ${verificationCode} `);
      });
      expect(Auth.confirmSignUp).toHaveBeenCalledWith(
        username,
        verificationCode
      );
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      verificationCode = "";

      act(() => {
        verifyAccount(username, verificationCode);
      });

      expect(appErrors.items).toHaveLength(2);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter the 6 digit code sent to your email",
          "Enter your email address",
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueType: "required",
      });

      expect(Auth.confirmSignUp).not.toHaveBeenCalled();
    });

    it("validates verification code format and tracks when it's invalid", () => {
      const malformedCodes = [
        "12345", // too short,
        "1234567", // too long,
        "123A5", // has digits
        "123.4", // has punctuation
      ];
      expect.assertions(malformedCodes.length * 4);
      for (const code of malformedCodes) {
        act(() => {
          verifyAccount(username, code);
        });
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toEqual(
          "Enter the 6 digit code sent to your email and ensure it does not include any punctuation."
        );

        expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
          issueField: "code",
          issueType: "pattern",
        });

        expect(Auth.confirmSignUp).not.toHaveBeenCalled();
      }
    });

    it("sets app errors when verification code is incorrect", () => {
      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "CodeMismatchException",
          message: "Invalid verification code provided, please try again.",
          name: "CodeMismatchException",
        };
      });
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Invalid verification code. Make sure the code matches the code emailed to you."`
      );
    });

    it("sets app errors when verification code has expired", () => {
      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "ExpiredCodeException",
          message: "Invalid code provided, please request a code again.",
          name: "ExpiredCodeException",
        };
      });
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, your verification code has expired or has already been used."`
      );
    });

    it("redirects to the login page when account is already verified", () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "User cannot be confirmed. Current status is CONFIRMED",
          name: "NotAuthorizedException",
        };
      });

      act(() => {
        verifyAccount(username, verificationCode);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith(
        "AuthError",
        expect.any(Object)
      );
      expect(spy).toHaveBeenCalledWith(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    });

    it("sets app errors when Auth.confirmSignIn throws AuthError", () => {
      const authErrorMessages = [
        "Username cannot be empty",
        "Confirmation code cannot be empty",
      ];

      const cognitoErrors = authErrorMessages.map((message) => {
        return {
          code: "AuthError",
          message,
          name: "AuthError",
        };
      });

      expect.assertions(cognitoErrors.length * 2);

      for (const cognitoError of cognitoErrors) {
        jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
          // Ignore lint rule since AWS Auth class actually throws an object literal
          // eslint-disable-next-line no-throw-literal
          throw cognitoError;
        });
        act(() => {
          verifyAccount(username, verificationCode);
        });
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
        );
      }
    });

    it("sets system error message when Auth.confirmSignUp throws unanticipated error", () => {
      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
      );
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        throw error;
      });

      await act(async () => {
        await verifyAccount(username, verificationCode);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(0);
    });

    it("routes to login page with account verified message", async () => {
      const spy = jest.spyOn(portalFlow, "goToPageFor");
      await act(async () => {
        await verifyAccount(username, verificationCode);
      });

      expect(spy).toHaveBeenCalledWith(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    });
  });
});
