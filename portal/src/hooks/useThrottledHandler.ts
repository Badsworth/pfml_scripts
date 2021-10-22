import { useEffect, useRef, useState } from "react";

/**
 * Hook that prevents simultaneous calls for react event handlers
 */
const useThrottledHandler = <T>(
  asyncHandler: (...args: T[]) => Promise<void>
) => {
  const [isThrottled, setIsThrottled] = useState(false);
  const hasCanceled = useRef(false);

  const throttledHandler = async (...args: T[]) => {
    if (isThrottled) return;

    setIsThrottled(true);
    await asyncHandler(...args);

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
