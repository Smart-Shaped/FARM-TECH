/**
 * Dashboard Publisher - React 18 app
 * Segue il pattern delle altre farmtech apps
 */
import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { createStore, combineReducers } from 'redux';
import { DashboardPublisherApp } from '../components/dashboard-publisher/DashboardPublisherApp';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';
import '../styles/react-apps.css';

const rootReducer = combineReducers({
    dashboardPublisher: (state = {}, action) => state
});

const store = createStore(rootReducer);

// Funzione per controllare se siamo nella pagina dashboards
const isDashboardPage = () => {
    const hash = window.location.hash;
    // Rimuove il # iniziale e splitta per ? per gestire query params
    const hashPath = hash.replace('#', '').split('?')[0];
    // Controlla se il path è esattamente /dashboards
    return hashPath === '/dashboards';
};

// Funzione per controllare se l'utente ha il permesso uploader
const hasUploaderPermission = () => {
    const user = window.__FARMTECH_USER__;
    const isAdmin = user.is_superuser
    return isAdmin || (user && user.is_authenticated && user.permissions && user.permissions.includes('farmtech.uploader') && user.group_members?.[0]?.role==='manager');
};

// Funzione per mostrare/nascondere il widget nel container principale
const updateWidgetVisibility = () => {
    const container = document.getElementById('farmtech-dashboard-publisher-container');
    if (!container) return;

    const shouldShow = isDashboardPage() && hasUploaderPermission();

    if (shouldShow) {
        container.style.display = 'block';
        console.log('✅ Dashboard Publisher widget visible');
    } else {
        container.style.display = 'none';
        console.log('🔒 Dashboard Publisher widget hidden');
    }
};

// Funzione per inizializzare l'app in un container specifico
const initializeApp = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container || !hasUploaderPermission() ) return false;

    console.log(`📦 Initializing Dashboard Publisher in ${containerId}...`);

    const root = createRoot(container);
    root.render(
        <Provider store={store}>
             <I18nextProvider i18n={i18n}>
                <DashboardPublisherApp />
             </I18nextProvider>
        </Provider>
    );

    console.log(`✅ Dashboard Publisher initialized in ${containerId}`);
    return true;
};

// Funzione per tentare il mount nel topbar con retry
const mountInTopbar = () => {
    const maxAttempts = 50; // 5 secondi (50 * 100ms)
    let attempts = 0;

    const tryMount = setInterval(() => {
        attempts++;
        const topbarContainer = document.getElementById('farmtech-dashboard-publisher-topbar');

        if (topbarContainer) {
            clearInterval(tryMount);
            initializeApp('farmtech-dashboard-publisher-topbar');
        } else if (attempts >= maxAttempts) {
            clearInterval(tryMount);
            console.log('⚠️ Dashboard Publisher topbar placeholder not found after 5s');
        }
    }, 100);
};

document.addEventListener('DOMContentLoaded', function() {
    if (!hasUploaderPermission()) {
        console.log('🔒 User does not have uploader permission, Dashboard Publisher not initialized');
        return;
    }

    // 1. Monta nel container principale (per pagine custom)
    const mainContainerMounted = initializeApp('farmtech-dashboard-publisher-container');

    if (mainContainerMounted) {
        // Controlla visibilità iniziale
        updateWidgetVisibility();
        // Ascolta i cambiamenti di hash per mostrare/nascondere
        window.addEventListener('hashchange', updateWidgetVisibility);
    }

    // 2. Monta nel topbar (per MapStore e altre pagine)
    // Usa un retry perché il topbar potrebbe non essere ancora pronto
    mountInTopbar();
});
