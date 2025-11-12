import { createRoot } from 'react-dom/client';
import { Provider } from 'react-redux';
import { createStore, combineReducers } from 'redux';
import { I18nextProvider } from 'react-i18next';
import i18n from '../i18n/config';
import '../styles/react-apps.css';
import {InferenceApp} from '../components/inference/InferenceApp';

const rootReducer = combineReducers({
    inference: (state = {}, action) => state
});

const store = createStore(rootReducer);

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('farmtech-inference-container');

    if (container) {
        const hasPermission = container.dataset.hasPermission === 'true';

        const root = createRoot(container);
        root.render(
            <Provider store={store}>
                <I18nextProvider i18n={i18n}>
                    <InferenceApp hasPermission={hasPermission} />
                </I18nextProvider>
            </Provider>
        );
    }
});
