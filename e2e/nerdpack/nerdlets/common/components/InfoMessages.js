import { Icon } from "nr1";

export function Warning(props) {
  return (
    <span className="message warning">
      <Icon type={Icon.TYPE.INTERFACE__STATE__WARNING} />
      {props.children}
    </span>
  );
}
