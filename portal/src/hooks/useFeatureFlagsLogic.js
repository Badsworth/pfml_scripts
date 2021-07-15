import FeatureFlagsApi from "../api/FeatureFlagsApi";
import Flag from "../models/Flag";
import tracker from "../services/tracker";
import { useState } from "react";

/**
 * Hook that defines feature flags state. This will eventually replace services/featureFlags.js. 
 * @param {object} props
 * @param {object} props.appErrorsLogic - Utilities for set application's error state
 * @returns {object} { flags: Object, getFlag: Function, loadFlags: Function }
 */
const useFlagsLogic = ({ appErrorsLogic }) => {
  const [flags, setFlags] = useState([]);
  const featureFlagsApi = new FeatureFlagsApi();

  /**
   * Get current maintenance status from /flags/maintenance
   * and set the result in the state
   */
  const loadFlags = async () => {
    appErrorsLogic.clearErrors();

    try {
      setFlags(await featureFlagsApi.getFlags());
    } catch (error) {
      tracker.trackEvent("Feature flags API request failed", {
        errorMessage: error.message,
      });
    }
  };

  /**
   * Get and return a specific feature flag from the
   * set of flags
   * @param {string} flag_name - Flag name to retrieve
   * @returns {object} { flag }
   */
  const getFlag = (flag_name) => {
    return (
      new Flag(flags.filter((flag) => flag.name === flag_name)[0]) || new Flag()
    );
  };

  return {
    flags,
    getFlag,
    loadFlags,
  };
};

export default useFlagsLogic;
