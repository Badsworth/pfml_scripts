import FormLabel from "../FormLabel";
import InputChoiceGroup from "../InputChoiceGroup";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import { Trans } from "react-i18next";
import classnames from "classnames";
import { useTranslation } from "../../locales/i18n";

/**
 * Display language and form for Leave Admin to include comment
 * in the Leave Admin claim review page.
 */

const Feedback = ({
  context,
  getFunctionalInputProps,
  shouldDisableNoOption,
  shouldShowCommentBox,
}) => {
  const { t } = useTranslation();
  const { errorMsg, name, onChange, value } =
    getFunctionalInputProps("comment");

  const commentClasses = classnames("usa-form-group", {
    "usa-form-group--error": !!errorMsg,
  });
  const textAreaClasses = classnames("usa-textarea margin-top-3", {
    "usa-input--error": !!errorMsg,
  });

  return (
    <React.Fragment>
      <InputChoiceGroup
        {...getFunctionalInputProps("should_show_comment_box")}
        smallLabel
        choices={[
          {
            checked: shouldShowCommentBox,
            label: t("components.employersFeedback.choiceYes"),
            value: "true",
          },
          {
            checked: !shouldShowCommentBox,
            disabled: shouldDisableNoOption,
            label: t("components.employersFeedback.choiceNo"),
            value: "false",
          },
        ]}
        label={
          <ReviewHeading level="2">
            {t("components.employersFeedback.instructionsLabel")}
          </ReviewHeading>
        }
        type="radio"
      />
      {shouldShowCommentBox && (
        <div className={commentClasses}>
          <FormLabel
            className="usa-label"
            htmlFor={name}
            small
            errorMsg={errorMsg}
          >
            <Trans
              data-test="feedback-comment-solicitation"
              i18nKey="components.employersFeedback.commentSolicitation"
              tOptions={{ context }}
            />
          </FormLabel>
          <textarea
            className={textAreaClasses}
            data-test="feedback-comment-textbox"
            name={name}
            onChange={onChange}
            value={value}
          />
        </div>
      )}
    </React.Fragment>
  );
};

Feedback.propTypes = {
  context: PropTypes.string.isRequired,
  getFunctionalInputProps: PropTypes.func.isRequired,
  shouldDisableNoOption: PropTypes.bool.isRequired,
  shouldShowCommentBox: PropTypes.bool.isRequired,
};

export default Feedback;
