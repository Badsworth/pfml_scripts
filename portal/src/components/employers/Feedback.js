/* eslint-disable no-console */
import React, { useState } from "react";
import Button from "../Button";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
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

  const handleSubmit = async (event) => {
    event.preventDefault();
    const e = event.currentTarget;
    const submission = [
      "User Submitted:",
      `1. ${e["employer-review-options"].value}`,
      `2. ${
        e["employer-comment"] && e["employer-comment"].value
          ? e["employer-comment"].value
          : "No comment"
      }`,
    ];

    await printToConsole(submission.concat(getUploadedFiles()));
  };

  const getUploadedFiles = () => {
    const fileUpload = [];

    if (employerReviewFiles.length > 0) {
      fileUpload.push("3. Uploaded files:");
      employerReviewFiles.forEach((reviewFile) => {
        const { id, file } = reviewFile;
        fileUpload.push(`${id}: ${file.name}`);
      });
    } else {
      fileUpload.push("3. No uploaded files");
    }

    return fileUpload;
  };

  const printToConsole = (arr) => {
    const delimiter = "===============";

    console.log(delimiter);
    arr.forEach((string) => {
      console.log(string);
    });
    console.log(delimiter);
    return Promise.resolve();
  };

  return (
    <React.Fragment>
      <form
        onSubmit={handleSubmit}
        id="employer-feedback-form"
        className="usa-form"
      >
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
              {t("pages.employersClaimsReview.feedback.header")}
            </ReviewHeading>
          }
          hint={t("pages.employersClaimsReview.feedback.instructionsLabel")}
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

        <Button className="margin-top-4" type="submit">
          {t("pages.employersClaimsReview.submitButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default Feedback;
