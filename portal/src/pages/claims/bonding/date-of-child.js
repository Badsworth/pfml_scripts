import InputDate from "../../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../../components/QuestionPage";
import React from "react";
import get from "lodash/get";
import { pick } from "lodash";
import useFormState from "../../../hooks/useFormState";
import useHandleInputChange from "../../../hooks/useHandleInputChange";
import { useTranslation } from "../../../locales/i18n";
import valueWithFallback from "../../../utils/valueWithFallback";
import withClaim from "../../../hoc/withClaim";

const tempBondingDateOfChildField = "temp.leave_details.bonding.date_of_child";
export const fields = [`claim.${tempBondingDateOfChildField}`];

export const DateOfChild = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(pick(props, fields).claim);
  const handleInputChange = useHandleInputChange(updateFields);
  const handleSave = () => {
    props.appLogic.updateClaim(props.claim.application_id, formState);
  };

  return (
    <QuestionPage
      title={t("pages.claimsBondingDateOfChild.title")}
      onSave={handleSave}
    >
      <InputDate
        name={tempBondingDateOfChildField}
        label={t("pages.claimsBondingDateOfChild.sectionLabel")}
        hint={
          <React.Fragment>
            <p>{t("pages.claimsBondingDateOfChild.hint")}</p>
            <p>{t("components.form.dateInputHint")}</p>
          </React.Fragment>
        }
        value={valueWithFallback(get(formState, tempBondingDateOfChildField))}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={handleInputChange}
      />
    </QuestionPage>
  );
};

DateOfChild.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.object.isRequired,
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

export default withClaim(DateOfChild);
