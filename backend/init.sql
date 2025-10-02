-- Fichier: backend/init.sql
-- Script d'initialisation de la base de données

-- Créer la table examples
CREATE TABLE IF NOT EXISTS examples (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Créer un index sur le nom
CREATE INDEX IF NOT EXISTS idx_examples_name ON examples(name);

-- Insérer des données d'exemple
INSERT INTO examples (name, description) VALUES 
    ('Example 1', 'Ceci est le premier exemple'),
    ('Example 2', 'Ceci est le deuxième exemple'),
    ('Example 3', 'Un exemple avec une description plus longue pour tester');

-- Afficher les données insérées
SELECT * FROM examples;