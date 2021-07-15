import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";

/**
 * Display intermittent leave schedule
 * in the Leave Admin claim review page.
 */
const IntermittentLeaveSchedule = ({ hasDocuments }) => {
  // TODO (EMPLOYER-655): Update intermittent leave details
  // const leavePeriod = props.intermittentLeavePeriods[0];
  const { t } = useTranslation();
  // TODO (EMPLOYER-655): Update intermittent leave details
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
        {/* TODO (EMPLOYER-448): Support intermittent leave
        TODO (EMPLOYER-655): Update intermittent leave details */}
        {/* {formatDateRange(leavePeriod.start_date, leavePeriod.end_date)} */}
      </th>
      <td>
        {t(
          "components.employersIntermittentLeaveSchedule.claimDurationType_intermittent"
        )}
      </td>
      <td>
        {/* TODO (EMPLOYER-448): Support intermittent leave
        TODO (EMPLOYER-655): Update intermittent leave details */}
        {/* <div className="text-bold">
          {t("components.employersIntermittentLeaveSchedule.frequencyBasis", {
            context: getFormattedFrequencyBasis(),
          })}
        </div> */}
        <div>
          {/* TODO (EMPLOYER-448): Support intermittent leave
          TODO (EMPLOYER-655): Update intermittent leave details */}
          <Trans
            i18nKey={`components.employersIntermittentLeaveSchedule.${
              hasDocuments
                ? "downloadAttachments"
                : "contactForLeaveScheduleDetails"
            }`}
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
            }}
            tOptions={{
              context: hasDocuments ? "hasDocs" : "noDocs",
            }}
          />
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

IntermittentLeaveSchedule.propTypes = {
  // TODO (EMPLOYER-655): Update intermittent leave details
  // intermittentLeavePeriods: PropTypes.arrayOf(
  //   PropTypes.instanceOf(IntermittentLeavePeriod)
  // ).isRequired,
  hasDocuments: PropTypes.bool,
};

export default IntermittentLeaveSchedule;
