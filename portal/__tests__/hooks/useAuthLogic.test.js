import { Auth } from "aws-amplify";
import User from "../../src/models/User";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";
import { testHook } from "../test-utils";
import useAuthLogic from "../../src/hooks/useAuthLogic";
import { useState } from "react";

jest.mock("aws-amplify");

describe("useAuthLogic", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  describe("login", () => {
    let appErrors, login, password, setAppErrors, username;
    beforeEach(() => {
      username = "test@email.com";
      password = "TestP@ssw0rd!";
      testHook(() => {
        [appErrors, setAppErrors] = useState([]);
        ({ login } = useAuthLogic({ setAppErrors }));
      });
    });

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

    it("sets app errors when username and password are empty", () => {
      username = "";
      password = "";
      act(() => {
        login(username, password);
      });
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
        `"Enter your email address and password"`
      );
      expect(Auth.signIn).not.toHaveBeenCalled();
    });

    it("sets app errors when username is empty", () => {
      username = "";
      act(() => {
        login(username, password);
      });
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
        `"Enter your email address"`
      );
      expect(Auth.signIn).not.toHaveBeenCalled();
    });

    it("sets app errors when password is empty", () => {
      const password = "";
      act(() => {
        login(username, password);
      });
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
        `"Enter your password"`
      );
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
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
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
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
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
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
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
      expect(appErrors).toHaveLength(1);
      expect(appErrors[0].message).toMatchInlineSnapshot(
        `"Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (XXX) XXX-XXXX"`
      );
    });

    it("clears existing errors", () => {
      act(() => {
        setAppErrors([{ message: "Pre-existing error" }]);
        login(username, password);
      });
      expect(appErrors).toEqual([]);
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
