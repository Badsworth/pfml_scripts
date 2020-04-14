import { removeField, updateFieldFromEvent } from "../../actions";
import ConditionalContent from "../../components/ConditionalContent";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { connect } from "react-redux";
import routes from "../../routes";
import { useTranslation } from "react-i18next";
import valueWithFallback from "../../utils/valueWithFallback";

export const StateId = (props) => {
  const { t } = useTranslation();
  const { stateId, hasStateId } = props.formData;

  return (
    <QuestionPage
      title={t("pages.claimsStateId.title")}
      nextPage={routes.claims.ssn}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: hasStateId,
            label: t("pages.claimsStateId.hasIdChoiceYes"),
            value: "true",
          },
          {
            checked: !hasStateId && hasStateId !== undefined,
            label: t("pages.claimsStateId.hasIdChoiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsStateId.hasIdChoiceLabel")}
        name="hasStateId"
        onChange={props.updateFieldFromEvent}
        type="radio"
      />

      <ConditionalContent
        fieldNamesClearedWhenHidden={["stateId"]}
        removeField={props.removeField}
        visible={hasStateId}
      >
        <InputText
          name="stateId"
          label={t("pages.claimsStateId.idLabel")}
          value={valueWithFallback(stateId)}
          onChange={props.updateFieldFromEvent}
        />
      </ConditionalContent>
    </QuestionPage>
  );
};

StateId.propTypes = {
  formData: PropTypes.shape({
    hasStateId: PropTypes.bool,
    stateId: PropTypes.string,
  }).isRequired,
  removeField: PropTypes.func.isRequired,
  updateFieldFromEvent: PropTypes.func.isRequired,
};

const mapStateToProps = (state) => ({
  formData: state.form,
});

const mapDispatchToProps = { updateFieldFromEvent, removeField };

export default connect(mapStateToProps, mapDispatchToProps)(StateId);
