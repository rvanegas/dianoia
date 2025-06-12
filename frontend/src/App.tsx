import "./App.css";

import { useEffect, useRef, useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";

type Message = {
  role: "user" | "assistant";
  content: string;
};

function App() {
  const [prompt, setPrompt] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const handleSend = async () => {
    if (!prompt.trim()) return;
    const userMessage: Message = { role: "user", content: prompt };
    const newMessages = [...messages, userMessage];
    setPrompt("");
    setMessages((prev) => newMessages);
    setLoading(true);
    try {
      const response = await axios.post("http://localhost:8000/api/chat", {
        prompt,
        history: newMessages,
      });
      const botMessage: Message = {
        role: "assistant",
        content: response.data.reply,
      };
      setMessages((prev) => [...newMessages, botMessage]);
      setPrompt("");
    } catch (error) {
      console.log("Error: ", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="px-4  pt-4 max-w-[720px] size-full max-h-[90vh] flex flex-col">
      <div className="rounded px-4 h-screen overflow-y-scroll bg-white dark:bg-zinc-800">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`my-2 ${
              m.role === "user" ? "text-right" : "text-left"
            }`}>
            <p
              className={`${
                m.role == "user"
                  ? "text-indigo-600"
                  : "text-slate-500 dark:text-gray-400"
              }`}>
              {m.role === "user" ? "You" : "Dianoia"}
            </p>
            {/* <p
              className={`inline-block px-3 py-1 rounded-md ${
                m.role === "user"
                  ? "bg-indigo-600"
                  : "bg-slate-200 text-slate-700 dark:bg-gray-600 dark:text-slate-100"
              }`}>
              {m.content}
            </p> */}
            {m.role === "assistant" ? (
              <div className="bg-slate-100 dark:bg-zinc-700 rounded-md text-zinc-700 p-3">
                <div className="prose dark:prose-invert max-w-none">
                  {/* let's maybe fix image and codeblock */}
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                  }
                </div>
              </div>
            ) : (
              <p className="inline-block px-3 py-1 rounded-md bg-indigo-400 text-indigo-50">
                {m.content}
              </p>
            )}
          </div>
        ))}
        {loading && (
          <div className="mt-2 flex items-center space-x-4">
            <span className="text-sm text-zinc-400 italic">
              Dianoia is thinking
            </span>
            <span className="typing-indicator">
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
              <span className="typing-dot"></span>
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="flex mt-4">
        <input
          className="flex-1 border border-zinc-600 rounded-md p-2 mr-2 text-gray-700 dark:text-gray-200"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
            if (e.key == "Enter") {
              handleSend();
              e.preventDefault();
            }
          }}
          placeholder="Type your message..."
        />
        <button
          onClick={handleSend}
          className="bg-indigo-600 text-white font-bold px-4 py-2 rounded-md hover:bg-indigo-500">
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
