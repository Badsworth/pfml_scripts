import Button from "./core/Button";
import ButtonLink from "./ButtonLink";
import Icon from "./core/Icon";
import React from "react";
import User from "src/models/User";
import { isFeatureEnabled } from "src/services/featureFlags";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface AuthNavProps {
  user?: User;
  onLogout: React.MouseEventHandler<HTMLButtonElement>;
}

/**
 * Displays auth links and info about the user if they're logged in
 */
const AuthNav = (props: AuthNavProps) => {
  const { t } = useTranslation();
  const isLoggedIn = !!props.user?.email_address;
  const showSettings =
    isFeatureEnabled("claimantShowMFA") &&
    !props.user?.hasEmployerRole &&
    props.user?.consented_to_data_sharing;

  const back = (
    <ButtonLink
      href={routes.external.massgov.paidLeave}
      className="width-auto"
      inversed
      variation="unstyled"
    >
      {t("pages.authCreateAccount.backButton")}
    </ButtonLink>
  );

  const settings = (
    <ButtonLink
      variation="unstyled"
      inversed
      className="width-auto"
      href={routes.user.settings}
    >
      <Icon
        name="account_circle"
        className="margin-right-05 position-relative top-1"
        size={3}
      />
      {t("components.header.settingsLinkText")}
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
      {!showSettings && (
        <span className="display-inline-block" data-testid="email_address">
          {props.user?.email_address}
        </span>
      )}
      {showSettings && settings}
      <Button
        className="width-auto margin-left-2"
        inversed
        onClick={props.onLogout}
        variation="unstyled"
      >
        {t("components.authNav.logOutButton")}
      </Button>
    </React.Fragment>
  );

  return (
    <div className="flex-fill margin-y-1 margin-left-2">
      <div className="grid-row grid-gap">
        {!isLoggedIn && <div className="grid-col">{back}</div>}
        <div className="grid-col text-right">{isLoggedIn ? logout : login}</div>
      </div>
    </div>
  );
};

export default AuthNav;
