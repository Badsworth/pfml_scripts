import * as api from "../api";
import { useEffect, useState } from "react";
import { SSO_ACCESS_TOKENS } from "./_app";

function Logout() {
  const [localTokens, setLocalTokens] = useState<string | null>(null)
  const logout = () => {
    setLocalTokens(localStorage.getItem(SSO_ACCESS_TOKENS));
    if (localTokens) {
      api
        .getAdminLogout()
        .then(({ data }) => {
          localStorage.removeItem(SSO_ACCESS_TOKENS);
          setTimeout(() => {
            location.href = data as string;
          }, 1000);
        })
        .catch((e) => {
          console.error(e);
        });
    }
  };

  useEffect(() => {
    logout();
  });

  return (
    <div className="login">
      <h1 className="login__title">{localTokens ? "Logging out..." : "Logged out!"}</h1>
    </div>
  );
}

export default Logout;
