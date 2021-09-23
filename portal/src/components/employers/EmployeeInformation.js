import EmployerClaim from "../../models/EmployerClaim";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

/**
 * Display personal details of an employee applying for leave
 * in the Leave Admin claim review page.
 */

const EmployeeInformation = (props) => {
  const { t } = useTranslation();
  const {
    first_name,
    last_name,
    middle_name,
    date_of_birth,
    tax_identifier,
    residential_address: { city, line_1, line_2, state, zip },
  } = props.claim;

  return (
    <React.Fragment>
      <ReviewHeading id="employee-information" level="2">
        {t("components.employersEmployeeInformation.header")}
      </ReviewHeading>
      <dl aria-labelledby="employee-information">
        <ReviewRow
          level="3"
          label={t("components.employersEmployeeInformation.employeeNameLabel")}
        >
          {first_name} {middle_name} {last_name}
        </ReviewRow>
        <ReviewRow
          level="3"
          label={t("components.employersEmployeeInformation.addressLabel")}
        >
          <span
            className="residential-address"
            data-testid="residential-address"
          >
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
      </dl>
    </React.Fragment>
  );
};

EmployeeInformation.propTypes = {
  claim: PropTypes.instanceOf(EmployerClaim).isRequired,
};

export default EmployeeInformation;
