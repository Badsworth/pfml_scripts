import React, { FormEvent, useCallback, useEffect, useState } from "react";
import { camelCase, get, isEqual, startCase } from "lodash";
import { AbsenceCaseStatus } from "../../models/Claim";
import Button from "../../components/core/Button";
import Dropdown from "../../components/core/Dropdown";
import { GetClaimsParams } from "../../api/ClaimsApi";
import Icon from "../../components/core/Icon";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import { PageQueryParam } from "../../features/employer-dashboard/SortDropdown";
import { UserLeaveAdministrator } from "../../models/User";
import { isFeatureEnabled } from "../../services/featureFlags";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

interface FiltersProps {
  params: GetClaimsParams;
  updatePageQuery: (params: PageQueryParam[]) => void;
  verifiedEmployers: UserLeaveAdministrator[];
}

const Filters = (props: FiltersProps) => {
  const { updatePageQuery, verifiedEmployers } = props;
  const { t } = useTranslation();
  const showDashboardV2Filters = isFeatureEnabled(
    "employerShowMultiLeaveDashboard"
  );

  /**
   * Returns all filter fields with their values set based on
   * what's currently being applied to the API requests
   */
  const getFormStateFromQuery = useCallback(() => {
    const {
      claim_status,
      employer_id,
      // Empty strings represent the default "Show all" option.
      // We use empty strings to avoid passing a param to the API
      // when these default options are selected, since they really mean:
      // "no filter selected".
      is_reviewable = "",
      request_decision = "",
    } = props.params;
    return {
      is_reviewable,
      employer_id,
      // Convert checkbox field query param into array, to conform to how we manage checkbox form state
      claim_status: claim_status ? claim_status.split(",") : [],
      request_decision,
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
  if (activeFilters.is_reviewable) activeFiltersCount++;
  if (activeFilters.request_decision) activeFiltersCount++;

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

  return (
    <React.Fragment>
      <div className="padding-bottom-3 bg-base-lightest padding-x-3">
        <Button
          aria-controls={filtersContainerId}
          aria-expanded={showFilters ? "true" : "false"}
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

      {/* `hidden` is set on div, instead of the form, to workaround a quirk in E2E scripts (https://lwd.atlassian.net/browse/PORTAL-1592) */}
      <div hidden={!showFilters} id={filtersContainerId}>
        <form
          className="bg-primary-lighter padding-x-3 padding-top-1px padding-bottom-3 usa-form maxw-none"
          onSubmit={handleSubmit}
        >
          {!showDashboardV2Filters && (
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
          )}

          {verifiedEmployers.length > 1 && (
            <Dropdown
              autocomplete
              {...getFunctionalInputProps("employer_id")}
              choices={[
                ...verifiedEmployers.map((employer) => ({
                  label: `${employer.employer_dba} (${employer.employer_fein})`,
                  value: employer.employer_id,
                })),
              ]}
              label={t("pages.employersDashboard.filterOrgsLabel")}
              smallLabel
            />
          )}

          {showDashboardV2Filters && (
            <React.Fragment>
              <ReviewableFilter {...getFunctionalInputProps("is_reviewable")} />
              <RequestDecisionFilter
                {...getFunctionalInputProps("request_decision")}
              />
            </React.Fragment>
          )}

          <Button type="submit" disabled={isEqual(formState, activeFilters)}>
            {t("pages.employersDashboard.filtersApply")}
          </Button>

          {activeFiltersCount > 0 && (
            <Button variation="outline" onClick={handleFilterReset}>
              {t("pages.employersDashboard.filtersReset")}
            </Button>
          )}
        </form>
      </div>

      {activeFiltersCount > 0 && (
        <div
          className="margin-top-1 margin-bottom-4"
          data-testid="filters-menu"
        >
          <strong className="margin-right-2 display-inline-block">
            {t("pages.employersDashboard.filterNavLabel")}
          </strong>
          {activeFilters.employer_id && (
            <FilterMenuButton
              onClick={() => handleRemoveFilterClick("employer_id")}
            >
              {
                verifiedEmployers.find(
                  ({ employer_id }) => employer_id === activeFilters.employer_id
                )?.employer_dba
              }
            </FilterMenuButton>
          )}

          {activeFilters.is_reviewable && (
            <FilterMenuButton
              onClick={() => handleRemoveFilterClick("is_reviewable")}
            >
              {t("pages.employersDashboard.filterReviewable", {
                context: activeFilters.is_reviewable,
              })}
            </FilterMenuButton>
          )}

          {activeFilters.request_decision && (
            <FilterMenuButton
              onClick={() => handleRemoveFilterClick("request_decision")}
            >
              {t("pages.employersDashboard.filterRequestDecision", {
                context: activeFilters.request_decision,
              })}
            </FilterMenuButton>
          )}

          {activeFilters.claim_status.length > 0 &&
            activeFilters.claim_status.map((status) => (
              <FilterMenuButton
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

function RequestDecisionFilter(props: {
  onChange: React.ChangeEventHandler<HTMLInputElement>;
  name: string;
  value: string;
}) {
  const { t } = useTranslation();
  const choices: Array<{
    label: string;
    value: "" | Required<GetClaimsParams>["request_decision"];
  }> = [
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "approved",
      }),
      value: "approved",
    },
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "cancelled",
      }),
      value: "cancelled",
    },
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "denied",
      }),
      value: "denied",
    },
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "pending",
      }),
      value: "pending",
    },
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "withdrawn",
      }),
      value: "withdrawn",
    },
    {
      label: t("pages.employersDashboard.filterRequestDecision", {
        context: "all",
      }),
      value: "",
    },
  ];

  return (
    <InputChoiceGroup
      name={props.name}
      onChange={props.onChange}
      choices={choices.map((choice) => ({
        checked: props.value === choice.value,
        ...choice,
      }))}
      label={t("pages.employersDashboard.filterRequestDecisionLabel")}
      type="radio"
      smallLabel
    />
  );
}

function ReviewableFilter(props: {
  onChange: React.ChangeEventHandler<HTMLInputElement>;
  name: string;
  value: string;
}) {
  const { t } = useTranslation();
  const choices: Array<{
    label: string;
    value: "" | Required<GetClaimsParams>["is_reviewable"];
  }> = [
    {
      label: t("pages.employersDashboard.filterReviewable", {
        context: "yes",
      }),
      value: "yes",
    },
    {
      label: t("pages.employersDashboard.filterReviewable", {
        context: "no",
      }),
      value: "no",
    },
    {
      label: t("pages.employersDashboard.filterReviewable", {
        context: "all",
      }),
      value: "",
    },
  ];

  return (
    <InputChoiceGroup
      name={props.name}
      onChange={props.onChange}
      choices={choices.map((choice) => ({
        checked: props.value === choice.value,
        ...choice,
      }))}
      label={t("pages.employersDashboard.filterReviewableLabel")}
      type="radio"
      smallLabel
    />
  );
}

export default Filters;
