import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import ConditionalContent from "../ConditionalContent";
import InputText from "../InputText";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { useTranslation } from "../../locales/i18n";

// TODO (EMPLOYER-364): Remove hardcoded link
const detailedWorkScheduleFile = "example-work-schedule-link.pdf";

/**
 * Display weekly hours worked for intermittent leave
 * in the Leave Admin claim review page.
 */

const SupportingWorkDetails = (props) => {
  const { t } = useTranslation();
  const { hoursWorkedPerWeek, onChange } = props;
  const [amendment, setAmendment] = useState(hoursWorkedPerWeek);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendDuration = (value) => {
    setAmendment(value);
    onChange(value);
  };

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("pages.employersClaimsReview.supportingWorkDetails.header")}
      </ReviewHeading>
      <ReviewRow
        level="3"
        label={t(
          "pages.employersClaimsReview.supportingWorkDetails.hoursWorkedLabel"
        )}
        action={
          <AmendButton onClick={() => setIsAmendmentFormDisplayed(true)} />
        }
      >
        <p className="margin-top-0">{hoursWorkedPerWeek}</p>
        <ConditionalContent visible={isAmendmentFormDisplayed}>
          <AmendmentForm
            onCancel={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(hoursWorkedPerWeek);
              onChange(hoursWorkedPerWeek);
            }}
            className="input-text-first-child"
          >
            <InputText
              onChange={(e) => amendDuration(e.target.value)}
              value={amendment}
              label={t("components.amendmentForm.question_leavePeriodDuration")}
              hint={t(
                "components.amendmentForm.question_leavePeriodDuration_hint"
              )}
              name="supporting-work-detail-amendment"
              type="number"
              width="small"
              smallLabel
            />
          </AmendmentForm>
        </ConditionalContent>
      </ReviewRow>
      <ReviewRow
        level="3"
        label={t("pages.employersClaimsReview.documentationLabel")}
      >
        <a href={detailedWorkScheduleFile} className="text-normal">
          {t(
            "pages.employersClaimsReview.supportingWorkDetails.viewScheduleLink"
          )}
        </a>
      </ReviewRow>
    </React.Fragment>
  );
};

SupportingWorkDetails.propTypes = {
  hoursWorkedPerWeek: PropTypes.number.isRequired,
  onChange: PropTypes.func,
};

export default SupportingWorkDetails;
