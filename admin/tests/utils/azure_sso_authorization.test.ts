import * as api from "../../src/_api";
import * as azureAuth from "../../src/utils/azure_sso_authorization";
import { NextRouter } from "next/router";
import { waitFor } from "@testing-library/react";
import mockFetch from "../test-utils/mockFetch";
import mockLocalStorage from "../test-utils/mockLocalStorage";
import mockData from "../mock-data/azure_authorization";

describe("azure_sso_authorization Utility", () => {
  beforeEach(() => {
    Object.defineProperty(window, "localStorage", {
      value: mockLocalStorage,
    });

    window.localStorage.clear();
  });

  const { router, setUser, setError, loadingState, setLoadingState } = {
    router: {
      pathname: "",
      query: {},
      asPath: "",
      basePath: "",
    } as NextRouter,
    setUser: jest.fn(),
    setError: jest.fn(),
    loadingState: {
      loading: false,
      loggingIn: false,
      loggingOut: false,
    },
    setLoadingState: jest.fn(),
  };

  describe("authorizeUser()", () => {
    test("returns false if no tokens are saved in local storage and there's no 'code' microsoft url parameter present", async () => {
      const authorizeUserCheck = await azureAuth.authorizeUser(
        router,
        setUser,
        setError,
        loadingState,
        setLoadingState,
      );

      expect(authorizeUserCheck).toEqual(false);
    });

    test("successfully calls /admin/login if tokens exist in local storage", async () => {
      api.http.fetchJson = mockFetch({
        response: {
          data: mockData.user,
        },
      });

      window.localStorage.setItem(
        "SSO_ACCESS_TOKENS",
        JSON.stringify(mockData.sso_access_tokens),
      );

      const setUserMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      const authorizeUserCheck = await azureAuth.authorizeUser(
        router,
        setUserMock,
        setError,
        loadingState,
        setLoadingStateMock,
      );

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/login", {});
      expect(setUserMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });

    test("successfully calls getAccessToken() if no tokens are saved in local storage and the 'code' microsoft url parameter is present", async () => {
      const getAccessTokenFunction = jest.spyOn(azureAuth, "getAccessToken");

      api.http.fetchJson = mockFetch({
        response: {
          data: mockData.sso_access_tokens,
        },
      });

      const routerMock = {
        ...router,
        query: {
          ...mockData.sso_code_response,
        },
      };

      const setLoadingStateMock = jest.fn();
      const authorizeUserCheck = await azureAuth.authorizeUser(
        routerMock,
        setUser,
        setError,
        loadingState,
        setLoadingStateMock,
      );

      expect(getAccessTokenFunction).toHaveBeenCalled();
    });

    test("error is set if /admin/login fails", async () => {
      api.http.fetchJson = jest.fn(() => {
        throw new Error("Something really bad happened.");
      });

      window.localStorage.setItem(
        "SSO_ACCESS_TOKENS",
        JSON.stringify(mockData.sso_access_tokens),
      );

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.authorizeUser(
        router,
        setUser,
        setErrorMock,
        loadingState,
        setLoadingStateMock,
      );

      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });
  });

  describe("getAccessToken()", () => {
    test("successfully calls /admin/token, sets access tokens and redirects via POST_LOGIN_REDIRECT", async () => {
      Object.defineProperty(window, "location", {
        value: {
          href: "",
        },
        writable: true,
      });

      api.http.fetchJson = mockFetch({
        response: {
          data: mockData.sso_access_tokens,
        },
      });

      const routerMock = {
        ...router,
        query: {
          ...mockData.sso_code_response,
        },
      };

      window.localStorage.setItem(
        "SSO_AUTH_URI",
        JSON.stringify(mockData.sso_auth_uri),
      );
      window.localStorage.setItem(
        "POST_LOGIN_REDIRECT",
        mockData.post_login_redirect,
      );
      const setItem = jest.spyOn(localStorage, "setItem");
      const removeItem = jest.spyOn(localStorage, "removeItem");

      const setLoadingStateMock = jest.fn();
      const authorizeUserCheck = await azureAuth.getAccessToken(
        routerMock,
        setError,
        loadingState,
        setLoadingStateMock,
      );

      const mockRequestBody = {
        auth_uri_res: mockData.sso_auth_uri,
        auth_code_res: mockData.sso_code_response,
      };

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/token", {
        body: JSON.stringify(mockRequestBody),
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: true,
        loggingIn: true,
      });
      expect(removeItem).toHaveBeenCalledWith("SSO_AUTH_URI");
      expect(setItem).toHaveBeenCalledWith(
        "SSO_ACCESS_TOKENS",
        JSON.stringify(mockData.sso_access_tokens),
      );
      expect(window.location.href).toEqual(mockData.post_login_redirect);
      expect(removeItem).toHaveBeenCalledWith("POST_LOGIN_REDIRECT");
    });

    test("successfully calls /admin/token, sets access tokens and redirects to dashboard", async () => {
      Object.defineProperty(window, "location", {
        value: {
          href: "",
        },
        writable: true,
      });

      api.http.fetchJson = mockFetch({
        response: {
          data: mockData.sso_access_tokens,
        },
      });

      const routerMock = {
        ...router,
        query: {
          ...mockData.sso_code_response,
        },
      };

      window.localStorage.setItem(
        "SSO_AUTH_URI",
        JSON.stringify(mockData.sso_auth_uri),
      );

      const authorizeUserCheck = await azureAuth.getAccessToken(
        routerMock,
        setError,
        loadingState,
        setLoadingState,
      );

      expect(window.location.href).toEqual("");
    });

    test("error is set if /admin/token response does not include the 'access_token' key", async () => {
      let malformedAccessTokensResponse = { ...mockData.sso_access_tokens };
      delete malformedAccessTokensResponse.access_token;

      api.http.fetchJson = mockFetch({
        response: {
          data: malformedAccessTokensResponse,
        },
      });

      const routerMock = {
        ...router,
        query: {
          ...mockData.sso_code_response,
        },
      };

      window.localStorage.setItem(
        "SSO_AUTH_URI",
        JSON.stringify(mockData.sso_auth_uri),
      );

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.getAccessToken(
        routerMock,
        setErrorMock,
        loadingState,
        setLoadingStateMock,
      );

      const mockRequestBody = {
        auth_uri_res: mockData.sso_auth_uri,
        auth_code_res: mockData.sso_code_response,
      };

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/token", {
        body: JSON.stringify(mockRequestBody),
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });

    test("error is set if /admin/token request fails", async () => {
      api.http.fetchJson = jest.fn(() => {
        throw new Error("Something really bad happened.");
      });

      const routerMock = {
        ...router,
        query: {
          ...mockData.sso_code_response,
        },
      };

      window.localStorage.setItem(
        "SSO_AUTH_URI",
        JSON.stringify(mockData.sso_auth_uri),
      );

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.getAccessToken(
        routerMock,
        setErrorMock,
        loadingState,
        setLoadingStateMock,
      );

      const mockRequestBody = {
        auth_uri_res: mockData.sso_auth_uri,
        auth_code_res: mockData.sso_code_response,
      };

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/token", {
        body: JSON.stringify(mockRequestBody),
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });
  });

  describe("getAuthCode()", () => {
    test("successfully calls /admin/authorize and sets auth uri", async () => {
      Object.defineProperty(window, "location", {
        value: {
          href: "",
        },
        writable: true,
      });

      const setItem = jest.spyOn(localStorage, "setItem");

      api.http.fetchJson = mockFetch({
        response: {
          data: mockData.sso_auth_uri,
        },
      });

      await azureAuth.getAuthCode(
        router,
        setError,
        loadingState,
        setLoadingState,
      );

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/authorize", {});
      expect(setItem).toHaveBeenCalledWith(
        "SSO_AUTH_URI",
        JSON.stringify(mockData.sso_auth_uri),
      );
      expect(window.location.href).toEqual(mockData.sso_auth_uri.auth_uri);
    });

    test("error is set if /admin/authorize response does not include the 'auth_uri' key", async () => {
      let malformedAuthURIResponse = { ...mockData.sso_auth_uri };
      delete malformedAuthURIResponse.auth_uri;

      api.http.fetchJson = mockFetch({
        response: {
          data: {
            ...malformedAuthURIResponse,
          },
        },
      });

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.getAuthCode(
        router,
        setErrorMock,
        loadingState,
        setLoadingStateMock,
      );

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/authorize", {});
      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });

    test("error is set if /admin/authorize request fails", async () => {
      api.http.fetchJson = jest.fn(() => {
        throw new Error("Something really bad happened.");
      });

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.getAuthCode(
        router,
        setErrorMock,
        loadingState,
        setLoadingStateMock,
      );

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/authorize", {});
      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingIn: false,
      });
    });
  });

  describe("logout()", () => {
    test("successfully calls /admin/logout if tokens exist in local storage", async () => {
      jest.useFakeTimers();

      Object.defineProperty(window, "location", {
        value: {
          href: "",
        },
        writable: true,
      });

      api.http.fetchJson = mockFetch({
        response: {
          data: {
            logout_uri: mockData.post_logout_redirect,
          },
        },
      });

      window.localStorage.setItem(
        "SSO_ACCESS_TOKENS",
        JSON.stringify(mockData.sso_access_tokens),
      );
      const removeItem = jest.spyOn(localStorage, "removeItem");

      const setUserMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.logout(
        setError,
        setUserMock,
        loadingState,
        setLoadingStateMock,
      );

      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: true,
        loggingOut: true,
      });
      expect(setUserMock).toHaveBeenCalledWith(null);
      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/logout", {});
      expect(removeItem).toHaveBeenCalledWith("SSO_ACCESS_TOKENS");

      jest.runOnlyPendingTimers();

      expect(window.location.href).toEqual(mockData.post_logout_redirect);

      jest.useRealTimers();
    });

    test("does not call /admin/logout if tokens do not exist in local storage", async () => {
      const logout = await azureAuth.logout(
        setError,
        setUser,
        loadingState,
        setLoadingState,
      );

      expect(logout).toEqual(false);
    });

    test("error is set if /admin/logout request fails", async () => {
      window.localStorage.setItem(
        "SSO_ACCESS_TOKENS",
        JSON.stringify(mockData.sso_access_tokens),
      );

      api.http.fetchJson = jest.fn(() => {
        throw new Error("Something really bad happened.");
      });

      const setErrorMock = jest.fn();
      const setLoadingStateMock = jest.fn();
      await azureAuth.logout(
        setErrorMock,
        setUser,
        loadingState,
        setLoadingStateMock,
      );

      expect(api.http.fetchJson).toHaveBeenCalledWith("/admin/logout", {});
      expect(setErrorMock).toHaveBeenCalled();
      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: false,
        loggingOut: false,
      });
    });
  });

  describe("startLogin()", () => {
    test("sets POST_LOGIN_REDIRECT value and calls getAuthCode()", () => {
      const getAuthCodeFunction = jest.spyOn(azureAuth, "getAuthCode");
      const setItem = jest.spyOn(localStorage, "setItem");

      const routerMock = {
        ...router,
        pathname: "/settings",
        asPath: "http://localhost:3000/settings",
      };
      const setLoadingStateMock = jest.fn();
      azureAuth.startLogin(
        routerMock,
        setError,
        loadingState,
        setLoadingStateMock,
      );

      expect(setLoadingStateMock).toHaveBeenCalledWith({
        ...loadingState,
        loading: true,
        loggingIn: true,
      });
      expect(setItem).toHaveBeenLastCalledWith(
        "POST_LOGIN_REDIRECT",
        "http://localhost:3000/settings",
      );
      expect(getAuthCodeFunction).toHaveBeenCalled();
    });

    test("POST_LOGIN_REDIRECT is not set when current page is the dashboard", () => {
      const routerMock = {
        ...router,
        pathname: "/",
      };

      azureAuth.startLogin(routerMock, setError, loadingState, setLoadingState);

      expect(localStorage.setItem).not.toHaveBeenCalled();
    });
  });
});
