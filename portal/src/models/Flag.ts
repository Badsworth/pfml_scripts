class Flag {
  enabled = false;
  name: string | null = null;
  options: Record<string, unknown> = {};
  start: string | null = null;
  end: string | null = null;

  constructor(attrs: Partial<Flag>) {
    Object.assign(this, attrs);
  }
}

export default Flag;
