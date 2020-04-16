import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { updateFieldFromEvent } from "../../actions";
import { useTranslation } from "../../locales/i18n";
import valueWithFallback from "../../utils/valueWithFallback";

export const Name = (props) => {
  const { t } = useTranslation();
  const formData = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsName.title")}
      nextPage={routes.claims.dateOfBirth}
    >
      <FormLabel
        component="legend"
        hint={t("pages.claimsName.nameSectionHint")}
      >
        {t("pages.claimsName.sectionLabel")}
      </FormLabel>
      <InputText
        name="firstName"
        value={valueWithFallback(formData.firstName)}
        label={t("pages.claimsName.firstNameLabel")}
        onChange={props.updateFieldFromEvent}
        smallLabel
      />
      <InputText
        name="middleName"
        value={valueWithFallback(formData.middleName)}
        label={t("pages.claimsName.middleNameLabel")}
        onChange={props.updateFieldFromEvent}
        optionalText={t("components.form.optionalText")}
        smallLabel
      />
      <InputText
        name="lastName"
        value={valueWithFallback(formData.lastName)}
        label={t("pages.claimsName.lastNameLabel")}
        onChange={props.updateFieldFromEvent}
        smallLabel
      />
    </QuestionPage>
  );
};

Name.propTypes = {
  formData: PropTypes.shape({
    firstName: PropTypes.string,
    middleName: PropTypes.string,
    lastName: PropTypes.string,
  }).isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent };

export default connect(mapStateToProps, mapDispatchToProps)(Name);
