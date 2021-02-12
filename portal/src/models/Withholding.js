import BaseModel from "./BaseModel";

class Withholding extends BaseModel {
  get defaults() {
    return {
      filing_period: null,
    };
  }
}

export default Withholding;
