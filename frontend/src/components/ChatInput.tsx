import React, { useState, useRef, useEffect } from "react";
import { ArrowUpIcon } from "@heroicons/react/24/outline";

function ChatInput({ onSend }: { onSend: (message: string) => void }) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Automatically resize the textarea height
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${textarea.scrollHeight}px`;
    }
  }, [input]);

  // Handle Enter/Shift+Enter
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() !== "") {
        onSend(input.trim());
        setInput("");
      }
    }
  };

  return (
    <div className="sticky bottom-0 left-0 w-full border-t border-softsand p-4">
      <div className="relative flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          rows={1}
          className="w-full resize-none overflow-auto rounded-md border border-softsand px-3 py-2 text-sm text-charcoal placeholder-softsand focus:outline-none"
        />
        <button
          onClick={() => {
            if (input.trim()) {
              onSend(input.trim());
              setInput("");
            }
          }}
          className="shrink-0 rounded-full bg-sagegreen px-4 py-2 text-sm font-medium text-white">
          <ArrowUpIcon className="h-5 w-5 transform" />
        </button>
      </div>
    </div>
  );
}

export default ChatInput;
