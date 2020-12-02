import React, { useEffect, useRef, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import routes from "../../routes";

const EmployerDecision = ({ fraud, onChange = () => {} }) => {
  const { t } = useTranslation();
  const [employerDecision, setEmployerDecision] = useState();
  // keep track of previous value for fraud prop to know when to clear employer decision
  const prevFraud = useRef(false);

  const handleOnChange = (event) => {
    setEmployerDecision(event.target.value);
  };

  useEffect(() => {
    onChange(employerDecision);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employerDecision]);

  useEffect(() => {
    if (fraud === "Yes") {
      setEmployerDecision("Deny");
    } else if (fraud === "No" && prevFraud.current) {
      setEmployerDecision(undefined);
    }
    prevFraud.current = fraud;
  }, [fraud]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        smallLabel
        label={
          <ReviewHeading level="2">
            {t("pages.employersClaimsReview.employerDecision.heading")}
          </ReviewHeading>
        }
        hint={
          <Trans
            i18nKey="pages.employersClaimsReview.employerDecision.explanation"
            className="font-heading-xs text-normal"
            components={{
              "employer-pfml-guide-link": (
                <a
                  href={routes.external.massgov.employersGuide}
                  target="_blank"
                  rel="noopener"
                />
              ),
            }}
          />
        }
        smallabel
        choices={[
          {
            checked: employerDecision === "Approve",
            disabled: fraud === "Yes",
            label: t(
              "pages.employersClaimsReview.employerDecision.choiceApprove"
            ),
            value: "Approve",
          },
          {
            checked: employerDecision === "Deny",
            label: t("pages.employersClaimsReview.employerDecision.choiceDeny"),
            value: "Deny",
          },
        ]}
        name="employerDecision"
        onChange={handleOnChange}
        type="radio"
      />
    </React.Fragment>
  );
};

EmployerDecision.propTypes = {
  fraud: PropTypes.string,
  onChange: PropTypes.func.isRequired,
};

export default EmployerDecision;
