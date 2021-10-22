export type Props = {
  text: string;
  color: "green" | "blue";
};

const Tag = ({ text, color }: Props) => {
  return (
    <span className={`tag tag--${color}`} data-testid="tag">
      {text}
    </span>
  );
};

export default Tag;
