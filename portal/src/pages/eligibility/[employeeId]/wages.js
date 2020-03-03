import React, { useEffect, useState } from "react";
import summarizeWages from "../../../utils/summarizeWages";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

// TODO: Integrate with api endpoint
// https://lwd.atlassian.net/browse/CP-111
const mockWage = (employeeId, employerId) => ({
  period_id: {
    year: 2019,
    quarter: 1,
  },
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

const Wages = () => {
  const router = useRouter();
  const { employeeId } = router.query;
  const { t } = useTranslation();
  const [wagesSummary, setWagesSummary] = useState({
    totalEmployers: 0,
    earningsByEmployer: [],
  });
  const { totalEmployers, earningsByEmployer } = wagesSummary;

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
            {earningsByEmployer.map(({ employer, earnings }) => (
              <tr key={`${employer}`}>
                <th scope="row">{employer}</th>
                <td>{earnings}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </React.Fragment>
  );
};

export default Wages;
