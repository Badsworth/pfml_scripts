type StringGenerator = () => string;

/**
 * Higher-order function for generating unique strings of a given pattern.
 */
const unique = (generator: StringGenerator): StringGenerator => {
  // Set of unique generated strings.
  const used = new Set();
  return () => {
    let value;
    let i = 0;
    do {
      if (i++ >= 100) {
        throw new Error(
          `It took 100 tries to generate a unique value. Add randomness`
        );
      }
      value = generator();
    } while (used.has(value));
    used.add(value);
    return value;
  };
};

export default unique;
