import Table from "../components/Table";
import StatusIcon from "../components/StatusIcon";
import Badge from "../components/Badge";
import Toggle from "../components/Toggle";
import VerticalMenu from "../components/VerticalMenu";

const getFeatureDetails = function ({
  status,
  title,
  description,
  badges,
}: {
  status: boolean;
  title: string;
  description: string;
  badges: string[];
}) {
  return (
    <div className="features-row__section1">
      <StatusIcon status={status} />
      <p className="features-row__title">Caring leave type</p>

      <p className="features-row__description">
        When this flag is enabled, the “Care for a family member with a serious
        health condition” leave reason is available in the claimant and leave
        admin portal.
      </p>

      <div className="features-row__badges">
        {badges.map((badge: string, index: number) => (
          <Badge key={index} type={badge} />
        ))}
      </div>
    </div>
  );
};

const getFlagNameDetails = function ({
  flagName,
  status,
}: {
  flagName: string;
  status: boolean;
}) {
  const options = ["Enable", "Disable"];
  const selected = status ? "Enable" : "Disable";

  return (
    <>
      <section className="features-flagname">
        <span className="features-flagname__text">{flagName}</span>
      </section>

      <section className="features-status">
        <div className="features__toggle-container">
          <Toggle status={status} />
        </div>

        <div className="features__menu-container">
          <VerticalMenu options={options} selected={selected} />
        </div>
      </section>
    </>
  );
};

export default function Features() {
  return (
    <div className="features container">
      <h1 className="container__title">Features</h1>

      <Table
        rows={[
          {
            status: true,
            badges: ["employee", "leave-admin"],
            title: "Caring leave type",
            description:
              "When this flag is enabled, the “Care for a family member with a serious health condition” leave reason is available in the claimant and leave admin portal.",
            flagName: "showCaringLeaveType",
          },
          {
            status: false,
            badges: ["employee", "leave-admin"],
            title: "Caring leave type",
            description:
              "When this flag is enabled, the “Care for a family member with a serious health condition” leave reason is available in the claimant and leave admin portal.",
            flagName: "showCaringLeaveType",
          },
        ]}
        cols={[
          {
            title: "Feature",
            width: "55%",
            content: getFeatureDetails,
          },
          {
            title: "Flag Name",
            width: "45%",
            content: getFlagNameDetails,
          },
        ]}
      />
    </div>
  );
}
