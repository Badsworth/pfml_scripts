import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../ReviewHeading";
import Table from "../Table";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a current leave taken by the employee
 * in the Leave Admin claim review page.
 */

const ConcurrentLeave = (props) => {
  const { t } = useTranslation();
  const { appErrors, concurrentLeave, onChange } = props;

  return (
    <React.Fragment>
      <ReviewHeading level="2">
        {t("components.employersConcurrentLeave.header")}
      </ReviewHeading>
      <p>{t("components.employersConcurrentLeave.explanation")}</p>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col">
              {t("components.employersConcurrentLeave.dateRangeLabel")}
            </th>
          </tr>
        </thead>
        <tbody>
          {concurrentLeave ? (
            <AmendableConcurrentLeave
              appErrors={appErrors}
              concurrentLeave={concurrentLeave}
              onChange={onChange}
            />
          ) : (
            <tr>
              <th scope="row">{t("shared.noneReported")}</th>
              <td colSpan="3" />
            </tr>
          )}
        </tbody>
      </Table>
      <p>{t("components.employersConcurrentLeave.commentInstructions")}</p>
    </React.Fragment>
  );
};

ConcurrentLeave.propTypes = {
  appErrors: PropTypes.instanceOf(AppErrorInfoCollection).isRequired,
  onChange: PropTypes.func.isRequired,
  concurrentLeave: PropTypes.instanceOf(ConcurrentLeaveModel),
};

export default ConcurrentLeave;
