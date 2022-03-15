import React, { useEffect } from "react";
import withBenefitsApplications, {
  WithBenefitsApplicationsProps,
} from "../../hoc/withBenefitsApplications";
import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import ApplicationCard from "../../components/ApplicationCard";
import ButtonLink from "../../components/ButtonLink";
import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import Lead from "../../components/core/Lead";
import Link from "next/link";
import MfaSetupSuccessAlert from "src/components/MfaSetupSuccessAlert";
import { NullableQueryParams } from "src/utils/routeWithParams";
import PaginationNavigation from "src/components/PaginationNavigation";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import formatDate from "src/utils/formatDate";
import { isFeatureEnabled } from "../../services/featureFlags";
import { pick } from "lodash";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface IndexProps extends WithUserProps {
  query: {
    applicationAssociated?: string;
    page_offset?: string;
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

  const PaginatedApplicationCardsWithRedirect = withRedirectToGetReadyPage(
    PaginatedApplicationCards,
    pick(query, "smsMfaConfirmed")
  );

  const PaginatedApplicationCardsWithBenefitsApplications =
    withBenefitsApplications(PaginatedApplicationCardsWithRedirect, {
      page_offset: query?.page_offset,
    });

  const applicationCardProps = { appLogic, query };

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
      {query?.smsMfaConfirmed && <MfaSetupSuccessAlert />}

      <div className="grid-row grid-gap-6">
        <div className="desktop:grid-col margin-bottom-2">
          <Title>{t("pages.applications.title")}</Title>
          <ApplicationApprovalsInformation {...props} />
          <PaginatedApplicationCardsWithBenefitsApplications
            {...applicationCardProps}
          />
        </div>
        <div className="desktop:grid-col-4">
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
            <Details label={t("pages.applications.startByPhoneLabel")}>
              <p>{t("pages.applications.startByPhoneDescription")}</p>
              <Link
                href={appLogic.portalFlow.getNextPageRoute(
                  "IMPORT_APPLICATION"
                )}
              >
                <a className="display-inline-block margin-bottom-5">
                  {t("pages.applications.addApplication")}
                </a>
              </Link>
            </Details>
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

const ApplicationApprovalsInformation = (props: WithUserProps) => {
  const { appLogic } = props;
  const { loadBenefitYears, getCurrentBenefitYear } = appLogic.benefitYears;

  useEffect(() => {
    loadBenefitYears();
  }, [loadBenefitYears]);
  const currentBenefitYear = getCurrentBenefitYear();

  if (!isFeatureEnabled("splitClaimsAcrossBY") || !currentBenefitYear) {
    return (
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
    );
  }

  return (
    <React.Fragment>
      <p>
        <Trans
          i18nKey="pages.applications.your_benefit_year"
          values={{
            startDate: formatDate(
              currentBenefitYear.benefit_year_start_date
            ).short(),
            endDate: formatDate(
              currentBenefitYear.benefit_year_end_date
            ).short(),
          }}
          components={{
            "benefit-year-guide-link": (
              <a
                href={routes.external.massgov.benefitsGuide_benefitYears}
                rel="noopener noreferrer"
                target="_blank"
              />
            ),
          }}
        />
      </p>
      <p>
        <Trans
          i18nKey="pages.applications.can_submit_application_across_benefit_year"
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
      </p>
    </React.Fragment>
  );
};

interface QueryForApplicationAssociated {
  applicationAssociated?: string;
}

const PaginatedApplicationCards = (
  props: WithBenefitsApplicationsProps & {
    query: QueryForApplicationAssociated;
  }
) => {
  const { appLogic, claims, paginationMeta, query } = props;

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

  const associatedId = query?.applicationAssociated || "";

  if (claims.isEmpty) return null;

  return (
    <React.Fragment>
      {claims.items.map((claim) => {
        return (
          <ApplicationCard
            key={claim.application_id}
            appLogic={appLogic}
            claim={claim}
            user={props.user}
            successfullyImported={associatedId === claim.fineos_absence_id}
          />
        );
      })}

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
