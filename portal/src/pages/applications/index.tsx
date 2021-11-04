import Alert from "../../components/Alert";
import { AppLogic } from "../../hooks/useAppLogic";
import ApplicationCardV1 from "../../components/ApplicationCard";
import ApplicationCardV2 from "../../components/ApplicationCardV2";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import Lead from "../../components/Lead";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplications from "../../hoc/withBenefitsApplications";

interface IndexProps {
  appLogic: AppLogic;
  claims: BenefitsApplicationCollection;
  query?: {
    uploadedAbsenceId?: string;
  };
}

/**
 * List of all applications associated with the authenticated user
 */
export const Index = (props: IndexProps) => {
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
        <Alert
          className="margin-bottom-3"
          heading={t("pages.applications.uploadSuccessHeading")}
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

          {hasInProgressClaims && (
            <React.Fragment>
              <div className="measure-6">
                <Lead>
                  <Trans
                    i18nKey="pages.applications.claimsApprovalProcess"
                    components={{
                      "approval-process-link": (
                        <a
                          href={routes.external.massgov.approvalTimeline}
                          rel="noopener noreferrer"
                          target="_blank"
                        />
                      ),
                    }}
                  />
                </Lead>
              </div>
              <Heading level="2">
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
              <Heading level="2">
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

/**
 * Allowing claimantShowStatusPage feature flag
 */
// @ts-expect-error TODO (PORTAL-287) Remove v1 application card
function ApplicationCard(props) {
  return isFeatureEnabled("claimantShowStatusPage") ? (
    <ApplicationCardV2 {...props} />
  ) : (
    <ApplicationCardV1 {...props} />
  );
}

export default withBenefitsApplications(Index);
