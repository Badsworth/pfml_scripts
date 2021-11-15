import React from "react";
import Button from "./Button";

export type Props = {
  children: React.ReactChild;
  showLogButton: boolean;
  onClickViewLog?: Function;
};

export default function InfoRow({
  children,
  showLogButton,
  onClickViewLog,
}: Props) {
  return (
    <>
      {children}
      {showLogButton && onClickViewLog && (
        <Button className="btn--plain btn--right" onClick={onClickViewLog}>
          View Log
        </Button>
      )}
    </>
  );
}
