import "../../styles/index.scss";
import { Helmet, HelmetProvider } from "react-helmet-async";
import type { AppProps } from "next/app";
import { useState, useEffect, MouseEvent } from "react";
import * as api from "../api";

export const SSO_AUTH_URI = "SSO_AUTH_URI";
export const SSO_ACCESS_TOKENS = "SSO_ACCESS_TOKENS";
export const POST_LOGIN_REDIRECT = "POST_LOGIN_REDIRECT";
const noop = () => {};

function MyApp({ Component, pageProps }: AppProps) {
  // @todo: change user type
  const [user, setUser] = useState<api.UserResponse>();

  let authURIRes: api.AuthURIResponse;
  let localTokens: api.AdminTokenResponse;

  const retryLogin = (time: number) => {
    return (e: Error) => {
      console.error(e);
      localStorage.removeItem(SSO_AUTH_URI);
      localStorage.removeItem(SSO_ACCESS_TOKENS);
      setTimeout(() => {
        window.location.href = window.location.origin;
      }, time * 1000);
    };
  };

  const canLogin = () => {
    localTokens = JSON.parse(localStorage.getItem(SSO_ACCESS_TOKENS) || "{}");
    if ("access_token" in localTokens) {
      api
        .getAdminLogin({
          headers: {
            Authorization: `Bearer ${localTokens.access_token}`,
          },
        })
        .then(({ data }) => {
          console.info("Logged in!", data);
          setUser(data);
        })
        .catch(retryLogin(10));

      return true;
    }
    return false;
  };

  const getAuthCode = () => {
    // If the user doesn't have a token, initiate auth code flow
    authURIRes = JSON.parse(localStorage.getItem(SSO_AUTH_URI) || "{}");
    if (!location.search.includes("code")) {
      api
        .getAdminAuthorize()
        .then(({ data }) => {
          if (!data.auth_uri) {
            // @todo: show error
            return;
          }
          localStorage.setItem(SSO_AUTH_URI, JSON.stringify(data));
          location.href = data.auth_uri;
        })
        .catch((e) => {
          // @todo: show error
          return;
        });
    }
  };

  const getAccessToken = () => {
    if (location.search.includes("code") && "state" in authURIRes) {
      // when the user receives the code, we'll trade it for an access_token
      localStorage.removeItem(SSO_AUTH_URI);
      const authCodeRes: api.AuthCodeResponse = parseURLSearch(
        location.search.substring(1),
      );
      api
        .postAdminToken({
          authURIRes,
          authCodeRes,
        })
        .then(({ data }) => {
          if (!data.access_token) {
            // @todo: show error
            return;
          }
          localStorage.setItem(SSO_ACCESS_TOKENS, JSON.stringify(data));
          location.href =
            localStorage.getItem(POST_LOGIN_REDIRECT) || location.origin;
          localStorage.removeItem(POST_LOGIN_REDIRECT);
        })
        .catch((e) => {
          // @todo: show error
          return;
        });
    }
  };

  useEffect(() => {
    if (user) return noop;
    // Handle the cases where user already has a token
    if (canLogin()) return noop;
    // User could not login
    // If the user is not trying to logout
    if (Component.name !== "Logout") {
      // If user was not in home directory
      // redirect back to where they left off after the login
      if (location.pathname !== "/") {
        localStorage.setItem(
          POST_LOGIN_REDIRECT,
          location.origin + location.pathname,
        );
      }
      // Initiate auth code flow
      getAuthCode();
      // Trade auth code for access tokens
      getAccessToken();
    }
    return noop;
  }, []);

  console.log(Component.name);
  return (
    <HelmetProvider>
      <div className="page">
        <Helmet htmlAttributes={{ lang: "en" }}>
          <title>Admin Portal</title>
          <link rel="icon" href="/favicon.ico" />
        </Helmet>

        <header className="page__header">
          <div className="page__logo">
            <a
              href="/"
              title="Paid Family & Medical Leave - Massachusetts"
              className="page__logo-link"
            ></a>
          </div>
          {user && (
            <div className="page__user-options">
              <a
                href="/logout"
                role="button"
                aria-label={`${user.email_address} - User Options`}
                className="user-options"
              >
                <span className="user-options__avatar">
                  <img
                    className="user-options__avatar-image"
                    src="https://via.placeholder.com/32"
                    alt={user.email_address}
                  />
                </span>
                <span className="user-options__name">{user.email_address}</span>
                <span className="user-options__dropdown"></span>
              </a>
            </div>
          )}
        </header>
        {/* @todo reduce login calls */}
        {typeof user !== "undefined" && Component.name !== "Logout" && (
          <>
            <aside className="page__sidebar" tabIndex={0}>
              <nav className="menu">
                <ul className="menu__list">
                  <li className="menu__list-item">
                    <a href="#" className="menu__link menu__link--dashboard">
                      Dashboard
                    </a>
                  </li>
                  <li className="menu__list-item">
                    <a href="#" className="menu__link menu__link--user-lookup">
                      User Lookup
                    </a>
                  </li>
                  <li className="menu__list-item">
                    <a href="#" className="menu__link menu__link--maintenance">
                      Maintenance
                    </a>
                  </li>
                  <li className="menu__list-item">
                    <a href="#" className="menu__link menu__link--features">
                      Features
                    </a>
                  </li>
                </ul>
              </nav>
              <div className="settings">
                <ul className="settings__list">
                  <li className="settings__list-item">
                    <a
                      href="#"
                      className="settings__link settings__link--settings"
                    >
                      Settings
                    </a>
                  </li>
                  <li className="settings__list-item">
                    <a href="#" className="settings__link settings__link--help">
                      Help
                    </a>
                  </li>
                </ul>
              </div>
              <div className="environment">
                <div className="environment__label">Environment</div>
                <div className="environment__flag">Production</div>
              </div>
            </aside>
            <main className="page__main" tabIndex={0}>
              <Component {...pageProps} />
            </main>
          </>
        )}
        {Component.name === "Logout" && <Component {...pageProps} />}
        {typeof user === "undefined" && Component.name !== "Logout" && (
          <div className="login">
            <h1 className="login__title">Logging in...</h1>
            <button className="login__button">Login</button>
          </div>
        )}
      </div>
    </HelmetProvider>
  );
}

export default MyApp;

const parseURLSearch = (search: string) =>
  JSON.parse(
    '{"' +
      decodeURI(search)
        .replace(/"/g, '\\"')
        .replace(/&/g, '","')
        .replace(/=/g, '":"') +
      '"}',
  );
