import withBenefitsApplications, {
  WithBenefitsApplicationsProps,
} from "../../hoc/withBenefitsApplications";
import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import ApplicationCard from "../../components/ApplicationCard";
import BenefitsApplication from "../../models/BenefitsApplication";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/core/Heading";
import Lead from "../../components/core/Lead";
import MfaSetupSuccessAlert from "src/components/MfaSetupSuccessAlert";
import { NullableQueryParams } from "src/utils/routeWithParams";
import PaginationNavigation from "src/components/PaginationNavigation";
import React from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface IndexProps extends WithUserProps {
  query: {
    applicationAssociated?: string;
    uploadedAbsenceId?: string;
    smsMfaConfirmed?: string;
  };
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

  const PaginatedApplicationCardsWithRedirect = withRedirectToGetReadyPage(
    PaginatedApplicationCards,
    pick(query, "smsMfaConfirmed")
  );

  const PaginatedApplicationCardsWithBenefitsApplications =
    withBenefitsApplications(PaginatedApplicationCardsWithRedirect, apiParams);

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
      {query?.applicationAssociated && (
        <Alert className="margin-bottom-3" state="success">
          <p>{t("pages.applications.claimAssociatedSuccessfully")}</p>
        </Alert>
      )}
      {query?.smsMfaConfirmed && <MfaSetupSuccessAlert />}

      <div className="grid-row grid-gap-6">
        <div className="desktop:grid-col margin-bottom-2">
          <Title>{t("pages.applications.title")}</Title>
          <PaginatedApplicationCardsWithBenefitsApplications
            appLogic={appLogic}
          />
        </div>
        <div className="desktop:grid-col-auto">
          <Heading level="2" className="usa-sr-only">
            {t("pages.applications.createApplicationHeading")}
          </Heading>

          <ButtonLink
            className="margin-bottom-2"
            href={appLogic.portalFlow.getNextPageRoute("NEW_APPLICATION")}
            variation="outline"
          >
            {t("pages.applications.getReadyLink")}
          </ButtonLink>

          <br />

          {isFeatureEnabled("channelSwitching") && (
            <ButtonLink
              href={appLogic.portalFlow.getNextPageRoute("FIND_APPLICATION")}
              variation="unstyled"
            >
              {t("pages.applications.findLink")}
            </ButtonLink>
          )}
        </div>
      </div>
    </React.Fragment>
  );
};

// Redirect users who don't yet have any claims to the Get Ready page
function withRedirectToGetReadyPage<T extends WithBenefitsApplicationsProps>(
  Component: React.ComponentType<T>,
  nextPageParams: NullableQueryParams
) {
  const ComponentWithRedirect = (props: WithBenefitsApplicationsProps) => {
    const { appLogic, claims } = props;
    const { isLoadingClaims } = appLogic.benefitsApplications;

    // Redirect users who do not have claims
    if (isLoadingClaims === false && claims.isEmpty) {
      appLogic.portalFlow.goTo(routes.applications.getReady, nextPageParams);
      return null;
    }

    return <Component {...(props as T)} />;
  };

  return ComponentWithRedirect;
}

const PaginatedApplicationCards = (props: WithBenefitsApplicationsProps) => {
  const { appLogic, claims, paginationMeta } = props;
  const { t } = useTranslation();
  const inProgressClaims = BenefitsApplication.inProgress(claims.items);
  const completedClaims = BenefitsApplication.completed(claims.items);

  /**
   * Update the page's query string, to load a different page number,
   * Our withBenefitsApplication component watches the query string and
   * will trigger an API request when it changes.
   */
  const updatePageQuery = (pageNumber: number | string) => {
    appLogic.portalFlow.updateQuery({ page_offset: String(pageNumber) });
  };

  /**
   * Event handler for when a next/prev pagination button is clicked
   */
  const handlePaginationNavigationClick = (pageOffset: number) => {
    updatePageQuery(pageOffset);
  };

  return (
    <React.Fragment>
      {inProgressClaims.length > 0 && (
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
          {inProgressClaims.map((claim, index) => {
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

      {completedClaims.length > 0 && (
        <React.Fragment>
          <Heading level="2">
            {t("pages.applications.submittedHeading")}
          </Heading>
          {completedClaims.map((claim, index) => {
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
