export type Props = {
  title: string;
};

const Loading = ({ title }: Props) => {
  return (
    <div className="loading">
      <div className="loading__container">
        <h1 className="loading__title">{title}</h1>
        <p className="loading__description">
          This may take a few seconds, please don’t close this page.
        </p>
      </div>
    </div>
  );
};

export default Loading;
