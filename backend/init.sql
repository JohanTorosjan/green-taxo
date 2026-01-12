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
    used BOOLEAN DEFAULT FALSE,
    
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

CREATE TABLE IF NOT EXISTS criterias (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    nom VARCHAR(255),
    description TEXT,
    coefficient INTEGER,
    data JSONB,
    used BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);



CREATE TABLE IF NOT EXISTS analysis (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    doc_date DATE NOT NULL,
    file_data BYTEA NOT NULL,
    
    -- Champs pour l'analyse LLM
    analysis_status VARCHAR(50) DEFAULT 'pending',
    company VARCHAR(255),
    task_id VARCHAR(255),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE analysis ADD COLUMN IF NOT EXISTS calculation_model JSONB DEFAULT NULL, ADD COLUMN IF NOT EXISTS score FLOAT DEFAULT NULL, ADD COLUMN IF NOT EXISTS analysis_results JSONB DEFAULT NULL;

-- ⚠️ VERSION NON SÉCURISÉE - À ÉVITER ⚠️
-- Cette version stocke les mots de passe en clair
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,  -- ⚠️ Mot de passe en clair
    admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Index sur l'email pour les recherches rapides
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Trigger pour mettre à jour automatiquement updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Modifier la table analysis pour ajouter la relation avec users
ALTER TABLE analysis 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;

-- Index sur user_id pour les jointures
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis(user_id);

-- Créer un utilisateur admin par défaut
INSERT INTO users (nom, prenom, email, password, admin) 
VALUES ('Admin', 'Système', 'a@a.a', 'a', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (nom, prenom, email, password, admin) 
VALUES ('client', 'c', 'c@c.c', 'c', FALSE)
ON CONFLICT (email) DO NOTHING;