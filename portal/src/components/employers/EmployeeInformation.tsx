import EmployerClaim from "../../models/EmployerClaim";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import formatDateRange from "../../utils/formatDateRange";
import { isFeatureEnabled } from "../../services/featureFlags";
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
    first_name,
    last_name,
    middle_name,
    date_of_birth,
    employer_dba,
    employer_fein,
    tax_identifier,
    residential_address: { city, line_1, line_2, state, zip },
  } = props.claim;
  const showMultipleLeave = isFeatureEnabled("employerShowMultiLeave");

  return (
    <React.Fragment>
      {!showMultipleLeave && !!employer_dba && (
        <ReviewRow
          level="2"
          label={t(
            "components.employersEmployeeInformation.organizationNameLabel"
          )}
          noBorder
        >
          {employer_dba}
        </ReviewRow>
      )}
      {!showMultipleLeave && (
        <ReviewRow
          level="2"
          label={t(
            "components.employersEmployeeInformation.employerIdentifierLabel"
          )}
          noBorder
        >
          {employer_fein}
        </ReviewRow>
      )}
      <ReviewHeading level="2">
        {t("components.employersEmployeeInformation.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t("components.employersEmployeeInformation.employeeNameLabel")}
      >
        {first_name} {middle_name} {last_name}
      </ReviewRow>
      {showMultipleLeave && !!employer_dba && (
        <ReviewRow
          level="3"
          label={t(
            "components.employersEmployeeInformation.organizationNameLabel"
          )}
        >
          {employer_dba}
        </ReviewRow>
      )}
      {showMultipleLeave && (
        <ReviewRow
          level="3"
          label={t(
            "components.employersEmployeeInformation.employerIdentifierLabel"
          )}
        >
          {employer_fein}
        </ReviewRow>
      )}
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