import Alert from "../../components/core/Alert";
import ApplicationSplit from "src/models/ApplicationSplit";
import { ISO8601Timestamp } from "types/common";
import LeaveSpansBenefitYearsMessage from "src/features/benefits-applications/LeaveSpansBenefitYearsMessage";
import React from "react";
import { isFeatureEnabled } from "src/services/featureFlags";

interface BenefitYearsSpanAlertProps {
  computed_application_split: ApplicationSplit | null;
  computed_earliest_submission_date: ISO8601Timestamp | null;
  final_content_before_submit?: boolean;
}

/**
 * Alert component shared across multiple pages for displaying
 * a claimant's leave dates that crosses benefit years
 */
function BenefitYearsSpanAlert(props: BenefitYearsSpanAlertProps) {
  const {
    computed_application_split,
    computed_earliest_submission_date,
    final_content_before_submit,
  } = props;

  if (
    isFeatureEnabled("splitClaimsAcrossBY") &&
    computed_application_split &&
    computed_earliest_submission_date
  ) {
    return (
      <Alert
        heading="Your leave dates extend into a new benefit year."
        headingSize="2"
        role="alert"
        state="info"
      >
        <LeaveSpansBenefitYearsMessage
          computed_application_split={computed_application_split}
          computed_earliest_submission_date={computed_earliest_submission_date}
          final_content_before_submit={final_content_before_submit}
        />
      </Alert>
    );
  }

  return null;
}

export default BenefitYearsSpanAlert;
