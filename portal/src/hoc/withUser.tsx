import React, { useEffect } from "react";
import { AppLogic } from "../hooks/useAppLogic";
import Spinner from "../components/Spinner";
import User from "../models/User";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

interface ComponentWithUserProps {
  appLogic: AppLogic;
  user: User;
}

/**
 * Higher order component that provides the current logged in Portal user object
 * to the wrapped component.
 * If the user is not logged in, redirect the user to the login page.
 * If the user is not loaded, load the user.
 * If the logged in user has not consented to the data agreement, redirect the user
 * to the consent to data sharing page.
 * @param {React.Component} Component - Component to receive user prop
 * @returns {React.Component} - Component with user prop
 */
// @ts-expect-error TODO (PORTAL-966) Fix HOC typing
const withUser = (Component) => {
  const ComponentWithUser = (props: ComponentWithUserProps) => {
    const { appLogic } = props;
    const { auth, portalFlow, users } = appLogic;
    const { t } = useTranslation();

    useEffect(() => {
      // requireLogin is an async function, but we don't actually care about it completing
      // before we move on to the rest of this effect. The reason is because if auth.isLoggedIn
      // isn't yet defined, then it'll be defined on a subsequent render, so we won't be able to
      // use the value on this render even if we used `await`
      auth.requireLogin();
      if (auth.isLoggedIn && appLogic.appErrors.isEmpty) {
        users.loadUser();
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [auth.isLoggedIn, appLogic.appErrors.isEmpty]);

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
          <Spinner aria-valuetext={t("components.withUser.loadingLabel")} />
        </div>
      );

    if (
      !users.user.consented_to_data_sharing &&
      portalFlow.pathname !== routes.user.consentToDataSharing
    )
      return null;

    return <Component {...props} user={users.user} />;
  };

  return ComponentWithUser;
};

export default withUser;
