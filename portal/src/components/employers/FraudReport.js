import React, { useEffect, useState } from "react";
import Alert from "../Alert";
import ConditionalContent from "../ConditionalContent";
import Details from "../Details";
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
      <InputChoiceGroup
        smallLabel
        label={
          <ReviewHeading level="2">
            {t("pages.employersClaimsReview.fraudReport.heading")}
          </ReviewHeading>
        }
        hint={
          <Details
            label={t("pages.employersClaimsReview.fraudReport.detailsLabel")}
          >
            <ul className="usa-list">
              <li>
                {t(
                  "pages.employersClaimsReview.fraudReport.fraudContent_personalInfo"
                )}
              </li>
              <li>
                {t(
                  "pages.employersClaimsReview.fraudReport.fraudContent_falseDocuments"
                )}
              </li>
              <li>
                {t(
                  "pages.employersClaimsReview.fraudReport.fraudContent_falseInfo"
                )}
              </li>
            </ul>
          </Details>
        }
        choices={[
          {
            checked: isFraud === "Yes",
            label: t("pages.employersClaimsReview.fraudReport.choiceYes"),
            value: "Yes",
          },
          {
            checked: isFraud === "No",
            label: t("pages.employersClaimsReview.fraudReport.choiceNo"),
            value: "No",
          },
        ]}
        name="isFraud"
        onChange={handleOnChange}
        type="radio"
      />
      <ConditionalContent visible={isFraud === "Yes"}>
        <React.Fragment>
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
