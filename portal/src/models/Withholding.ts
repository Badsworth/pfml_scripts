import BaseModel from "./BaseModel";

class Withholding extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'Withholding' is not a... Remove this comment to see the full error message
  get defaults() {
    return {
      filing_period: null,
    };
  }
}

export default Withholding;
