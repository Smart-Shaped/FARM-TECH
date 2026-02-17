import { createRoot } from 'react-dom/client';
import { I18nextProvider } from 'react-i18next';
import { ChangePasswordApp } from '../components/change-password/ChangePasswordApp';
import i18n from '../i18n/config';
import '../styles/react-apps.css';

document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('farmtech-change-password-container');

    if (container) {
        const root = createRoot(container);
        root.render(
            <I18nextProvider i18n={i18n}>
                <ChangePasswordApp />
            </I18nextProvider>
        );
    }
});
