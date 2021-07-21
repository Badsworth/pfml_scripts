import "../../styles/index.scss";
import { Helmet, HelmetProvider } from "react-helmet-async";
import type { AppProps } from "next/app";
import { useState, useEffect, MouseEvent } from "react";
import * as api from "../api";

export const SSO_AUTH_URI = "SSO_AUTH_URI";
export const SSO_ACCESS_TOKENS = "SSO_ACCESS_TOKENS";
const noop = () => {};
function MyApp({ Component, pageProps }: AppProps) {
  const [user, setUser] = useState<api.UserResponse>();

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

  const logout = (e: MouseEvent) => {
    e.preventDefault();
    api
      .getAdminLogout()
      .then(({ data }) => {
        localStorage.removeItem(SSO_ACCESS_TOKENS);
        console.log(data);
        location.href = data as string;
      })
      .catch(retryLogin(10));
  };

  useEffect(() => {
    if (user) return noop;
    // Handle the cases where user already has a token
    const localTokens: api.AdminTokenResponse = JSON.parse(
      localStorage.getItem(SSO_ACCESS_TOKENS) || "{}",
    );
    if ("access_token" in localTokens) {
      api
        .getAdminLogin(
          /* localTokens, */ {
            headers: {
              Authorization: `Bearer ${localTokens.access_token}`,
            },
          },
        )
        .then(({ data }) => {
          console.info("Logged in!", data);
          setUser(data);
        })
        .catch(retryLogin(10));
      return noop;
    }
    // If the user doesn't have a token, initiate auth code flow
    let authURIRes: api.AuthURIResponse;
    authURIRes = JSON.parse(localStorage.getItem(SSO_AUTH_URI) || "{}");
    if (!location.search) {
      api
        .getAdminAuthorize()
        .then(({ data }) => {
          // console.log("Authorization:", data);
          localStorage.setItem(SSO_AUTH_URI, JSON.stringify(data));
          location.href = data.auth_uri as string;
        })
        .catch(retryLogin(10));
    } else if ("state" in authURIRes) {
      // when the user receives the code, we'll trade it for an access_token
      const authCodeRes: api.AuthCodeResponse = parseURLSearch(
        location.search.substring(1),
      );
      api
        .postAdminToken({
          authURIRes,
          authCodeRes,
        })
        .then(({ data }) => {
          // console.log("Tokens:", data);
          localStorage.removeItem(SSO_AUTH_URI);
          localStorage.setItem(SSO_ACCESS_TOKENS, JSON.stringify(data));
          location.href = location.origin;
        })
        .catch(retryLogin(10));
    }
    return noop;
  }, []);

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
              href="#"
              title="Paid Family & Medical Leave - Massachusetts"
              className="page__logo-link"
            ></a>
          </div>
          {user && (
            <div className="page__user-options">
              <a
                href="#"
                role="button"
                aria-label={`${user.email_address} - User Options`}
                className="user-options"
                onClick={logout}
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
        {user && (
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
        {!user && (
          <div className="login">
            <div className="login__title">Logging in...</div>
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
