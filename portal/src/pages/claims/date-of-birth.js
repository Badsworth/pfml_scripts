import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { updateFieldFromEvent } from "../../actions";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

export const DateOfBirth = (props) => {
  const { t } = useTranslation();
  const formData = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsDateOfBirth.title")}
      nextPage={routes.home}
    >
      <InputDate
        name="dateOfBirth"
        label={t("pages.claimsDateOfBirth.sectionLabel")}
        value={valueWithFallback(formData.dateOfBirth)}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        onChange={props.updateFieldFromEvent}
      />
    </QuestionPage>
  );
};

DateOfBirth.propTypes = {
  formData: PropTypes.shape({
    dateOfBirth: PropTypes.string,
  }).isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent };

export default connect(mapStateToProps, mapDispatchToProps)(DateOfBirth);
