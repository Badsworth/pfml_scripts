import { Auth } from "@aws-amplify/auth";
import routes from "../routes";
import { useEffect } from "react";

/**
 * Hook that redirects a user if they're logged in. By default, they're redirected to
 * the landing page, which has its own redirect logic based on the user's role.
 */
const useLoggedInRedirect = (portalFlow, redirectTo = routes.index) => {
  useEffect(() => {
    Auth.currentUserInfo()
      .then((userInfo) => {
        if (userInfo?.attributes) {
          portalFlow.goTo(redirectTo, {}, { redirect: true });
        }
      })
      .catch((err) => {
        // Not concerned about this error because it's expected if the user isn't logged in.
        return err;
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
};

export default useLoggedInRedirect;
