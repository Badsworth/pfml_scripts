import FeatureFlagsApi from "../api/FeatureFlagsApi";
import Flag from "../models/Flag";
import tracker from "../services/tracker";
import { useState } from "react";

/**
 * Hook that defines feature flags state
 * @returns {object} { flags: Object, getFlag: Function, loadFlags: Function }
 */
const useFlagsLogic = () => {
  const [flags, setFlags] = useState([]);
  const featureFlagsApi = new FeatureFlagsApi();

  /**
   * Get all feature flags set in the API
   */
  const loadFlags = async () => {
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
   * @returns {Flag}
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
