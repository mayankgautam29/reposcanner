export default function ErrorNote({ message }) {
  return (
    <p role="alert" className="reveal border-l-4 border-vermilion bg-vermilion/10 px-5 py-4 font-mono text-sm">
      {message}
    </p>
  );
}
