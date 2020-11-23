import React, { useEffect, useState } from "react";
import ConditionalContent from "../ConditionalContent";
import FileCardList from "../FileCardList";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comment
 * in the Leave Admin claim review page.
 */

const Feedback = ({ appLogic, comment, setComment, employerDecision }) => {
  // TODO (EMPLOYER-583) add frontend validation
  const { t } = useTranslation();
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [hasComment, setHasComment] = useState(false);

  useEffect(() => {
    if (!hasComment) {
      setUploadedFiles([]);
      setComment("");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasComment]);

  useEffect(() => {
    setHasComment(employerDecision === "Deny" || !!comment);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employerDecision]);

  return (
    <React.Fragment>
      <InputChoiceGroup
        choices={[
          {
            checked: !hasComment,
            disabled: employerDecision === "Deny",
            label: t("pages.employersClaimsReview.feedback.choiceNo"),
            value: "false",
          },
          {
            checked: hasComment,
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
        onChange={(event) => setHasComment(event.target.value === "true")}
        type="radio"
      />
      <ConditionalContent
        getField={() => comment}
        clearField={() => setComment("")}
        updateFields={(event) => setComment(event.target.value)}
        visible={hasComment}
      >
        <React.Fragment>
          <FormLabel className="usa-label" htmlFor="comment" small>
            {t("pages.employersClaimsReview.feedback.tellUsMoreLabel")}
          </FormLabel>
          <textarea
            className="usa-textarea"
            name="comment"
            onChange={(event) => setComment(event.target.value)}
          />
          <FormLabel small>
            {t(
              "pages.employersClaimsReview.feedback.supportingDocumentationLabel"
            )}
          </FormLabel>
          <FileCardList
            filesWithUniqueId={uploadedFiles}
            setFiles={setUploadedFiles}
            setAppErrors={appLogic.setAppErrors}
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
    </React.Fragment>
  );
};

Feedback.propTypes = {
  appLogic: PropTypes.shape({
    setAppErrors: PropTypes.func.isRequired,
  }).isRequired,
  comment: PropTypes.string.isRequired,
  employerDecision: PropTypes.oneOf(["Approve", "Deny"]),
  setComment: PropTypes.func.isRequired,
};

export default Feedback;
