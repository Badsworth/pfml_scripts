import React, { useEffect } from "react";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { Trans } from "react-i18next";
import routes from "../../routes";
import usePreviousValue from "../../hooks/usePreviousValue";
import { useTranslation } from "../../locales/i18n";

const EmployerDecision = (props) => {
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
    <React.Fragment>
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
            className="font-heading-xs text-normal"
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
        smallabel
        choices={[
          {
            checked: props.employerDecision === "Approve",
            disabled: props.fraud === "Yes",
            label: t("components.employersEmployerDecision.choiceApprove"),
            value: "Approve",
          },
          {
            checked: props.employerDecision === "Deny",
            label: t("components.employersEmployerDecision.choiceDeny"),
            value: "Deny",
          },
        ]}
        type="radio"
      />
    </React.Fragment>
  );
};

EmployerDecision.propTypes = {
  employerDecision: PropTypes.oneOf(["Approve", "Deny"]),
  fraud: PropTypes.string,
  getFunctionalInputProps: PropTypes.func.isRequired,
  updateFields: PropTypes.func.isRequired,
};

export default EmployerDecision;
