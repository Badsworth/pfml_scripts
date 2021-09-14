import Button from "./Button";

type Props = {
  title: string;
  description: string;
  buttonText?: string;
  onButtonClick?: () => void;
};

export default function ActionCard({
  title,
  description,
  buttonText = "",
  onButtonClick = () => {},
}: Props) {
  return (
    <div className="card">
      <div className="card__info">
        <h2 className="card__title">{title}</h2>
        {description && <p>{description}</p>}
      </div>
      <div className="card__controls">
        {buttonText && onButtonClick && (
          <Button className="card__btn btn--blue" onClick={onButtonClick}>
            {buttonText}
          </Button>
        )}
      </div>
    </div>
  );
}
