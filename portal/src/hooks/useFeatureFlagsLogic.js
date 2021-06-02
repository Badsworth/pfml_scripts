import AdminApi from "../api/AdminApi";
import FlagModel from "../models/AdminFlag";
import { useState } from "react";

/**
 * Hook that defines feature flags state
 * @param {object} props.appErrorsLogic - Utilities for set application's error  state
 * @returns {object} { flags: Object, loadFeatureFlags: Function }
 */
const useFlagsLogic = ({ appErrorsLogic }) => {
    const flagModel = new FlagModel();
    const initialState = [{...flagModel}];
    
    const [flags, setFlags] = useState(initialState);
    const adminApi = new AdminApi();

    /**
     * Get current maintenance status from /flags/maintenance and set the result in the state
     */
    const loadFeatureFlags = async () => {
        appErrorsLogic.clearErrors();

        try {
            setFlags(await adminApi.getFlag("maintenance"));
        } catch (error) {
            appErrorsLogic.catchError(error);
        }
    };

    return {
        flags,
        loadFeatureFlags
    };

};

export default useFlagsLogic;
