import tracker from "../services/tracker";
import { useEffect } from "react";
// Reference the module directly to fix an IE11 bug:
// https://github.com/streamich/react-use/issues/1189
import useIdle from "react-use/lib/useIdle";

/**
 *
 * @param {number} secondsOfInactivityUntilLogout Amount of time (in seconds) before we log the user out
 * @param {object} authLogic
 */
const useSessionTimeout = (secondsOfInactivityUntilLogout, authLogic) => {
  const { isLoggedIn, logout } = authLogic;
  const idleMilliseconds = secondsOfInactivityUntilLogout * 1000; // 30 minutes
  const isIdle = useIdle(idleMilliseconds);
  useEffect(() => {
    if (isLoggedIn && isIdle) {
      // @ts-expect-error ts-migrate(2554) FIXME: Expected 2 arguments, but got 1.
      tracker.trackEvent("Session timed out");

      logout({
        sessionTimedOut: true,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn, isIdle]);
};

export default useSessionTimeout;
