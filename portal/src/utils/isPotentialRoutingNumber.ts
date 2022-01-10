export const isPotentialRoutingNumber = (accountNum: string): boolean => {
  if (!accountNum || accountNum.length !== 9) {
    return false;
  }
  const n = computeChecksum(accountNum);
  if (n !== 0 && n % 10 === 0) {
    return true;
  } else {
    return false;
  }
};

/**
 * This is an algorithm to validate routing numbers.
 * http://en.wikipedia.org/wiki/Routing_transit_number#Check_digit
 *
 * We are using it here to surface to the claimant when they may have mistakenly entered
 * a routing number in place of an account number.
 *
 * We do also have this logic on the backend. see pfml/util/routing_number_validation.py
 */
const computeChecksum = (num: string): number => {
  let n = 0;
  for (let i = 0; i < num.length; i += 3) {
    n +=
      parseInt(num.charAt(i), 10) * 3 +
      parseInt(num.charAt(i + 1), 10) * 7 +
      parseInt(num.charAt(i + 2), 10);
  }

  return n;
};
