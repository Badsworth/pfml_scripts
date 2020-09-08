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
      <ReviewHeading>
        {t("pages.employersClaimsReview.employeeInformation.header")}
      </ReviewHeading>
      <ReviewRow
        label={t(
          "pages.employersClaimsReview.employeeInformation.employeeNameLabel"
        )}
      >
        {first_name} {middle_name} {last_name}
      </ReviewRow>
      <ReviewRow
        label={t(
          "pages.employersClaimsReview.employeeInformation.addressLabel"
        )}
      >
        <span className="residential-address">
          {line_1}
          <br />
          {line_2}
          {line_2 && <br />}
          {city}, {state} {zip}
        </span>
      </ReviewRow>
      <ReviewRow
        label={t(
          "pages.employersClaimsReview.employeeInformation.ssnOrItinLabel"
        )}
      >
        {tax_identifier}
      </ReviewRow>
      <ReviewRow
        label={t("pages.employersClaimsReview.employeeInformation.dobLabel")}
      >
        {formatDateRange(date_of_birth)}
      </ReviewRow>
    </React.Fragment>
  );
};

EmployeeInformation.propTypes = {
  claim: PropTypes.object.isRequired,
};

export default EmployeeInformation;
