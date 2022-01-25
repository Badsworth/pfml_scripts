import Claim, { AbsenceCaseStatus } from "../../models/Claim";
import React, {
  FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import SortDropdown, {
  PageQueryParam,
} from "../../features/employer-dashboard/SortDropdown";
import { camelCase, get, isEqual, startCase } from "lodash";
import withClaims, { ApiParams, WithClaimsProps } from "../../hoc/withClaims";
import withUser, { WithUserProps } from "../../hoc/withUser";
import AbsenceCaseStatusTag from "../../components/AbsenceCaseStatusTag";
import Alert from "../../components/core/Alert";
import ApiResourceCollection from "../../models/ApiResourceCollection";
import { AppLogic } from "../../hooks/useAppLogic";
import Button from "../../components/core/Button";
import Details from "../../components/core/Details";
import Dropdown from "../../components/core/Dropdown";
import EmployerNavigationTabs from "../../components/employers/EmployerNavigationTabs";
import Icon from "../../components/core/Icon";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import InputText from "../../components/core/InputText";
import Link from "next/link";
import PaginationNavigation from "../../components/PaginationNavigation";
import PaginationSummary from "../../components/PaginationSummary";
import Table from "../../components/core/Table";
import Title from "../../components/core/Title";
import TooltipIcon from "../../components/core/TooltipIcon";
import { Trans } from "react-i18next";
import User from "../../models/User";
import formatDateRange from "../../utils/formatDateRange";
import isBlank from "../../utils/isBlank";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const Dashboard = (props: WithUserProps & { query: ApiParams }) => {
  const { t } = useTranslation();
  const introElementRef = useRef<HTMLElement>(null);
  const apiParams = {
    // Default the dashboard to show claims requiring action first
    order_by: "absence_status",
    order_direction: "ascending",
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

  const PaginatedClaimsTableWithClaims = withClaims(
    PaginatedClaimsTable,
    apiParams
  );
  const componentSpecificProps = {
    updatePageQuery,
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
                    <a href={routes.employers.organizations} />
                  ),
                }}
              />
            </p>
          </Alert>
        )}
      </div>

      <section className="margin-bottom-4 margin-top-2" ref={introElementRef}>
        <Details label={t("pages.employersDashboard.statusDescriptionsLabel")}>
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

      <Search
        initialValue={get(apiParams, "search", "")}
        updatePageQuery={updatePageQuery}
      />
      <Filters
        params={apiParams}
        updatePageQuery={updatePageQuery}
        user={props.user}
      />
      <PaginatedClaimsTableWithClaims
        appLogic={props.appLogic}
        {...componentSpecificProps}
      />
    </React.Fragment>
  );
};

interface PaginatedClaimsTableProps extends WithClaimsProps {
  updatePageQuery: (params: PageQueryParam[]) => void;
  /** Pass in the SortDropdown so it can be rendered in the expected inline UI position */
  sort: React.ReactNode;
}

const PaginatedClaimsTable = (props: PaginatedClaimsTableProps) => {
  const { paginationMeta, updatePageQuery, user } = props;
  const { t } = useTranslation();

  const hasOnlyUnverifiedEmployers = user.hasOnlyUnverifiedEmployers;
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
   */
  const tableColumnKeys = Object.entries(tableColumnVisibility)
    .filter(([_columnKey, isVisible]) => isVisible)
    .map(([columnKey]) => columnKey);

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
      <div className="margin-y-2 grid-row grid-gap flex-align-center">
        <div className="grid-col grid-col-12 margin-bottom-2 mobile-lg:grid-col-fill mobile-lg:margin-bottom-0">
          <PaginationSummary
            pageOffset={paginationMeta.page_offset}
            pageSize={paginationMeta.page_size}
            totalRecords={paginationMeta.total_records}
          />
        </div>
        <div className="grid-col grid-col-auto">{props.sort}</div>
      </div>
      <Table className="width-full" responsive scrollable>
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

interface ClaimTableRowsProps {
  appLogic: AppLogic;
  claims: ApiResourceCollection<Claim>;
  tableColumnKeys: string[];
  user: User;
}

/**
 * Renders the <tr> elements for each claim, or a message indicating
 * no claim data exists
 */
const ClaimTableRows = (props: ClaimTableRowsProps) => {
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
   */
  const getValueForColumn = (claim: Claim, columnKey: string) => {
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
        return (
          <AbsenceCaseStatusTag
            status={get(claim, "claim_status")}
            managedRequirements={get(claim, "managed_requirements")}
          />
        );

      default:
        return "";
    }
  };

  const renderClaimItems = () => {
    const claimItemsJSX: JSX.Element[] = [];

    claims.items.forEach((claim) => {
      claimItemsJSX.push(
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
      );
    });

    return claimItemsJSX;
  };

  return <React.Fragment>{renderClaimItems()}</React.Fragment>;
};

