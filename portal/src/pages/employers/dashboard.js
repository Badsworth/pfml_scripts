import { find, get, pick } from "lodash";
import { AbsenceCaseStatus } from "../../models/Claim";
import AbsenceCaseStatusTag from "../../components/AbsenceCaseStatusTag";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import ClaimCollection from "../../models/ClaimCollection";
import Details from "../../components/Details";
import Dropdown from "../../components/Dropdown";
import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import Icon from "../../components/Icon";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import Link from "next/link";
import PaginationMeta from "../../models/PaginationMeta";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import PropTypes from "prop-types";
import React from "react";
import Table from "../../components/Table";
import Title from "../../components/Title";
import TooltipIcon from "../../components/TooltipIcon";
import { Trans } from "react-i18next";
import User from "../../models/User";
import classnames from "classnames";
import formatDateRange from "../../utils/formatDateRange";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const Dashboard = (props) => {
  const { appLogic, paginationMeta, user } = props;
  const { t } = useTranslation();

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
  const hasVerifiableEmployer = user.hasVerifiableEmployer;

  const tableColumnVisibility = {
    employee_name: true,
    fineos_absence_id: true,
    employer_dba: user.user_leave_administrators.length > 1,
    employer_fein: true,
    created_at: true,
    status: true,
  };
  /**
   * Columns rendered in the table.
   * Used for rendering header labels and the field(s) in each column. These
   * mostly mirror the name of the fields rendered, but not exactly
   * since some columns might require multiple fields.
   * @type {string[]}
   */
  const tableColumnKeys = Object.entries(tableColumnVisibility)
    .filter(([columnKey, isVisible]) => isVisible)
    .map(([columnKey, isVisible]) => columnKey);

  /**
   * Update the page's query string, to load a different page number,
   * or change the filter/sort of the loaded claims. The name/value
   * are merged with the existing query string.
   * @param {Array<{ name: string, value: number|string }>} paramsToUpdate
   */
  const updatePageQuery = (paramsToUpdate) => {
    const params = new URLSearchParams(window.location.search);

    paramsToUpdate.forEach(({ name, value }) => {
      if (!value) {
        params.delete(name);
      } else {
        params.set(name, value);
      }
    });

    const paramsObj = {};
    for (const [paramKey, paramValue] of params.entries()) {
      paramsObj[paramKey] = paramValue;
    }

    // Our withClaims component watches the query string and
    // will trigger an API request when it changes.
    appLogic.portalFlow.updateQuery(paramsObj);
  };

  /**
   * Event handler for when a next/prev pagination button is clicked
   * @param {number|string} pageOffset - Page number to load
   */
  const handlePaginationNavigationClick = (pageOffset) => {
    updatePageQuery([
      {
        name: "page_offset",
        value: pageOffset,
      },
    ]);
  };

  return (
    <React.Fragment>
      <EmployerNavigationTabs activePath={appLogic.portalFlow.pathname} />
      <Title>{t("pages.employersDashboard.title")}</Title>

      <div className="measure-6">
        {hasVerifiableEmployer && (
          <Alert
            state="warning"
            heading={t("pages.employersDashboard.verificationTitle")}
          >
            <p>
              <Trans
                i18nKey="pages.employersDashboard.verificationBody"
                components={{
                  "your-organizations-link": (
                    <a href={routes.employers.organizations} />
                  ),
                }}
              />
            </p>
          </Alert>
        )}

        <DashboardInfoAlert user={user} />
      </div>

      <section className="margin-bottom-4">
        <p className="margin-y-2">
          {t("pages.employersDashboard.instructions")}
        </p>
        <Details label={t("pages.employersDashboard.statusDescriptionsLabel")}>
          <ul className="usa-list">
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_none" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_approved" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_closed" />
            </li>
            <li>
              <Trans i18nKey="pages.employersDashboard.statusDescription_denied" />
            </li>
          </ul>
        </Details>
      </section>

      <Search
        initialValue={get(props.activeFilters, "search", "")}
        updatePageQuery={updatePageQuery}
      />
      <Filters
        activeFilters={props.activeFilters}
        showFilters={props.query["show-filters"] === "true"}
        updatePageQuery={updatePageQuery}
        user={user}
      />

      {paginationMeta.total_records > 0 && (
        <PaginationSummary
          pageOffset={paginationMeta.page_offset}
          pageSize={paginationMeta.page_size}
          totalRecords={paginationMeta.total_records}
        />
      )}
      <Table className="width-full tablet:width-auto" responsive scrollable>
        <thead>
          <tr>
            {tableColumnKeys.map((columnKey) => (
              <th key={columnKey} scope="col">
                {t("pages.employersDashboard.tableColHeading", {
                  context: columnKey,
                })}
                {columnKey === "created_at" && (
                  <TooltipIcon position="bottom">
                    {t("pages.employersDashboard.startDateTooltip")}
                  </TooltipIcon>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {hasOnlyUnverifiedEmployers && (
            <tr data-test="verification-instructions-row">
              <td colSpan={tableColumnKeys.length}>
                <Trans
                  i18nKey="pages.employersDashboard.verificationInstructions"
                  components={{
                    "your-organizations-link": (
                      <a href={routes.employers.organizations} />
                    ),
                  }}
                />
              </td>
            </tr>
          )}
          {!hasOnlyUnverifiedEmployers && (
            <ClaimTableRows
              appLogic={props.appLogic}
              claims={props.claims}
              tableColumnKeys={tableColumnKeys}
              user={user}
            />
          )}
        </tbody>
      </Table>
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

Dashboard.propTypes = {
  activeFilters: PropTypes.shape({
    claim_status: PropTypes.string,
    employer_id: PropTypes.string,
  }).isRequired,
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
      updateQuery: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection),
  query: PropTypes.shape({
    "show-filters": PropTypes.oneOf(["false", "true"]),
  }),
  paginationMeta: PropTypes.instanceOf(PaginationMeta),
  user: PropTypes.instanceOf(User).isRequired,
};

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props) => {
  const { appLogic, claims, tableColumnKeys, user } = props;
  const { t } = useTranslation();

  if (claims.isEmpty) {
    return (
      <tr>
        <td colSpan={tableColumnKeys.length}>
          {t("pages.employersDashboard.noClaimResults")}
        </td>
      </tr>
    );
  }

  /**
   * Helper for mapping a column key to the value
   * the user should see
   * @param {EmployerClaim} claim
   * @param {string} columnKey
   * @returns {string|React.ReactNode}
   */
  const getValueForColumn = (claim, columnKey) => {
    const claimRoute = appLogic.portalFlow.getNextPageRoute(
      "VIEW_CLAIM",
      {},
      { absence_id: get(claim, "fineos_absence_id") }
    );
    const employerFein = get(claim, "employer.employer_fein");
    const fullName = get(claim, "employee.fullName", "--");
    const isEmployerRegisteredInFineos = user.isEmployerIdRegisteredInFineos(
      get(claim, "employer.employer_id")
    );

    switch (columnKey) {
      case "created_at":
        return formatDateRange(get(claim, columnKey));
      case "fineos_absence_id":
        return isEmployerRegisteredInFineos ? (
          <Link href={claimRoute}>
            <a>{get(claim, columnKey)}</a>
          </Link>
        ) : (
          get(claim, columnKey)
        );
      case "employee_name":
        return isEmployerRegisteredInFineos ? (
          <Link href={claimRoute}>
            <a>{fullName}</a>
          </Link>
        ) : (
          fullName
        );
      case "employer_dba":
        return get(claim, "employer.employer_dba");
      case "employer_fein":
        return employerFein;
      case "status":
        return <AbsenceCaseStatusTag status={get(claim, "claim_status")} />;
      default:
        return "";
    }
  };

  return claims.items.map((claim) => (
    <tr key={claim.fineos_absence_id}>
      <th
        scope="row"
        data-label={t("pages.employersDashboard.tableColHeading", {
          context: tableColumnKeys[0],
        })}
        data-test={tableColumnKeys[0]}
      >
        {getValueForColumn(claim, tableColumnKeys[0])}
      </th>
      {tableColumnKeys.slice(1).map((columnKey) => (
        <td
          key={columnKey}
          data-label={t("pages.employersDashboard.tableColHeading", {
            context: columnKey,
          })}
        >
          {getValueForColumn(claim, columnKey)}
        </td>
      ))}
    </tr>
  ));
};

ClaimTableRows.propTypes = {
  appLogic: Dashboard.propTypes.appLogic,
  claims: Dashboard.propTypes.claims,
  tableColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

const DashboardInfoAlert = (props) => {
  const { user } = props;
  const { t } = useTranslation();

  const getCommaDelimitedEmployerEINs = () => {
    const employers = user.verifiedEmployersNotRegisteredInFineos;
    return employers.map((employer) => employer.employer_fein).join(", ");
  };

  // Leave admins not registered in Fineos won't be able to access associated claim data from Fineos.
  // We use this flag to communicate this to the user.
  if (user.hasVerifiedEmployerNotRegisteredInFineos) {
    return (
      <Alert
        state="info"
        heading={t("pages.employersDashboard.unavailableClaimsTitle", {
          employers: getCommaDelimitedEmployerEINs(),
        })}
      >
        <p>
          <Trans
            i18nKey="pages.employersDashboard.unavailableClaimsBody"
            components={{
              "learn-more-link": (
                <a
                  href={routes.external.massgov.employerAccount}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
        </p>
      </Alert>
    );
  }

  return (
    <Alert state="info" heading={t("pages.employersDashboard.betaHeader")}>
      <p>
        <Trans
          i18nKey="pages.employersDashboard.betaMessage"
          components={{
            "user-feedback-link": (
              <a
                href={routes.external.massgov.feedbackEmployer}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
    </Alert>
  );
};

DashboardInfoAlert.propTypes = {
  user: PropTypes.instanceOf(User).isRequired,
};

const Filters = (props) => {
  const filterFields = ["claim_status", "employer_id"];
  const { showFilters, updatePageQuery, user } = props;
  const { t } = useTranslation();

  const initialFormState = { ...pick(props.activeFilters, filterFields) };
  if (initialFormState.claim_status) {
    // Convert checkbox field query param into array, to conform to how we manage checkbox form state
    initialFormState.claim_status = initialFormState.claim_status.split(",");
  }

  const { formState, updateFields } = useFormState(initialFormState);
  const getFunctionalInputProps = useFunctionalInputProps({
    formState,
    updateFields,
  });

  const filtersContainerId = "filters";
  let activeFiltersCount = Object.values(initialFormState).length;
  if (initialFormState.claim_status) {
    // Count each selected status as an active filter
    activeFiltersCount += initialFormState.claim_status.length - 1;
  }

  const handleSubmit = (evt) => {
    evt.preventDefault();
    const params = [];

    Object.entries(formState).forEach(([name, value]) => {
      params.push({ name, value });
    });

    updatePageQuery([
      ...params,
      {
        name: "show-filters",
        value: false,
      },
      {
        // Reset the page to 1 since filters affect what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  const handleFilterReset = () => {
    const params = [];

    Object.keys(initialFormState).forEach((name) => {
      // Reset by setting to an empty string
      params.push({ name, value: "" });
    });

    updatePageQuery([
      ...params,
      {
        // Reset the page to 1 since filters affect what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  /**
   * Click event handler for an individual filter's removal button.
   * @param {string} name - Filter query param name
   * @param {string|Array} value - Leave empty to remove filter, or pass in the updated
   *  value if the filter is a checkbox field
   */
  const handleRemoveFilterClick = (name, value = "") => {
    updatePageQuery([
      {
        name,
        value,
      },
      {
        // Reset the page to 1 since filters affect what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);
  };

  const handleFilterToggleClick = () => {
    // We use a query param instead of useState since the page re-mounts
    // every time a filter changes, so we lose any local component state
    // each time that happens.
    updatePageQuery([
      {
        name: "show-filters",
        value: !showFilters,
      },
    ]);
  };

  if (!isFeatureEnabled("employerShowDashboardFilters")) {
    return null;
  }

  return (
    <React.Fragment>
      <div
        className={classnames({
          // When search is enabled, we visually display this as if it's
          // part of the same gray container box
          "margin-bottom-2": !isFeatureEnabled("employerShowDashboardSearch"),
          "padding-bottom-3 bg-base-lightest padding-x-3": isFeatureEnabled(
            "employerShowDashboardSearch"
          ),
        })}
      >
        <Button
          aria-controls={filtersContainerId}
          aria-expanded={showFilters.toString()}
          onClick={handleFilterToggleClick}
          variation="outline"
        >
          {activeFiltersCount > 0 && !showFilters
            ? t("pages.employersDashboard.filtersShowWithCount", {
                count: activeFiltersCount,
              })
            : t("pages.employersDashboard.filtersToggle", {
                context: showFilters ? "expanded" : undefined,
              })}
        </Button>
      </div>

      <form
        className="bg-primary-lighter padding-x-3 padding-top-1px padding-bottom-3 usa-form maxw-none"
        hidden={!showFilters}
        id={filtersContainerId}
        onSubmit={handleSubmit}
      >
        <InputChoiceGroup
          {...getFunctionalInputProps("claim_status")}
          smallLabel
          choices={[
            AbsenceCaseStatus.approved,
            AbsenceCaseStatus.closed,
            AbsenceCaseStatus.declined,
            "Pending", // API filtering uses this as a catchall for several pending-like statuses
          ].map((value) => ({
            checked: get(formState, "claim_status", []).includes(value),
            label: t("pages.employersDashboard.filterStatusChoice", {
              context: value,
            }),
            value,
          }))}
          label={t("pages.employersDashboard.filterStatusLabel")}
          type="checkbox"
        />

        {user.verifiedEmployers.length > 1 && (
          <Dropdown
            autocomplete
            {...getFunctionalInputProps("employer_id")}
            choices={[
              ...user.verifiedEmployers.map((employer) => ({
                label: `${employer.employer_dba} (${employer.employer_fein})`,
                value: employer.employer_id,
              })),
            ]}
            label={t("pages.employersDashboard.filterOrgsLabel")}
            smallLabel
          />
        )}

        <Button type="submit" disabled={Object.values(formState).length === 0}>
          {t("pages.employersDashboard.filtersApply")}
        </Button>

        {activeFiltersCount > 0 && (
          <Button
            data-test="reset-filters"
            variation="outline"
            onClick={handleFilterReset}
          >
            {t("pages.employersDashboard.filtersReset")}
          </Button>
        )}
      </form>

      {activeFiltersCount > 0 && (
        <div className="margin-top-1 margin-bottom-4" data-test="filters-menu">
          <strong className="margin-right-2 display-inline-block">
            {t("pages.employersDashboard.filterNavLabel")}
          </strong>
          {initialFormState.employer_id && (
            <FilterMenuButton
              data-test="employer_id"
              onClick={() => handleRemoveFilterClick("employer_id")}
            >
              {
                find(user.verifiedEmployers, {
                  employer_id: initialFormState.employer_id,
                }).employer_dba
              }
            </FilterMenuButton>
          )}
          {initialFormState.claim_status &&
            initialFormState.claim_status.map((status) => (
              <FilterMenuButton
                data-test={`claim_status_${status}`}
                key={status}
                onClick={() =>
                  handleRemoveFilterClick(
                    "claim_status",
                    initialFormState.claim_status.filter((s) => s !== status)
                  )
                }
              >
                {t("pages.employersDashboard.filterStatusChoice", {
                  context: status,
                })}
              </FilterMenuButton>
            ))}
        </div>
      )}
    </React.Fragment>
  );
};

Filters.propTypes = {
  activeFilters: PropTypes.shape({
    claim_status: PropTypes.string,
    employer_id: PropTypes.string,
  }).isRequired,
  showFilters: PropTypes.bool,
  updatePageQuery: PropTypes.func.isRequired,
  user: PropTypes.instanceOf(User).isRequired,
};

const FilterMenuButton = (props) => {
  const { t } = useTranslation();

  return (
    <Button
      className="text-bold text-no-underline hover:text-underline margin-right-2"
      onClick={props.onClick}
      type="button"
      variation="unstyled"
    >
      <Icon
        name="cancel"
        size={3}
        className="text-ttop margin-top-neg-1px margin-right-05"
        fill="currentColor"
      />
      <span className="usa-sr-only">
        {t("pages.employersDashboard.filterRemove")}
      </span>
      {props.children}
    </Button>
  );
};

FilterMenuButton.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func.isRequired,
};

const Search = (props) => {
  const { initialValue, updatePageQuery } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({ search: initialValue });
  const getFunctionalInputProps = useFunctionalInputProps({
    formState,
    updateFields,
  });

  const handleSubmit = (evt) => {
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

  if (!isFeatureEnabled("employerShowDashboardSearch")) return null;

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

Search.propTypes = {
  /** The current search value */
  initialValue: PropTypes.string,
  updatePageQuery: PropTypes.func.isRequired,
};

export default withClaims(Dashboard);
