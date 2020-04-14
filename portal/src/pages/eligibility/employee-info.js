import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { connect } from "react-redux";
import { updateFieldFromEvent } from "../../actions";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

export const EmployeeInfo = (props) => {
  const { t } = useTranslation();
  const router = useRouter();
  const formData = props.formData;

  const handleSubmit = (event) => {
    event.preventDefault();
    // the empoyeeId will ultimately be returned by API /employee endpoint
    // TODO replace with POST request to API /employee to get employeeId
    // https://lwd.atlassian.net/browse/CP-112
    const employeeId = "b05cbd07-03ba-46e7-a2b8-f3466ca1139c";
    // set a random eligibility result for mocking
    const eligibility = ["eligible", "exempt", "ineligible", "notfound"][
      Math.floor(Math.random() * 4)
    ];
    router.push(
      `/eligibility/result?mockEligibility=${eligibility}&employeeId=${employeeId}`
    );
  };

  return (
    <form onSubmit={handleSubmit} className="usa-form usa-form--large">
      <Title small>{t("pages.eligibility.form.title")}</Title>
      <fieldset className="usa-fieldset">
        <FormLabel
          component="legend"
          hint={t("pages.eligibility.form.nameSectionHint")}
        >
          {t("pages.eligibility.form.nameSectionLabel")}
        </FormLabel>
        <InputText
          name="firstName"
          value={valueWithFallback(formData.firstName)}
          label={t("pages.eligibility.form.firstNameLabel")}
          onChange={props.updateFieldFromEvent}
          smallLabel
        />
        <InputText
          name="middleName"
          value={valueWithFallback(formData.middleName)}
          label={t("pages.eligibility.form.middleNameLabel")}
          onChange={props.updateFieldFromEvent}
          optionalText={t("components.form.optionalText")}
          smallLabel
        />
        <InputText
          name="lastName"
          value={valueWithFallback(formData.lastName)}
          label={t("pages.eligibility.form.lastNameLabel")}
          onChange={props.updateFieldFromEvent}
          smallLabel
        />
      </fieldset>
      <div className="margin-top-5">
        <InputText
          name="ssnOrItin"
          value={valueWithFallback(formData.ssnOrItin)}
          label={t("pages.eligibility.form.ssnSectionLabel")}
          hint={t("pages.eligibility.form.ssnSectionHint")}
          onChange={props.updateFieldFromEvent}
          width="medium"
        />
      </div>
      <input
        className="usa-button"
        type="submit"
        value={t("components.form.submitButtonText")}
      />
    </form>
  );
};

EmployeeInfo.propTypes = {
  formData: PropTypes.shape({
    firstName: PropTypes.string,
    middleName: PropTypes.string,
    lastName: PropTypes.string,
    ssnOrItin: PropTypes.string,
  }).isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = (dispatch) => ({
  updateFieldFromEvent: (event) => dispatch(updateFieldFromEvent(event)),
});

export default connect(mapStateToProps, mapDispatchToProps)(EmployeeInfo);
