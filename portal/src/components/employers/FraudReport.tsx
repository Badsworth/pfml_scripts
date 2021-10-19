import { Trans, useTranslation } from "react-i18next";
import Alert from "../Alert";
import ConditionalContent from "../ConditionalContent";
import Details from "../Details";
import InputChoiceGroup from "../InputChoiceGroup";
import React from "react";
import ReviewHeading from "../ReviewHeading";

interface FraudReportProps {
  fraudInput?: "Yes" | "No";
  getFunctionalInputProps: (...args: any[]) => any;
}

const FraudReport = ({
  fraudInput,
  getFunctionalInputProps,
}: FraudReportProps) => {
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

export default FraudReport;
