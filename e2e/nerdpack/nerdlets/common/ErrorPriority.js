export const CATEGORY_PRIORITY = {
  content: {
    "potential-edm": "EDM",
    "test-update": "HIGH",
  },
  infrastructure: {
    "timeout-service": "LOW",
    authentication: "HIGH",
    "authentication-sso": "HIGH",
    "failure-400": "EDM",
    "failure-500": "EDM",
    "failure-503": "MEDIUM",
    "failure-504": "LOW",
  },
  known: { priority: "LOW" },
  notification: { priority: "MEDIUM" },
};

export const ERROR_PRIORITY = ["EDM", "HIGH", "MEDIUM", "LOW"];

export function getErrorPriority(cat, sub) {
  if (CATEGORY_PRIORITY[cat]) {
    if (CATEGORY_PRIORITY[cat].priority) {
      return CATEGORY_PRIORITY[cat]?.priority;
    }
    if (CATEGORY_PRIORITY[cat][sub]) {
      return CATEGORY_PRIORITY[cat][sub];
    }
  }
  return "HIGH";
}

export function getCategoriesByPriority(priority) {
  priority = priority.toUpperCase();
  let returnValues = [];
  Object.keys(CATEGORY_PRIORITY).map((cat) => {
    if (CATEGORY_PRIORITY[cat]?.priority === priority) {
      returnValues.push({ category: cat });
    } else {
      Object.keys(CATEGORY_PRIORITY[cat]).map((sub) => {
        if (CATEGORY_PRIORITY[cat][sub] === priority) {
          returnValues.push({ category: cat, subCategory: sub });
        }
      });
    }
  });
  return returnValues;
}
