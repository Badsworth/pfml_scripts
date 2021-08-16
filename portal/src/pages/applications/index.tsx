import Alert from "../../components/Alert";
import ApplicationCard from "../../components/ApplicationCard";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplications from "../../hoc/withBenefitsApplications";

/**
 * List of all applications associated with the authenticated user
 */
export const Index = (props) => {
  const { appLogic, claims, query } = props;
  const { t } = useTranslation();

  // Redirect users who do not have claims
  if (props.claims.isEmpty) {
    appLogic.portalFlow.goTo(routes.applications.getReady);
    return null;
  }

  const hasClaims = claims.items.length > 0;
  const hasInProgressClaims = hasClaims && claims.inProgress.length > 0;
  const hasCompletedClaims = hasClaims && claims.completed.length > 0;

  return (
    <React.Fragment>
      {query && query.uploadedAbsenceId && (
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: string; className: string; headi... Remove this comment to see the full error message
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

      <div className="grid-row grid-gap-6">
        <div className="desktop:grid-col">
          <Title>{t("pages.applications.title")}</Title>

          {!hasClaims && <p>{t("pages.applications.noClaims")}</p>}

          {hasInProgressClaims && (
            <React.Fragment>
              <div className="measure-6">
                <Lead>{t("pages.applications.claimsReflectPortal")}</Lead>
              </div>
              <Heading level="2">
                {t("pages.applications.inProgressHeading")}
              </Heading>
              {claims.inProgress.map((claim, index) => {
                return (
                  <ApplicationCard
                    appLogic={appLogic}
                    key={claim.application_id}
                    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ appLogic: any; key: any; claim: any; numbe... Remove this comment to see the full error message
                    claim={claim}
                    number={index + 1}
                  />
                );
              })}
            </React.Fragment>
          )}

          {hasCompletedClaims && (
            <React.Fragment>
              <Heading level="2">
                {t("pages.applications.submittedHeading")}
              </Heading>
              {claims.completed.map((claim, index) => {
                return (
                  <ApplicationCard
                    appLogic={appLogic}
                    key={claim.application_id}
                    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ appLogic: any; key: any; claim: any; numbe... Remove this comment to see the full error message
                    claim={claim}
                    number={claims.inProgress.length + index + 1}
                  />
                );
              })}
            </React.Fragment>
          )}
        </div>
        <div className="desktop:grid-col-auto">
          <Heading level="2" className="usa-sr-only">
            {t("pages.applications.createApplicationHeading")}
          </Heading>

          <ButtonLink href={routes.applications.getReady} variation="outline">
            {t("pages.applications.getReadyLink")}
          </ButtonLink>
        </div>
      </div>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
  }).isRequired,
  claims: PropTypes.instanceOf(BenefitsApplicationCollection).isRequired,
  query: PropTypes.shape({
    uploadedAbsenceId: PropTypes.string,
  }),
};

export default withBenefitsApplications(Index);
