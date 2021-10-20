import React, { useEffect } from "react";
import { AppLogic } from "../hooks/useAppLogic";
import Spinner from "../components/Spinner";
import { useTranslation } from "../locales/i18n";
import withUser from "./withUser";

interface ComponentWithClaimsProps {
  appLogic: AppLogic;
}

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 * @param {React.Component} Component - Component to receive claims prop
 * @returns {React.Component} - Component with claims prop
 */
const withBenefitsApplications = (Component) => {
  const ComponentWithClaims = (props: ComponentWithClaimsProps) => {
    const { appLogic } = props;
    const { t } = useTranslation();

    const benefitsApplications =
      appLogic.benefitsApplications.benefitsApplications;
    const shouldLoad = !appLogic.benefitsApplications.hasLoadedAll;

    useEffect(() => {
      if (shouldLoad) {
        appLogic.benefitsApplications.loadAll();
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    if (shouldLoad) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-valuetext={t(
              "components.withBenefitsApplications.loadingLabel"
            )}
          />
        </div>
      );
    }

    return <Component {...props} claims={benefitsApplications} />;
  };
  return withUser(ComponentWithClaims);
};

export default withBenefitsApplications;
