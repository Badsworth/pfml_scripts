import React, { useEffect } from "react";
import withUser, { WithUserProps } from "./withUser";
import EmployerClaim from "../models/EmployerClaim";
import PageNotFound from "../components/PageNotFound";
import { Spinner } from "../components/core/Spinner";
import { useTranslation } from "react-i18next";

interface QueryForWithEmployerClaim {
  absence_id?: string;
}
export interface WithEmployerClaimProps extends WithUserProps {
  claim: EmployerClaim;
}

/**
 * Higher order component that loads an absence case's data for actions
 * like info requests. This should be used in routes meant for employers.
 */
function withEmployerClaim<T extends WithEmployerClaimProps>(
  Component: React.ComponentType<T>
) {
  const ComponentWithClaim = (
    props: WithUserProps & { query: QueryForWithEmployerClaim }
  ) => {
    const { appLogic, query } = props;
    const { t } = useTranslation();
    const absenceId = query.absence_id;
    const claim =
      appLogic.employers.claim?.fineos_absence_id === absenceId
        ? appLogic.employers.claim
        : null;

    useEffect(() => {
      if (!claim && absenceId) {
        appLogic.employers.loadClaim(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [claim]);

    if (!absenceId) {
      return <PageNotFound />;
    }

    if (!claim) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-label={t("components.withEmployerClaim.loadingLabel")}
          />
        </div>
      );
    }

    return (
      <Component
        {...(props as T & { query: QueryForWithEmployerClaim })}
        claim={claim}
      />
    );
  };

  return withUser(ComponentWithClaim);
}

export default withEmployerClaim;
