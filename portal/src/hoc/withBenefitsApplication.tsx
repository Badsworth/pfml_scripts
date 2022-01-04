import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import BenefitsApplication from "../models/BenefitsApplication";
import PageNotFound from "../components/PageNotFound";
import Spinner from "../components/core/Spinner";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export interface QueryForWithBenefitsApplication {
  claim_id?: string;
}

export interface WithBenefitsApplicationProps extends WithUserProps {
  claim: BenefitsApplication;
}

/**
 * Higher order component that loads a claim if not yet loaded,
 * then adds a single claim to the wrapped component based on query parameters
 */
function withBenefitsApplication<T extends WithBenefitsApplicationProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithClaim = (
    props: WithUserProps & { query: QueryForWithBenefitsApplication }
  ) => {
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

    if (shouldLoad) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-label={t("components.withBenefitsApplications.loadingLabel")}
          />
        </div>
      );
    }

    if (!application_id || !claim) {
      return <PageNotFound />;
    }

    return (
      <Component
        {...(props as T & { query: QueryForWithBenefitsApplication })}
        claim={claim}
      />
    );
  };

  return withUser(ComponentWithClaim);
}

export default withBenefitsApplication;
