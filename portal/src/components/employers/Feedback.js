import React, { useState } from "react";
import Button from "../Button";
import ConditionalContent from "../ConditionalContent";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { get } from "lodash";
import routeWithParams from "../../utils/routeWithParams";
import { useRouter } from "next/router";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comments
 * in the Leave Admin claim review page.
 */

const Feedback = (props) => {
  const { t } = useTranslation();
  const router = useRouter();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [formState, setFormState] = useState({
    hasComments: "false",
    comments: "",
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
      name === "hasComments" && value === "false";

    if (hasSelectedNoCommentOption) {
      setUploadedFiles([]);
      updateFields({
        [name]: value,
        comments: "",
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
    const route = routeWithParams("employers.success", {
      absence_id: props.absenceId,
    });
    router.push(route);
  };

  return (
    <React.Fragment>
      <form id="employer-feedback-form" onSubmit={handleSubmit}>
        <InputChoiceGroup
          choices={[
            {
              checked: formState.hasComments === "false",
              label: t("pages.employersClaimsReview.feedback.choiceNo"),
              value: "false",
            },
            {
              checked: formState.hasComments === "true",
              label: t("pages.employersClaimsReview.feedback.choiceYes"),
              value: "true",
            },
          ]}
          label={
            <ReviewHeading level="2">
              {t("pages.employersClaimsReview.feedback.instructionsLabel")}
            </ReviewHeading>
          }
          name="hasComments"
          onChange={handleOnChange}
          type="radio"
        />
        <ConditionalContent
          getField={getField}
          clearField={clearField}
          updateFields={updateFields}
          visible={formState.hasComments === "true"}
        >
          <React.Fragment>
            <FormLabel className="usa-label" htmlFor="comments" small>
              {t("pages.employersClaimsReview.feedback.tellUsMoreLabel")}
            </FormLabel>
            <textarea
              className="usa-textarea"
              name="comments"
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
  absenceId: PropTypes.string.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default Feedback;
