import { useState, useRef, useEffect } from "react";
import { Send, AlertTriangle, MessageCircleQuestion } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { askFollowUp } from "@/api/analysis";
import { ROUTES } from "@/constants/routes";
import { Link } from "react-router-dom";

/**
 * Chat thread for asking follow-up questions about an analysis.
 *
 * Stateless on the backend (see app/models/followup.py) - this
 * component is the only place the conversation is held, in plain React
 * state. Refreshing the page loses the thread; that's a known,
 * deliberate first-version limitation, not a bug.
 */
export function FollowUpChat({ originalSymptoms }) {
  const [messages, setMessages] = useState([]); // [{role, content, escalation?}]
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const conversationForApi = messages.map((m) => ({ role: m.role, content: m.content }));
    const nextMessages = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    setIsSending(true);
    setError(null);

    try {
      const response = await askFollowUp({
        originalSymptoms,
        conversation: conversationForApi,
        message: trimmed,
      });
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: response.reply,
          escalation: response.escalation_detected,
          sosRecommended: response.sos_recommended,
        },
      ]);
    } catch (err) {
      setError(err.message || "Couldn't send that message. Please try again.");
    } finally {
      setIsSending(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <MessageCircleQuestion className="size-4 text-primary" /> Ask a follow-up
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-ink-faint">
            Ask something like "why is this serious?" or "what if I also have a fever?"
          </p>
        )}

        <div className="max-h-80 space-y-3 overflow-y-auto">
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
              <div
                className={`inline-block max-w-[85%] rounded-[var(--radius-control)] px-3 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-primary-light text-primary-dark"
                    : m.escalation
                      ? "bg-danger-light text-danger"
                      : "bg-[var(--color-mist)] text-ink"
                }`}
              >
                {m.escalation && (
                  <div className="mb-1 flex items-center gap-1.5 font-semibold">
                    <AlertTriangle className="size-3.5" /> This sounds more urgent
                  </div>
                )}
                {m.content}
                {m.sosRecommended && (
                  <div className="mt-2">
                    <Link
                      to={ROUTES.SOS}
                      className="inline-block rounded-full bg-danger px-3 py-1 text-xs font-semibold text-white hover:bg-danger-dark"
                    >
                      Go to SOS →
                    </Link>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={scrollRef} />
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a follow-up question..."
            rows={1}
            className="flex-1 resize-none rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-sm"
          />
          <Button onClick={handleSend} disabled={isSending || !input.trim()}>
            {isSending ? <Spinner size={16} /> : <Send className="size-4" />}
          </Button>
        </div>

        <p className="text-xs text-ink-faint">
          This chat doesn't remember anything after you leave the page. The same rule-based
          safety checks from your original analysis apply here too - though those checks
          currently only recognize English wording, so if you're chatting in another language and
          anything feels urgent, use the SOS page directly rather than waiting for a reply.
        </p>
      </CardContent>
    </Card>
  );
}
