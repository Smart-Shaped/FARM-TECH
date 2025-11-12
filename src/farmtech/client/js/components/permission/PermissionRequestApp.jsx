import  { useState } from 'react';
import {PermissionRequestButton} from './PermissionRequestButton';
import {PermissionRequestDialog} from './PermissionRequestDialog';

export const PermissionRequestApp = () => {
    const [showDialog, setShowDialog] = useState(false);

    return (
        <>
            <PermissionRequestButton onClick={() => setShowDialog(true)} />
            {showDialog && (
                <PermissionRequestDialog
                    onClose={() => setShowDialog(false)}
                />
            )}
        </>
    );
};
