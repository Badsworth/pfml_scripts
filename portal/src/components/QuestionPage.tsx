import BackButton from "./BackButton";
import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "./Title";
import tracker from "../services/tracker";
import useThrottledHandler from "../hooks/useThrottledHandler";
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

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();

    const resp = props.onSave();
    if (!(resp instanceof Promise)) {
      tracker.trackEvent(
        "onSave wasn't a Promise, so user isn't seeing a loading indicator."
      );
      // eslint-disable-next-line no-console
      console.warn("onSave should be a Promise");
    }
    await resp;
  });

  return (
    <React.Fragment>
      <BackButton />
      <form
        onSubmit={handleSubmit}
        data-cy={props.dataCy}
        className="usa-form"
        method="post"
      >
        <Title small>{props.title}</Title>
        {props.children}
        <Button
          className="margin-top-4"
          type="submit"
          loading={handleSubmit.isThrottled}
        >
          {t("components.form.continueButton")}
        </Button>
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
   * The text of the small title of the form.
   */
  title: PropTypes.node.isRequired,
  /**
   * Function that performs the save operation. Can be asynchronous.
   */
  onSave: PropTypes.func.isRequired,
  /**
   * A data selector to support end-to-end testing with Cypress.js
   */
  dataCy: PropTypes.string,
};

export default QuestionPage;
