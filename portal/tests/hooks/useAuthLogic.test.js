import { act, renderHook } from "@testing-library/react-hooks";
import { Auth } from "@aws-amplify/auth";
import UsersApi from "../../src/api/UsersApi";
import routes from "../../src/routes";
import tracker from "../../src/services/tracker";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useAuthLogic from "../../src/hooks/useAuthLogic";
import usePortalFlow from "../../src/hooks/usePortalFlow";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/api/UsersApi");
jest.mock("../../src/services/tracker");

function mockPortalFlow() {
  return {
    goTo: jest.fn(),
    goToPageFor: jest.fn(),
    pathname: "",
  };
}

describe("useAuthLogic", () => {
  let appErrors,
    appErrorsLogic,
    ein,
    password,
    portalFlow,
    render,
    setAppErrors,
    username,
    verificationCode;

  beforeEach(() => {
    username = "test@email.com";
    password = "TestP@ssw0rd!";
    ein = "12-3456789";
    verificationCode = "123456";

    render = (customPortalFlow) => {
      return renderHook(() => {
        portalFlow = customPortalFlow || usePortalFlow();
        appErrorsLogic = useAppErrorsLogic({ portalFlow });
        ({ appErrors, setAppErrors } = appErrorsLogic);
        return useAuthLogic({
          appErrorsLogic,
          portalFlow,
        });
      });
    };
  });

  it("can call out to Auth.forgotPassword", async () => {
    const { result } = render();
    await act(async () => {
      await result.current.forgotPassword(username);
    });
    expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
  });

  it("forgotPassword routes to next page when successful", async () => {
    const portalFlow = mockPortalFlow();
    const { result } = render(portalFlow);

    await act(async () => {
      await result.current.forgotPassword(username);
    });

    expect(portalFlow.goToPageFor).toHaveBeenCalledWith("SEND_CODE");
  });

  it("For forgotPassword, does not change page when Cognito request fails", async () => {
    const portalFlow = mockPortalFlow();
    const { result } = renderHook(() => {
      appErrorsLogic = useAppErrorsLogic({ portalFlow });
      return useAuthLogic({
        appErrorsLogic,
        portalFlow,
      });
    });
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
      await result.current.forgotPassword(username);
    });

    expect(portalFlow.goToPageFor).not.toHaveBeenCalled();
  });

  it("stores username in authData for Reset Password page", async () => {
    const { result } = render();

    await act(async () => {
      await result.current.forgotPassword(username);
    });

    expect(result.current.authData.resetPasswordUsername).toBe(username);
  });

  it("For resendForgotPasswordCode, calls forgotPassword with whitespace trimmed from username", async () => {
    const { result } = render();

    await act(async () => {
      await result.current.resendForgotPasswordCode(`  ${username} `);
    });
    expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
  });

  it("For resendForgotPasswordCode, tracks request", async () => {
    const { result } = render();

    await act(async () => {
      await result.current.resendForgotPasswordCode(username);
    });

    expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
  });

  it("For resendForgotPasswordCode, requires all fields to not be empty and tracks the errors", () => {
    username = "";
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
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

  it("For resendForgotPasswordCode, sets app errors when an account isn't found", () => {
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      // Ignore lint rule since AWS Auth class actually throws an object literal
      // eslint-disable-next-line no-throw-literal
      throw {
        code: "UserNotFoundException",
        message: "An account with the given email does not exist.",
        name: "UserNotFoundException",
      };
    });
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(1);
    expect(appErrors.items[0].message).toMatchInlineSnapshot(
      `"Incorrect email"`
    );
  });

  it("For resendForgotPasswordCode, sets app errors when Auth.forgotPassword throws InvalidParameterException", () => {
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
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(1);
    expect(appErrors.items[0].message).toMatchInlineSnapshot(
      `"Enter all required information"`
    );
  });

  it("For resendForgotPasswordCode, sets app errors when Auth.forgotPassword throws NotAuthorizedException due to security reasons", () => {
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      // Ignore lint rule since AWS Auth class actually throws an object literal
      // eslint-disable-next-line no-throw-literal
      throw {
        code: "NotAuthorizedException",
        message: "Request not allowed due to security reasons.",
        name: "NotAuthorizedException",
      };
    });
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(1);
    expect(appErrors.items[0].message).toMatchInlineSnapshot(
      `"Your authentication attempt has been blocked due to suspicious activity. We sent you an email to confirm your identity. Check your email and then follow the instructions to try again. If this continues to occur, call the contact center at (833) 344‑7365."`
    );
  });

  it("For resendForgotPasswordCode, sets app errors when Auth.forgotPassword throws LimitExceededException due to too many forget password requests", () => {
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      // Ignore lint rule since AWS Auth class actually throws an object literal
      // eslint-disable-next-line no-throw-literal
      throw {
        code: "LimitExceededException",
        message: "Attempt limit exceeded, please try after some time.",
        name: "LimitExceededException",
      };
    });
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(1);
    expect(appErrors.items[0].message).toMatchInlineSnapshot(
      `"Your account is temporarily locked because of too many forget password requests. Wait 15 minutes before trying again."`
    );
  });

  it("For resendForgotPasswordCode, sets system error message when Auth.forgotPassword throws unanticipated error", () => {
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      throw new Error("Some unknown error");
    });
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(1);
    expect(appErrors.items[0].message).toMatchInlineSnapshot(
      `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
    );
  });

  it("For resendForgotPasswordCode, tracks Cognito request errors", async () => {
    const error = new Error("Some unknown error");
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      throw error;
    });
    const { result } = render();

    await act(async () => {
      await result.current.resendForgotPasswordCode(username);
    });

    expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
      errorCode: undefined,
      errorMessage: error.message,
      errorName: error.name,
    });
  });

  it("For resendForgotPasswordCode,clears existing errors", async () => {
    const { result } = render();
    await act(async () => {
      appErrors = [{ message: "Pre-existing error" }];
      await result.current.resendForgotPasswordCode(username);
    });
    expect(appErrors.items).toHaveLength(0);
  });

  describe("login", () => {
    it("calls Auth.signIn", async () => {
      const { result } = render();
      await act(async () => {
        await result.current.login(username, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("tracks request", async () => {
      const { result } = render();
      await act(async () => {
        await result.current.login(username, password);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("sets isLoggedIn to true", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
      });
      expect(result.current.isLoggedIn).toBe(true);
    });

    it("trims whitespace from username", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.login(`  ${username} `, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("requires fields to not be empty and tracks the errors", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.login();
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
      const { result } = render();

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
        await result.current.login(username, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email or password"`
      );
    });

    it("sets app errors when Auth.signIn throws NotAuthorizedException due to too many failed login attempts", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Password attempts exceeded",
          name: "NotAuthorizedException",
        };
      });
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
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
      const { result, waitFor } = render();

      await act(async () => {
        await result.current.login(username, password);
      });
      await waitFor(() => {
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365"`
        );
      });
    });

    it("tracks Cognito request errors", async () => {
      const error = new Error("Some unknown error");
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        throw error;
      });
      const { result } = render();

      await act(async () => {
        await result.current.login(username, password);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", async () => {
      const { result, waitFor } = render();

      await act(async () => {
        appErrors = [{ message: "Pre-existing error" }];
        await result.current.login(username, password);
      });
      await waitFor(() => {
        expect(appErrors.items).toHaveLength(0);
      });
    });

    it("redirects to the specific page while passing next param", async () => {
      const next = "/applications";
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);

      await act(async () => {
        await result.current.login(username, password, next);
      });
      expect(portalFlow.goTo).toHaveBeenCalledWith(next);
    });

    it("calls goToPageFor func while no next param", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);

      await act(async () => {
        await result.current.login(username, password);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith("LOG_IN");
    });

    it("redirects to verify account page while receiving UserNotConfirmedException error", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotConfirmedException",
          message: "User is not confirmed.",
          name: "UserNotConfirmedException",
        };
      });
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.login(username, password);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith(
        "UNCONFIRMED_ACCOUNT"
      );
    });

    it("sets app errors when Auth.signIn throws PasswordResetRequiredException", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw { code: "PasswordResetRequiredException" };
      });
      const { result, waitFor } = render();
      await act(async () => {
        await result.current.login(username, password);
      });
      await waitFor(() => {
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toMatchInlineSnapshot(
          `"Your password must be reset before you can log in again. Click the \\"Forgot your password?\\" link below to reset your password."`
        );
      });
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
      const { result } = render();

      await act(async () => {
        await result.current.logout();
      });

      expect(window.location.assign).toHaveBeenCalledWith(routes.auth.login);
    });

    it("when called with no params, calls Auth.signOut and redirects to home", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.logout();
      });
      expect(Auth.signOut).toHaveBeenCalledTimes(1);
      expect(Auth.signOut).toHaveBeenCalledWith({ global: true });
      expect(window.location.assign).toHaveBeenCalledWith(routes.auth.login);
    });

    it("with sessionTimedOut param, redirects to login page with session timed out query parameter", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.logout({
          sessionTimedOut: true,
        });
      });
      expect(window.location.assign).toHaveBeenCalledWith(
        `${routes.auth.login}?session-timed-out=true`
      );
    });

    it("tracks request", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.logout();
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });
  });

  describe("createAccount", () => {
    it("sends request through API module", async () => {
      const usersApi = new UsersApi();
      const { result } = render();

      await act(async () => {
        // Add whitespace to username to also cover trimming
        await result.current.createAccount(username + " ", password);
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
      const { result } = render();

      await act(async () => {
        await result.current.createAccount(username, password);
      });

      expect(result.current.authData).toEqual({
        createAccountUsername: username,
        createAccountFlow: "claimant",
      });
    });

    it("routes to Verify Account page when request succeeds", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);

      await act(async () => {
        await result.current.createAccount(username, password);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith("CREATE_ACCOUNT");
    });
  });

  describe("createEmployerAccount", () => {
    it("sends request through API module", async () => {
      const usersApi = new UsersApi();
      const { result } = render();

      await act(async () => {
        // Add whitespace to username to also cover trimming
        await result.current.createEmployerAccount(
          username + " ",
          password,
          ein
        );
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
      const { result } = render();

      await act(async () => {
        await result.current.createEmployerAccount(username, password, ein);
      });

      expect(result.current.authData).toEqual({
        createAccountUsername: username,
        createAccountFlow: "employer",
      });
    });

    it("routes to Verify Account page when request succeeds", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.createEmployerAccount(username, password, ein);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith("CREATE_ACCOUNT");
    });
  });

  describe("requireLogin", () => {
    it("doesn't redirect to the login page when user is loggedin", async () => {
      const portalFlow = mockPortalFlow();
      Auth.currentUserInfo.mockResolvedValue({
        attributes: {
          email: username,
        },
      });
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.requireLogin();
      });
      expect(portalFlow.goTo).not.toHaveBeenCalled();
    });

    it("sets isLoggedIn", async () => {
      const { result } = render();
      Auth.currentUserInfo.mockResolvedValue({
        attributes: {
          email: username,
        },
      });

      await act(async () => {
        await result.current.requireLogin();
      });
      expect(result.current.isLoggedIn).toBe(true);
    });

    it("does check auth status if auth status is already set", async () => {
      Auth.currentUserInfo.mockResolvedValue({
        attributes: {
          email: username,
        },
      });
      const { result } = render();
      await act(async () => {
        await result.current.requireLogin();
        await result.current.requireLogin();
      });

      expect(result.current.isLoggedIn).toBe(true);
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
      const { result } = render();

      await act(async () => {
        try {
          await result.current.requireLogin();
        } catch {
          await result.current.requireLogin();
        }
      });

      expect(result.current.isLoggedIn).toBe(true);
      expect(Auth.currentUserInfo).toHaveBeenCalledTimes(2);
    });

    it("when user is not logged in, redirects to login page", async () => {
      Auth.currentUserInfo.mockResolvedValueOnce(null);
      const portalFlow = mockPortalFlow();
      portalFlow.pathWithParams = "";
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.requireLogin();
      });
      expect(portalFlow.goTo).toHaveBeenCalledWith(routes.auth.login, {
        next: "",
      });
    });

    it("doesn't redirect if route is already set to login page", async () => {
      Auth.currentUserInfo.mockResolvedValueOnce(null);
      const portalFlow = mockPortalFlow();
      portalFlow.pathname = routes.auth.login;
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.requireLogin();
      });
      expect(portalFlow.goTo).not.toHaveBeenCalled();
    });

    it("redirects to login page with nextUrl", async () => {
      Auth.currentUserInfo.mockResolvedValueOnce(null);

      const portalFlow = mockPortalFlow();
      portalFlow.pathWithParams = routes.applications.checklist;
      const { result } = render(portalFlow);

      await act(async () => {
        await result.current.requireLogin();
      });

      expect(portalFlow.goTo).toHaveBeenCalledWith(routes.auth.login, {
        next: routes.applications.checklist,
      });
    });
  });

  describe("resendVerifyAccountCode", () => {
    it("calls Auth.resendSignUp", () => {
      const { result } = render();
      act(() => {
        result.current.resendVerifyAccountCode(username);
      });
      expect(Auth.resendSignUp).toHaveBeenCalledWith(username);
    });

    it("tracks request", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.resendVerifyAccountCode(username);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      const { result } = render();

      act(() => {
        result.current.resendVerifyAccountCode(username);
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
      const { result } = render();

      act(() => {
        result.current.resendVerifyAccountCode(username);
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
      const { result } = render();

      await act(async () => {
        await result.current.resendVerifyAccountCode(username);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      const { result } = render();

      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        result.current.resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("resetPassword", () => {
    it("calls Auth.forgotPasswordSubmit", () => {
      const { result } = render();
      act(() => {
        result.current.resetPassword(username, verificationCode, password);
      });

      expect(Auth.forgotPasswordSubmit).toHaveBeenCalledWith(
        username,
        verificationCode,
        password
      );
    });

    it("tracks request", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.resetPassword(
          username,
          verificationCode,
          password
        );
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("routes to login page", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);

      await act(async () => {
        await result.current.resetPassword(
          username,
          verificationCode,
          password
        );
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith("SET_NEW_PASSWORD");
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      const { result } = render();
      act(() => {
        result.current.resetPassword();
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      act(() => {
        result.current.resetPassword(username, verificationCode, password);
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
      const { result } = render();

      await act(async () => {
        await result.current.resetPassword(
          username,
          verificationCode,
          password
        );
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      const { result } = render();

      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        result.current.resetPassword(username, verificationCode, password);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("verifyAccount", () => {
    it("calls Auth.confirmSignUp", () => {
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, verificationCode);
      });
      expect(Auth.confirmSignUp).toHaveBeenCalledWith(
        username,
        verificationCode
      );
    });

    it("tracks request", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyAccount(username, verificationCode);
      });

      expect(tracker.trackFetchRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("trims whitespace from code", () => {
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, `  ${verificationCode} `);
      });
      expect(Auth.confirmSignUp).toHaveBeenCalledWith(
        username,
        verificationCode
      );
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      verificationCode = "";
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, verificationCode);
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
        const { result } = render();

        act(() => {
          result.current.verifyAccount(username, code);
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
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, verificationCode);
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
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, your verification code has expired or has already been used."`
      );
    });

    it("redirects to the login page when account is already verified", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);

      jest.spyOn(Auth, "confirmSignUp").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "User cannot be confirmed. Current status is CONFIRMED",
          name: "NotAuthorizedException",
        };
      });

      await act(async () => {
        await result.current.verifyAccount(username, verificationCode);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith(
        "AuthError",
        expect.any(Object)
      );
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith(
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
        const { result } = render();
        act(() => {
          result.current.verifyAccount(username, verificationCode);
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
      const { result } = render();

      act(() => {
        result.current.verifyAccount(username, verificationCode);
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
      const { result } = render();

      await act(async () => {
        await result.current.verifyAccount(username, verificationCode);
      });

      expect(tracker.trackEvent).toHaveBeenCalledWith("AuthError", {
        errorCode: undefined,
        errorMessage: error.message,
        errorName: error.name,
      });
    });

    it("clears existing errors", () => {
      const { result } = render();

      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        result.current.verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(0);
    });

    it("routes to login page with account verified message", async () => {
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.verifyAccount(username, verificationCode);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith(
        "SUBMIT",
        {},
        {
          "account-verified": true,
        }
      );
    });
  });
});
