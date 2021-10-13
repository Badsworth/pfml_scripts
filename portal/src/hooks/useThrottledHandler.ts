import { useEffect, useRef, useState } from "react";
import assert from "assert";

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
  const hasCanceled = useRef(false);

  const throttledHandler = async (...args) => {
    if (isThrottled) return;

    setIsThrottled(true);
    const resultPromise = asyncHandler(...args);

    // enforce that handler must return a promise
    assert(resultPromise instanceof Promise);
    await resultPromise;

    if (!hasCanceled.current) {
      setIsThrottled(false);
    }
  };

  useEffect(() => {
    // cancel callback when component is unmounted
    // to prevent setting isThrottled state
    return function cancelCallback() {
      hasCanceled.current = true;
    };
  }, []);

  throttledHandler.isThrottled = isThrottled;

  return throttledHandler;
};

export default useThrottledHandler;
