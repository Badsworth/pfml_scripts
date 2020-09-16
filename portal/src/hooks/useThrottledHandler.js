import assert from "assert";
import { useState } from "react";

/**
 * @callback asyncHandler
 * @param {Event} DOM event
 * @returns {Promise}
 */

/**
 * Hook that prevents simultaneous calls for react event handlers
 * @param {Function} asyncHandler - async react event handler
 * @returns {Function} { throttledHandler, throttledHandler.isThrottled }
 */
const useThrottledHandler = (asyncHandler) => {
  const [isThrottled, setIsThrottled] = useState(false);

  const throttledHandler = async (...args) => {
    if (isThrottled) return;

    setIsThrottled(true);
    // eslint-disable-next-line standard/no-callback-literal
    const resultPromise = asyncHandler(...args);
    // enforce that handler must return a promise
    assert(resultPromise instanceof Promise);
    await resultPromise;

    setIsThrottled(false);
  };

  throttledHandler.isThrottled = isThrottled;

  return throttledHandler;
};

export default useThrottledHandler;
