import { useCallback, useState } from "react";

/**
 * Wraps an async API call with loading / error / data state.
 *
 * const { run, data, error, isLoading } = useApi(analyzeSymptoms);
 * await run(payload);
 */
export function useApi(apiFn) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const run = useCallback(
    async (...args) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await apiFn(...args);
        setData(result);
        return result;
      } catch (err) {
        setError(err.message ? err : { message: "Something went wrong. Please try again." });
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [apiFn]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return { run, data, error, isLoading, reset };
}
