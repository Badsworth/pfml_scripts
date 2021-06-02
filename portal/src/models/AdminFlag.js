import BaseModel from "./BaseModel";

class FlagModel extends BaseModel {
  get defaults() {
    return {
      flag_id: null,
      name: null,
      enabled: false,
      options: {},
      start: null,
      end: null,
    };
  }
}

export default FlagModel;
