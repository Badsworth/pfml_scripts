import React, { useEffect, useState } from "react";
import Details from "./Details";
import Heading from "./Heading";
import Lead from "./Lead";
import PropType from "prop-types";
import summarizeWages from "../utils/summarizeWages";
import { useTranslation } from "../locales/i18n";

// TODO: Integrate with api endpoint
// https://lwd.atlassian.net/browse/CP-111
const mockWage = (employeeId, employerId) => ({
  period_id: "Q22020",
  employee_id: employeeId,
  employer_id: employerId,
  independent_contractor: false,
  opt_in: false,
  employer_ytd_wages: 25000,
  employer_qtr_wages: 5000,
  employer_medical_contribution: 2000,
  employee_medical_contribution: 975,
  employer_fam_contribution: 2000,
  employee_fam_contribution: 975,
});

const mockGetWageData = (id) => {
  const employer1 = "e4e3a70d-c9bf-4d1e-acf1-e3adefa20a32";
  const employer2 = "e72751a0-3ab4-4593-a08b-7f332c359fb4";
  return [
    mockWage(id, employer1),
    mockWage(id, employer1),
    mockWage(id, employer2),
  ];
};

/**
 * A component that fetches wages for an employee and displays them in a table by employer.
 */
const WagesTable = (props) => {
  const { t } = useTranslation();
  const [wagesSummary, setWagesSummary] = useState({
    totalEmployers: 0,
    earningsByEmployer: [],
  });
  const { totalEmployers, earningsByEmployer } = wagesSummary;
  const isEligible = props.eligibility === "eligible";

  useEffect(() => {
    const wages = mockGetWageData(props.employeeId);
    setWagesSummary(summarizeWages(wages));
  }, [props.employeeId]);

  const lead = () => {
    if (isEligible) {
      return (
        <React.Fragment>
          <Lead>
            {t("components.wagesTable.eligibleDescriptionP1", {
              totalEmployers,
            })}
          </Lead>
          <Lead>{t("components.wagesTable.eligibleDescriptionP2")}</Lead>
        </React.Fragment>
      );
    }

    return <Lead>{t("components.wagesTable.ineligibleDescription")}</Lead>;
  };

  return (
    <React.Fragment>
      {lead()}

      <Heading level="2">{t("components.wagesTable.tableHeading")}</Heading>
      <table className="usa-table">
        <thead>
          <tr>
            <th scope="col">
              {t("components.wagesTable.tableEmployerHeading")}
            </th>
            <th scope="col">
              {t("components.wagesTable.tableEarningsHeading")}
            </th>
          </tr>
        </thead>
        <tbody>
          {earningsByEmployer.map(({ employer, totalEarnings }) => (
            <tr key={`${employer}-summary`}>
              <th scope="row">{employer}</th>
              <td>{totalEarnings}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <Details label={t("components.wagesTable.detailsLabel")}>
        {earningsByEmployer.map(({ employer, wages }) => (
          <table className="usa-table" key={`${employer}-history`}>
            <caption>
              {t("components.wagesTable.historyTableCaption", {
                employer,
              })}
            </caption>
            <thead>
              <tr>
                <th scope="col">
                  {t("components.wagesTable.historyTablePeriodHeading")}
                </th>
                <th scope="col">
                  {t("components.wagesTable.tableEarningsHeading")}
                </th>
              </tr>
            </thead>
            <tbody>
              {/**
                * TODO this only shows a row for quarters
                * where wages exist. We will need to show
                * $0.00 for empty quarters once we've integrated with
                * a mock endpoint
                */}
              {wages.map(({ quarter, earnings, period_id }, i) => (
                <tr key={`${employer}-history-${period_id}-${i}`}>
                  <th scope="row">{quarter}</th>
                  <td>{earnings}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ))}
      </Details>
    </React.Fragment>
  );
};

WagesTable.propTypes = {
  /**
   * Eligibility of employee. This determines the copy that is displayed.
   */
  eligibility: PropType.oneOf(["eligible", "ineligible"]).isRequired,
  /**
   * Id for employee whose wages will be displayed.
   */
  employeeId: PropType.string.isRequired,
};

export default WagesTable;
