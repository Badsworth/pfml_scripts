import React, { useEffect, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import ConditionalContent from "../ConditionalContent";
import Details from "../Details";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";

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
            {t("components.employersFraudReport.heading")}
          </ReviewHeading>
        }
        hint={
          <Details label={t("components.employersFraudReport.detailsLabel")}>
            <ul className="usa-list">
              <li>
                {t("components.employersFraudReport.example_personalInfo")}
              </li>
              <li>
                {t("components.employersFraudReport.example_falseDocuments")}
              </li>
              <li>{t("components.employersFraudReport.example_falseInfo")}</li>
            </ul>
          </Details>
        }
        choices={[
          {
            checked: isFraud === "Yes",
            label: t("components.employersFraudReport.choiceYes"),
            value: "Yes",
          },
          {
            checked: isFraud === "No",
            label: t("components.employersFraudReport.choiceNo"),
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
            heading={t("components.employersFraudReport.alertHeading")}
          >
            <Trans
              i18nKey="components.employersFraudReport.alertBody"
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
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
