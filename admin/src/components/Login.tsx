import React from "react";
import * as api from "../api";
import Alert from "../../src/components/Alert";
import { startLogin } from "../../src/utils/azure_sso_authorization";
import { LoadingState } from "../../src/pages/_app";
import isClient from "../../src/utils/isClient";
import { useRouter } from "next/router";

export type Props = {
  error: Partial<api.ErrorResponse> | undefined;
  setError: React.Dispatch<
    React.SetStateAction<Partial<api.ErrorResponse> | undefined>
  >;
  loadingState: LoadingState;
  setLoadingState: React.Dispatch<React.SetStateAction<LoadingState>>;
};

const Login = ({ error, setError, loadingState, setLoadingState }: Props) => {
  const router = useRouter();

  const handleLogin = (e: React.MouseEvent<HTMLElement>) => {
    e.preventDefault();

    startLogin(router, setError, loadingState, setLoadingState);
  };

  let urlParams = {};
  if (isClient()) {
    urlParams = router.query;
  }

  return (
    <>
      <h1>Paid Family & Medical Leave Administrative Portal</h1>
      <div className="login">
        {"logged_out" in urlParams && (
          <Alert type="success">You have successfully logged out!</Alert>
        )}
        {error && (
          <Alert type="error">{error.data.message || error.data.detail}</Alert>
        )}
        <h2 className="login__sub-heading">
          Log in to manage settings and functions for the PFML Portal.
        </h2>
        <p className="login__info">A mass.gov account is required to log in.</p>
        <a href="#" className="btn btn--login" onClick={handleLogin}>
          Login
        </a>
      </div>
    </>
  );
};

export default Login;
