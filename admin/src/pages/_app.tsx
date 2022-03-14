import "../../styles/index.scss";

import * as api from "../api";

import { Helmet, HelmetProvider } from "react-helmet-async";
import { useEffect, useState } from "react";

import type { AppProps } from "next/app";
import Header from "../components/Header";
// import Sidebar from "../components/Sidebar";
import Loading from "../components/Loading";
import WithPermissions from "../components/WithPermissions";
import { authorizeUser } from "../utils/azure_sso_authorization";
import classNames from "classnames";
import dynamic from "next/dynamic";
import { useRouter } from "next/router";

const Login = dynamic(() => import("../components/Login"));

export type LoadingState = {
  loading: boolean;
  loggingIn: boolean;
  loggingOut: boolean;
};

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [user, setUser] = useState<api.AdminUserResponse | null>(null);
  const [error, setError] = useState<Partial<api.ErrorResponse>>();
  const [loadingState, setLoadingState] = useState<LoadingState>({
    loading: false,
    loggingIn: false,
    loggingOut: false,
  });

  useEffect(() => {
    authorizeUser(router, setUser, setError, loadingState, setLoadingState);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router.query]);

  const pageClasses = classNames("page", {
    "page--login": !user,
  });

  const pageMainClasses = classNames("page__main", {
    "page__main--login": !user,
    "page__main--loading": loadingState.loading,
  });

  return (
    <HelmetProvider>
      <div className={pageClasses}>
        <Helmet htmlAttributes={{ lang: "en" }}>
          <title>Paid Family & Medical Leave Administrative Portal</title>
          <link rel="icon" href="/assets/favicon.ico" />
        </Helmet>
        <Header
          user={user}
          setError={setError}
          setUser={setUser}
          loadingState={loadingState}
          setLoadingState={setLoadingState}
        />
        {/*user && <Sidebar user={user} />*/}
        <main className={pageMainClasses} tabIndex={0}>
          {loadingState.loading ? (
            <Loading
              title={
                loadingState.loggingIn
                  ? "Logging in..."
                  : loadingState.loggingOut
                  ? "Logging out..."
                  : "Please wait..."
              }
            />
          ) : !user && Component.name !== "Logout" ? (
            <Login
              error={error}
              setError={setError}
              loadingState={loadingState}
              setLoadingState={setLoadingState}
            />
          ) : user ? (
            <WithPermissions
              user={user}
              permissions={pageProps.permissions}
              isPage={true}
            >
              <Component {...pageProps} />
            </WithPermissions>
          ) : null}
        </main>
      </div>
    </HelmetProvider>
  );
}

export default MyApp;
