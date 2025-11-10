INSERT INTO auth_group (name) VALUES ('experiment_4_group');

INSERT INTO experiments (name, email, "startDate", "endDate", owner, "group") 
VALUES ('experiment_4', 'email4@gmail.com', '2025-10-01', '2025-10-31', 
    (SELECT id FROM auth_user WHERE username = 'admin'), 
    (SELECT id FROM auth_group WHERE name = 'experiment_4_group')
);

INSERT INTO dataset_experiments (layer_dataset, experiment, model_package) 
VALUES (1, 
    (SELECT id FROM experiments WHERE name = 'Azione 4'), 
    'farmtech.models.Experiment4');

INSERT INTO dataset_experiments (layer_dataset, experiment, model_package) 
VALUES (4, 
    (SELECT id FROM experiments WHERE name = 'Azione 3'), 
    'farmtech.models.Experiment3');
