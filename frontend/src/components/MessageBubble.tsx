import ReactMarkdown from "react-markdown";

type Message = {
  role: "user" | "assistant";
  content: string;
};

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex flex-col max-w-full my-2 ${
        isUser ? "items-end" : "items-start"
      }`}>
      <p className={`text-sm text-gray-500 italic ${
        isUser ? "text-sagegreen" : "text-umber"
      }`}>
        {isUser ? "You" : "Dianoia"}
      </p>

      <div
        className={`max-w-[85%] px-4 font-serif border break-words ${
          isUser
            ? "bg-sagegreen text-ivory rounded-2xl rounded-tr-none text-right"
            : "text-umber border-umber rounded-2xl rounded-tl-none text-left"
        }`}>
        <div className={`font-serif prose prose-sm prose-p:my-1 prose-pre:my-2 prose-pre:rounded-md dark:prose-invert ${
          isUser ? "text-ivory" : "text-umber"
        }`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
