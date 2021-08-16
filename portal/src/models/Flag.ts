import BaseModel from "./BaseModel";

class Flag extends BaseModel {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'defaults' in type 'Flag' is not assignab... Remove this comment to see the full error message
  get defaults() {
    return {
      enabled: false,
      name: null,
      options: {},
      start: null,
      end: null,
    };
  }
}

export default Flag;
