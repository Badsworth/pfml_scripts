import {
  BlockText,
  Card,
  CardBody,
  HeadingText,
  Link,
  navigation,
  Popover,
  PopoverBody,
  PopoverFooter,
  PopoverTrigger,
} from "nr1";
import { format } from "date-fns";
import React from "react";

export function E2EVisualIndicator({ run, runIds }) {
  let state = "error";
  if (run.pass_rate >= 0.85) {
    state = "warn";
  }
  if (run.pass_rate == 1) {
    state = "ok";
  }
  const passRate = Math.round(run.pass_rate * 100);
  const link = navigation.getOpenStackedNerdletLocation({
    id: "e2e-tests",
    urlState: { runIds: runIds },
  });
  return (
    <Popover openOnHover={true}>
      <PopoverTrigger>
        <Link to={link} className={`e2e-run-indicator ${state}`}>
          <span className={"visually-hidden"}>{state}</span>
          {passRate}
        </Link>
      </PopoverTrigger>
      <PopoverBody>
        <Card style={{ width: "250px" }}>
          <CardBody>
            <HeadingText>{format(run.timestamp, "PPPppp")}</HeadingText>
            <BlockText
              spacingType={[
                BlockText.SPACING_TYPE.MEDIUM,
                BlockText.SPACING_TYPE.NONE,
              ]}
            >
              {run.tag
                .split(",")
                .filter((tag) => !tag.includes("Env-") && tag != "Deploy")}
            </BlockText>
          </CardBody>
        </Card>
        <PopoverFooter style={{ textAlign: "right" }}>
          <Link to={run.runUrl}>View in Cypress</Link>
        </PopoverFooter>
      </PopoverBody>
    </Popover>
  );
}
