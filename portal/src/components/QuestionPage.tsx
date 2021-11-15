import BackButton from "./BackButton";
import Button from "./core/Button";
import React from "react";
import Title from "./core/Title";
import tracker from "../services/tracker";
import useThrottledHandler from "../hooks/useThrottledHandler";
import { useTranslation } from "../locales/i18n";

interface QuestionPageProps {
  /**
   * The contents of the form question page.
   */
  children: React.ReactNode;
  continueButtonLabel?: string;
  /**
   * The text of the small title of the form.
   */
  title: React.ReactNode;
  /**
   * Function that performs the save operation. Can be asynchronous.
   */
  onSave: () => Promise<void>;
  /**
   * A data selector to support end-to-end testing with Cypress.js
   */
  dataCy?: string;
}

/**
 * This is a page template for form questions, including back link and continue
 * (submit) button.
 *
 * Note: If you add a fieldset as the first child inside this template, there
 * will be inconsistent spacing between the title and the rest of the contents.
 */
export const QuestionPage = (props: QuestionPageProps) => {
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
          {props.continueButtonLabel ?? t("components.form.continueButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

export default QuestionPage;
