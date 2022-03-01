import React, { useEffect } from "react";

import { AppLogic } from "../hooks/useAppLogic";
import Spinner from "../components/core/Spinner";
import User from "../models/User";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export interface WithUserProps extends PageProps {
  user: User;
}

export interface PageProps {
  appLogic: AppLogic;
}

/**
 * Higher order component that provides the current logged in Portal user object
 * to the wrapped component.
 * If the user is not logged in, redirect the user to the login page.
 * If the user is not loaded, load the user.
 * If the logged in user has not consented to the data agreement, redirect the user
 * to the consent to data sharing page.
 */
function withUser<T extends WithUserProps>(Component: React.ComponentType<T>) {
  const ComponentWithUser = (props: PageProps) => {
    const { appLogic } = props;
    const { auth, portalFlow, users } = appLogic;
    const { t } = useTranslation();

    useEffect(() => {
      // requireLogin is an async function, but we don't actually care about it completing
      // before we move on to the rest of this effect. The reason is because if auth.isLoggedIn
      // isn't yet defined, then it'll be defined on a subsequent render, so we won't be able to
      // use the value on this render even if we used `await`
      auth.requireLogin();
      if (auth.isLoggedIn && !appLogic.errors.length) {
        users.loadUser();
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [auth.isLoggedIn, !appLogic.errors.length]);

    useEffect(() => {
      if (users.user) {
        users.requireUserConsentToDataAgreement();
        users.requireUserRole();
      }

      // Only trigger this effect when the user is set/updated
      // or when the user attempts to navigate to another page
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [users.user, portalFlow.pathname]);

    if (!users.user)
      return (
        <div className="margin-top-8 text-center">
          <Spinner aria-label={t("components.withUser.loadingLabel")} />
        </div>
      );

    if (
      !users.user.consented_to_data_sharing &&
      portalFlow.pathname !== routes.user.consentToDataSharing
    )
      return null;

    return <Component {...(props as T)} user={users.user} />;
  };

  return ComponentWithUser;
}

export default withUser;
