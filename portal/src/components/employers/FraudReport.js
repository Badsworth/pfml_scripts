import React, { useEffect, useState } from "react";
import Alert from "../Alert";
import ConditionalContent from "../ConditionalContent";
import Heading from "../Heading";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { useTranslation } from "react-i18next";

const FraudReport = ({ onChange = () => {} }) => {
  const { t } = useTranslation();
  const [isFraud, setIsFraud] = useState();

  const handleOnChange = (event) => {
    setIsFraud(event.target.value);
  };

  useEffect(() => {
    if (isFraud === "Yes" || isFraud === "No") {
      onChange(isFraud);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isFraud]);

  return (
    <React.Fragment>
      <form id="employer-fraud-report-form">
        <InputChoiceGroup
          label={
            <ReviewHeading level="2">
              {t("pages.employersClaimsReview.fraudReport.heading")}
            </ReviewHeading>
          }
          choices={[
            {
              checked: isFraud === "No",
              label: t("pages.employersClaimsReview.fraudReport.choiceNo"),
              value: "No",
            },
            {
              checked: isFraud === "Yes",
              label: t("pages.employersClaimsReview.fraudReport.choiceYes"),
              value: "Yes",
            },
          ]}
          name="isFraud"
          onChange={handleOnChange}
          type="radio"
        />
      </form>
      <ConditionalContent visible={isFraud === "Yes"}>
        <React.Fragment>
          <Heading level="4" weight="bold" className="text-error">
            {t("pages.employersClaimsReview.fraudReport.commentSolicitation")}
          </Heading>
          <Alert
            state="warning"
            heading={t("pages.employersClaimsReview.fraudReport.alertHeading")}
          >
            {t("pages.employersClaimsReview.fraudReport.alertBody")}
          </Alert>
        </React.Fragment>
      </ConditionalContent>
    </React.Fragment>
  );
};

FraudReport.propTypes = {
  onChange: PropTypes.func.isRequired,
};

export default FraudReport;
