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
    additionalComments: "false",
    comment: "",
  });

  const getField = (fieldName) => {
    return get(formState, fieldName);
  };

  const updateFields = (fields) => {
    setFormState({ ...formState, ...fields });
  };

  const removeField = (fieldName) => {
    setFormState({
      ...formState,
      [fieldName]: "",
    });
  };

  const handleOnChange = (event) => {
    const { name, value } = event.target;
    if (name === "additionalComments" && value === "false") {
      setUploadedFiles([]);
    }

    setFormState({
      ...formState,
      [event.target.name]: event.target.value,
    });
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
              checked: formState.additionalComments === "false",
              label: t("pages.employersClaimsReview.feedback.choiceNo"),
              value: "false",
            },
            {
              checked: formState.additionalComments === "true",
              label: t("pages.employersClaimsReview.feedback.choiceYes"),
              value: "true",
            },
          ]}
          label={
            <ReviewHeading level="2">
              {t("pages.employersClaimsReview.feedback.instructionsLabel")}
            </ReviewHeading>
          }
          name="additionalComments"
          onChange={handleOnChange}
          type="radio"
        />
        <ConditionalContent
          fieldNamesClearedWhenHidden={["comment"]}
          getField={getField}
          removeField={removeField}
          updateFields={updateFields}
          visible={formState.additionalComments === "true"}
        >
          <React.Fragment>
            <FormLabel className="usa-label" htmlFor="employer-comment" small>
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
  appLogic: PropTypes.object.isRequired,
  absenceId: PropTypes.string,
  onSubmit: PropTypes.func,
};

export default Feedback;
