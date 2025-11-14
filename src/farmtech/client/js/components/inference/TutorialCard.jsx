export const TutorialCard = ({ Icon, title, description }) => {
  return (
    <div className="tutorial-card-item">
      <div className="card h-100 border-primary shadow-sm">
        <div className="card-body d-flex flex-column gap-3">
          <div className="d-flex gap-2">
            <div
              className="tutorial-icon text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0"
              style={{
                background:
                  "linear-gradient(135deg, var(--gn-primary-dark, #2e5f7d) 0%, var(--gn-primary, #397aab) 100%)",
              }}
            >
              <Icon className="tutorial-icon-svg" />
            </div>
            <div className="tutorial-title mb-2 fw-bold">{title}</div>
          </div>
          <p className="tutorial-desc text-muted mb-0">{description}</p>
        </div>
      </div>
    </div>
  );
};
