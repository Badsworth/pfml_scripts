import React, { useEffect, useState } from "react";
import ConditionalContent from "../ConditionalContent";
import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import ReviewHeading from "../ReviewHeading";
import { Trans } from "react-i18next";
import classnames from "classnames";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comment
 * in the Leave Admin claim review page.
 */

const Feedback = ({
  getField,
  getFunctionalInputProps,
  isReportingFraud,
  isDenyingRequest,
  isEmployeeNoticeInsufficient,
  comment,
  updateFields,
}) => {
  // TODO (EMPLOYER-583) add frontend validation
  const { t } = useTranslation();
  const [shouldShowCommentBox, setShouldShowCommentBox] = useState(false);

  useEffect(() => {
    setShouldShowCommentBox(
      isDenyingRequest || isEmployeeNoticeInsufficient || !!comment
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDenyingRequest, isEmployeeNoticeInsufficient]);

  const buildContext = () => {
    if (isReportingFraud) return "fraud";
    if (!isReportingFraud && isDenyingRequest) return "employerDecision";
    if (!isDenyingRequest && isEmployeeNoticeInsufficient)
      return "employeeNotice";
  };

  const clearCommentBox = () => updateFields({ comment: "" });

  const { errorMsg, name, onChange } = getFunctionalInputProps("comment");

  const commentClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!errorMsg,
  });
  const textAreaClasses = classnames("usa-textarea margin-top-3", {
    "usa-input--error": !!errorMsg,
  });

  return (
    <React.Fragment>
      <InputChoiceGroup
        smallLabel
        choices={[
          {
            checked: shouldShowCommentBox,
            label: t("components.employersFeedback.choiceYes"),
            value: "true",
          },
          {
            checked: !shouldShowCommentBox,
            disabled: isDenyingRequest || isEmployeeNoticeInsufficient,
            label: t("components.employersFeedback.choiceNo"),
            value: "false",
          },
        ]}
        label={
          <ReviewHeading level="2">
            {t("components.employersFeedback.instructionsLabel")}
          </ReviewHeading>
        }
        name="shouldShowCommentBox"
        onChange={(event) => {
          setShouldShowCommentBox(event.target.value === "true");
        }}
        type="radio"
      />
      <ConditionalContent
        getField={getField}
        clearField={clearCommentBox}
        updateFields={updateFields}
        fieldNamesClearedWhenHidden={["comment"]}
        visible={shouldShowCommentBox}
      >
        <div className={commentClasses}>
          <FormLabel
            className="usa-label"
            htmlFor={name}
            small
            errorMsg={errorMsg}
          >
            <Trans
              i18nKey="components.employersFeedback.commentSolicitation"
              tOptions={{
                context: buildContext() || "",
              }}
            />
          </FormLabel>
          <textarea
            className={textAreaClasses}
            name={name}
            onChange={onChange}
          />
        </div>
      </ConditionalContent>
    </React.Fragment>
  );
};

Feedback.propTypes = {
  getField: PropTypes.func.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  isReportingFraud: PropTypes.bool,
  isDenyingRequest: PropTypes.bool,
  isEmployeeNoticeInsufficient: PropTypes.bool,
  comment: PropTypes.string.isRequired,
  updateFields: PropTypes.func.isRequired,
};

export default Feedback;
