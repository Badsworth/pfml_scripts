import React, { FormEvent, useRef } from "react";
import SortDropdown, {
  PageQueryParam,
} from "../../features/employer-dashboard/SortDropdown";
import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import Button from "../../components/core/Button";
import DeprecatedPaginatedClaimsTable from "../../features/employer-dashboard/DeprecatedPaginatedClaimsTable";
import Details from "../../components/core/Details";
import EmployerNavigationTabs from "../../components/EmployerNavigationTabs";
import Filters from "../../features/employer-dashboard/Filters";
import { GetClaimsParams } from "../../api/ClaimsApi";
import InputText from "../../components/core/InputText";
import PaginatedClaimsTable from "../../features/employer-dashboard/PaginatedClaimsTable";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import { get } from "lodash";
import isBlank from "../../utils/isBlank";
import { isFeatureEnabled } from "../../services/featureFlags";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const Dashboard = (
  props: WithUserProps & { query: GetClaimsParams }
) => {
  const { t } = useTranslation();
  const introElementRef = useRef<HTMLElement>(null);
  const showMultiLeaveDash = isFeatureEnabled(
    "employerShowMultiLeaveDashboard"
  );
  const apiParams = {
    // Default the dashboard to show claims requiring action first
    order_by: showMultiLeaveDash ? "latest_follow_up_date" : "absence_status",
    order_direction: showMultiLeaveDash ? "descending" : "ascending",
    page_offset: 1,
    ...props.query,
  } as const;

  /**
   * Update the page's query string, to load a different page number,
   * or change the filter/sort of the loaded claims. The name/value
   * are merged with the existing query string.
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

    // Our withClaims component watches the query string and
    // will trigger an API request when it changes.
    props.appLogic.portalFlow.updateQuery(paramsObj);

    // Scroll user back to top of the table actions
    if (introElementRef.current) introElementRef.current.scrollIntoView();
  };

  const PaginatedClaimsTableWithClaims = showMultiLeaveDash
    ? withClaims(PaginatedClaimsTable, apiParams)
    : withClaims(DeprecatedPaginatedClaimsTable, apiParams);
  const claimsTableProps = {
    updatePageQuery,
    getNextPageRoute: props.appLogic.portalFlow.getNextPageRoute,
    hasOnlyUnverifiedEmployers: props.user.hasOnlyUnverifiedEmployers,
    showEmployer: props.user.user_leave_administrators.length > 1,
    sort: (
      <SortDropdown
        order_by={apiParams.order_by}
        order_direction={apiParams.order_direction}
        updatePageQuery={updatePageQuery}
      />
    ),
  };

  return (
    <React.Fragment>
      <EmployerNavigationTabs activePath={props.appLogic.portalFlow.pathname} />
      <Title>{t("pages.employersDashboard.title")}</Title>

      <div className="measure-6">
        {props.user.hasVerifiableEmployer && (
          <Alert
            state="warning"
            heading={t("pages.employersDashboard.verificationTitle")}
          >
            <p>
              <Trans
                i18nKey="pages.employersDashboard.verificationBody"
                components={{
                  "your-organizations-link": (
                    <a
                      href={props.appLogic.portalFlow.getNextPageRoute(
                        "VERIFY_ORG"
                      )}
                    />
                  ),
                }}
              />
            </p>
          </Alert>
        )}
      </div>

      {!showMultiLeaveDash && (
        <section className="margin-bottom-4 margin-top-2">
          <Details
            label={t("pages.employersDashboard.statusDescriptionsLabel")}
          >
            <ul className="usa-list">
              <li>
                <Trans i18nKey="pages.employersDashboard.statusDescription_reviewBy" />
              </li>
              <li>
                <Trans i18nKey="pages.employersDashboard.statusDescription_noAction" />
              </li>
              <li>
                <Trans i18nKey="pages.employersDashboard.statusDescription_denied" />
              </li>
              <li>
                <Trans i18nKey="pages.employersDashboard.statusDescription_approved" />
              </li>
              <li>
                <Trans i18nKey="pages.employersDashboard.statusDescription_closed" />
              </li>
            </ul>
          </Details>
        </section>
      )}
      <section ref={introElementRef} className="margin-top-2">
        <Search
          initialValue={get(apiParams, "search", "")}
          updatePageQuery={updatePageQuery}
        />
      </section>
      <Filters
        params={apiParams}
        updatePageQuery={updatePageQuery}
        verifiedEmployers={props.user.verifiedEmployers}
      />
      <PaginatedClaimsTableWithClaims
        appLogic={props.appLogic}
        {...claimsTableProps}
      />
    </React.Fragment>
  );
};

interface SearchProps {
  /** The current search value */
  initialValue?: string;
  updatePageQuery: (params: PageQueryParam[]) => void;
}

const Search = (props: SearchProps) => {
  const { initialValue, updatePageQuery } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({ search: initialValue });
  const getFunctionalInputProps = useFunctionalInputProps({
    formState,
    updateFields,
  });

  const handleSubmit = (evt: FormEvent) => {
    evt.preventDefault();

    updatePageQuery([
      {
        name: "search",
        value: get(formState, "search", ""),
      },
      {
        // Reset the page to 1 since search affects what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  return (
    <div className="bg-base-lightest padding-x-3 padding-top-1px padding-bottom-2">
      <form className="usa-form grid-row" onSubmit={handleSubmit}>
        <div className="grid-col-fill tablet:grid-col-auto">
          <InputText
            {...getFunctionalInputProps("search")}
            label={t("pages.employersDashboard.searchLabel")}
            smallLabel
          />
        </div>
        <div className="grid-col-auto flex-align-self-end">
          <Button className="width-auto" type="submit">
            {t("pages.employersDashboard.searchSubmit")}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default withUser(Dashboard);
