import React, { useState } from "react";
import Button from "../Button";
import ConditionalContent from "../ConditionalContent";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { get } from "lodash";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comment
 * in the Leave Admin claim review page.
 */

const Feedback = (props) => {
  const { t } = useTranslation();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [formState, setFormState] = useState({
    hasComment: "false",
    comment: "",
  });

  const getField = (fieldName) => {
    return get(formState, fieldName);
  };

  const updateFields = (fields) => {
    setFormState({ ...formState, ...fields });
  };

  const clearField = (fieldName) => {
    setFormState({
      ...formState,
      [fieldName]: "",
    });
  };

  const handleOnChange = (event) => {
    const { name, value } = event.target;
    const hasSelectedNoCommentOption =
      name === "hasComment" && value === "false";

    if (hasSelectedNoCommentOption) {
      setUploadedFiles([]);
      updateFields({
        [name]: value,
        comment: "",
      });
    } else {
      updateFields({
        [name]: value,
      });
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    props.onSubmit({ ...formState, uploadedFiles });
  };

  return (
    <React.Fragment>
      <form id="employer-feedback-form" onSubmit={handleSubmit}>
        <InputChoiceGroup
          choices={[
            {
              checked: formState.hasComment === "false",
              label: t("pages.employersClaimsReview.feedback.choiceNo"),
              value: "false",
            },
            {
              checked: formState.hasComment === "true",
              label: t("pages.employersClaimsReview.feedback.choiceYes"),
              value: "true",
            },
          ]}
          label={
            <ReviewHeading level="2">
              {t("pages.employersClaimsReview.feedback.instructionsLabel")}
            </ReviewHeading>
          }
          name="hasComment"
          onChange={handleOnChange}
          type="radio"
        />
        <ConditionalContent
          getField={getField}
          clearField={clearField}
          updateFields={updateFields}
          visible={formState.hasComment === "true"}
        >
          <React.Fragment>
            <FormLabel className="usa-label" htmlFor="comment" small>
              {t("pages.employersClaimsReview.feedback.tellUsMoreLabel")}
            </FormLabel>
            <textarea
              className="usa-textarea"
              name="comment"
              onChange={handleOnChange}
            />
            <FormLabel small>
              {t(
                "pages.employersClaimsReview.feedback.supportingDocumentationLabel"
              )}
            </FormLabel>
            <FileCardList
              files={uploadedFiles}
              setFiles={setUploadedFiles}
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
        </ConditionalContent>
        <Button className="margin-top-4" type="submit">
          {t("pages.employersClaimsReview.submitButton")}
        </Button>
      </form>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.shape({
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default Feedback;
