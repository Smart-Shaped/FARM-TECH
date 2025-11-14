import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { createStore, combineReducers } from 'redux';
import { I18nextProvider } from 'react-i18next';
import { IndexApp } from '../components/index/IndexApp';
import i18n from '../i18n/config';
import '../styles/react-apps.css';

const rootReducer = combineReducers({
    index: (state = {}, action) => state
});

const store = createStore(rootReducer);

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('farmtech-index-container');

    if (container) {
        const staticUrl = window.STATIC_URL || '/static/';

        const root = createRoot(container);
        root.render(
            <Provider store={store}>
                <I18nextProvider i18n={i18n}>
                    <IndexApp staticUrl={staticUrl} />
                </I18nextProvider>
            </Provider>
        );
    }
});
