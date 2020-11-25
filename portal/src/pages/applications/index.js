import Alert from "../../components/Alert";
import ApplicationCard from "../../components/ApplicationCard";
import ClaimCollection from "../../models/ClaimCollection";
import DashboardNavigation from "../../components/DashboardNavigation";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

/**
 * List of all applications associated with the authenticated user
 */
const Applications = (props) => {
  const { appLogic, claims, query } = props;
  const { t } = useTranslation();

  const hasClaims = claims.items.length > 0;
  const hasInProgressClaims = hasClaims && claims.inProgress.length > 0;
  const hasCompletedClaims = hasClaims && claims.completed.length > 0;

  return (
    <React.Fragment>
      {query && query.uploadedAbsenceId && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.applications.uploadSuccessHeading")}
          name="upload-success-message"
          state="success"
        >
          {t("pages.applications.uploadSuccessMessage", {
            absence_id: query.uploadedAbsenceId,
          })}
        </Alert>
      )}

      <DashboardNavigation activeHref={appLogic.portalFlow.pathname} />
      <Title hidden={hasClaims}>{t("pages.applications.title")}</Title>

      {!hasClaims && <p>{t("pages.applications.noClaims")}</p>}

      {hasInProgressClaims && (
        <React.Fragment>
          <div className="measure-6">
            <Lead>{t("pages.applications.claimsReflectPortal")}</Lead>
          </div>
          <Heading level="2" size="1">
            {t("pages.applications.inProgressHeading")}
          </Heading>
          {claims.inProgress.map((claim, index) => {
            return (
              <ApplicationCard
                appLogic={appLogic}
                key={claim.application_id}
                claim={claim}
                number={index + 1}
              />
            );
          })}
        </React.Fragment>
      )}

      {hasCompletedClaims && (
        <React.Fragment>
          <Heading level="2" size="1">
            {t("pages.applications.submittedHeading")}
          </Heading>
          {claims.completed.map((claim, index) => {
            return (
              <ApplicationCard
                appLogic={appLogic}
                key={claim.application_id}
                claim={claim}
                number={claims.inProgress.length + index + 1}
              />
            );
          })}
        </React.Fragment>
      )}
    </React.Fragment>
  );
};

Applications.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
  query: PropTypes.shape({
    uploadedAbsenceId: PropTypes.string,
  }),
};

export default withClaims(Applications);
