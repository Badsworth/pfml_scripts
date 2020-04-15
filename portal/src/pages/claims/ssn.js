import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { updateFieldFromEvent } from "../../actions";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

/**
 * A form page to capture the worker's SSN or ITIN.
 */
export const Ssn = (props) => {
  const { t } = useTranslation();
  const formData = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsSsn.title")}
      // TODO Route this to address or occupation page what that page is ready.
      nextPage={routes.claims.duration}
    >
      {/* TODO(CP-296) Use masked field component for SSN styling. */}
      <InputText
        name="ssn"
        value={valueWithFallback(formData.ssn)}
        label={t("pages.claimsSsn.sectionLabel")}
        hint={t("pages.claimsSsn.sectionHint")}
        onChange={props.updateFieldFromEvent}
      />
    </QuestionPage>
  );
};

Ssn.propTypes = {
  formData: PropTypes.shape({
    ssn: PropTypes.string,
  }).isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent };

export default connect(mapStateToProps, mapDispatchToProps)(Ssn);
