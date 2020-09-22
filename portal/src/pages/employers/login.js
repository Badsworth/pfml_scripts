import routes from "../../../src/routes";
import { useEffect } from "react";
import { useRouter } from "next/router";

export const Login = () => {
  const router = useRouter();
  const redirectUrl = `${routes.auth.login}/?next=${routes.employers.dashboard}`;

  useEffect(() => {
    router.push(redirectUrl);
  });

  return null;
};

export default Login;
