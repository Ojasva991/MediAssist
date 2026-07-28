import { useState, useRef, useCallback, useEffect } from "react";

/**
 * Wraps the browser's built-in SpeechRecognition API (client-side only,
 * no backend call, no new dependency). Support varies by browser -
 * Chrome/Edge/Safari (recent versions) support it, Firefox largely
 * doesn't as of this writing. Always feature-detect via
 * `isSupported` before showing a mic button - there is no server-side
 * fallback for unsupported browsers, since that would need a real
 * speech-to-text API/service, a different (and bigger) feature.
 *
 * Usage:
 *   const { isSupported, isListening, start, stop } = useVoiceInput({
 *     onResult: (transcript) => setSymptoms((prev) => `${prev} ${transcript}`.trim()),
 *   });
 */
export function useVoiceInput({ onResult, lang = "en-US" } = {}) {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  const SpeechRecognitionCtor =
    typeof window !== "undefined"
      ? window.SpeechRecognition || window.webkitSpeechRecognition
      : null;
  const isSupported = !!SpeechRecognitionCtor;

  useEffect(() => {
    return () => {
      recognitionRef.current?.stop();
    };
  }, []);

  const start = useCallback(() => {
    if (!isSupported) {
      setError("Voice input isn't supported in this browser.");
      return;
    }
    setError(null);
    const recognition = new SpeechRecognitionCtor();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join(" ");
      onResult?.(transcript);
    };
    recognition.onerror = (event) => {
      setError(
        event.error === "not-allowed"
          ? "Microphone permission was denied."
          : "Couldn't hear that. Please try again."
      );
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }, [SpeechRecognitionCtor, isSupported, lang, onResult]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setIsListening(false);
  }, []);

  return { isSupported, isListening, error, start, stop };
}
