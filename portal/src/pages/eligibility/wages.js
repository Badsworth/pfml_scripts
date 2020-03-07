import React, { useEffect, useState } from "react";
import Details from "../../components/Details";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import summarizeWages from "../../utils/summarizeWages";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

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
  employee_fam_contribution: 975
});

const mockGetWageData = id => {
  const employer1 = "e4e3a70d-c9bf-4d1e-acf1-e3adefa20a32";
  const employer2 = "e72751a0-3ab4-4593-a08b-7f332c359fb4";
  return [
    mockWage(id, employer1),
    mockWage(id, employer1),
    mockWage(id, employer2)
  ];
};

const Wages = () => {
  const router = useRouter();
  const { employeeId } = router.query;
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    dataIsCorrect: null
  });
  const [wagesSummary, setWagesSummary] = useState({
    totalEmployers: 0,
    earningsByEmployer: []
  });
  const { totalEmployers, earningsByEmployer } = wagesSummary;

  const handleChange = event => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  useEffect(() => {
    const wages = mockGetWageData(employeeId);
    setWagesSummary(summarizeWages(wages));
  }, [employeeId]);

  return (
    <React.Fragment>
      <h1 className="font-sans-3xl line-height-sans-2">
        {t("pages.eligibility.wages.title")}
      </h1>
      <div className="usa-prose">
        <p>{t("pages.eligibility.wages.descriptionP1", { totalEmployers })}</p>
        <p>{t("pages.eligibility.wages.descriptionP2")}</p>
        <h2>{t("pages.eligibility.wages.wagesTableHeading")}</h2>
        <table className="usa-table">
          <thead>
            <tr>
              <th scope="col">
                {t("pages.eligibility.wages.wagesTableEmployerHeading")}
              </th>
              <th scope="col">
                {t("pages.eligibility.wages.wagesTableEarningsHeading")}
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

        <Details label={t("pages.eligibility.wages.detailsLabel")}>
          {earningsByEmployer.map(({ employer, wages }) => (
            <table className="usa-table" key={`${employer}-history`}>
              <caption>
                {t("pages.eligibility.wages.wagesHistoryTableCaption", {
                  employer
                })}
              </caption>
              <thead>
                <tr>
                  <th scope="col">
                    {t("pages.eligibility.wages.wagesTablePeriodHeading")}
                  </th>
                  <th scope="col">
                    {t("pages.eligibility.wages.wagesTableEarningsHeading")}
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

        <form className="usa-form usa-form--large margin-y-6">
          <InputChoiceGroup
            label={t("pages.eligibility.wages.dataIsCorrectLabel")}
            type="radio"
            name="dataIsCorrect"
            onChange={handleChange}
            choices={[
              {
                checked: formData.dataIsCorrect === "yes",
                label: "Yes",
                value: "yes"
              },
              {
                checked: formData.dataIsCorrect === "no",
                label: "No",
                value: "no"
              }
            ]}
          />
        </form>
      </div>
    </React.Fragment>
  );
};

export default Wages;
