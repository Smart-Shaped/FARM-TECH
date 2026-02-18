import { Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ChangePasswordButton = ({ onClick }) => {
    const { t } = useTranslation('changePassword');

    return (
        <a
            href='#'
            onClick={onClick}
        >
            <Lock size={14} className='me-2'/>
            {t('change_password')}
        </a>
    );
};
