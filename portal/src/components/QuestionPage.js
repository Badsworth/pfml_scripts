import BackButton from "./BackButton";
import PropTypes from "prop-types";
import React from "react";
import Title from "./Title";
import { useTranslation } from "../locales/i18n";

/**
 * This is a page template for form questions, including back link and continue
 * (submit) button.
 *
 * Note: If you add a fieldset as the first child inside this template, there
 * will be inconsistent spacing between the title and the rest of the contents.
 */
export const QuestionPage = (props) => {
  const { t } = useTranslation();

  const handleSubmit = async (event) => {
    event.preventDefault();
    await props.onSave(props.formState);
  };

  return (
    <React.Fragment>
      <BackButton />
      <form onSubmit={handleSubmit} className="usa-form usa-form--large">
        <Title small>{props.title}</Title>
        {props.children}
        <input
          className="usa-button"
          type="submit"
          value={t("components.form.continueButton")}
        />
      </form>
    </React.Fragment>
  );
};

QuestionPage.propTypes = {
  /**
   * The state of the form.
   * todo: remove this prop if it's no longer useful
   */
  formState: PropTypes.object,
  /**
   * The contents of the form question page.
   */
  children: PropTypes.node.isRequired,
  /**
   * The text of the small title of the form.
   */
  title: PropTypes.node.isRequired,
  /**
   * Function that performs the save operation. Can be asynchronous.
   */
  onSave: PropTypes.func.isRequired,
};

QuestionPage.defaultProps = {
  formState: {},
};

export default QuestionPage;
