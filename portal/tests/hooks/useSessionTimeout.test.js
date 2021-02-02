import { act } from "react-dom/test-utils";
import { testHook } from "../test-utils";
import tracker from "../../src/services/tracker";
import useAppLogic from "../../src/hooks/useAppLogic";
import useSessionTimeout from "../../src/hooks/useSessionTimeout";

jest.mock("../../src/hooks/useAppLogic");
jest.useFakeTimers();

describe("useSessionTimeout", () => {
  let appLogic;
  const secondsOfInactivityUntilLogout = 3;

  describe("when user is logged in", () => {
    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
        appLogic.auth.isLoggedIn = true;
        useSessionTimeout(secondsOfInactivityUntilLogout, appLogic.auth);
      });
    });

    it("logs user out and tracks event after secondsOfInactivityUntilLogout seconds", () => {
      const trackEventSpy = jest.spyOn(tracker, "trackEvent");
      expect(appLogic.auth.isLoggedIn).toBe(true);

      const millisecondsOfInactivityUntilLogout =
        secondsOfInactivityUntilLogout * 1000;

      act(() => {
        jest.advanceTimersByTime(millisecondsOfInactivityUntilLogout - 1);
      });

      expect(appLogic.auth.logout).not.toHaveBeenCalled();
      expect(trackEventSpy).not.toHaveBeenCalled();

      act(() => {
        jest.advanceTimersByTime(1);
      });

      expect(appLogic.auth.logout).toHaveBeenCalledWith({
        sessionTimedOut: true,
      });
      expect(trackEventSpy).toHaveBeenCalledWith("Session timed out");
    });
  });

  describe("when user is logged out", () => {
    beforeEach(() => {
      testHook(() => {
        appLogic = useAppLogic();
        appLogic.auth.isLoggedIn = false;
        useSessionTimeout(secondsOfInactivityUntilLogout, appLogic.auth);
      });
    });

    it("does not call logout", () => {
      const millisecondsOfInactivityUntilLogout =
        secondsOfInactivityUntilLogout * 1000;
      act(() => {
        jest.advanceTimersByTime(millisecondsOfInactivityUntilLogout);
      });
      expect(appLogic.auth.logout).not.toHaveBeenCalled();
    });
  });
});
