import { useEffect } from "react";
import { useLocation, useNavigationType } from "react-router-dom";

/** Scrolls to the top on navigation (but not on back/forward). */
export default function ScrollToTop() {
  const { pathname } = useLocation();
  const navigationType = useNavigationType();

  useEffect(() => {
    if (navigationType === "POP") return;
    window.scrollTo({ top: 0, left: 0 });
  }, [pathname, navigationType]);

  return null;
}
