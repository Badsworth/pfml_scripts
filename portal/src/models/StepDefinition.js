/* eslint sort-keys: ["error", "asc"] */
import BaseModel from "./BaseModel";

/**
 * A grouping of pages, and their corresponding fields, that make up a
 * specific section of a user flow
 * @returns {StepDefinition}
 */
class StepDefinition extends BaseModel {
  get defaults() {
    return {
      // array of StepDefinitions this StepDefinition depends on
      dependsOn: [],
      name: null,
      // array of pages with structure
      // { route: routes.name, fields: [] }
      pages: [],
    };
  }

  get fields() {
    return this.pages.flatMap((page) => page.fields);
  }

  get initialPage() {
    // TODO, remove OR when all steps are complete
    return (this.pages[0] || {}).route || "#";
  }
}

export default StepDefinition;
