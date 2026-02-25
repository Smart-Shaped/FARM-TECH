/**
 * Dashboard Publisher App Component
 * Mostra un selettore per pubblicare/unpublicare dashboard
 */
import { useState, useEffect } from "react";
import api from "../../utils/api";

export const DashboardPublisherApp = () => {
  const [dashboards, setDashboards] = useState([]);
  const [publishedDashboard, setPublishedDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Carica la lista delle dashboard e quale è pubblicata
  useEffect(() => {
    loadDashboards();
    window.addEventListener('mapstore:ready',onMapstoreReady)
    return () => {
      window.removeEventListener('mapstore:ready',onMapstoreReady)
    }
  }, []);

  const onMapstoreReady = (e) => {
    const msAPI = e.details
  }

  const publish = async (pk) => {
    await api.patch(`/api/dashboard/${pk}/publish/`);
  };

  const loadDashboards = async () => {
    try {
      setLoading(true);
      setError(null);

      // Carica la lista di tutte le dashboard
      const user = window.__FARMTECH_USER__
      const dashboardsData = await api.get(
        `/api/v2/resources?api_preset=catalog_list&filter%7Bgroup.in%7D=${user.group_members?.[0]?.auth_group_id}&filter%7Bmetadata_only%7D=false&filter%7Bresource_type.in%7D=dashboard`
      );

      const dashboardList = (dashboardsData.resources || [])

      const publishedPk = dashboardList.find((d) => d.is_approved)?.pk;
      setDashboards(dashboardList);


      setPublishedDashboard(publishedPk);
    } catch (err) {
      console.error("Error loading dashboards:", err);
      setError("Errore nel caricamento delle dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handlePublishChange = async (event) => {
    const selectedId = event.target.value;
    const newPublishedId = parseInt(selectedId);

    // Non permettere selezione vuota
    if (!newPublishedId) return;

    try {
      setSaving(true);
      setError(null);

      // Chiama POST /api/published/dashboard con il pk della dashboard selezionata

      await publish(newPublishedId);

      setPublishedDashboard(newPublishedId);

      const dashboardName = dashboards.find(
        (d) => d.pk === newPublishedId
      )?.title;

    } catch (err) {
      console.error("Error publishing dashboard:", err);
      setError("Errore durante la pubblicazione");
      // Ricarica per sincronizzare lo stato
      loadDashboards();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return null;
  }

  if (!dashboards.length) {
    return null;
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: 0,
        flexWrap: "nowrap",
      }}
    >
      <label
        htmlFor="dashboard-select"
        className="dashboard-publisher-label"
        style={{
          margin: 0,
          whiteSpace: "nowrap",
          fontSize: "0.9rem",
          fontWeight: "500",
        }}
      >
        Dashboard:
      </label>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          flex: "1",
          minWidth: 0,
        }}
      >
        <select
          id="dashboard-select"
          className="form-select form-select-sm"
          value={publishedDashboard || ""}
          onChange={handlePublishChange}
          disabled={saving || !dashboards.length}
          style={{
            color: "#000",
            fontWeight: "500",
            minWidth: "120px",
            maxWidth: "200px",
          }}
        >
          {dashboards.map((dashboard) => (
            <option
              key={dashboard.pk}
              value={dashboard.pk}
              style={{
                fontWeight:
                  dashboard.pk === publishedDashboard ? "bold" : "normal",
              }}
            >
              {dashboard.title}
            </option>
          ))}
        </select>
      </div>
      <style>
        {`
        @media (max-width: 768px) {
            .dashboard-publisher-label {
                display: none !important;
            }
            #dashboard-select {
                min-width: 100px !important;
                max-width: 150px !important;
                font-size: 0.85rem !important;
            }
        }     
        `}
      </style>
    </div>
  );
};
