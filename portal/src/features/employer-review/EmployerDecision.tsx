import React, { useEffect } from "react";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import ReviewHeading from "../../components/ReviewHeading";
import { Trans } from "react-i18next";
import routes from "../../routes";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "../../locales/i18n";

interface EmployerDecisionProps {
  employerDecisionInput?: "Approve" | "Deny";
  fraud?: string;
  getFunctionalInputProps: ReturnType<typeof useFunctionalInputProps>;
  updateFields: (fields: { [fieldName: string]: unknown }) => void;
}

const EmployerDecision = (props: EmployerDecisionProps) => {
  const { t } = useTranslation();
  // keep track of previous value for fraud prop to know when to clear employer decision
  const previouslyFraud = usePreviousValue(props.fraud);

  useEffect(() => {
    if (props.fraud === "Yes") {
      props.updateFields({ employer_decision: "Deny" });
    } else if (props.fraud === "No" && previouslyFraud === "Yes") {
      props.updateFields({ employer_decision: undefined });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.fraud]);

  return (
    <InputChoiceGroup
      {...props.getFunctionalInputProps("employer_decision")}
      smallLabel
      label={
        <ReviewHeading level="2">
          {t("components.employersEmployerDecision.heading")}
        </ReviewHeading>
      }
      hint={
        <Trans
          i18nKey="components.employersEmployerDecision.explanation"
          components={{
            "mass-employer-role-link": (
              <a
                href={routes.external.massgov.employersGuide}
                target="_blank"
                rel="noreferrer noopener"
              />
            ),
          }}
        />
      }
      choices={[
        {
          checked: props.employerDecisionInput === "Approve",
          disabled: props.fraud === "Yes",
          label: t("components.employersEmployerDecision.choiceApprove"),
          value: "Approve",
        },
        {
          checked: props.employerDecisionInput === "Deny",
          label: t("components.employersEmployerDecision.choiceDeny"),
          value: "Deny",
        },
      ]}
      type="radio"
    />
  );
};

export default EmployerDecision;
