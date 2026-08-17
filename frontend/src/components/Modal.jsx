// A simple reusable popup used for "New Subject" and delete confirmations.

export default function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      {/* stopPropagation keeps a click inside the box from closing it */}
      <div className="glass modal" onClick={(event) => event.stopPropagation()}>
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  );
}
