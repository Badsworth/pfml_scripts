export const COMPONENTS = ["portal", "api", "fineos"];
export const ENVS = [
  "prod",
  "breakfix",
  "training",
  "trn2",
  "uat",
  "performance",
  "stage",
  "long",
  "cps-preview",
  "test",
  "infra-test",
];
export const GROUPS = [
  "Stable",
  "Unstable",
  "Morning",
  "Integration",
  "Targeted",
];
export const ENV_NOT_CONFIGURED = ["prod", "infra-test"];
export const ENV_OFFLINE = {};

export const extractGroup = (item, name) => {
  const group = item.metadata.groups.find((g) => g.name === name);
  if (group) {
    return group.value;
  }
  throw new Error(`Unable to determine ${name}`);
};

export const labelComponent = (name) => {
  if (!name) {
    return name;
  }
  switch (name) {
    case "api":
      return "API";
    default:
      return name[0].toUpperCase() + name.substring(1);
  }
};

export const labelEnv = (name) => {
  name = name.toLowerCase();
  switch (name) {
    case "test":
      return "Test/DT2";
    case "stage":
      return "Stage/IDT";
    case "cps-preview":
      return "CPS-Preview/DT3";
    case "breakfix":
      return "Breakfix/PFX";
    case "uat":
      return "UAT";
    case "long":
      return "LONG/DT4";
    case "training":
      return "Training/TRN";
    case "trn2":
      return "Training2/TRN2";
    default:
      return name[0].toUpperCase() + name.substring(1);
  }
};

export function setDefault(val, def) {
  if (val === undefined) {
    return def;
  }
  return val;
}

export function msToTime(duration) {
  var milliseconds = Math.floor((duration % 1000) / 100),
    seconds = Math.floor((duration / 1000) % 60),
    minutes = Math.floor((duration / (1000 * 60)) % 60),
    hours = Math.floor((duration / (1000 * 60 * 60)) % 24);

  hours = hours < 10 ? "0" + hours : hours;
  minutes = minutes < 10 ? "0" + minutes : minutes;
  seconds = seconds < 10 ? "0" + seconds : seconds;

  return hours + ":" + minutes + ":" + seconds + "." + milliseconds;
}
