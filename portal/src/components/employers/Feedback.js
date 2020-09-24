/* eslint-disable no-console */
import React, { useState } from "react";
import ButtonLink from "../ButtonLink";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import routeWithParams from "../../utils/routeWithParams";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comments
 * in the Leave Admin claim review page.
 */

const Feedback = (props) => {
  const { t } = useTranslation();
  const [isApplicationCorrect, setIsApplicationCorrect] = useState(true);
  const [employerReviewFiles, setEmployerReviewFiles] = useState([]);

  const handleInputChange = (event) => {
    setEmployerReviewFiles([]);
    setIsApplicationCorrect(
      event.target.value === t("pages.employersClaimsReview.feedback.choiceNo")
    );
    const employerComment = document.getElementById("employer-comment");
    if (employerComment && employerComment.value) {
      employerComment.value = "";
    }
  };

  return (
    <React.Fragment>
      <form id="employer-feedback-form">
        <InputChoiceGroup
          choices={[
            {
              checked: isApplicationCorrect,
              label: t("pages.employersClaimsReview.feedback.choiceNo"),
              value: t("pages.employersClaimsReview.feedback.choiceNo"),
              id: t("pages.employersClaimsReview.feedback.choiceNo"),
            },
            {
              label: t("pages.employersClaimsReview.feedback.choiceYes"),
              value: t("pages.employersClaimsReview.feedback.choiceYes"),
              id: t("pages.employersClaimsReview.feedback.choiceYes"),
            },
          ]}
          label={
            <ReviewHeading level="2">
              {t("pages.employersClaimsReview.feedback.instructionsLabel")}
            </ReviewHeading>
          }
          name="employer-review-options"
          onChange={handleInputChange}
          type="radio"
        />

        {!isApplicationCorrect && (
          <React.Fragment>
            <FormLabel className="usa-label" htmlFor="employer-comment" small>
              {t("pages.employersClaimsReview.feedback.tellUsMoreLabel")}
            </FormLabel>
            <textarea
              className="usa-textarea"
              id="employer-comment"
              name="employer-comment"
            />
            <FormLabel small>
              {t(
                "pages.employersClaimsReview.feedback.supportingDocumentationLabel"
              )}
            </FormLabel>
            <FileCardList
              files={employerReviewFiles}
              setFiles={setEmployerReviewFiles}
              setAppErrors={props.appLogic.setAppErrors}
              fileHeadingPrefix={t(
                "pages.employersClaimsReview.feedback.fileHeadingPrefix"
              )}
              addFirstFileButtonText={t(
                "pages.employersClaimsReview.feedback.addFirstFileButton"
              )}
              addAnotherFileButtonText={t(
                "pages.employersClaimsReview.feedback.addAnotherFileButton"
              )}
            />
          </React.Fragment>
        )}
        <ButtonLink
          href={routeWithParams("employers.success", {
            claim_id: props.claimId,
          })}
          className="margin-top-4"
        >
          {t("pages.employersClaimsReview.submitButton")}
        </ButtonLink>
      </form>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claimId: PropTypes.string,
};

export default Feedback;
