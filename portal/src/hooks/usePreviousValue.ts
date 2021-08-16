import { useEffect, useRef } from "react";

/**
 * Access the previous value so you can compare it with the new value,
 * when it changes on subsequent renders. This is a hook version of
 * how `componentDidUpdate` would make a `prevProps` argument available.
 * @example const previousLength = usePreviousValue(entries.length);
 * @param {*} value
 * @returns {*} previous value
 * @see https://reactjs.org/docs/hooks-faq.html#how-to-get-the-previous-props-or-state
 */
function usePreviousValue(value) {
  const ref = useRef();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

export default usePreviousValue;
