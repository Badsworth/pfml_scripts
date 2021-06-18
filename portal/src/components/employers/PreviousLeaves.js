import AddButton from "./AddButton";
import AmendablePreviousLeave from "./AmendablePreviousLeave";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Details from "../Details";
import Heading from "../Heading";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import React from "react";
import Table from "../Table";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

/**
 * Display past leaves taken by the employee
 * in the Leave Admin claim review page.
 */

const PreviousLeaves = (props) => {
  const { t } = useTranslation();
  const {
    addedPreviousLeaves,
    appErrors,
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
      <p>
        <Trans
          i18nKey="components.employersPreviousLeaves.explanation"
          components={{
            "calculate-reductions-link": (
              <a
                href={routes.external.massgov.calculateReductions}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
      </p>
      <Details
        label={t(
          "components.employersPreviousLeaves.qualifyingReasonDetailsLabel"
        )}
        className="text-bold"
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
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersPreviousLeaves.dateRangeLabel")}
            </th>
            <th scope="col" colSpan="2">
              {t("components.employersPreviousLeaves.leaveTypeLabel")}
            </th>
          </tr>
        </thead>
        <tbody>
          {previousLeaves.length ? (
            <React.Fragment>
              {previousLeaves.map((previousLeave) => (
                <AmendablePreviousLeave
                  appErrors={appErrors}
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
              <th scope="row">{t("shared.noneReported")}</th>
              <td colSpan="3" />
            </tr>
          )}
          {shouldShowV2 &&
            addedPreviousLeaves.map((addedLeave) => (
              <AmendablePreviousLeave
                appErrors={appErrors}
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
              <td colSpan="4" className="padding-y-2 padding-left-0">
                <AddButton
                  label={t(
                    "components.employersAmendablePreviousLeave.addButton"
                  )}
                  onClick={onAdd}
                  disabled={addedPreviousLeaves.length >= limit}
                />
              </td>
            </tr>
          )}
        </tbody>
      </Table>
      <p className="margin-top-neg-1 padding-left-2">
        {t("components.employersPreviousLeaves.commentInstructions")}
      </p>
    </React.Fragment>
  );
};

PreviousLeaves.propTypes = {
  addedPreviousLeaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave))
    .isRequired,
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  onAdd: PropTypes.func.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  previousLeaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)),
  shouldShowV2: PropTypes.bool.isRequired,
};

export default PreviousLeaves;
