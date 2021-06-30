import "../../styles/index.scss";
import Head from "next/head";
import { HelmetProvider } from "react-helmet-async";
import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <HelmetProvider>
      <div className="page">
        <Head>
          <title>Admin Portal</title>
          <link rel="icon" href="/favicon.ico" />
        </Head>

        <header className="page__header">LOGO HERE</header>
        <aside className="page__sidebar">
          <nav className="menu">
            <ul className="menu__list">
              <li className="menu__list-item">
                  <a href="#" className="menu__link">Nav Item One</a>
              </li>
              <li className="menu__list-item">
                  <a href="#" className="menu__link">Nav Item Two</a>
              </li>
              <li className="menu__list-item">
                  <a href="#" className="menu__link">Nav Item Three</a>
              </li>
            </ul>
          </nav>
          <div className="settings">
              <ul className="settings__list">
                  <li className="settings__list-item">
                      <a href="#" className="settings__link">Settings</a>
                  </li>
                  <li className="settings__list-item">
                      <a href="#" className="settings__link">Help</a>
                  </li>
              </ul>
          </div>
          <div className="environment">
              <div className="environment__label">Environment</div>
              <div className="environment__flag">Production</div>
          </div>
        </aside>
        <main className="page__main">
          <Component {...pageProps} />
        </main>
      </div>
    </HelmetProvider>
  );
}
export default MyApp;
