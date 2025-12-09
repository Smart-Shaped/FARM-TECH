import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { createStore, combineReducers } from 'redux';
import { I18nextProvider } from 'react-i18next';
import { PermissionRequestApp } from '../components/permission/PermissionRequestApp';
import i18n from '../i18n/config';
import '../styles/react-apps.css';

const rootReducer = combineReducers({
    permission: (state = {}, action) => state
});

const store = createStore(rootReducer);

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('farmtech-permission-request-container');

    if (container) {
        const root = createRoot(container);
        root.render(
            <Provider store={store}>
                <I18nextProvider i18n={i18n}>
                    <PermissionRequestApp />
                </I18nextProvider>
            </Provider>
        );
    }
});
