import { SyntheticEvent, useEffect, useRef, useState } from "react";

/**
 * Hook that prevents simultaneous calls for react event handlers
 */
const useThrottledHandler = <TEvent extends SyntheticEvent>(
  asyncHandler: (event: TEvent) => Promise<void>
) => {
  const [isThrottled, setIsThrottled] = useState(false);
  const hasCanceled = useRef(false);

  const throttledHandler = async (event: TEvent) => {
    if (isThrottled) return;

    setIsThrottled(true);
    await asyncHandler(event);

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
