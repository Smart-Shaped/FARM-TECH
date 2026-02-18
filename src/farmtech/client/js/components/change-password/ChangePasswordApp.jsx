import { useState } from 'react';
import { ChangePasswordButton } from './ChangePasswordButton';
import { ChangePasswordDialog } from './ChangePasswordDialog';

export const ChangePasswordApp = () => {
    const [showDialog, setShowDialog] = useState(false);

    return (
        <>
            <ChangePasswordButton onClick={() => setShowDialog(true)} />
            {showDialog && (
                <ChangePasswordDialog
                    onClose={() => setShowDialog(false)}
                />
            )}
        </>
    );
};
