import "../../styles/index.scss";
import Head from "next/head";
import type { AppProps } from "next/app";

function MyApp({ Component, pageProps }: AppProps) {
  return (
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

      </aside>
      <main className="page__main">
        <Component {...pageProps} />
      </main>
    </div>
  );
}
export default MyApp;
