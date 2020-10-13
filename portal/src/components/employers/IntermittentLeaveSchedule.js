import {
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../models/Claim";
import PropTypes from "prop-types";
import React from "react";
import { Trans } from "react-i18next";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import getI18nContextForIntermittentFrequencyDuration from "../../utils/getI18nContextForIntermittentFrequencyDuration";
import { useTranslation } from "../../locales/i18n";

/**
 * Display intermittent leave schedule
 * in the Leave Admin claim review page.
 */

const IntermittentLeaveSchedule = (props) => {
  const leavePeriod = props.intermittentLeavePeriods[0];
  const { t } = useTranslation();
  const getFormattedFrequencyBasis = () => {
    if (
      leavePeriod.frequency_interval_basis === FrequencyIntervalBasis.months &&
      leavePeriod.frequency_interval === 6
    ) {
      return "irregular";
    } else {
      return findKeyByValue(
        FrequencyIntervalBasis,
        leavePeriod.frequency_interval_basis
      );
    }
  };

  return (
    <tr>
      <th scope="row">
        {formatDateRange(leavePeriod.start_date, leavePeriod.end_date)}
      </th>
      <td>
        {t("pages.employersClaimsReview.leaveSchedule.type_intermittent")}
      </td>
      <td>
        <div className="text-bold">
          {t("pages.employersClaimsReview.leaveSchedule.frequencyBasis", {
            context: getFormattedFrequencyBasis(),
          })}
        </div>
        <div>
          <Trans
            i18nKey="pages.employersClaimsReview.leaveSchedule.intermittentFrequencyDuration"
            tOptions={{
              context: getI18nContextForIntermittentFrequencyDuration(
                leavePeriod
              ),
              duration: leavePeriod.duration,
              durationBasis: leavePeriod.durationBasis,
              frequency: leavePeriod.frequency,
            }}
          />
        </div>
      </td>
    </tr>
  );
};

IntermittentLeaveSchedule.propTypes = {
  intermittentLeavePeriods: PropTypes.arrayOf(
    PropTypes.instanceOf(IntermittentLeavePeriod)
  ).isRequired,
};

export default IntermittentLeaveSchedule;
