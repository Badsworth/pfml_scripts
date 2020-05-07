import Claim from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import routes from "../../routes";
import useFormState from "../../hooks/useFormState";
import useHandleInputChange from "../../hooks/useHandleInputChange";
import { useTranslation } from "../../locales/i18n";

/**
 * A form page to capture a user's attestation of having notified their employer.
 */
const NotifiedEmployer = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState(props.claim);
  const { notified } = formState;
  const handleInputChange = useHandleInputChange(updateFields);

  // TODO call API
  const handleSave = async () => {};

  return (
    <QuestionPage
      formState={formState}
      title={t("pages.claimsNotifiedEmployer.title")}
      onSave={handleSave}
      nextPage={routes.home}
    >
      <InputChoiceGroup
        choices={[
          {
            checked: notified === true,
            label: t("pages.claimsNotifiedEmployer.choiceYes"),
            value: "true",
          },
          {
            checked: notified === false,
            label: t("pages.claimsNotifiedEmployer.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsNotifiedEmployer.label")}
        hint={t("pages.claimsNotifiedEmployer.hint")}
        // TODO Align field name with API
        name="notified"
        onChange={handleInputChange}
        type="radio"
      />
    </QuestionPage>
  );
};

NotifiedEmployer.propTypes = {
  claim: PropTypes.instanceOf(Claim),
};

export default NotifiedEmployer;
