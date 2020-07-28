import React, { useEffect } from "react";
import ApplicationCard from "../components/ApplicationCard";
import DashboardNavigation from "../components/DashboardNavigation";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import Spinner from "../components/Spinner";
import Title from "../components/Title";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * List of all applications associated with the authenticated user
 */
const Applications = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();
  const router = useRouter();

  useEffect(() => {
    appLogic.loadClaims();
  });

  const claimsLoaded = !!appLogic.claims;
  const hasClaims = claimsLoaded && appLogic.claims.items.length > 0;
  const hasInProgressClaims =
    hasClaims && appLogic.claims.inProgress.length > 0;
  const hasSubmittedClaims = hasClaims && appLogic.claims.submitted.length > 0;

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={router.route} />
      <Title hidden={hasClaims}>{t("pages.applications.title")}</Title>

      {claimsLoaded && !hasClaims && <p>{t("pages.applications.noClaims")}</p>}

      {!claimsLoaded && (
        <div className="margin-top-8 text-center">
          <Spinner aria-valuetext={t("components.spinner.label")} />
        </div>
      )}

      {hasInProgressClaims && (
        <React.Fragment>
          <Heading level="2" size="1">
            {t("pages.applications.inProgressHeading")}
          </Heading>
          {appLogic.claims.inProgress.map((claim, index) => (
            <ApplicationCard
              key={claim.application_id}
              claim={claim}
              number={index + 1}
            />
          ))}
        </React.Fragment>
      )}

      {hasSubmittedClaims && (
        <React.Fragment>
          <Heading level="2" size="1">
            {t("pages.applications.submittedHeading")}
          </Heading>
          {appLogic.claims.submitted.map((claim, index) => (
            <ApplicationCard
              key={claim.application_id}
              claim={claim}
              number={appLogic.claims.inProgress.length + index + 1}
            />
          ))}
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

Applications.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Applications;
