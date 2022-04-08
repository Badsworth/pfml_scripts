import Alert from "src/components/core/Alert";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import BenefitsApplication from "src/models/BenefitsApplication";
import React from "react";
import { Trans } from "react-i18next";
import formatDate from "src/utils/formatDate";

function ApplicationWasSplitAlert({
  benefitsApplications,
  applicationWasSplitInto,
}: {
  applicationWasSplitInto: string;
  benefitsApplications: ApiResourceCollection<BenefitsApplication>;
}) {
  if (benefitsApplications.isEmpty) {
    return null;
  }

  const splitApplication = benefitsApplications.getItem(
    applicationWasSplitInto
  );
  const originalApplication =
    splitApplication &&
    benefitsApplications.items.find(
      (ba) => ba.split_into_application_id === splitApplication.application_id
    );

  if (!originalApplication) {
    return null;
  }

  if (splitApplication.isSubmitted) {
    return (
      <Alert state="warning" className="margin-bottom-3">
        <p>
          <Trans i18nKey="pages.applications.bothApplicationsWereSubmitted" />
        </p>
      </Alert>
    );
  }

  return (
    <Alert state="warning" className="margin-bottom-3">
      <p>
        <Trans i18nKey="pages.applications.yourApplicationWasSplit" />
      </p>
      <p>
        <Trans
          i18nKey="pages.applications.currentBenefitYearLeave"
          values={{
            startDate: formatDate(originalApplication.leaveStartDate).short(),
            endDate: formatDate(originalApplication.leaveEndDate).short(),
          }}
        />
      </p>
      <ul className="usa-list">
        <li>
          <Trans i18nKey="pages.applications.applicationOneSuccess" />
        </li>
      </ul>
      <p>
        <Trans
          i18nKey="pages.applications.nextBenefitYearLeave"
          values={{
            startDate: formatDate(splitApplication.leaveStartDate).short(),
            endDate: formatDate(splitApplication.leaveEndDate).short(),
          }}
        />
      </p>
      <ul>
        <li>
          <Trans
            i18nKey="pages.applications.applicationTwoSubmitLater"
            values={{
              submitDate: formatDate(
                splitApplication.computed_earliest_submission_date
              ).short(),
            }}
          />
        </li>
      </ul>
    </Alert>
  );
}

export default ApplicationWasSplitAlert;