interface FiltersProps {
  params: {
    claim_status?: string;
    employer_id?: string;
  };
  updatePageQuery: (params: PageQueryParam[]) => void;
  user: User;
}

const Filters = (props: FiltersProps) => {
  const { updatePageQuery, user } = props;
  const { t } = useTranslation();

  /**
   * Returns all filter fields with their values set based on
   * what's currently being applied to the API requests
   */
  const getFormStateFromQuery = useCallback(() => {
    const claim_status = get(props.params, "claim_status");
    return {
      employer_id: get(props.params, "employer_id", ""),
      // Convert checkbox field query param into array, to conform to how we manage checkbox form state
      claim_status: claim_status ? claim_status.split(",") : [],
    };
  }, [props.params]);

  /**
   * Form visibility and state management
   */
  const activeFilters = getFormStateFromQuery();
  const [showFilters, setShowFilters] = useState(false);

  const { formState, updateFields } = useFormState(activeFilters);
  const getFunctionalInputProps = useFunctionalInputProps({
    formState,
    updateFields,
  });

  /**
   * Watch the query string for changes, and update the selected form fields
   * anytime those change. This is handy since a filter might get removed
   * outside of this component, and it also saves us from calling
   * updateFields every time we call updatePageQuery. Instead, we treat
   * the query string as the source of truth, and react to its changes.
   */
  useEffect(() => {
    updateFields(getFormStateFromQuery());
  }, [getFormStateFromQuery, updateFields]);

  /**
   * UI variables
   */
  const filtersContainerId = "filters";
  let activeFiltersCount = activeFilters.claim_status.length;
  if (activeFilters.employer_id) activeFiltersCount++;

  /**
   * Event handler for when the user applies their status and
   * organization filter selections
   */
  const handleSubmit = (evt: FormEvent) => {
    evt.preventDefault();
    const params: PageQueryParam[] = [];

    Object.entries(formState).forEach(([name, value]) => {
      params.push({ name, value });
    });

    updatePageQuery([
      ...params,
      {
        // Reset the page to 1 since filters affect what shows on the first page
        name: "page_offset",
        value: "1",
      },
    ]);

    setShowFilters(false);
  };

  /**
   * Event handler for the "Reset filters" action
   */
  const handleFilterReset = () => {
    const params: PageQueryParam[] = [];

    Object.keys(activeFilters).forEach((name) => {
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
   * @param name - Filter query param name
   * @param value - Leave empty to remove filter, or pass in the updated
   *  value if the filter is a checkbox field
   */
  const handleRemoveFilterClick = (
    name: string,
    value: string | string[] = ""
  ) => {
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
    setShowFilters(!showFilters);
  };

  const expandAria = showFilters ? "true" : "false";

  return (
    <React.Fragment>
      <div className="padding-bottom-3 bg-base-lightest padding-x-3">
        <Button
          aria-controls={filtersContainerId}
          aria-expanded={expandAria}
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
            "Pending - no action",
            "Open requirement",
          ].map((value) => ({
            checked: get(formState, "claim_status", []).includes(value),
            label: t("pages.employersDashboard.filterStatusChoice", {
              context: startCase(camelCase(value)).replace(/[-\s]/g, ""),
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

        <Button type="submit" disabled={isEqual(formState, activeFilters)}>
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
          {activeFilters.employer_id && (
            <FilterMenuButton
              data-test="employer_id"
              onClick={() => handleRemoveFilterClick("employer_id")}
            >
              {
                user.verifiedEmployers.find(
                  ({ employer_id }) => employer_id === activeFilters.employer_id
                )?.employer_dba
              }
            </FilterMenuButton>
          )}
          {activeFilters.claim_status.length &&
            activeFilters.claim_status.map((status) => (
              <FilterMenuButton
                data-test={`claim_status_${status}`}
                key={status}
                onClick={() =>
                  handleRemoveFilterClick(
                    "claim_status",
                    activeFilters.claim_status.filter((s) => s !== status)
                  )
                }
              >
                {t("pages.employersDashboard.filterStatusChoice", {
                  context: startCase(camelCase(status)).replace(/[-\s]/g, ""),
                })}
              </FilterMenuButton>
            ))}
        </div>
      )}
    </React.Fragment>
  );
};

interface FilterMenuButtonProps {
  children: React.ReactNode;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
}

const FilterMenuButton = (props: FilterMenuButtonProps) => {
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
