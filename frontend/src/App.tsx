import "./App.css";

import { useEffect, useRef, useState } from "react";
import axios from "axios";
import ChatInput from "./components/ChatInput";
import MessageBubble from "./components/MessageBubble";

type Message = {
  role: "user" | "assistant"
  content: string
};

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleSend = async (prompt: string) => {
    if (!prompt.trim()) return
    const userMessage: Message = { role: "user", content: prompt }
    const newMessages = [...messages, userMessage]
    setLoading(true)
    setMessages(newMessages)

    try {
      const response = await axios.post(`${VITE_API_BASE_URL}/api/v1/chat`, {
        prompt,
        history: newMessages,
      });

      const botMessage: Message = {
        role: "assistant",
        content: response.data.reply,
      };
      setMessages([...newMessages, botMessage])
    } catch (error) {
      console.error("Error:", error)
    } finally {
      setLoading(false)
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  useEffect(() => {
    const handleFocus = () => {
      setTimeout(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" })
      }, 100)
    };

    const textarea = document.querySelector("textarea")
    textarea?.addEventListener("focus", handleFocus)

    return () => {
      textarea?.removeEventListener("focus", handleFocus)
    };
  }, [])

  return (
    <div className="flex h-screen bg-ivory">
      {/* Left pane: Chat */}
      <div className="flex flex-col w-1/2 border-r border-[#CBBFAE]">
        {/* Chat messages */}
        <div className="flex-1 overflow-y-scroll px-4 py-6">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {loading && (
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm text-softsand italic">
                thinking
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
        {/* Input area */}
        <ChatInput onSend={handleSend} />
      </div>

      {/* Right pane: Canvas */}
      <div className="flex-1 p-6 overflow-auto">
        {/* Here you can render propositions and premises */}
        <h2 className="text-xl font-semibold mb-4 text-charcoal">
          (Premises and conclusions go here)
        </h2>
        {/* Example placeholder */}
        <div className="h-full">{/* Your canvas content goes here */}</div>
      </div>
    </div>
  )
}

export default App;
