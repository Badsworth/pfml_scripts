import SpinnerIcon from "../../styles/icons/icon_glyphs/spinner.svg"

type Props = {
  title: string;
  loading: boolean;
};

const Loading = ({ title, loading }: Props) => {
  return (
    <div className="loading">
      <div className="loading__container">
        {loading && (<div className="loading__icon"><SpinnerIcon /></div>)}
        <h1 className="loading__title">{title}</h1>
        {loading && (
          <p className="loading__description">
            This may take a few seconds, please don’t close this page.
          </p>
        )}
      </div>
    </div>
  );
};

export default Loading;
