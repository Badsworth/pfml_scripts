import AddButton from "./AddButton";
import AmendablePreviousLeave from "./AmendablePreviousLeave";
import Details from "../../components/core/Details";
import EmployerClaimReview from "../../models/EmployerClaimReview";
import Heading from "../../components/core/Heading";
import PreviousLeave from "../../models/PreviousLeave";
import React from "react";
import Table from "../../components/core/Table";
import { Trans } from "react-i18next";
import formatDate from "../../utils/formatDate";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

interface PreviousLeavesProps {
  addedPreviousLeaves: PreviousLeave[];
  errors: Error[];
  claim: EmployerClaimReview;
  onAdd: React.MouseEventHandler<HTMLButtonElement>;
  onChange: (
    arg: PreviousLeave | { [key: string]: unknown },
    arg2: string
  ) => void;
  onRemove: (arg: PreviousLeave) => void;
  previousLeaves: PreviousLeave[];
  shouldShowV2: boolean;
}

/**
 * Display past leaves taken by the employee
 * in the Leave Admin claim review page.
 */

const PreviousLeaves = (props: PreviousLeavesProps) => {
  const { t } = useTranslation();
  const {
    addedPreviousLeaves,
    errors,
    claim,
    onAdd,
    onChange,
    onRemove,
    previousLeaves,
    shouldShowV2,
  } = props;
  const limit = 4;

  return (
    <React.Fragment>
      <Heading level="3">
        {t("components.employersPreviousLeaves.header")}
      </Heading>
      <Trans
        i18nKey="components.employersPreviousLeaves.explanation"
        tOptions={{
          context:
            claim.computed_start_dates.other_reason ===
            claim.computed_start_dates.same_reason
              ? undefined
              : "differentDates",
        }}
        values={{
          other_reason_date: formatDate(
            claim.computed_start_dates.other_reason
          ).full(),
          same_reason_date: formatDate(
            claim.computed_start_dates.same_reason
          ).full(),
        }}
      />
      <Details
        label={t(
          "components.employersPreviousLeaves.qualifyingReasonDetailsLabel"
        )}
      >
        <p>{t("components.employersPreviousLeaves.qualifyingReasonContent")}</p>
        <ul className="usa-list">
          <li>
            <Trans
              i18nKey="components.employersPreviousLeaves.qualifyingReason_manageHealth"
              components={{
                "mass-benefits-guide-serious-health-condition-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={
                      routes.external.massgov
                        .benefitsGuide_seriousHealthCondition
                    }
                  />
                ),
              }}
            />
          </li>
          <li>
            {t(
              "components.employersPreviousLeaves.qualifyingReason_bondWithChild"
            )}
          </li>
          <li>
            {t(
              "components.employersPreviousLeaves.qualifyingReason_activeDuty"
            )}
          </li>
          <li>
            {t(
              "components.employersPreviousLeaves.qualifyingReason_careForFamilyMilitary"
            )}
          </li>
          <li>
            <Trans
              i18nKey="components.employersPreviousLeaves.qualifyingReason_careForFamilyMedical"
              components={{
                "mass-benefits-guide-serious-health-condition-link": (
                  <a
                    target="_blank"
                    rel="noopener"
                    href={
                      routes.external.massgov
                        .benefitsGuide_seriousHealthCondition
                    }
                  />
                ),
              }}
            />
          </li>
        </ul>
      </Details>
      <Table className="width-full" responsive>
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersPreviousLeaves.dateRangeLabel")}
            </th>
            <th scope="col">
              {t("components.employersPreviousLeaves.leaveTypeLabel")}
            </th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {previousLeaves.length ? (
            <React.Fragment>
              {previousLeaves.map((previousLeave) => (
                <AmendablePreviousLeave
                  errors={errors}
                  isAddedByLeaveAdmin={false}
                  key={previousLeave.previous_leave_id}
                  onChange={onChange}
                  onRemove={onRemove}
                  previousLeave={previousLeave}
                  shouldShowV2={shouldShowV2}
                />
              ))}
            </React.Fragment>
          ) : (
            <tr>
              <td>{t("shared.noneReported")}</td>
              <td></td>
              <td></td>
            </tr>
          )}
          {shouldShowV2 &&
            addedPreviousLeaves.map((addedLeave) => (
              <AmendablePreviousLeave
                errors={errors}
                isAddedByLeaveAdmin
                key={addedLeave.previous_leave_id}
                onChange={onChange}
                onRemove={onRemove}
                previousLeave={addedLeave}
                shouldShowV2={shouldShowV2}
              />
            ))}
          {shouldShowV2 && (
            <tr>
              <td className="padding-y-2 padding-left-0">
                <AddButton
                  label={t(
                    "components.employersAmendablePreviousLeave.addButton",
                    {
                      context:
                        addedPreviousLeaves.length === 0
                          ? "first"
                          : "subsequent",
                    }
                  )}
                  onClick={onAdd}
                  disabled={addedPreviousLeaves.length >= limit}
                />
              </td>
              <td></td>
              <td></td>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

export default PreviousLeaves;
