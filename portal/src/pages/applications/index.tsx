import withBenefitsApplications, {
  WithBenefitsApplicationsProps,
} from "../../hoc/withBenefitsApplications";
import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import ApplicationCard from "../../components/ApplicationCard";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/core/Heading";
import Lead from "../../components/core/Lead";
import PaginationNavigation from "src/components/PaginationNavigation";
import React from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface IndexProps extends WithUserProps {
  query: { uploadedAbsenceId?: string };
}

/**
 * List of all applications associated with the authenticated user
 */
export const Index = (props: IndexProps) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();
  const apiParams = {
    order_direction: "ascending",
    ...query,
  } as const;

  const PaginatedApplicationCardsWithBenefitsApplications =
    withBenefitsApplications(PaginatedApplicationCards, apiParams);

  return (
    <React.Fragment>
      {query?.uploadedAbsenceId && (
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
          <PaginatedApplicationCardsWithBenefitsApplications
            appLogic={appLogic}
          />
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

const PaginatedApplicationCards = (props: WithBenefitsApplicationsProps) => {
  const { appLogic, claims, paginationMeta } = props;
  const { t } = useTranslation();

  /**
   * Update the page's query string, to load a different page number,
   * Our withBenefitsApplication component watches the query string and
   * will trigger an API request when it changes.
   */
  const updatePageQuery = (pageNumber: number | string) => {
    appLogic.portalFlow.updateQuery({ page_offset: String(pageNumber) });
  };

  const hasClaims = !claims.isEmpty;
  const hasInProgressClaims = hasClaims && claims.inProgress.length > 0;
  const hasCompletedClaims = hasClaims && claims.completed.length > 0;

  const { isLoadingClaims } = appLogic.benefitsApplications;

  /**
   * Event handler for when a next/prev pagination button is clicked
   */
  const handlePaginationNavigationClick = (pageOffset: number) => {
    updatePageQuery(pageOffset);
  };

  // Redirect users who do not have claims
  if (isLoadingClaims === false && claims.isEmpty) {
    appLogic.portalFlow.goTo(routes.applications.getReady);
    return null;
  }

  return (
    <React.Fragment>
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
                key={claim.application_id}
                appLogic={appLogic}
                claim={claim}
                number={index + 1}
                user={props.user}
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
                key={claim.application_id}
                claim={claim}
                number={index}
                appLogic={props.appLogic}
                user={props.user}
              />
            );
          })}
        </React.Fragment>
      )}
      {paginationMeta.total_pages > 1 && (
        <PaginationNavigation
          pageOffset={paginationMeta.page_offset}
          totalPages={paginationMeta.total_pages}
          onClick={handlePaginationNavigationClick}
        />
      )}
    </React.Fragment>
  );
};

export default withUser(Index);
