import AddButton from "./AddButton";
import AmendableConcurrentLeave from "./AmendableConcurrentLeave";
import ConcurrentLeaveModel from "../../models/ConcurrentLeave";
import Heading from "../Heading";
import PropTypes from "prop-types";
import React from "react";
import Table from "../Table";
import { useTranslation } from "../../locales/i18n";

/**
 * Display a current leave taken by the employee
 * in the Leave Admin claim review page.
 */

const ConcurrentLeave = (props) => {
  const { t } = useTranslation();
  const {
    currentConcurrentLeave,
    getFunctionalInputProps,
    originalConcurrentLeave,
    updateFields,
  } = props;

  const addConcurrentLeave = () => {
    updateFields({
      concurrent_leave: new ConcurrentLeaveModel({
        is_for_current_employer: true,
      }),
    });
  };

  return (
    <React.Fragment>
      <Heading level="3">
        {t("components.employersConcurrentLeave.header")}
      </Heading>
      <p>{t("components.employersConcurrentLeave.explanation")}</p>
      <Table className="width-full">
        <thead>
          <tr>
            <th scope="col" colSpan="2">
              {t("components.employersConcurrentLeave.dateRangeLabel")}
            </th>
          </tr>
        </thead>
        <tbody>
          {originalConcurrentLeave ? (
            <AmendableConcurrentLeave
              getFunctionalInputProps={getFunctionalInputProps}
              isAddedByLeaveAdmin={false}
              originalConcurrentLeave={originalConcurrentLeave}
              updateFields={updateFields}
            />
          ) : (
            <tr>
              <th scope="row">{t("shared.noneReported")}</th>
              <td colSpan="3" />
            </tr>
          )}
          {currentConcurrentLeave && !originalConcurrentLeave && (
            <AmendableConcurrentLeave
              getFunctionalInputProps={getFunctionalInputProps}
              isAddedByLeaveAdmin
              originalConcurrentLeave={originalConcurrentLeave}
              updateFields={updateFields}
            />
          )}
          {!currentConcurrentLeave && (
            <tr>
              <td colSpan="2" className="padding-y-2 padding-left-0">
                <AddButton
                  label={t("components.employersConcurrentLeave.addButton")}
                  onClick={addConcurrentLeave}
                />
              </td>
            </tr>
          )}
        </tbody>
      </Table>
    </React.Fragment>
  );
};

ConcurrentLeave.propTypes = {
  currentConcurrentLeave: PropTypes.instanceOf(ConcurrentLeaveModel),
  getFunctionalInputProps: PropTypes.func.isRequired,
  originalConcurrentLeave: PropTypes.instanceOf(ConcurrentLeaveModel),
  updateFields: PropTypes.func.isRequired,
};

export default ConcurrentLeave;
