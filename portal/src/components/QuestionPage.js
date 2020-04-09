import BackButton from "./BackButton";
import PropTypes from "prop-types";
import React from "react";
import Title from "./Title";
import { useRouter } from "next/router";
import { useTranslation } from "react-i18next";

/**
 * This is a page template for form questions, including back link and continue
 * (submit) button.
 *
 * Note: If you add a fieldset as the first child inside this template, there
 * will be inconsistent spacing between the title and the rest of the contents.
 */
export const QuestionPage = (props) => {
  const { t } = useTranslation();
  const router = useRouter();

  const handleSubmit = (event) => {
    event.preventDefault();
    router.push(props.nextPage);
    // TODO handle submission of data to API
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
   * The contents of the form question page.
   */
  children: PropTypes.node.isRequired,
  /**
   * The route for the next page in the form, relative to the portal root.
   */
  nextPage: PropTypes.string.isRequired,
  /**
   * The text of the small title of the form.
   */
  title: PropTypes.node.isRequired,
};

export default QuestionPage;
