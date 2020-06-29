import { Auth } from "aws-amplify";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { testHook } from "../test-utils";
import useAppErrorsLogic from "../../src/hooks/useAppErrorsLogic";
import useAuthLogic from "../../src/hooks/useAuthLogic";

jest.mock("aws-amplify");

describe("useAuthLogic", () => {
  let appErrors,
    createAccount,
    forgotPassword,
    login,
    password,
    setAppErrors,
    username;

  beforeEach(() => {
    jest.resetAllMocks();
    username = "test@email.com";
    password = "TestP@ssw0rd!";
    testHook(() => {
      const appErrorsLogic = useAppErrorsLogic();
      ({ appErrors, setAppErrors } = appErrorsLogic);
      ({ forgotPassword, login, createAccount } = useAuthLogic({
        appErrorsLogic,
      }));
    });
  });

  describe("forgotPassword", () => {
    it("calls Auth.forgotPassword", () => {
      act(() => {
        forgotPassword(username);
      });
      expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
    });

    it("trims whitespace from username", () => {
      act(() => {
        forgotPassword(`  ${username} `);
      });
      expect(Auth.forgotPassword).toHaveBeenCalledWith(username);
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

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        forgotPassword(username);
      });
      expect(appErrors).toBeNull();
    });
  });

  describe("login", () => {
    it("calls Auth.signIn", () => {
      act(() => {
        login(username, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("trims whitespace from username", () => {
      act(() => {
        login(`  ${username} `, password);
      });
      expect(Auth.signIn).toHaveBeenCalledWith(username, password);
    });

    it("requires fields to not be empty", () => {
      username = "";
      password = "";
      act(() => {
        login(username, password);
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

    it("sets app errors when username and password are incorrect", () => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
        // Ignore lint rule since AWS Auth class actually throws an object literal
        // eslint-disable-next-line no-throw-literal
        throw {
          code: "NotAuthorizedException",
          message: "Incorrect username or password",
          name: "NotAuthorizedException",
        };
      });
      act(() => {
        login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Incorrect email or password"`
      );
    });

    it("sets app errors when Auth.signIn throws InvalidParameterException", () => {
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
      act(() => {
        login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Please enter all required information"`
      );
    });

    it("sets app errors when Auth.signIn throws AuthError", () => {
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
      act(() => {
        login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Please enter all required information"`
      );
    });

    it("sets system error message when Auth.signIn throws unanticipated error", () => {
      jest.spyOn(Auth, "signIn").mockImplementation(() => {
        throw new Error("Some unknown error");
      });
      act(() => {
        login(username, password);
      });
      expect(appErrors.items).toHaveLength(1);
      expect(appErrors.items[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        login(username, password);
      });
      expect(appErrors).toBeNull();
    });
  });

  describe("createAccount", () => {
    it("calls Auth.signUp", () => {
      act(() => {
        createAccount(username, password);
      });
      expect(Auth.signUp).toHaveBeenCalledWith({ username, password });
    });

    it("trims whitespace from username", () => {
      act(() => {
        createAccount(`  ${username} `, password);
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

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        createAccount(username, password);
      });
      expect(appErrors).toEqual(null);
    });
  });

  describe("requireUserConsentToDataAgreement", () => {
    describe("when user consented to data sharing", () => {
      it("doesn't redirect to the consent page", () => {
        let requireUserConsentToDataAgreement;
        const user = new User({ consented_to_data_sharing: true });

        testHook(() => {
          ({ requireUserConsentToDataAgreement } = useAuthLogic({ user }));
        });

        requireUserConsentToDataAgreement();

        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });

    describe("when user didn't consent to data sharing", () => {
      it("redirects to consent page if user", () => {
        let requireUserConsentToDataAgreement;
        const user = new User({ consented_to_data_sharing: false });

        testHook(() => {
          ({ requireUserConsentToDataAgreement } = useAuthLogic({ user }));
        });

        requireUserConsentToDataAgreement();

        expect(mockRouter.push).toHaveBeenCalledWith(
          "/user/consent-to-data-sharing"
        );
      });

      it("doesn't redirect if route is already set to consent page", () => {
        let requireUserConsentToDataAgreement;
        mockRouter.pathname = "/user/consent-to-data-sharing";
        const user = new User({ consented_to_data_sharing: false });

        testHook(() => {
          ({ requireUserConsentToDataAgreement } = useAuthLogic({ user }));
        });

        requireUserConsentToDataAgreement();

        expect(mockRouter.push).not.toHaveBeenCalled();
      });
    });
  });
});
