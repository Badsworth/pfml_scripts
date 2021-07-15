import "../../styles/index.scss";
import { Helmet, HelmetProvider } from "react-helmet-async";
import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
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
          <div className="page__user-options">
            <a href="#" role="button" aria-label="FirstName LastName - User Options" className="user-options">
              <span className="user-options__avatar">
                <img className="user-options__avatar-image" src="https://via.placeholder.com/32" alt="FirstName LastName" />
              </span>
              <span className="user-options__name">FirstName LastName</span>
              <span className="user-options__dropdown">

              </span>
            </a>
          </div>
        </header>
        <aside className="page__sidebar" tabIndex="0">
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
                <a href="#" className="settings__link settings__link--settings">
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
        <main className="page__main" tabIndex="0">
          <Component {...pageProps} />
        </main>
      </div>
    </HelmetProvider>
  );
}
export default MyApp;
