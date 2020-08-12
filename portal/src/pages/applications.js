import ApplicationCard from "../components/ApplicationCard";
import ClaimCollection from "../models/ClaimCollection";
import DashboardNavigation from "../components/DashboardNavigation";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";
import withClaims from "../hoc/withClaims";

/**
 * List of all applications associated with the authenticated user
 */
const Applications = (props) => {
  const { claims } = props;
  const { t } = useTranslation();
  const router = useRouter();

  const hasClaims = claims.items.length > 0;
  const hasInProgressClaims = hasClaims && claims.inProgress.length > 0;
  const hasSubmittedClaims = hasClaims && claims.submitted.length > 0;

  return (
    <React.Fragment>
      <DashboardNavigation activeHref={router.route} />
      <Title hidden={hasClaims}>{t("pages.applications.title")}</Title>

      {!hasClaims && <p>{t("pages.applications.noClaims")}</p>}

      {hasInProgressClaims && (
        <React.Fragment>
          <Heading level="2" size="1">
            {t("pages.applications.inProgressHeading")}
          </Heading>
          {claims.inProgress.map((claim, index) => (
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
          {claims.submitted.map((claim, index) => (
            <ApplicationCard
              key={claim.application_id}
              claim={claim}
              number={claims.inProgress.length + index + 1}
            />
          ))}
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

Applications.propTypes = {
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
};

export default withClaims(Applications);
