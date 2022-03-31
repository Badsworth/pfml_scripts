import EmployerClaim from "../../models/EmployerClaim";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

interface EmployeeInformationProps {
  claim: EmployerClaim;
}

/**
 * Display personal details of an employee applying for leave
 * in the Leave Admin claim review page.
 */

const EmployeeInformation = (props: EmployeeInformationProps) => {
  const { t } = useTranslation();
  const {
    date_of_birth,
    employer_dba,
    employer_fein,
    fullName,
    tax_identifier,
    residential_address: { city, line_1, line_2, state, zip },
  } = props.claim;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersEmployeeInformation.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t("components.employersEmployeeInformation.employeeNameLabel")}
      >
        {fullName}
      </ReviewRow>
      {!!employer_dba && (
        <ReviewRow
          level="3"
          label={t(
            "components.employersEmployeeInformation.organizationNameLabel"
          )}
        >
          {employer_dba}
        </ReviewRow>
      )}
      <ReviewRow
        level="3"
        label={t(
          "components.employersEmployeeInformation.employerIdentifierLabel"
        )}
      >
        {employer_fein}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersEmployeeInformation.addressLabel")}
      >
        <span className="residential-address" data-testid="residential-address">
          {line_1}
          <br />
          {line_2}
          {line_2 && <br />}
          {city}, {state} {zip}
        </span>
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersEmployeeInformation.ssnOrItinLabel")}
      >
        {tax_identifier}
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("components.employersEmployeeInformation.dobLabel")}
      >
        {formatDateRange(date_of_birth)}
      </ReviewRow>
    </React.Fragment>
  );
};

export default EmployeeInformation;
