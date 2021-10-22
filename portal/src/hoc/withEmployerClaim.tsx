import React, { useEffect } from "react";
import { AppLogic } from "../hooks/useAppLogic";
import { Spinner } from "../components/Spinner";
import User from "../models/User";
import routes from "../routes";
import { useTranslation } from "react-i18next";
import withUser from "./withUser";

interface ComponentWithClaimProps {
  appLogic: AppLogic;
  query: {
    absence_id: string;
  };
  user: User;
}

/**
 * Higher order component that (1) loads a claim if not yet loaded and adds a single claim to the wrapper component
 * based on query parameters, and (2) redirects to Verify Business page if an unverified employer exists.
 * This should be used in routes meant for employers.
 * @param {React.Component} Component - Component to receive claim prop
 * @returns {React.Component} component with claim prop
 */
const withEmployerClaim = (Component) => {
  const ComponentWithClaim = (props: ComponentWithClaimProps) => {
    const { appLogic, query, user } = props;
    const { t } = useTranslation();
    const absenceId = query.absence_id;
    const claim =
      appLogic.employers.claim?.fineos_absence_id === absenceId
        ? appLogic.employers.claim
        : null;

    useEffect(() => {
      if (!claim) {
        appLogic.employers.loadClaim(absenceId);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [claim]);

    useEffect(() => {
      if (claim) {
        const verifiableEmployer = user.getVerifiableEmployerById(
          claim.employer_id
        );

        if (verifiableEmployer) {
          redirectToVerifyPage(verifiableEmployer);
          return;
        }

        const unverifiableEmployer = user.getUnverifiableEmployerById(
          claim.employer_id
        );
        if (unverifiableEmployer) {
          redirectToCannotVerifyPage(unverifiableEmployer);
        }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appLogic.portalFlow, claim, user]);

    const redirectToVerifyPage = (employer) => {
      // the current employer can and should be verified; the page is blocked.
      appLogic.portalFlow.goTo(routes.employers.verifyContributions, {
        employer_id: employer.employer_id,
        next: appLogic.portalFlow.pathWithParams,
      });
    };

    const redirectToCannotVerifyPage = (employer) => {
      // the current employer cannot be verified; the page is blocked.
      appLogic.portalFlow.goTo(routes.employers.cannotVerify, {
        employer_id: employer.employer_id,
      });
    };

    if (!claim && appLogic.appErrors.isEmpty) {
      return (
        <div className="margin-top-8 text-center">
          <Spinner
            aria-valuetext={t("components.withEmployerClaim.loadingLabel")}
          />
        </div>
      );
    } else if (!claim) {
      return null;
    }

    return <Component {...props} claim={claim} />;
  };

  return withUser(ComponentWithClaim);
};

export default withEmployerClaim;
