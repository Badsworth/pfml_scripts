import "../../styles/index.scss";
import { Helmet, HelmetProvider } from "react-helmet-async";
import type { AppProps } from "next/app";
import Header from "../components/Header";
import Sidebar from "../components/Sidebar";

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <HelmetProvider>
      <div className="page">
        <Helmet htmlAttributes={{ lang: "en" }}>
          <title>Admin Portal</title>
          <link rel="icon" href="/favicon.ico" />
        </Helmet>

        <Header />

        <Sidebar />

        <main className="page__main" tabIndex={0}>
          <Component {...pageProps} />
        </main>
      </div>
    </HelmetProvider>
  );
}
export default MyApp;
