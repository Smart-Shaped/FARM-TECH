import { Key } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const PermissionRequestButton = ({ onClick }) => {
    const { t } = useTranslation('permission');

    return (
        <a
            href='#'
            onClick={onClick}
        >
            <Key size={14} className='me-2'/>
            {t('request_permissions')}
        </a>
    );
};

