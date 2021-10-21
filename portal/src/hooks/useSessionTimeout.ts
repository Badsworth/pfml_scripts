import { AuthLogic } from "./useAuthLogic";
import tracker from "../services/tracker";
import { useEffect } from "react";
// Reference the module directly to fix an IE11 bug:
// https://github.com/streamich/react-use/issues/1189
import useIdle from "react-use/lib/useIdle";

/**
 * @param secondsOfInactivityUntilLogout Amount of time (in seconds) before we log the user out
 */
const useSessionTimeout = (
  secondsOfInactivityUntilLogout: number,
  authLogic: AuthLogic
) => {
  const { isLoggedIn, logout } = authLogic;
  const idleMilliseconds = secondsOfInactivityUntilLogout * 1000; // 30 minutes
  const isIdle = useIdle(idleMilliseconds);
  useEffect(() => {
    if (isLoggedIn && isIdle) {
      tracker.trackEvent("Session timed out");

      logout({
        sessionTimedOut: true,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn, isIdle]);
};

export default useSessionTimeout;
