import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import ConditionalContent from "../ConditionalContent";
import Details from "../Details";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";

const FraudReport = ({ fraudInput, getFunctionalInputProps }) => {
  const { t } = useTranslation();

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps("fraud")}
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
            checked: fraudInput === "Yes",
            label: t("components.employersFraudReport.choiceYes"),
            value: "Yes",
          },
          {
            checked: fraudInput === "No",
            label: t("components.employersFraudReport.choiceNo"),
            value: "No",
          },
        ]}
        type="radio"
      />
      <ConditionalContent visible={fraudInput === "Yes"}>
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
  fraudInput: PropTypes.oneOf(["Yes", "No"]),
  getFunctionalInputProps: PropTypes.func.isRequired,
};

export default FraudReport;
