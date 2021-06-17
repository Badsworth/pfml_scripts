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
  const { appErrors, previousLeaves, onChange } = props;

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
              {previousLeaves.map((leavePeriod) => {
                return (
                  <AmendablePreviousLeave
                    appErrors={appErrors}
                    key={leavePeriod.previous_leave_id}
                    leavePeriod={leavePeriod}
                    onChange={onChange}
                  />
                );
              })}
            </React.Fragment>
          ) : (
            <tr>
              <th scope="row">{t("shared.noneReported")}</th>
              <td colSpan="3" />
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
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  onChange: PropTypes.func.isRequired,
  previousLeaves: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)),
};

export default PreviousLeaves;
