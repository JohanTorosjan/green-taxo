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

-- VRAI DB : 

-- Créer la table documents avec les champs d'analyse
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    doc_date DATE NOT NULL,
    file_data BYTEA NOT NULL,
    
    -- Champs pour l'analyse LLM
    analysis_status VARCHAR(50) DEFAULT 'pending',
    extracted_text TEXT,
    analysis_results TEXT,
    task_id VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Créer des index pour les performances
CREATE INDEX IF NOT EXISTS idx_documents_analysis_status ON documents(analysis_status);
CREATE INDEX IF NOT EXISTS idx_documents_task_id ON documents(task_id);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);

-- Mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
CREATE TRIGGER update_documents_updated_at
BEFORE UPDATE ON documents
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();