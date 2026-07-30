import { useState, useEffect } from "react";

/**
 * Tracks browser connectivity via the native online/offline events.
 *
 * Note the honest limitation: navigator.onLine only reflects whether
 * the device has a network interface that's "up" (e.g. connected to
 * Wi-Fi) - it does NOT guarantee actual internet reachability (a
 * Wi-Fi network with no real internet access still reports online).
 * Good enough to decide whether to attempt a network call and show a
 * sensible message, not a guarantee the call will succeed.
 */
export function useOnlineStatus() {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return isOnline;
}
