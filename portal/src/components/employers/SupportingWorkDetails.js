import React, { useState } from "react";
import AmendButton from "./AmendButton";
import AmendmentForm from "./AmendmentForm";
import InputText from "../InputText";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import ReviewRow from "../ReviewRow";
import { useTranslation } from "../../locales/i18n";

const detailedWorkScheduleFile = "example-work-schedule-link.pdf";

/**
 * Display weekly hours worked for intermittent leave
 * in the Leave Admin claim review page.
 */

const SupportingWorkDetails = (props) => {
  const { t } = useTranslation();
  const { intermittentLeavePeriods } = props;
  const leavePeriod = intermittentLeavePeriods[0];
  const [amendment, setAmendment] = useState(leavePeriod.duration);
  const [isAmendmentFormDisplayed, setIsAmendmentFormDisplayed] = useState(
    false
  );
  const amendDuration = (event) => {
    setAmendment(event.target.value);
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
        <p className="margin-top-0">{leavePeriod.duration}</p>
        {isAmendmentFormDisplayed && (
          <AmendmentForm
            onCancel={() => {
              setIsAmendmentFormDisplayed(false);
              setAmendment(leavePeriod.duration);
            }}
            className="input-text-first-child"
          >
            <InputText
              onChange={amendDuration}
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
        )}
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
  intermittentLeavePeriods: PropTypes.array,
};

export default SupportingWorkDetails;
