// "Continue with Google" and "Continue with Facebook" buttons.
//
// How it works:
//   1. Google / Facebook show their own login window in the browser.
//   2. They give us a token.
//   3. We send ONLY that token to our FastAPI backend.
//   4. The backend checks the token with the provider and returns OUR JWT.
//
// Only the public client id / app id is used here.
// The client secrets stay on the backend.
//
// If the ids are not set in frontend/.env, the buttons are hidden and normal
// email/password login keeps working. In development we print one line in the
// browser console explaining why, so a missing setting is never a silent mystery.

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginWithFacebook, loginWithGoogle, readError } from "../services/api.js";
import { saveSession } from "../services/auth.js";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const FACEBOOK_APP_ID = import.meta.env.VITE_FACEBOOK_APP_ID || "";

// Which Facebook Graph API version the JS SDK should use.
// Check https://developers.facebook.com/docs/graph-api/changelog/versions
// and bump this when the version is retired.
const FACEBOOK_SDK_VERSION = "v23.0";

const GOOGLE_SCRIPT = "https://accounts.google.com/gsi/client";
const FACEBOOK_SCRIPT = "https://connect.facebook.net/en_US/sdk.js";

/**
 * Add a <script> tag to the page once, and call onReady when it has FINISHED
 * loading. If another component already started the same script we wait for
 * that one instead of assuming it is ready - otherwise the second page to use
 * this component would render nothing.
 */
function loadScript(source, onReady) {
  const existing = document.querySelector(`script[src="${source}"]`);

  if (existing) {
    if (existing.dataset.loaded === "true") {
      onReady();
    } else {
      existing.addEventListener("load", onReady);
    }
    return;
  }

  const script = document.createElement("script");
  script.src = source;
  script.async = true;
  script.addEventListener("load", () => {
    script.dataset.loaded = "true";
    onReady();
  });
  script.addEventListener("error", () => {
    console.error(`StudyMate: could not load ${source} (offline or blocked?)`);
  });
  document.body.appendChild(script);
}

export default function SocialLogin() {
  const navigate = useNavigate();
  const googleButtonRef = useRef(null);
  const [error, setError] = useState("");

  // Save our JWT and go to the dashboard.
  function finishLogin(response) {
    saveSession(response.data.access_token, response.data.user);
    navigate("/dashboard");
  }

  // ---- Google ----
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    loadScript(GOOGLE_SCRIPT, () => {
      // The component may have been removed from the screen while we waited.
      if (!window.google || !googleButtonRef.current) return;

      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (googleResponse) => {
          try {
            // googleResponse.credential is the ID token.
            finishLogin(await loginWithGoogle(googleResponse.credential));
          } catch (err) {
            setError(readError(err));
          }
        },
      });

      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: "filled_black",
        size: "large",
        width: 320,
        text: "continue_with",
        shape: "pill",
      });
    });
  }, []);

  // ---- Facebook ----
  useEffect(() => {
    if (!FACEBOOK_APP_ID) return;

    loadScript(FACEBOOK_SCRIPT, () => {
      if (window.FB) {
        window.FB.init({ appId: FACEBOOK_APP_ID, version: FACEBOOK_SDK_VERSION });
      }
    });
  }, []);

  // ---- Development hint ----
  useEffect(() => {
    if (import.meta.env.DEV && !GOOGLE_CLIENT_ID && !FACEBOOK_APP_ID) {
      console.info(
        "StudyMate: social login buttons are hidden because VITE_GOOGLE_CLIENT_ID " +
          "and VITE_FACEBOOK_APP_ID are empty in frontend/.env. " +
          "Add them and restart 'npm run dev' to show the buttons."
      );
    }
  }, []);

  async function completeFacebookLogin(accessToken) {
    try {
      finishLogin(await loginWithFacebook(accessToken));
    } catch (err) {
      setError(readError(err));
    }
  }

  function handleFacebookClick() {
    if (!window.FB) {
      setError("Facebook login is still loading, please try again.");
      return;
    }
    // Facebook's SDK only accepts a plain (non-async) function here - passing
    // an async function directly makes the SDK throw internally. So we keep
    // this callback synchronous and do the async work in a helper below.
    window.FB.login(
      (fbResponse) => {
        if (!fbResponse.authResponse) return; // the user closed the popup
        completeFacebookLogin(fbResponse.authResponse.accessToken);
      },
      { scope: "public_profile,email" }
    );
  }

  // Nothing configured -> show nothing at all.
  if (!GOOGLE_CLIENT_ID && !FACEBOOK_APP_ID) return null;

  return (
    <div className="social-login">
      <div className="social-divider">
        <span>or continue with</span>
      </div>

      {error && <div className="alert">{error}</div>}

      {GOOGLE_CLIENT_ID && <div ref={googleButtonRef} className="google-button" />}

      {FACEBOOK_APP_ID && (
        <button
          type="button"
          className="btn btn-facebook btn-block"
          onClick={handleFacebookClick}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor">
            <path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.96.93-1.96 1.89v2.25h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07z" />
          </svg>
          Continue with Facebook
        </button>
      )}
    </div>
  );
}
