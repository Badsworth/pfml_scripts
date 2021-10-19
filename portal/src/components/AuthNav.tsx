import Button from "./Button";
import ButtonLink from "./ButtonLink";
import React from "react";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface AuthNavProps {
  user?: {
    email_address?: string;
  };
  onLogout: (...args: any[]) => any;
}

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = (props: AuthNavProps) => {
  const { t } = useTranslation();
  const user = props.user || {};
  const isLoggedIn = !!user.email_address;

  const back = (
    <ButtonLink
      href={routes.external.massgov.index}
      className="width-auto"
      inversed
      variation="unstyled"
    >
      {t("pages.authCreateAccount.backButton")}
    </ButtonLink>
  );

  const login = (
    <ButtonLink
      href={routes.auth.login}
      className="width-auto"
      inversed
      variation="unstyled"
    >
      {t("pages.authCreateAccount.logInFooterLink")}
    </ButtonLink>
  );

  const logout = (
    <React.Fragment>
      <span
        className="display-inline-block margin-right-1"
        data-testid="email_address"
      >
        {user.email_address}
      </span>
      <Button
        className="width-auto"
        inversed
        onClick={props.onLogout}
        variation="unstyled"
      >
        {t("components.authNav.logOutButton")}
      </Button>
    </React.Fragment>
  );

  return (
    <div className="flex-fill margin-y-1">
      <div className="grid-row grid-gap">
        {!isLoggedIn && <div className="grid-col">{back}</div>}
        <div className="grid-col text-right">{isLoggedIn ? logout : login}</div>
      </div>
    </div>
  );
};

export default AuthNav;
