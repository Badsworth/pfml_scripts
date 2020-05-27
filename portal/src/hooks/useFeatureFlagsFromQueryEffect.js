import { storeFeatureFlagsFromQuery } from "../services/featureFlags";
import { useEffect } from "react";

/**
 * Sets feature flags on initial page load based on the query string parameter.
 * This effect is only run on initial render of the app.
 */
function useFeatureFlagsFromQueryEffect() {
  useEffect(() => {
    // We read from location.search rather than the Next.js router.query since it's empty on
    // the very first render, which is relevant here since this callback is only called once
    // Related issue: https://github.com/zeit/next.js/issues/9066
    const searchParams = new URLSearchParams(window.location.search);

    storeFeatureFlagsFromQuery(searchParams);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  // Passing this ^ empty array causes this effect to be run only once upon mount. See:
  // https://reactjs.org/docs/hooks-effect.html#tip-optimizing-performance-by-skipping-effects
}

export default useFeatureFlagsFromQueryEffect;
