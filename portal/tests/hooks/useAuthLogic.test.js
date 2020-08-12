import { Auth } from "@aws-amplify/auth";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useAuthLogic from "../../src/hooks/useAuthLogic";

jest.mock("@aws-amplify/auth");

describe("useAuthLogic", () => {
  let appErrors,
    authData,
    createAccount,
    forgotPassword,
    isLoggedIn,
    login,
    logout,
    password,
    requireLogin,
    resendVerifyAccountCode,
    resetPassword,
    setAppErrors,
    username,
    verificationCode,
    verifyAccount;

  beforeEach(() => {
    jest.resetAllMocks();
    username = "test@email.com";
    password = "TestP@ssw0rd!";
    verificationCode = "123456";
    testHook(() => {
      const appErrorsLogic = useAppErrorsLogic();
      ({ appErrors, setAppErrors } = appErrorsLogic);
      ({
        authData,
        forgotPassword,
        login,
        logout,
        isLoggedIn,
        createAccount,
        requireLogin,
        resendVerifyAccountCode,
        resetPassword,
        verifyAccount,
      } = useAuthLogic({
        appErrorsLogic,
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

    it("trims whitespace from username", async () => {
      await act(async () => {
        await forgotPassword(`  ${username} `);
      });
      expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
    });

    it("stores username in authData for Reset Password page", async () => {
      await act(async () => {
        await forgotPassword(username);
      });

      expect(authData.resetPasswordUsername).toBe(username);
    });

    it("sets app errors when username is empty", () => {
      username = "";
      act(() => {
        forgotPassword(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );
      expect(Auth.forgotPassword).not.toHaveBeenCalled();
    });

    it("sets app errors when an account isn't found", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementation(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UserNotFoundException",
          message: "An account with the given email does not exist.",
          name: "UserNotFoundException",
        };
      });
      act(() => {
        forgotPassword(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email"`
      );
    });

    it("sets app errors when Auth.forgotPassword throws InvalidParameterException", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementation(() => {
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
        forgotPassword(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Please enter all required information"`
      );
    });

    it("sets system error message when Auth.forgotPassword throws unanticipated error", () => {
      jest.spyOn(Auth, "forgotPassword").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        forgotPassword(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", async () => {
      await act(async () => {
        setAppErrors([{ message: "Pre-existing error" }]);
        await forgotPassword(username);
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

    it("requires fields to not be empty", async () => {
      username = "";
      password = "";

      await act(async () => {
        await login(username, password);
      });

      expect(appErrors.items).toHaveLength(2);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter your email address",
          "Enter your password",
        ]
      `);
      expect(Auth.signIn).not.toHaveBeenCalled();
    });

    it("sets app errors when username and password are incorrect", async () => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
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
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
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
        `"Please enter all required information"`
      );
    });

    it("sets app errors when Auth.signIn throws AuthError", async () => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
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
        `"Please enter all required information"`
      );
    });

    it("sets system error message when Auth.signIn throws unanticipated error", async () => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      await act(async () => {
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", async () => {
      await act(async () => {
        setAppErrors([{ message: "Pre-existing error" }]);
        await login(username, password);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });

  describe("logout", () => {
    beforeEach(() => {
      // Mock window.location.assign since browser navigation isn't available in unit tests
      jest.spyOn(window, "location", "get").mockImplementationOnce(() => {
        return {
          assign: jest.fn(),
        };
      });
    });

    it("calls Auth.signOut", () => {
      act(() => {
        logout();
      });
      expect(Auth.signOut).toHaveBeenCalledTimes(1);
    });

    it("redirects to home page", async () => {
      const originalLocation = window.location;

      delete window.location;
      window.location = { assign: jest.fn() };
      await act(async () => {
        await logout();
      });
      expect(window.location.assign).toHaveBeenCalledWith(routes.auth.login);

      window.location = originalLocation;
      jest.restoreAllMocks();
    });
  });

  describe("createAccount", () => {
    it("calls Auth.signUp", async () => {
      await act(async () => {
        await createAccount(username, password);
      });
      expect(Auth.signUp).toHaveBeenCalledWith({ username, password });
    });

    it("routes to Verify Account page", async () => {
      await act(async () => {
        await createAccount(username, password);
      });

      expect(mockRouter.push).toHaveBeenCalledWith(routes.auth.verifyAccount);
    });

    it("stores username in authData for Verify Account page", async () => {
      await act(async () => {
        await createAccount(username, password);
      });

      expect(authData.createAccountUsername).toBe(username);
    });

    it("trims whitespace from username", async () => {
      await act(async () => {
        await createAccount(`  ${username} `, password);
      });
      expect(Auth.signUp).toHaveBeenCalledWith({ username, password });
    });

    it("requires fields to not be empty", () => {
      username = "";
      password = "";
      act(() => {
        createAccount(username, password);
      });

      expect(appErrors.items).toHaveLength(2);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter your email address",
          "Enter your password",
        ]
      `);
      expect(Auth.signUp).not.toHaveBeenCalled();
    });

    it("sets individual app errors when username and password are empty", () => {
      username = "";
      password = "";
      act(() => {
        createAccount(username, password);
      });
      expect(appErrors.items).toHaveLength(2);
      expect(Auth.signUp).not.toHaveBeenCalled();
    });

    it("sets app errors when an account with the username already exists", () => {
      jest.spyOn(Auth, "signUp").mockImplementation(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "UsernameExistsException",
          message: "An account with the given email already exists.",
          name: "UsernameExistsException",
        };
      });
      act(() => {
        createAccount(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"An account with the given email already exists"`
      );
    });

    it("sets app errors when Auth.signUp throws InvalidParameterException", () => {
      jest.spyOn(Auth, "signUp").mockImplementation(() => {
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
        createAccount(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Your password does not meet the requirements. Please check the requirements and try again."`
      );
    });

    it("sets app errors when Auth.signUp throws InvalidPasswordException", () => {
      const invalidPasswordErrorMessages = [
        "Password did not conform with policy: Password not long enough",
        "Password did not conform with policy: Password must have uppercase characters",
        "Password did not conform with policy: Password must have lowercase characters",
        "Password did not conform with policy: Password must have numeric characters",
      ];

      const cognitoErrors = invalidPasswordErrorMessages.map((message) => {
        return {
          code: "InvalidParameterException",
          message,
          name: "InvalidParameterException",
        };
      });

      expect.assertions(cognitoErrors.length * 2);

      for (const cognitoError of cognitoErrors) {
        jest.resetAllMocks();
        jest.spyOn(Auth, "signUp").mockImplementation(() => {
          // Ignore lint rule since AWS Auth class actually throws an object literal
          // eslint-disable-next-line no-throw-literal
          throw cognitoError;
        });
        act(() => {
          createAccount(username, password);
        });
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toMatchInlineSnapshot(
          `"Your password does not meet the requirements. Please check the requirements and try again."`
        );
      }
    });

    it("sets system error message when Auth.signUp throws unanticipated error", () => {
      jest.spyOn(Auth, "signUp").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        createAccount(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", async () => {
      await act(async () => {
        setAppErrors([{ message: "Pre-existing error" }]);
        await createAccount(username, password);
      });
      expect(appErrors.items).toHaveLength(0);
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
        await act(async () => {
          await requireLogin();
        });
        expect(mockRouter.push).not.toHaveBeenCalled();
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
      beforeEach(() => {
        Auth.currentUserInfo.mockResolvedValueOnce(null);
      });

      it("redirects to login page", async () => {
        await act(async () => {
          await requireLogin();
        });
        expect(mockRouter.push).toHaveBeenCalledWith(routes.auth.login);
      });

      it("doesn't redirect if route is already set to login page", async () => {
        mockRouter.pathname = routes.auth.login;
        await act(async () => {
          await requireLogin();
        });
        expect(mockRouter.push).not.toHaveBeenCalled();
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

    it("sets app errors when username is empty", () => {
      username = "";
      act(() => {
        resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );
      expect(Auth.resendSignUp).not.toHaveBeenCalled();
    });

    it("sets system error message when Auth.resendSignUp throws unanticipated error", () => {
      jest.spyOn(Auth, "resendSignUp").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        resendVerifyAccountCode(username);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
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

    it("routes to login page with account verified success message", async () => {
      await act(async () => {
        await resetPassword(username, verificationCode, password);
      });

      expect(mockRouter.push).toHaveBeenCalledWith(
        "/login?account-verified=true"
      );
    });

    it("requires all fields to not be empty", () => {
      username = "";
      password = "";
      verificationCode = "";

      act(() => {
        resetPassword(username, verificationCode, password);
      });

      expect(appErrors.items).toHaveLength(3);
      expect(appErrors.items.map((e) => e.message)).toMatchInlineSnapshot(`
        Array [
          "Enter the 6-digit code sent to your email",
          "Enter your email address",
          "Enter your password",
        ]
      `);
      expect(Auth.forgotPasswordSubmit).not.toHaveBeenCalled();
    });

    it("sets app errors when CodeMismatchException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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
        `"Please check the requirements and try again. Ensure all required information is entered and the password meets the requirements."`
      );
    });

    it("sets app errors when InvalidPasswordException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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

    it("sets app errors when UserNotConfirmedException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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
        `"Please first confirm your account by following the instructions in the verification email sent to your inbox."`
      );
    });

    it("sets app errors when UserNotFoundException is thrown", () => {
      jest.spyOn(Auth, "forgotPasswordSubmit").mockImplementation(() => {
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

    it("trims whitespace from code", () => {
      act(() => {
        verifyAccount(username, `  ${verificationCode} `);
      });
      expect(Auth.confirmSignUp).toHaveBeenCalledWith(
        username,
        verificationCode
      );
    });

    it("sets app errors when username is empty", () => {
      username = "";
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );
      expect(Auth.confirmSignUp).not.toHaveBeenCalled();
    });

    it("sets app errors when verification code is empty", () => {
      verificationCode = "";
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Enter the 6-digit code sent to your email"`
      );
      expect(Auth.confirmSignUp).not.toHaveBeenCalled();
    });

    it("sets app errors when verification code is malformed", () => {
      const malformedCodes = [
        "12345", // too short,
        "1234567", // too long,
        "123A5", // has digits
        "123.4", // has punctuation
      ];
      expect.assertions(malformedCodes.length * 3);
      for (const code of malformedCodes) {
        act(() => {
          verifyAccount(username, code);
        });
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toEqual(
          "Enter the 6-digit code sent to your email and ensure it does not include any punctuation."
        );
        expect(Auth.confirmSignUp).not.toHaveBeenCalled();
      }
    });

    it("sets app errors when verification code is incorrect", () => {
      jest.spyOn(Auth, "confirmSignUp").mockImplementation(() => {
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
      jest.spyOn(Auth, "confirmSignUp").mockImplementation(() => {
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
        jest.resetAllMocks();
        jest.spyOn(Auth, "confirmSignUp").mockImplementation(() => {
          // Ignore lint rule since AWS Auth class actually throws an object literal
          // eslint-disable-next-line no-throw-literal
          throw cognitoError;
        });
        act(() => {
          verifyAccount(username, verificationCode);
        });
        expect(appErrors.items).toHaveLength(1);
        expect(appErrors.items[0].message).toMatchInlineSnapshot(
          `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
        );
      }
    });

    it("sets system error message when Auth.confirmSignUp throws unanticipated error", () => {
      jest.spyOn(Auth, "confirmSignUp").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        verifyAccount(username, verificationCode);
      });
      expect(appErrors.items).toHaveLength(0);
    });
  });
});
