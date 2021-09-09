import Badge, { Props as BadgeProps } from "../components/Badge";
import ConfirmationDialog from "../components/ConfirmationDialog";
import Table from "../components/Table";
import StatusIcon from "../components/StatusIcon";
import React from "react";
import Toggle from "../components/Toggle";
import VerticalMenu from "../components/VerticalMenu";

export default function Features() {
  const [showConfirmationDialog, setShowConfirmationDialog] =
    React.useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    // disable at API.
    setShowConfirmationDialog(false);
  };

  const getFeatureDetails = ({
    status,
    badges,
  }: {
    status: boolean;
    title: string;
    description: string;
    badges: BadgeProps["type"][];
    flagName: string;
  }) => {
    return (
      <div className="features-row__section1">
        <StatusIcon status={status} />
        <p className="features-row__title">Caring leave type</p>

        <p className="features-row__description">
          When this flag is enabled, the “Care for a family member with a
          serious health condition” leave reason is available in the claimant
          and leave admin portal.
        </p>

        <div className="features-row__badges">
          {badges.map((badge: BadgeProps["type"], index: number) => (
            <Badge key={index} type={badge} />
          ))}
        </div>
      </div>
    );
  };

  const getFlagNameDetails = ({
    flagName,
    status,
  }: {
    flagName: string;
    status: boolean;
  }) => {
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
            <VerticalMenu
              options={[
                {
                  enabled: !status,
                  onClick: () => setShowConfirmationDialog(true),
                  text: "Enable",
                  type: "button",
                },
                {
                  enabled: status,
                  onClick: () => setShowConfirmationDialog(true),
                  text: "Disable",
                  type: "button",
                },
              ]}
            />
          </div>
        </section>
      </>
    );
  };

  return (
    <div className="features container">
      <h1 className="container__title">Features</h1>
      {showConfirmationDialog && (
        <ConfirmationDialog
          title="Test"
          body="If maintenance is turned off, the maintenance takeover component will no longer be shown in the portal. The change may take up to 5 minutes for some users due to browser cache."
          handleCancelCallback={confirmationDialogCancelCallback}
          handleContinueCallback={confirmationDialogContinueCallback}
        />
      )}
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
