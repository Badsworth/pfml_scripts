import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
import Spinner from "../components/core/Spinner";
import { useTranslation } from "../locales/i18n";

export interface WithBenefitsApplicationsProps extends WithUserProps {
  claims: BenefitsApplicationCollection;
}

/**
 * Higher order component that provides the current user's claims to the wrapped component.
 * The higher order component also loads the claims if they have not already been loaded.
 */
function withBenefitsApplications<T extends WithBenefitsApplicationsProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithClaims = (props: WithUserProps) => {
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

    return <Component {...(props as T)} claims={benefitsApplications} />;
  };
  return withUser(ComponentWithClaims);
}

export default withBenefitsApplications;
