import { IntermittentLeavePeriod } from "../../models/BenefitsApplication";
import React from "react";
import { Trans } from "react-i18next";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";

interface IntermittentLeaveScheduleProps {
  intermittentLeavePeriods: IntermittentLeavePeriod[];
  hasDocuments?: boolean;
}

/**
 * Display intermittent leave schedule
 * in the Leave Admin claim review page.
 */
const IntermittentLeaveSchedule = ({
  hasDocuments,
  intermittentLeavePeriods,
}: IntermittentLeaveScheduleProps) => {
  const leavePeriod = intermittentLeavePeriods[0];
  const { t } = useTranslation();
  // TODO (PORTAL-968): Update intermittent leave details
  // const getFormattedFrequencyBasis = () => {
  //   if (
  //     leavePeriod.frequency_interval_basis === FrequencyIntervalBasis.months &&
  //     leavePeriod.frequency_interval === 6
  //   ) {
  //     return "irregular";
  //   } else {
  //     return findKeyByValue(
  //       FrequencyIntervalBasis,
  //       leavePeriod.frequency_interval_basis
  //     );
  //   }
  // };

  return (
    <tr>
      <th scope="row">
        {formatDateRange(leavePeriod.start_date, leavePeriod.end_date)}
      </th>
      <td>
        {t(
          "components.employersIntermittentLeaveSchedule.claimDurationType_intermittent"
        )}
      </td>
      <td>
        {/* TODO (PORTAL-968): Update intermittent leave details */}
        {/* <div className="text-bold">
          {t("components.employersIntermittentLeaveSchedule.frequencyBasis", {
            context: getFormattedFrequencyBasis(),
          })}
        </div> */}
        <div>
          <Trans
            i18nKey="components.employersIntermittentLeaveSchedule.lead"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
            tOptions={{
              context: hasDocuments ? "hasDocs" : "noDocs",
            }}
          />
          {/* TODO (PORTAL-968): Update intermittent leave details */}
          {/* <Trans
            i18nKey="components.employersIntermittentLeaveSchedule.intermittentFrequencyDuration"
            tOptions={{
              context: getI18nContextForIntermittentFrequencyDuration(
                leavePeriod
              ),
              duration: leavePeriod.duration,
              frequency: leavePeriod.frequency,
            }}
          /> */}
        </div>
      </td>
    </tr>
  );
};

export default IntermittentLeaveSchedule;
