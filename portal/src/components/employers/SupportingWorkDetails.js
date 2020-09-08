import AmendLink from "./AmendLink";
import PropTypes from "prop-types";
import React from "react";
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

  return (
    <React.Fragment>
      <ReviewHeading>
        {t("pages.employersClaimsReview.supportingWorkDetails.header")}
      </ReviewHeading>
      <ReviewRow
        label={t(
          "pages.employersClaimsReview.supportingWorkDetails.hoursWorkedLabel"
        )}
        action={<AmendLink />}
      >
        {intermittentLeavePeriods.map((leavePeriod, index) => {
          return (
            <p key={index} className="margin-top-0">
              {leavePeriod.duration}
            </p>
          );
        })}
      </ReviewRow>
      <ReviewRow label={t("pages.employersClaimsReview.documentationLabel")}>
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
