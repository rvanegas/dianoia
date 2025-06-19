import ReactMarkdown from "react-markdown";


function MessageBubble({ role, content }: { role: string, content: string }) {
  const isUser = role === "user";

  return (
    <div
      className={`flex flex-col max-w-full my-2 ${
        isUser ? "items-end" : "items-start"
      }`}>
      <p className={`italic ${
        isUser ? "text-indigo-500" : "text-slate-400"
      }`}>
        {isUser ? "You" : "Dianoia"}
      </p>

      <div
        className={`max-w-[85%] px-4 font-serif ${
          isUser
            ? "text-white bg-indigo-500 rounded-2xl rounded-tr-none"
            : "text-slate-700 bg-slate-100 rounded-2xl rounded-tl-none"
        }`}>
        <div className={`font-serif prose prose-sm prose-p:my-[2px] prose-pre:my-[2px] prose-pre:rounded-md dark:prose-invert ${
          isUser ? 'text-white' : 'text-slate-700'
        }`}>
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
