import React, { useEffect } from "react";
import { AppLogic } from "../hooks/useAppLogic";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/Spinner";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";
import withUser from "./withUser";

interface ComponentWithClaimProps {
  appLogic: AppLogic;
  query: {
    claim_id?: string;
  };
}

/**
 * Higher order component that loads a claim if not yet loaded,
 * then adds a single claim to the wrapped component based on query parameters
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} - Component with claim prop
 */
// @ts-expect-error TODO (PORTAL-966) Fix HOC typing
const withBenefitsApplication = (Component) => {
  const ComponentWithClaim = (props: ComponentWithClaimProps) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();

    const application_id = query.claim_id;
    const benefitsApplications =
      appLogic.benefitsApplications.benefitsApplications;
    const claim = application_id
      ? benefitsApplications.getItem(application_id)
      : undefined;
    const shouldLoad = !!(
      application_id &&
      !appLogic.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings(
        application_id
      )
    );

    useEffect(() => {
      if (shouldLoad) {
        appLogic.benefitsApplications.load(application_id);
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [shouldLoad]);

    useEffect(() => {
      const { goTo, pathname } = appLogic.portalFlow;
      if (
        claim?.isCompleted &&
        (pathname === routes.applications.checklist ||
          pathname === routes.applications.review)
      ) {
        goTo(routes.applications.index);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [claim?.application_id]);

    if (!application_id) {
      return <PageNotFound />;
    }

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

    return <Component {...props} claim={claim} />;
  };

  return withUser(ComponentWithClaim);
};

export default withBenefitsApplication;
