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
import React, { useCallback, useMemo } from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import isBlank from "src/utils/isBlank";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface PageQueryParam {
  name: string;
  value: number | null | string | string[];
}
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

  /**
   * Update the page's query string, to load a different page number,
   */
  const updatePageQuery = (paramsToUpdate: PageQueryParam[]) => {
    const params = new URLSearchParams(window.location.search);

    paramsToUpdate.forEach(({ name, value }) => {
      if (isBlank(value) || (typeof value !== "number" && value.length === 0)) {
        // Remove param if its value is null, undefined, empty string, or empty array
        params.delete(name);
      } else {
        params.set(name, value.toString());
      }
    });

    const paramsObj: { [key: string]: string } = {};
    for (const [paramKey, paramValue] of Array.from(params.entries())) {
      paramsObj[paramKey] = paramValue;
    }

    // Our withBenefitsApplication component watches the query string and
    // will trigger an API request when it changes.
    appLogic.portalFlow.updateQuery(paramsObj);
  };
  const PaginatedIndexPageWithBenefitsApplications = withBenefitsApplications(
    PaginatedIndexPage,
    apiParams
  );
  const componentSpecificProps = {
    updatePageQuery,
  };

  return (
    <React.Fragment>
      {query.uploadedAbsenceId && (
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
        <PaginatedIndexPageWithBenefitsApplications
          appLogic={appLogic}
          {...componentSpecificProps}
        />
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

interface PaginatedIndexPageProps extends WithBenefitsApplicationsProps {
  updatePageQuery: (params: PageQueryParam[]) => void;
}

const AppCard = (props) => {
  return (
    <ApplicationCard
      appLogic={props.appLogic}
      key={props.application_id}
      // @ts-expect-error PORTAL-1078
      claim={props.claim}
      number={props.number}
    />
  );
};

const PaginatedIndexPage = (props: PaginatedIndexPageProps) => {
  const { appLogic, claims, paginationMeta, updatePageQuery } = props;
  const { t } = useTranslation();

  // Redirect users who do not have claims
  // if (props.claims.isEmpty) {
  //   appLogic.portalFlow.goTo(routes.applications.getReady);
  //   return null;
  // }

  const hasClaims = claims.items.length > 0;
  const hasInProgressClaims = hasClaims && claims.inProgress.length > 0;
  const hasCompletedClaims = hasClaims && claims.completed.length > 0;

  /**
   * Event handler for when a next/prev pagination button is clicked
   */
  const handlePaginationNavigationClick = (pageOffset: number | string) => {
    updatePageQuery([
      {
        name: "page_offset",
        value: pageOffset,
      },
    ]);
  };

  return (
    <React.Fragment>
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
                <AppCard
                  key={claim.application_id}
                  appLogic={appLogic}
                  application_id={claim.application_id}
                  // @ts-expect-error PORTAL-1078
                  claim={claim}
                  number={index}
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
                <AppCard
                  key={claim.application_id}
                  appLogic={appLogic}
                  application_id={claim.application_id}
                  // @ts-expect-error PORTAL-1078
                  claim={claim}
                  number={index}
                />
              );
            })}
          </React.Fragment>
        )}
        {paginationMeta.total_pages > 0 && (
          <PaginationNavigation
            pageOffset={paginationMeta.page_offset}
            totalPages={paginationMeta.total_pages}
            onClick={handlePaginationNavigationClick}
          />
        )}
      </div>
    </React.Fragment>
  );
};

export default withUser(Index);
