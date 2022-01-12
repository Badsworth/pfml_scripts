import React from "react";
import routes from "../../src/routes";
import * as api from "../api";
import { LoadingState } from "../../src/pages/_app";
import { NextRouter } from "next/router";
import * as azureAuth from "./azure_sso_authorization";

export const SSO_AUTH_URI = "SSO_AUTH_URI";
export const SSO_ACCESS_TOKENS = "SSO_ACCESS_TOKENS";
export const POST_LOGIN_REDIRECT = "POST_LOGIN_REDIRECT";

export const getAuthorizationHeader = () => {
  const localTokens: api.AdminTokenResponse = JSON.parse(
    localStorage.getItem(SSO_ACCESS_TOKENS) || "{}",
  );

  if ("access_token" in localTokens) {
    return {
      headers: {
        Authorization: `Bearer ${localTokens.access_token}`,
      },
    };
  }
  return {};
};

/**
 * authorizeUser() runs on every page request and router query change. It
 * runs in useEffect in _app.js.
 *
 * It logs the user in if an access token is already stored in local storage
 * or requires the user to log in again if their token has expired.
 *
 * It also runs when no access token is stored and the url query string
 * contains the 'code' parameter which is provided from microsoft in order
 * to complete the authentication process that was started by startLogin().
 *
 * Once authentication completes, the users information is saved in
 * the state. The user information comes from the flask global application
 * context and set in /api/massgov/pfml/api/authentication/__init__.py.
 */
export const authorizeUser = async (
  router: NextRouter,
  setUser: React.Dispatch<React.SetStateAction<api.AdminUserResponse | null>>,
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >,
  loadingState: LoadingState,
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>,
) => {
  const authorization_header = getAuthorizationHeader();
  if ("headers" in authorization_header) {
    return api
      .getAdminLogin()
      .then(({ data }) => {
        setUser(data);
      })
      .catch((e) => {
        setError(e);

        // Empty storage in case signature has expired
        // User needs a fresh login
        localStorage.removeItem(SSO_ACCESS_TOKENS);
        localStorage.removeItem(SSO_AUTH_URI);
        setUser(null);
      })
      .finally(() => {
        // Removes the Loading component in _app.js
        setLoadingState({
          ...loadingState,
          loading: false,
          loggingIn: false,
        });
      });
  } else {
    if (router.query.code) {
      /**
       * namespacing here purely for testing
       * @link https://stackoverflow.com/questions/51269431/jest-mock-inner-function
       */
      return azureAuth.getAccessToken(
        router,
        setError,
        loadingState,
        setLoadingState,
      );
    } else {
      return false;
    }
  }
};

/**
 * getAuthCode() is the first step in the login process. It is called
 * from startLogin().
 *
 * It gets an authorization code from microsoft and sets the response
 * data in local storage. It then redirects the user to the
 * authorization url returned from microsoft.
 *
 * Once the user enters their credentials on microsoft's domain, the
 * user is redirected back to the admin portal with code url query
 * parameters which fires the getAccessToken() function via
 * authorizeUser() which trades the authorization code for an access
 * token and ultimately finishes the auth flow.
 */
export const getAuthCode = async (
  router: NextRouter,
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >,
  loadingState: LoadingState,
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>,
): Promise<unknown> => {
  return api
    .getAdminAuthorize()
    .then(({ data }) => {
      if (!data.auth_uri) {
        setError({
          data: {
            message: "Missing authentication uri!",
          },
        });

        // Removes the Loading component in _app.js
        setLoadingState({
          ...loadingState,
          loading: false,
          loggingIn: false,
        });

        return;
      }

      localStorage.setItem(SSO_AUTH_URI, JSON.stringify(data));
      location.href = data.auth_uri;
    })
    .catch((e) => {
      setError(e);

      // Removes the Loading component in _app.js
      setLoadingState({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });
};

/**
 * getAccessToken is called via authorizeUser() when a 'code' url
 * query parameter is present.

 * It trades the authorization code for an access token and
 * ultimately finishes the auth flow. It also sets the access token
 * in local storage for future auth checks via authorizeUser().
 */
export const getAccessToken = (
  router: NextRouter,
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >,
  loadingState: LoadingState,
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>,
) => {
  const auth_uri_res: api.AuthURIResponse = JSON.parse(
    localStorage.getItem(SSO_AUTH_URI) || "{}",
  );

  if (router.query.code && "state" in auth_uri_res) {
    // Shows the Loading component in _app.js
    setLoadingState({
      ...loadingState,
      loading: true,
      loggingIn: true,
    });

    const auth_code_res: api.AuthCodeResponse = router.query;

    return api
      .postAdminToken({
        auth_uri_res,
        auth_code_res,
      })
      .then(({ data }) => {
        if (!data.access_token) {
          setError({
            data: {
              message: "Missing access token!",
            },
          });

          // Removes the Loading component in _app.js
          setLoadingState({
            ...loadingState,
            loading: false,
            loggingIn: false,
          });

          return;
        }

        localStorage.removeItem(SSO_AUTH_URI);
        localStorage.setItem(SSO_ACCESS_TOKENS, JSON.stringify(data));

        const redirectPath =
          localStorage.getItem(POST_LOGIN_REDIRECT) || router.pathname;
        location.href = redirectPath;
        localStorage.removeItem(POST_LOGIN_REDIRECT);
      })
      .catch((e) => {
        setError(e);

        // Removes the Loading component in _app.js
        setLoadingState({
          ...loadingState,
          loading: false,
          loggingIn: false,
        });
      });
  } else {
    return false;
  }
};

/**
 * The startLogin() function kicks off the entire login process.
 *
 * It's called from within the Login component.
 */
export const startLogin = (
  router: NextRouter,
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >,
  loadingState: LoadingState,
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>,
) => {
  // Shows the Loading component in _app.js
  setLoadingState({
    ...loadingState,
    loading: true,
    loggingIn: true,
  });

  if (router.pathname !== routes.dashboard) {
    localStorage.setItem(POST_LOGIN_REDIRECT, router.asPath);
  }

  /**
   * Initiate auth code flow
   * namespacing here purely for testing
   * @link https://stackoverflow.com/questions/51269431/jest-mock-inner-function
   */
  return azureAuth.getAuthCode(router, setError, loadingState, setLoadingState);
};

/**
 * logout() is called from the Header component.
 *
 * This is the only function for the logout process.
 */
type AdminApiResponse = {
  data: Object;
  mesage: string;
  meta: {
    method: string;
    resource: string;
  };
  status_code: string;
};
export const logout = async (
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse | undefined>>
  >,
  setUser: React.Dispatch<React.SetStateAction<api.AdminUserResponse | null>>,
  loadingState: LoadingState,
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>,
) => {
  // Shows the Loading component in _app.js
  setLoadingState({
    ...loadingState,
    loading: true,
    loggingOut: true,
  });

  const localTokens = localStorage.getItem(SSO_ACCESS_TOKENS);

  if (localTokens) {
    setUser(null);

    return api
      .getAdminLogout()
      .then(({ data }) => {
        localStorage.removeItem(SSO_ACCESS_TOKENS);

        setTimeout(() => {
          location.href = data.logout_uri as string;
        }, 1000);
      })
      .catch((e) => {
        setError(e);

        // Removes the Loading component in _app.js
        setLoadingState({
          ...loadingState,
          loading: false,
          loggingOut: false,
        });
      });
  } else {
    return false;
  }
};
