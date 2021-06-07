import React, { useState } from "react";
import {
  isFeatureEnabled,
  updateCookieWithFlag,
} from "src/services/featureFlags";
import InputChoiceGroup from "src/components/InputChoiceGroup";
import featureFlags from "../../config/featureFlags";

export default {
  title: "Feature flags",
};

export const Default = () => {
  /**
   * Reads the feature flag values and generates the choice objects for the field component
   * @returns {Array<{ label: string, value: string, checked: boolean }>}
   */
  const getFeatureFlagChoices = () => {
    const flags = featureFlags();
    return Object.keys(flags).map((featureName) => ({
      label: featureName,
      value: featureName,
      checked: isFeatureEnabled(featureName),
    }));
  };

  const handleChange = (evt) => {
    updateCookieWithFlag(evt.target.value, String(evt.target.checked));
    setChoices(getFeatureFlagChoices());
  };

  const [choices, setChoices] = useState(getFeatureFlagChoices());

  return (
    <div className="usa-prose">
      <InputChoiceGroup
        choices={choices}
        label="Toggle feature flags"
        onChange={handleChange}
        name="flags"
      />

      <p>
        Note to engineers: if you're toggling these in the localhost instance of
        Storybook, these feature flag settings will also apply to your localhost
        instance of Portal.
      </p>
    </div>
  );
};
