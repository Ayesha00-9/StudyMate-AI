// Flashcards made from the uploaded study material.
// Buttons: Previous, Flip, Next.

import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { useState } from "react";

import { getFlashcards, readError } from "../services/api.js";

export default function FlashcardDeck({ subjectId }) {
  const [cards, setCards] = useState([]);
  const [sources, setSources] = useState([]);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    setLoading(true);
    setError("");
    try {
      const response = await getFlashcards(subjectId, 8);
      setCards(response.data.cards);
      setSources(response.data.sources);
      setIndex(0);
      setFlipped(false);
    } catch (err) {
      setError(readError(err));
    } finally {
      setLoading(false);
    }
  }

  function goTo(newIndex) {
    setIndex(newIndex);
    setFlipped(false); // always show the front of a new card
  }

  if (cards.length === 0) {
    return (
      <div className="glass study-panel">
        <h3>Flashcards</h3>
        <p className="muted">
          Quick question-and-answer cards made from your uploaded study material.
        </p>
        {error && <div className="alert">{error}</div>}
        <button className="btn btn-primary" onClick={handleGenerate} disabled={loading}>
          {loading ? "Making cards..." : "Generate Flashcards"}
        </button>
      </div>
    );
  }

  const card = cards[index];

  return (
    <div className="glass study-panel">
      <div className="study-panel-head">
        <h3>Flashcards</h3>
        <span className="badge">
          Card {index + 1} of {cards.length}
        </span>
      </div>

      {sources.length > 0 && (
        <p className="rag-note">Based on your uploaded study material: {sources.join(", ")}</p>
      )}

      {/* Errors must also show here, not only on the first screen,
          otherwise "New set of cards" could fail silently. */}
      {error && <div className="alert">{error}</div>}

      {/* Clicking the card flips it too */}
      <div className="flashcard" onClick={() => setFlipped(!flipped)}>
        <div className="flashcard-side">{flipped ? "Back" : "Front"}</div>
        <div className="flashcard-text">{flipped ? card.back : card.front}</div>
        <div className="flashcard-hint">Click the card or press Flip</div>
      </div>

      <div className="flashcard-controls">
        <button
          className="btn btn-ghost"
          onClick={() => goTo(index - 1)}
          disabled={index === 0}
        >
          <ChevronLeft size={16} /> Previous
        </button>

        <button className="btn btn-primary" onClick={() => setFlipped(!flipped)}>
          <RefreshCw size={15} /> Flip
        </button>

        <button
          className="btn btn-ghost"
          onClick={() => goTo(index + 1)}
          disabled={index === cards.length - 1}
        >
          Next <ChevronRight size={16} />
        </button>
      </div>

      <button className="btn btn-ghost btn-sm" onClick={handleGenerate} disabled={loading}>
        {loading ? "Making cards..." : "New set of cards"}
      </button>
    </div>
  );
}
