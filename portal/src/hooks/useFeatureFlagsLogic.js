import AdminApi from "../api/AdminApi";
import Flag from "../models/Flag";
import { useState } from "react";

/**
 * Hook that defines feature flags state
 * @param {object} props
 * @param {object} props.appErrorsLogic - Utilities for set application's error state
 * @returns {object} { flags: Object, getFlag: Function, loadFlags: Function }
 */
const useFlagsLogic = ({ appErrorsLogic }) => {
  const flagModel = new Flag();
  const initialState = [flagModel];

  const [flags, setFlags] = useState(initialState);
  const adminApi = new AdminApi();

  /**
   * Get current maintenance status from /flags/maintenance
   * and set the result in the state
   */
  const loadFlags = async () => {
    appErrorsLogic.clearErrors();

    try {
      setFlags(await adminApi.getFlags());
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Get and return a specific feature flag from the
   * set of flags
   * @param {string} flag_name - Flag name to retrieve
   * @returns {object|null} { flag } or null
   */
  const getFlag = (flag_name) => {
    return flags.filter((flag) => flag.name === flag_name)[0] || null;
  };

  return {
    flags,
    getFlag,
    loadFlags,
  };
};

export default useFlagsLogic;
