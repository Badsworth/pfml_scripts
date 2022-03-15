import { act, renderHook } from "@testing-library/react-hooks";
import { Auth } from "@aws-amplify/auth";
import UsersApi from "../../src/api/UsersApi";
import routes from "../../src/routes";
import tracker from "../../src/services/tracker";
import useAuthLogic from "../../src/hooks/useAuthLogic";
import useErrorsLogic from "../../src/hooks/useErrorsLogic";
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
  let ein,
    errors,
    errorsLogic,
    password,
    portalFlow,
    render,
    setErrors,
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
        errorsLogic = useErrorsLogic({ portalFlow });
        ({ errors, setErrors } = errorsLogic);
        return useAuthLogic({
          errorsLogic,
          portalFlow,
        });
      });
    };
  });

  it("isPhoneVerified returns verification status of Cognito user's phone", async () => {
    Auth.currentAuthenticatedUser.mockResolvedValueOnce({
      attributes: {
        phone_number_verified: true,
      },
    });
    const { result } = render();

    await act(async () => {
      const isVerified = await result.current.isPhoneVerified();
      expect(isVerified).toBe(true);
    });

    Auth.currentAuthenticatedUser.mockResolvedValueOnce({
      attributes: {
        phone_number_verified: false,
      },
    });
    await act(async () => {
      const isVerified = await result.current.isPhoneVerified();
      expect(isVerified).toBe(false);
    });
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
      errorsLogic = useErrorsLogic({ portalFlow });
      return useAuthLogic({
        errorsLogic,
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

    expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
    expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
  });

  it("For resendForgotPasswordCode, requires all fields to not be empty and tracks the errors", () => {
    username = "";
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toMatchInlineSnapshot(`
      [
        {
          "field": "username",
          "namespace": "auth",
          "type": "required",
        },
      ]
    `);

    expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
      issueField: "username",
      issueNamespace: "auth",
      issueRule: "",
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
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toMatchInlineSnapshot(`
      [
        {
          "namespace": "auth",
          "type": "userNotFound",
        },
      ]
    `);
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
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toMatchInlineSnapshot(`
      [
        {
          "namespace": "auth",
          "type": "invalidParametersFallback",
        },
      ]
    `);
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
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toMatchInlineSnapshot(`
      [
        {
          "namespace": "auth",
          "type": "attemptBlocked_forgotPassword",
        },
      ]
    `);
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
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toMatchInlineSnapshot(`
      [
        {
          "namespace": "auth",
          "type": "attemptsLimitExceeded_forgotPassword",
        },
      ]
    `);
  });

  it("For resendForgotPasswordCode, sets system error message when Auth.forgotPassword throws unanticipated error", () => {
    jest.spyOn(Auth, "forgotPassword").mockImplementationOnce(() => {
      throw new Error("Some unknown error");
    });
    const { result } = render();

    act(() => {
      result.current.resendForgotPasswordCode(username);
    });
    expect(errors).toHaveLength(1);
    expect(errors[0].issues).toHaveLength(0);
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
      errors = [{ message: "Pre-existing error" }];
      await result.current.resendForgotPasswordCode(username);
    });
    expect(errors).toHaveLength(0);
  });

  describe("login", () => {
    beforeAll(() => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
        const cognitoUser = {};
        return cognitoUser;
      });
    });

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

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "username",
            "namespace": "auth",
            "type": "required",
          },
          {
            "field": "password",
            "namespace": "auth",
            "type": "required",
          },
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueNamespace: "auth",
        issueRule: "",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "password",
        issueNamespace: "auth",
        issueRule: "",
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "incorrectEmailOrPassword",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "invalidParametersFallback",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "attemptBlocked_login",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "incorrectEmailOrPassword",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "attemptsLimitExceeded_login",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "message": "This message wasn't expected by Portal code and is the error from Cognito.",
            "namespace": "auth",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "invalidParametersFallback",
          },
        ]
      `);
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
        expect(errors).toHaveLength(1);
        expect(errors[0].issues).toHaveLength(0);
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
        errors = [{ message: "Pre-existing error" }];
        await result.current.login(username, password);
      });
      await waitFor(() => {
        expect(errors).toHaveLength(0);
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

    it("directs to the page to verify an MFA challenge even if the feature flag is not on", async () => {
      jest.spyOn(Auth, "signIn").mockImplementationOnce(() => {
        const cognitoUser = { challengeName: "SMS_MFA" };
        return cognitoUser;
      });
      const portalFlow = mockPortalFlow();
      const { result } = render(portalFlow);
      await act(async () => {
        await result.current.login(username, password);
      });
      expect(portalFlow.goToPageFor).toHaveBeenCalledWith(
        "VERIFY_CODE",
        {},
        { next: undefined }
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
        expect(errors).toHaveLength(1);
        expect(errors[0].issues).toMatchInlineSnapshot(`
          [
            {
              "field": "password",
              "namespace": "auth",
              "type": "resetRequiredException",
            },
          ]
        `);
      });
    });

    describe("with claimantShowMFA feature flag enabled", () => {
      const next = "/applications";
      const portalFlow = mockPortalFlow();

      beforeEach(() => {
        process.env.featureFlags = JSON.stringify({
          claimantShowMFA: true,
        });
      });

      describe("with no MFA challenge", () => {
        let usersApi;

        beforeAll(() => {
          // The mock of UsersApi returns an object with references to a singleton
          // of getCurrentUser and updateUser so this will reference the same
          // jest.fn mocks that are used in the hook.
          usersApi = new UsersApi();

          jest.spyOn(Auth, "signIn").mockImplementation(() => {
            const cognitoUser = {};
            return cognitoUser;
          });
        });

        it("sets isLoggedIn to true", async () => {
          const { result } = render();

          await act(async () => {
            await result.current.login(username, password);
          });

          expect(result.current.isLoggedIn).toBe(true);
        });

        it("redirects to the ENABLE_MFA page if user has not made an MFA selection", async () => {
          const { result } = render(portalFlow);

          usersApi.getCurrentUser.mockImplementationOnce(() => {
            const apiUser = {
              user: {
                mfa_delivery_preference: null,
              },
            };

            return apiUser;
          });

          await act(async () => {
            await result.current.login(username, password, next);
          });

          expect(portalFlow.goToPageFor).toHaveBeenCalledWith("ENABLE_MFA");
        });

        it("does not redirect to MFA setup if user is an Employer", async () => {
          const { result } = render(portalFlow);

          usersApi.getCurrentUser.mockImplementationOnce(() => {
            const apiUser = {
              user: {
                mfa_delivery_preference: null,
                hasEmployerRole: true,
              },
            };

            return apiUser;
          });

          await act(async () => {
            await result.current.login(username, password, next);
          });

          expect(portalFlow.goTo).toHaveBeenCalledWith(next);
        });

        it("redirects to the next page if user has made MFA selection", async () => {
          const { result } = render(portalFlow);

          usersApi.getCurrentUser.mockImplementationOnce(() => {
            const apiUser = {
              user: {
                mfa_delivery_preference: "SMS",
              },
            };

            return apiUser;
          });

          await act(async () => {
            await result.current.login(username, password, next);
          });

          expect(portalFlow.goTo).toHaveBeenCalledWith(next);
        });
      });

      describe("with an MFA challenge", () => {
        beforeAll(() => {
          jest.spyOn(Auth, "signIn").mockImplementation(() => {
            const cognitoUser = {
              challengeName: "SMS_MFA",
            };
            return cognitoUser;
          });
        });

        it("does not mark the user as logged in", async () => {
          const { result } = render();

          await act(async () => {
            await result.current.login(username, password);
          });

          expect(result.current.isLoggedIn).not.toBe(true);
        });

        it("redirects to the VERIFY_CODE page", async () => {
          const { result } = render(portalFlow);

          await act(async () => {
            await result.current.login(username, password, next);
          });

          expect(portalFlow.goToPageFor).toHaveBeenCalledWith(
            "VERIFY_CODE",
            {},
            { next: "/applications" }
          );
        });
      });
    });
  });

  describe("verifyMFACodeAndLogin", () => {
    const next = "/applications";

    it("validates the code was entered", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin("", next);
      });

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "mfa",
            "type": "required",
          },
        ]
      `);
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueNamespace: "mfa",
        issueRule: "",
        issueType: "required",
      });
    });

    it("validates the code format", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin("aaaa", next);
      });

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "mfa",
            "type": "pattern",
          },
        ]
      `);
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueNamespace: "mfa",
        issueRule: "",
        issueType: "pattern",
      });
    });

    it("calls Auth.confirmSignIn", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin(verificationCode, next);
      });

      expect(Auth.confirmSignIn).toHaveBeenCalledWith(
        undefined,
        verificationCode,
        "SMS_MFA"
      );
    });

    it("throws an invalid code error when the code is rejected", async () => {
      jest.spyOn(Auth, "confirmSignIn").mockImplementationOnce(() => {
        throw new Error("invalid code");
      });
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin(verificationCode, next);
      });

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "invalidMFACode",
          },
        ]
      `);
    });

    it("throws an attempts exceeded error when throttles login", async () => {
      jest.spyOn(Auth, "confirmSignIn").mockImplementationOnce(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "User temporarily locked. Try again soon",
          name: "NotAuthorizedException",
        };
      });
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin(verificationCode, next);
      });

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "attemptsExceeded",
          },
        ]
      `);
    });

    it("tracks request", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin(verificationCode, next);
      });

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("sets isLoggedIn to true", async () => {
      const { result } = render();

      await act(async () => {
        await result.current.verifyMFACodeAndLogin(verificationCode, next);
      });

      expect(result.current.isLoggedIn).toBe(true);
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

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
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
        user_leave_administrator: {},
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

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
      expect(tracker.markFetchRequestEnd).toHaveBeenCalledTimes(1);
    });

    it("requires all fields to not be empty and tracks the errors", () => {
      username = "";
      const { result } = render();

      act(() => {
        result.current.resendVerifyAccountCode(username);
      });
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "username",
            "namespace": "auth",
            "type": "required",
          },
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueNamespace: "auth",
        issueRule: "",
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toHaveLength(0);
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
        setErrors([{ message: "Pre-existing error" }]);
        result.current.resendVerifyAccountCode(username);
      });
      expect(errors).toHaveLength(0);
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

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "mfa",
            "type": "required",
          },
          {
            "field": "username",
            "namespace": "auth",
            "type": "required",
          },
          {
            "field": "password",
            "namespace": "auth",
            "type": "required",
          },
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueNamespace: "mfa",
        issueRule: "",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueNamespace: "auth",
        issueRule: "",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "password",
        issueNamespace: "auth",
        issueRule: "",
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "mismatchException",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "expired",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "invalidParametersIncludingMaybePassword",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "password",
            "namespace": "auth",
            "type": "invalid",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "password",
            "namespace": "auth",
            "type": "insecure",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "userNotConfirmed",
          },
        ]
      `);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "namespace": "auth",
            "type": "userNotFound",
          },
        ]
      `);
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
        setErrors([{ message: "Pre-existing error" }]);
        result.current.resetPassword(username, verificationCode, password);
      });
      expect(errors).toHaveLength(0);
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

      expect(tracker.trackAuthRequest).toHaveBeenCalledTimes(1);
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

      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "mfa",
            "type": "required",
          },
          {
            "field": "username",
            "namespace": "auth",
            "type": "required",
          },
        ]
      `);

      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "username",
        issueNamespace: "auth",
        issueRule: "",
        issueType: "required",
      });
      expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
        issueField: "code",
        issueNamespace: "mfa",
        issueRule: "",
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
        expect(errors).toHaveLength(1);
        expect(errors[0].issues).toEqual([
          { field: "code", type: "pattern", namespace: "mfa" },
        ]);

        expect(tracker.trackEvent).toHaveBeenCalledWith("ValidationError", {
          issueField: "code",
          issueNamespace: "mfa",
          issueRule: "",
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "mismatchException",
          },
        ]
      `);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toMatchInlineSnapshot(`
        [
          {
            "field": "code",
            "namespace": "auth",
            "type": "expired",
          },
        ]
      `);
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
          "account-verified": "true",
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

      expect.assertions(cognitoErrors.length);

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
        expect(errors).toHaveLength(1);
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
      expect(errors).toHaveLength(1);
      expect(errors[0].issues).toHaveLength(0);
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
        setErrors([{ message: "Pre-existing error" }]);
        result.current.verifyAccount(username, verificationCode);
      });
      expect(errors).toHaveLength(0);
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
          "account-verified": "true",
        }
      );
    });
  });
});
